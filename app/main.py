import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.local_voice import LocalVoiceEngine

app = FastAPI(title="Local Voice Agent", version="0.2.0")
voice = LocalVoiceEngine()
sessions: dict[str, list[dict[str, str]]] = {}

class MessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)

class SynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)

@app.get("/health")
def health():
    return {"status": "ok", "mode": "local-first", "stt": "faster-whisper", "llm": "ollama", "tts": "piper"}

@app.post("/sessions/{session_id}/messages")
def send_message(session_id: str, request: MessageRequest):
    history = sessions.setdefault(session_id, [])
    try:
        answer = voice.reply(request.text, history)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Local Ollama is unavailable. Start Ollama and pull the configured model.") from exc
    history.extend([{"role": "user", "content": request.text}, {"role": "assistant", "content": answer}])
    return {"session_id": session_id, "reply": answer, "message_count": len(history)}

@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "messages": sessions[session_id]}

@app.post("/audio/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    suffix = Path(file.filename or "recording.wav").suffix or ".wav"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(await file.read())
            temp_path = temp.name
        return voice.transcribe(temp_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Audio transcription failed. Check audio format and Whisper model.") from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.post("/audio/synthesize")
def synthesize_audio(request: SynthesisRequest):
    temp_path = None
    try:
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        voice.synthesize(request.text, temp_path)
        return FileResponse(temp_path, media_type="audio/wav", filename="speech.wav", background=None)
    except Exception as exc:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=503, detail="Piper synthesis failed. Check the configured voice model.") from exc

@app.post("/sessions/{session_id}/voice")
async def voice_turn(session_id: str, file: UploadFile = File(...)):
    history = sessions.setdefault(session_id, [])
    suffix = Path(file.filename or "recording.wav").suffix or ".wav"
    input_path = output_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(await file.read())
            input_path = temp.name
        transcript = voice.transcribe(input_path)
        if not transcript["text"]:
            raise HTTPException(status_code=422, detail="No speech detected")
        answer = voice.reply(transcript["text"], history)
        fd, output_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        voice.synthesize(answer, output_path)
        history.extend([{"role": "user", "content": transcript["text"]}, {"role": "assistant", "content": answer}])
        return FileResponse(output_path, media_type="audio/wav", filename="reply.wav",
                            headers={"X-Transcript": transcript["text"][:500], "X-Session-Id": session_id})
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Voice turn failed. Check Ollama, Whisper and Piper configuration.") from exc
    finally:
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
