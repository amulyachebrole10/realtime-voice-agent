from dataclasses import dataclass,field
@dataclass
class Session:
    session_id:str
    messages:list[dict[str,str]]=field(default_factory=list)
class ConversationEngine:
    """Deterministic demo engine; replace reply() with an LLM client."""
    def reply(self,text:str,history:list[dict[str,str]])->str:
        cleaned=text.strip()
        if not cleaned: raise ValueError("Message cannot be empty.")
        return f"You said: {cleaned}\nThis is the demo voice-agent backend. Connect an LLM provider in ConversationEngine.reply() for intelligent responses."
