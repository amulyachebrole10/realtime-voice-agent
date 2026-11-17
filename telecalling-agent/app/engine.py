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

class LocalCallEngine:
    def __init__(self):
        self.whisper = None
        self.history: dict[str, list[dict[str, str]]] = {}

    def transcribe_pcm(self, pcm: bytes) -> str:
        with tempfile.TemporaryDirectory() as directory:
            raw_path = str(Path(directory) / "input.pcm")
            wav_path = str(Path(directory) / "input.wav")
            Path(raw_path).write_bytes(pcm)
            subprocess.run(["ffmpeg", "-y", "-f", "s16le", "-ar", "8000", "-ac", "1",
                            "-i", raw_path, "-ar", "16000", "-ac", "1", wav_path],
                           check=True, capture_output=True, timeout=30)
            if self.whisper is None:
                self.whisper = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            segments, _ = self.whisper.transcribe(wav_path, beam_size=1, vad_filter=True)
            return " ".join(segment.text.strip() for segment in segments).strip()

    def respond(self, call_id: str, transcript: str) -> str:
        history = self.history.setdefault(call_id, [])
        system = (
            "You are a transparent, polite AI phone assistant for a business. "
            "At the start, identify yourself as an AI assistant. Ask one question at a time. "
            "For a sales qualification conversation, understand the person's need, ask permission "
            "before collecting contact details, answer only from supplied business facts, and offer "
            "a human callback when unsure. Never pressure, mislead, invent prices, promise outcomes, "
            "or continue if the person declines. If they say stop, goodbye politely."
        )
        messages = [{"role": "system", "content": system}] + history[-8:] + [{"role": "user", "content": transcript}]
        response = requests.post(
            OLLAMA_URL.rstrip("/") + "/api/chat",
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False,
                  "options": {"temperature": 0.25, "num_ctx": 2048}},
            timeout=120,
        )
        response.raise_for_status()
        answer = response.json()["message"]["content"].strip()
        history.extend([{"role": "user", "content": transcript},
                        {"role": "assistant", "content": answer}])
        return answer

    def synthesize_pcm(self, text: str) -> bytes:
        if not Path(PIPER_MODEL).exists():
            raise FileNotFoundError("Piper ONNX voice model not found; mount a voice model and configure PIPER_MODEL.")
        with tempfile.TemporaryDirectory() as directory:
            wav_path = str(Path(directory) / "reply.wav")
            subprocess.run(["piper", "--model", PIPER_MODEL, "--output_file", wav_path],
                           input=text, text=True, check=True, capture_output=True, timeout=60)
            result = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", wav_path, "-f", "s16le", "-acodec", "pcm_s16le",
                 "-ac", "1", "-ar", "8000", "pipe:1"],
                check=True, capture_output=True, timeout=30,
            )
            return result.stdout
