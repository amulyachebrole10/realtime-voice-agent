# Local Voice Agent

A local-first speech assistant using Faster-Whisper (STT), Ollama + Qwen (LLM), and Piper (TTS). Runs on Windows 10/11 with Docker Desktop + WSL2. No paid AI API keys are required.

## Architecture

Audio upload → Faster-Whisper transcription → Ollama chat → Piper speech synthesis → WAV response.

This is a batch-turn prototype, not yet a low-latency full-duplex telephone agent. WebRTC/WebSocket streaming and telephony/PBX support belong in the separate third repository.

## Windows setup

1. Install Docker Desktop with the WSL2 backend.
2. Install Ollama for Windows: https://ollama.com/download
3. In PowerShell run:

~~~powershell
ollama pull qwen2.5:1.5b
ollama serve
~~~

4. Copy .env.example to .env.
5. Download a compatible Piper voice model and its JSON config into the models folder. The default configured path is /models/en_US-lessac-medium.onnx. Update PIPER_MODEL if you choose another voice.
6. Start the service:

~~~powershell
docker compose up --build
~~~

Open http://localhost:8010/docs.

## API examples

Text conversation:

~~~powershell
Invoke-RestMethod -Method Post http://localhost:8010/sessions/demo/messages -ContentType "application/json" -Body '{"text":"Hello, introduce yourself."}'
~~~

Audio transcription and speech turn are available as multipart upload endpoints: POST /audio/transcribe and POST /sessions/{session_id}/voice. Speech synthesis is POST /audio/synthesize.

## Resource profile

Start with Whisper tiny, Qwen 2.5 1.5B and one Piper voice. The Whisper model downloads on first use. Keep model-heavy services sequential on an 8 GB machine. Ollama runs natively on Windows; the Docker container reaches it through host.docker.internal.

## Tests

~~~powershell
pytest
~~~

## Limitations and safety

The current implementation handles uploaded audio in request/response turns; it is not telephony, does not place phone calls, and is not full-duplex streaming. The separate telecalling project will add SIP/PBX integration, call controls, consent flows and call logging. Obtain consent before recording or processing calls, disclose AI identity where required, and implement retention/deletion policies before production.
