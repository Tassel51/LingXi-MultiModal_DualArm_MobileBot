import speech_recognition as sr
from aip import AipSpeech
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal, QObject


# 语音转文字类
class SpeechRecognition(QObject):
    def __init__(self, app_id, api_key, secret_key, path="test.wav", parent=None):
        super(SpeechRecognition, self).__init__(parent)
        self.client = AipSpeech(app_id, api_key, secret_key)
        self.path = path
        self.signalRecordFinish = pyqtSignal(object)

    def record_audio(self, rate=16000):
        r = sr.Recognizer()
        with sr.Microphone(sample_rate=rate) as source:
            print("Please say something")
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, phrase_time_limit=6)
            print('Record finish')

        return audio.get_wav_data()

    def listen(self, audio_data):
        try:
            result = self.client.asr(audio_data, 'wav', 16000, {'dev_pid': 1537, })
            result_text = result["result"][0]
            print(result_text)
            return result_text
        except KeyError:
            print("KeyError")
            return " "


