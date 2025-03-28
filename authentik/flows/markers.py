"""Stage Markers"""
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from django.http.request import HttpRequest
from structlog.stdlib import get_logger

from authentik.flows.models import FlowStageBinding
from authentik.policies.engine import PolicyEngine
from authentik.policies.models import PolicyBinding

if TYPE_CHECKING:
    from authentik.flows.planner import FlowPlan

LOGGER = get_logger()


@dataclass
class StageMarker:
    """Base stage marker class, no extra attributes, and has no special handler."""

    # pylint: disable=unused-argument
    def process(
        self,
        plan: "FlowPlan",
        binding: FlowStageBinding,
        http_request: HttpRequest,
    ) -> Optional[FlowStageBinding]:
        """Process callback for this marker. This should be overridden by sub-classes.
        If a stage should be removed, return None."""
        return binding


@dataclass
class ReevaluateMarker(StageMarker):
    """Reevaluate Marker, forces stage's policies to be evaluated again."""

    binding: PolicyBinding

    def process(
        self,
        plan: "FlowPlan",
        binding: FlowStageBinding,
        http_request: HttpRequest,
    ) -> Optional[FlowStageBinding]:
        """Re-evaluate policies bound to stage, and if they fail, remove from plan"""
        from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER

        LOGGER.debug(
            "f(plan_inst)[re-eval marker]: running re-evaluation",
            binding=binding,
            policy_binding=self.binding,
        )
        engine = PolicyEngine(
            self.binding, plan.context.get(PLAN_CONTEXT_PENDING_USER, http_request.user)
        )
        engine.use_cache = False
        engine.request.set_http_request(http_request)
        engine.request.context = plan.context
        engine.build()
        result = engine.result
        if result.passing:
            return binding
        LOGGER.warning(
            "f(plan_inst)[re-eval marker]: binding failed re-evaluation",
            binding=binding,
            messages=result.messages,
        )
        return None
