"""
Set Barge-In Tool - Enable or disable barge-in for the current call phase.

Allows the AI to lock/unlock barge-in mid-call so that critical speech
segments (e.g. debt-collection disclosures, legal notices) cannot be
interrupted by the caller.

Usage pattern:
1. Call set_barge_in(enabled=False) before the critical segment.
2. Speak the critical content.
3. Call set_barge_in(enabled=True) to restore normal interruption behaviour.

This is a per-call, runtime-only setting.  It does NOT affect the global
barge_in.enabled config flag, and resets automatically when the call ends.
"""

from typing import Dict, Any
from src.tools.base import Tool, ToolDefinition, ToolParameter, ToolCategory
from src.tools.context import ToolExecutionContext
import structlog

logger = structlog.get_logger(__name__)


class SetBargeInTool(Tool):
    """
    Enable or disable barge-in for the current call phase.

    Use when:
    - You are about to speak a critical segment that must not be interrupted
      (e.g. legal disclosure, debt-collection demand, safety instruction).
    - You have finished the critical segment and want to allow the caller to
      speak again.

    Always re-enable barge-in after the critical segment completes.
    """

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="set_barge_in",
            description=(
                "Enable or disable the caller's ability to interrupt you mid-speech. "
                "Set enabled=false before a critical segment (e.g. debt-collection notice) "
                "so the caller cannot cut you off. Set enabled=true again immediately after "
                "the segment finishes to restore normal conversation flow."
            ),
            category=ToolCategory.TELEPHONY,
            requires_channel=True,
            max_execution_time=2,
            parameters=[
                ToolParameter(
                    name="enabled",
                    type="boolean",
                    description=(
                        "True to allow the caller to interrupt (default behaviour). "
                        "False to block barge-in during a critical speech phase."
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="reason",
                    type="string",
                    description=(
                        "Short label for why barge-in is being toggled "
                        "(e.g. 'debt_collection_disclosure', 'legal_notice'). "
                        "Used only for logging; not spoken aloud."
                    ),
                    required=False,
                ),
            ],
        )

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ToolExecutionContext,
    ) -> Dict[str, Any]:
        """
        Toggle per-call barge-in on or off.

        Args:
            parameters:
                enabled (bool): Whether barge-in should be active.
                reason  (str):  Optional label for log tracing.
            context: Tool execution context.

        Returns:
            {
                status:          "success" | "error",
                barge_in_enabled: bool,
                message:         str,
            }
        """
        enabled = parameters.get("enabled")
        if not isinstance(enabled, bool):
            return {
                "status": "error",
                "message": "Parameter 'enabled' must be a boolean (true or false).",
            }

        reason = str(parameters.get("reason") or "").strip() or "not_specified"

        try:
            await context.update_session(barge_in_enabled=enabled)

            logger.info(
                "🎙️ Barge-in toggled by tool",
                call_id=context.call_id,
                barge_in_enabled=enabled,
                reason=reason,
            )

            state_label = "ENABLED" if enabled else "DISABLED"
            return {
                "status": "success",
                "barge_in_enabled": enabled,
                "message": f"Barge-in {state_label} (reason: {reason}).",
            }

        except Exception as exc:
            logger.error(
                "set_barge_in tool failed",
                call_id=context.call_id,
                error=str(exc),
                exc_info=True,
            )
            return {
                "status": "error",
                "message": f"Failed to update barge-in state: {exc}",
            }
