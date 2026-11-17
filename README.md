# Real-Time Voice Agent

A modular voice-assistant backend foundation with session memory and replaceable speech-to-text (STT), language-model, and text-to-speech (TTS) adapters. A working text-chat API lets you test the conversation loop without audio hardware or paid services.

## Pipeline
Audio input → STT adapter → Conversation engine → LLM → TTS adapter → Audio output

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs.

```bash
curl -X POST http://127.0.0.1:8000/sessions/demo/messages -H 'Content-Type: application/json' -d '{"text":"Hello, what can you do?"}'
```

## Docker
```bash
docker build -t realtime-voice-agent .
docker run -p 8000:8000 realtime-voice-agent
```

## Tests
```bash
pytest
```

## Extension points
- `app/adapters.py`: implement streaming or batch STT/TTS providers.
- `app/engine.py`: integrate an LLM and tool calling.
- `app/main.py`: session-based HTTP interface.

## Production considerations
Use WebSocket or WebRTC for full-duplex streaming, persistent session storage, authentication, rate limits, and provider credential management. Define consent, retention, and deletion policies before recording voice data.

## Scope and limitations
The included conversation engine is deterministic demo logic; STT/TTS adapters are interfaces, not connected services. This is a runnable backend foundation, not yet a production real-time audio application.
