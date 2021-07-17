"""Radius Provider"""
from typing import Optional, Type

from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework.serializers import Serializer

from authentik.core.models import Provider
from authentik.crypto.models import CertificateKeyPair
from authentik.outposts.models import OutpostModel


class RadiusProvider(OutpostModel, Provider):
    """Allow applications to authenticate against authentik's users using Radius."""

    client_networks = models.TextField(
        default="0.0.0.0/0",
        help_text=_(
            "List of CIDRs (comma-seperated) that clients can connect from. A more specific "
            "CIDR will match before a looser one. Clients connecting from a non-specified CIDR "
            "will be dropped."
        ),
    )

    certificate = models.ForeignKey(
        CertificateKeyPair,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    @property
    def launch_url(self) -> Optional[str]:
        """Radius never has a launch URL"""
        return None

    @property
    def component(self) -> str:
        return "ak-provider-radius-form"

    @property
    def serializer(self) -> Type[Serializer]:
        from authentik.providers.radius.api import RadiusProviderSerializer

        return RadiusProviderSerializer

    def __str__(self):
        return f"Radius Provider {self.name}"

    class Meta:

        verbose_name = _("Radius Provider")
        verbose_name_plural = _("Radius Providers")
