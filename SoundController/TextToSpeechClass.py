### 语音播报类
import pyttsx3
from aip import AipSpeech


class TextToSpeech:
    def __init__(self, app_id, api_key, secret_key):
        self.client = AipSpeech(app_id, api_key, secret_key)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', self.engine.getProperty('rate') - 50)
        self.engine.setProperty('volume', self.engine.getProperty('volume') + 0.25)

    def speak_text(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    def say(self, text):
        result = self.client.synthesis(text, 'zh', 1, {'vol': 5, 'aue': 6})
        if not isinstance(result, dict):
            with open('audio2.wav', 'wb') as f:
                f.write(result)
        return result