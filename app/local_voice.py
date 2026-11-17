import os
import subprocess
import tempfile
from pathlib import Path
import requests
from faster_whisper import WhisperModel

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")
PIPER_MODEL = os.getenv("PIPER_MODEL", "/models/en_US-lessac-medium.onnx")

class LocalVoiceEngine:
    def __init__(self):
        self.whisper = None

    def _stt(self):
        if self.whisper is None:
            self.whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        return self.whisper

    def transcribe(self, audio_path: str):
        segments, info = self._stt().transcribe(audio_path, beam_size=1, vad_filter=True)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return {"text": text, "language": info.language, "language_probability": info.language_probability}

    def reply(self, text: str, history: list[dict]):
        messages = history[-6:] + [{"role": "user", "content": text}]
        response = requests.post(
            OLLAMA_URL.rstrip("/") + "/api/chat",
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False,
                  "options": {"temperature": 0.3, "num_ctx": 2048}},
            timeout=180,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def synthesize(self, text: str, output_path: str):
        if not Path(PIPER_MODEL).exists():
            raise FileNotFoundError("Piper voice model missing. Mount a Piper .onnx model and set PIPER_MODEL.")
        subprocess.run(
            ["piper", "--model", PIPER_MODEL, "--output_file", output_path],
            input=text, text=True, check=True, timeout=90,
        )
        return output_path
