"""Source API Views"""
from typing import Iterable

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer, TypeCreateSerializer
from authentik.core.models import Source, UserSourceConnection
from authentik.core.types import UserSettingSerializer
from authentik.lib.utils.reflection import all_subclasses
from authentik.policies.engine import PolicyEngine

LOGGER = get_logger()


class SourceSerializer(ModelSerializer, MetaNameSerializer):
    """Source Serializer"""

    component = SerializerMethodField()

    def get_component(self, obj: Source) -> str:
        """Get object component so that we know how to edit the object"""
        # pyright: reportGeneralTypeIssues=false
        if obj.__class__ == Source:
            return ""
        return obj.component

    class Meta:

        model = Source
        fields = [
            "pk",
            "name",
            "slug",
            "enabled",
            "authentication_flow",
            "enrollment_flow",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
            "policy_engine_mode",
            "user_matching_mode",
        ]


class SourceViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Source Viewset"""

    queryset = Source.objects.none()
    serializer_class = SourceSerializer
    lookup_field = "slug"

    def get_queryset(self):  # pragma: no cover
        return Source.objects.select_subclasses()

    @extend_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def types(self, request: Request) -> Response:
        """Get all creatable source types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            subclass: Source
            component = ""
            if len(subclass.__subclasses__()) > 0:
                continue
            if subclass._meta.abstract:
                component = subclass.__bases__[0]().component
            else:
                component = subclass().component
            # pyright: reportGeneralTypeIssues=false
            data.append(
                {
                    "name": subclass._meta.verbose_name,
                    "description": subclass.__doc__,
                    "component": component,
                    "model_name": subclass._meta.model_name,
                }
            )
        return Response(TypeCreateSerializer(data, many=True).data)

    @extend_schema(responses={200: UserSettingSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def user_settings(self, request: Request) -> Response:
        """Get all sources the user can configure"""
        _all_sources: Iterable[Source] = (
            Source.objects.filter(enabled=True).select_subclasses().order_by("name")
        )
        matching_sources: list[UserSettingSerializer] = []
        for source in _all_sources:
            user_settings = source.ui_user_settings
            if not user_settings:
                continue
            policy_engine = PolicyEngine(source, request.user, request)
            policy_engine.build()
            if not policy_engine.passing:
                continue
            source_settings = source.ui_user_settings
            source_settings.initial_data["object_uid"] = source.slug
            if not source_settings.is_valid():
                LOGGER.warning(source_settings.errors)
            matching_sources.append(source_settings.validated_data)
        return Response(matching_sources)


class UserSourceConnectionSerializer(SourceSerializer):
    """OAuth Source Serializer"""

    source = SourceSerializer(read_only=True)

    class Meta:
        model = UserSourceConnection
        fields = [
            "pk",
            "user",
            "source",
            "created",
        ]
        extra_kwargs = {
            "user": {"read_only": True},
            "created": {"read_only": True},
        }


class UserSourceConnectionViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """User-source connection Viewset"""

    queryset = UserSourceConnection.objects.all()
    serializer_class = UserSourceConnectionSerializer
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering = ["pk"]
