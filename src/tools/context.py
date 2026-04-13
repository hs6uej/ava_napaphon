"""
Tool execution context - provides access to system resources during tool execution.

Includes:
- ToolExecutionContext: For in-call tool execution (existing)
- PreCallContext: For pre-call tools (CRM lookup, enrichment)
- PostCallContext: For post-call tools (webhooks, CRM updates)
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionContext:
    """
    Context provided to tools during execution.
    
    Contains all information and system access needed for a tool to execute,
    including call metadata, session state, and system clients (ARI, etc.).
    """
    
    # Call information
    call_id: str
    caller_channel_id: Optional[str] = None
    bridge_id: Optional[str] = None
    caller_number: Optional[str] = None   # CALLERID(num) - caller's phone number
    called_number: Optional[str] = None   # DIALED_NUMBER or __FROM_DID - the number that was dialed
    caller_name: Optional[str] = None     # CALLERID(name) for personalization
    session_id: Optional[str] = None      # SESSION_ID for correlating with tools and providers
    globals_asterisk_instance: Optional[str] = None  # GLOBALS_ASTERISK_INSTANCE 
    call_metadata: Dict[str, Any] = None  # Arbitrary call metadata for tools and providers (e.g. CRM data, ATIS info, etc.)
    context_name: Optional[str] = None    # AI_CONTEXT from dialplan
    
    # System access (injected by provider)
    session_store: Any = None  # SessionStore instance
    ari_client: Any = None      # ARIClient instance
    config: Any = None           # Config dict
    
    # Provider information
    provider_name: str = None  # "deepgram", "openai_realtime", "custom_pipeline"
    provider_session: Any = None
    
    # Request metadata
    user_input: Optional[str] = None  # Original user utterance
    detected_intent: Optional[str] = None
    confidence: Optional[float] = None
    
    async def get_session(self):
        """
        Get current call session from session store.
        
        Returns:
            Session object with call state
        
        Raises:
            RuntimeError: If session not found
        """
        if not self.session_store:
            raise RuntimeError("SessionStore not available in context")
        
        session = await self.session_store.get_by_call_id(self.call_id)
        if not session:
            raise RuntimeError(f"Session not found for call_id: {self.call_id}")
        
        return session
    
    async def update_session(self, **kwargs):
        """
        Update call session with new attributes.
        
        Args:
            **kwargs: Attributes to update on session
        
        Example:
            await context.update_session(
                transfer_active=True,
                transfer_target="2765"
            )
        """
        if not self.session_store:
            raise RuntimeError("SessionStore not available in context")
        
        session = await self.get_session()
        
        for key, value in kwargs.items():
            setattr(session, key, value)
        
        await self.session_store.upsert_call(session)
        logger.debug(f"Updated session {self.call_id}: {kwargs}")
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Config key (supports dot notation, e.g., "tools.transfer.destinations.support_agent.target")
            default: Default value if key not found
        
        Returns:
            Config value or default
        """
        if not self.config:
            return default
        
        # Support dot notation for nested keys
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


@dataclass
class PreCallContext:
    """
    Context provided to pre-call tools.
    
    Pre-call tools run after the call is answered but before the AI speaks.
    They fetch enrichment data (e.g., CRM lookup) to inject into prompts.
    """
    
    # Call identifiers
    call_id: str
    caller_number: str  # ANI (caller's phone number)
    called_number: Optional[str] = None  # DID that was called
    caller_name: Optional[str] = None  # Caller ID name if available
    session_id: Optional[str] = None  # Session ID if session already exists at this point
    globals_asterisk_instance: Optional[str] = None  # GLOBALS_ASTERISK_INSTANCE 
    
    # Context information
    context_name: str = ""  # AI_CONTEXT from dialplan
    call_direction: str = "inbound"  # "inbound" or "outbound"
    
    # Outbound-specific (from campaign dialer)
    campaign_id: Optional[str] = None
    lead_id: Optional[str] = None
    
    # Channel variables from Asterisk
    channel_vars: Dict[str, str] = field(default_factory=dict)
    
    # Arbitrary call metadata for tools and providers (e.g. CRM data, ATIS info, etc.)
    call_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # System access
    config: Any = None  # Config dict
    ari_client: Any = None  # ARIClient instance (for hold audio playback)
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        if not self.config:
            return default
        
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value


