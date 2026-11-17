import asyncio
import logging
import struct
import uuid
import webrtcvad
from app.engine import LocalCallEngine

log = logging.getLogger(__name__)
HEADER_SIZE = 3
AUDIO_TYPE = 0x10
UUID_TYPE = 0x01
HANGUP_TYPE = 0x00
DTMF_TYPE = 0x03
FRAME_BYTES = 320  # 20 ms, 8 kHz, mono, signed 16-bit PCM

def packet(kind: int, payload: bytes = b"") -> bytes:
    return bytes([kind]) + struct.pack("!H", len(payload)) + payload

class AudioSocketServer:
    def __init__(self, engine: LocalCallEngine, host="0.0.0.0", port=9092):
        self.engine, self.host, self.port = engine, host, port
        self.server = None
        self.vad = webrtcvad.Vad(2)

    async def start(self):
        self.server = await asyncio.start_server(self.handle, self.host, self.port)
        log.info("AudioSocket listening on %s:%s", self.host, self.port)

    async def close(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def _send_audio(self, writer, pcm: bytes):
        for offset in range(0, len(pcm), FRAME_BYTES):
            chunk = pcm[offset:offset + FRAME_BYTES]
            if len(chunk) < FRAME_BYTES:
                chunk += b"\x00" * (FRAME_BYTES - len(chunk))
            writer.write(packet(AUDIO_TYPE, chunk))
            await writer.drain()
            await asyncio.sleep(0.018)

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        call_id = str(uuid.uuid4())
        try:
            while True:
                header = await reader.readexactly(HEADER_SIZE)
                kind, length = header[0], struct.unpack("!H", header[1:])[0]
                payload = await reader.readexactly(length) if length else b""
                if kind == UUID_TYPE and len(payload) == 16:
                    call_id = str(uuid.UUID(bytes=payload))
                    self.engine.history.setdefault(call_id, [])
                    greeting = "Hello, I am an AI assistant. Is now a good time to speak?"
                    pcm = await asyncio.to_thread(self.engine.synthesize_pcm, greeting)
                    await self._send_audio(writer, pcm)
                elif kind == HANGUP_TYPE:
                    break
                elif kind == DTMF_TYPE:
                    continue
                elif kind == AUDIO_TYPE and payload:
                    # Asterisk normally sends 20 ms frames. Segment speech using VAD.
                    utterance = bytearray()
                    silence_frames = 0
                    speech_frames = 0
                    # Read a bounded utterance from the socket; process when silence follows speech.
                    try:
                        frame = payload
                        while True:
                            if len(frame) == FRAME_BYTES:
                                is_speech = self.vad.is_speech(frame, 8000)
                                if is_speech:
                                    utterance.extend(frame)
                                    speech_frames += 1
                                    silence_frames = 0
                                elif speech_frames:
                                    utterance.extend(frame)
                                    silence_frames += 1
                                if speech_frames >= 8 and silence_frames >= 25:
                                    break
                            header2 = await asyncio.wait_for(reader.readexactly(HEADER_SIZE), timeout=0.7)
                            kind2, length2 = header2[0], struct.unpack("!H", header2[1:])[0]
                            frame = await reader.readexactly(length2) if length2 else b""
                            if kind2 == HANGUP_TYPE:
                                return
                            if kind2 != AUDIO_TYPE:
                                continue
                    except asyncio.TimeoutError:
                        pass
                    if speech_frames >= 8:
                        transcript = await asyncio.to_thread(self.engine.transcribe_pcm, bytes(utterance))
                        if transcript:
                            log.info("Call %s transcript: %s", call_id, transcript[:300])
                            answer = await asyncio.to_thread(self.engine.respond, call_id, transcript)
                            response_pcm = await asyncio.to_thread(self.engine.synthesize_pcm, answer)
                            await self._send_audio(writer, response_pcm)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            pass
        except Exception:
            log.exception("AudioSocket call %s failed", call_id)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
