from typing import Protocol
class SpeechToText(Protocol):
    def transcribe(self,audio:bytes)->str: ...
class TextToSpeech(Protocol):
    def synthesize(self,text:str)->bytes: ...
class DemoSpeechToText:
    def transcribe(self,audio:bytes)->str:
        raise NotImplementedError("Configure a real STT adapter.")
class DemoTextToSpeech:
    def synthesize(self,text:str)->bytes:
        raise NotImplementedError("Configure a real TTS adapter.")