@dataclass
class PostCallContext:
    """
    Context provided to post-call tools.
    
    Post-call tools run after the call ends (fire-and-forget).
    They receive comprehensive session data for webhooks, CRM updates, etc.
    """
    
    # Call identifiers
    call_id: str
    caller_number: str  # ANI
    called_number: Optional[str] = None  # DID
    caller_name: Optional[str] = None
    session_id: Optional[str] = None  # Session ID if session already exists at this point
    globals_asterisk_instance: Optional[str] = None  # GLOBALS_ASTERISK_INSTANCE 
        
    # Context and provider
    context_name: str = ""
    provider: str = ""  # Provider used for the call
    call_direction: str = "inbound"
    
    # Call metrics
    call_duration_seconds: int = 0
    call_outcome: str = ""  # e.g., "answered_human", "voicemail", "no_answer"
    call_start_time: Optional[str] = None  # ISO timestamp
    call_end_time: Optional[str] = None  # ISO timestamp
    session_id: Optional[str] = None  # SESSION_ID for correlating with tools and providers
    globals_asterisk_instance: Optional[str] = None  # GLOBALS_ASTERISK_INSTANCE
    
    # Conversation data
    conversation_history: List[Dict[str, str]] = field(default_factory=list)  # Transcript
    summary: Optional[str] = None  # AI-generated summary if available
    
    # Tool execution data
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # In-call tool executions
    pre_call_results: Dict[str, str] = field(default_factory=dict)  # Data from pre-call tools
    
    # Outbound-specific
    campaign_id: Optional[str] = None
    lead_id: Optional[str] = None

    # Provider usage/token summary (e.g. Google Gemini Live) — field: usageMetadataSummary
    # promptTokenCount/totalTokenCount = latest; total_candidates_token_count = accumulated sum.
    # usage_metadata_summary: Dict[str, Any] = field(default_factory=dict)
    # # Raw usageMetadata snapshot from the latest turn (as-is from Google)
    # usage_metadata: Dict[str, Any] = field(default_factory=dict)

    # Arbitrary call metadata for tools and providers (e.g. CRM data, ATIS info, etc.)
    call_metadata: Dict[str, Any] = field(default_factory=dict)  

    #transcription: Optional[List[Dict[str, Any]]] = field(default_factory=list)  # transcription
    
    session_stats: Optional[Dict[str, Any]] = field(default_factory=dict)
    # System access
    config: Any = None
    
    def calculate_session_stats(self) -> Dict[str, Any]:
        """
        Calculate session statistics from conversation_history.
        
        Returns:
            Dictionary with aggregated token usage statistics in API-compatible format:
            - promptTokenCount: Total prompt tokens across all messages
            - candidatesTokenCount: Total candidates tokens across all messages
            - totalTokenCount: Total of prompt + candidates tokens
            - promptTokensDetails: Array of {modality, tokenCount} for prompts
            - candidatesTokensDetails: Array of {modality, tokenCount} for candidates
        """
        # Accumulators for modality tokens
        prompt_modality_totals = {}
        candidates_modality_totals = {}
        
        total_prompt_tokens = 0
        total_candidates_tokens = 0
        
        if self.conversation_history:
            for message in self.conversation_history:
                if isinstance(message, dict) and "usage" in message:
                    usage = message["usage"]
                    
                    # Accumulate promptTokenCount
                    prompt_token_count = usage.get("promptTokenCount", 0)
                    if isinstance(prompt_token_count, str):
                        prompt_token_count = int(prompt_token_count) if prompt_token_count.isdigit() else 0
                    total_prompt_tokens += prompt_token_count
                    
                    # Accumulate candidatesTokenCount
                    candidates_token_count = usage.get("candidatesTokenCount", 0)
                    if isinstance(candidates_token_count, str):
                        candidates_token_count = int(candidates_token_count) if candidates_token_count.isdigit() else 0
                    total_candidates_tokens += candidates_token_count
                    
                    # Aggregate promptTokensDetails by modality
                    prompt_details = usage.get("promptTokensDetails", [])
                    if prompt_details and isinstance(prompt_details, list):
                        for detail in prompt_details:
                            modality = detail.get("modality", "").upper()  # Keep uppercase like API
                            token_count = detail.get("tokenCount", 0)
                            if isinstance(token_count, str):
                                token_count = int(token_count) if token_count.isdigit() else 0
                            
                            if modality:
                                prompt_modality_totals[modality] = prompt_modality_totals.get(modality, 0) + token_count
                    
                    # Aggregate candidatesTokensDetails by modality
                    candidates_details = usage.get("candidatesTokensDetails", [])
                    if candidates_details and isinstance(candidates_details, list):
                        for detail in candidates_details:
                            modality = detail.get("modality", "").upper()  # Keep uppercase like API
                            token_count = detail.get("tokenCount", 0)
                            if isinstance(token_count, str):
                                token_count = int(token_count) if token_count.isdigit() else 0
                            
                            if modality:
                                candidates_modality_totals[modality] = candidates_modality_totals.get(modality, 0) + token_count
        
        # Build promptTokensDetails array
        prompt_tokens_details = [
            {"modality": modality, "tokenCount": count}
            for modality, count in sorted(prompt_modality_totals.items())
        ]
        
        # Build candidatesTokensDetails array
        candidates_tokens_details = [
            {"modality": modality, "tokenCount": count}
            for modality, count in sorted(candidates_modality_totals.items())
        ]
        
        session_stats = {
            "promptTokenCount": total_prompt_tokens,
            "candidatesTokenCount": total_candidates_tokens,
            "totalTokenCount": total_prompt_tokens + total_candidates_tokens,
            "promptTokensDetails": prompt_tokens_details,
            "candidatesTokensDetails": candidates_tokens_details
        }
        
        self.session_stats = session_stats
        return session_stats
    
    def to_payload_dict(self) -> Dict[str, Any]:
        """
        Convert context to a dictionary suitable for webhook payloads.
        
        Returns:
            Dictionary with all call data for templating.
        """
        import json
        
        # Calculate session_stats if not already calculated
        self.calculate_session_stats()
        
        return {
            "call_id": self.call_id,
            "caller_number": self.caller_number,
            "called_number": self.called_number or "",
            "caller_name": self.caller_name or "",
            "context_name": self.context_name,
            "provider": self.provider,
            "call_direction": self.call_direction,
            "call_duration": self.call_duration_seconds,
            "call_outcome": self.call_outcome,
            "call_start_time": self.call_start_time or "",
            "call_end_time": self.call_end_time or "",
            "transcript_json": json.dumps(self.conversation_history),
            #"transcription": self.conversation_history,  # Add transcription as list for direct access
            "session_stats_json": json.dumps(self.session_stats or {}),  # Add calculated session_stats
            "summary": self.summary or "",
            "tool_calls_json": json.dumps(self.tool_calls),
            "pre_call_results_json": json.dumps(self.pre_call_results),
            "campaign_id": self.campaign_id or "",
            "lead_id": self.lead_id or "",
            "session_id": self.session_id or "",
            "globals_asterisk_instance": self.globals_asterisk_instance or "",
            # "usage_metadata_json": json.dumps(self.usage_metadata if self.usage_metadata else {}),
            # "usage_metadata_summary_json": json.dumps(self.usage_metadata_summary if self.usage_metadata_summary else {}),
            "call_metadata_json": json.dumps(self.call_metadata if self.call_metadata else {}),
        }
