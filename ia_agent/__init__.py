# Package declaration for ia_agent
from .schemas import CopilotChatPayload, CopilotConfig, ChatMessage, CopilotStructuredResponse
from .copilot import run_copilot_stream, recommend_config
