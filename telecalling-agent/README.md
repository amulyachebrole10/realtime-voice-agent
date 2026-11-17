# Local AI Telecalling Agent (staging scaffold)

This folder contains the third-project prototype, staged inside the voice-agent repository because the connected GitHub integration currently has no repository-creation operation. Once a separate empty repository named \`local-ai-telecalling-agent\` exists, these files can be copied there without changing the implementation.

A local-first AI phone agent prototype for consent-based sales lead qualification and appointment booking. Asterisk handles SIP/PSTN routing; AudioSocket streams 8 kHz mono PCM to Python; Faster-Whisper performs STT, Ollama/Qwen handles dialogue, and Piper generates speech.

## Windows + Docker
- Docker Desktop with WSL2.
- Ollama installed natively on Windows; pull \`qwen2.5:1.5b\`.
- Add a Piper ONNX voice model and JSON config under \`models/\`.
- Configure the SIP trunk in \`asterisk/etc/asterisk/pjsip.conf\` before calling real numbers.
- Start from this directory: \`docker compose up --build\`.
- A local SIP softphone can register as extension 1001 and call 7000 to test the AI path. Real mobile/landline calls require a SIP trunk/provider.

## API
- \`GET /health\`
- \`POST /calls/outbound\` — queues an outbound call file; requires \`consent_confirmed=true\`.
- \`GET /calls\` — call status snapshot.

Example:
~~~powershell
Invoke-RestMethod -Method Post http://localhost:8020/calls/outbound -ContentType "application/json" -Body '{"phone_number":"1001","lead_name":"Demo Lead","consent_confirmed":true}'
~~~

## Production gaps
Prototype only. CRM persistence, campaign scheduling, robust barge-in, call recording, DNC registry, retries, authentication, encrypted storage and jurisdiction-specific compliance are not complete. Disclose AI identity, honour opt-outs and obtain all required permissions. For India, implement applicable TRAI/DLT requirements before marketing calls. Never record without required notice/consent.
