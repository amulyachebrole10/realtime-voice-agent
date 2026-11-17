import os
import re
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.engine import LocalCallEngine
from app.audio_socket import AudioSocketServer

engine = LocalCallEngine()
audio_server = AudioSocketServer(engine)
calls: dict[str, dict] = {}
SPOOL = Path(os.getenv("ASTERISK_SPOOL", "/var/spool/asterisk/outgoing"))
TRUNK = os.getenv("SIP_TRUNK", "provider")
CALLER_ID = os.getenv("CALLER_ID", "AI Assistant <1000>")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await audio_server.start()
    yield
    await audio_server.close()

app = FastAPI(title="Local AI Telecalling Agent", version="0.1.0", lifespan=lifespan)

class OutboundCall(BaseModel):
    phone_number: str = Field(min_length=3, max_length=18)
    lead_name: str = Field(default="there", max_length=100)
    consent_confirmed: bool
    purpose: str = Field(default="sales lead qualification", max_length=120)

@app.get("/health")
def health():
    return {"status": "ok", "mode": "local-first", "telephony": "Asterisk AudioSocket",
            "stt": "Faster-Whisper", "llm": "Ollama", "tts": "Piper"}

@app.get("/calls")
def list_calls():
    return {"calls": list(calls.values())}

@app.post("/calls/outbound", status_code=202)
def queue_outbound_call(request: OutboundCall):
    if not request.consent_confirmed:
        raise HTTPException(status_code=400, detail="Do not call a lead without documented permission/consent.")
    number = request.phone_number.strip()
    if not re.fullmatch(r"\+?[0-9]{3,16}", number):
        raise HTTPException(status_code=422, detail="Use digits with an optional leading +; no spaces or extensions.")
    if not SPOOL.is_dir():
        raise HTTPException(status_code=503, detail="Asterisk outgoing-call spool is not mounted.")
    call_id = str(uuid.uuid4())
    local_extension = number.isdigit() and len(number) <= 5
    channel = f"PJSIP/{number}" if local_extension else f"PJSIP/{number}@{TRUNK}"
    content = (
        f"Channel: {channel}\n"
        f"CallerID: {CALLER_ID}\n"
        f"MaxRetries: 0\n"
        f"RetryTime: 60\n"
        f"WaitTime: 30\n"
        f"Application: AudioSocket\n"
        f"Data: {call_id},{os.getenv('AUDIO_SOCKET_HOST', 'voice-agent')}:9092\n"
        f"Archive: yes\n"
        f""
    )
    temp = SPOOL / f"{call_id}.call.tmp"
    target = SPOOL / f"{call_id}.call"
    temp.write_text(content, encoding="utf-8")
    os.replace(temp, target)
    calls[call_id] = {"call_id": call_id, "lead_name": request.lead_name,
                      "phone_number": number, "purpose": request.purpose,
                      "status": "queued", "consent_confirmed": True}
    return {"call_id": call_id, "status": "queued", "channel": channel,
            "message": "Call queued. Asterisk and a configured SIP endpoint/trunk are required."}
