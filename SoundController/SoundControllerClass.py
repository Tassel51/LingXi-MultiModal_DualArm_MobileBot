





##小车移动类
import serial
import time


class CarControl:
    def __init__(self, port, baudrate, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)

    def forward(self, forward_time):
        time.sleep(2)
        self.ser.write('w'.encode())  # w 2
        time.sleep(forward_time)
        self.ser.write('u'.encode())
        time.sleep(2)

    def backward(self, backward_time):
        time.sleep(2)
        self.ser.write('s'.encode())  # s 2
        time.sleep(backward_time)
        self.ser.write('u'.encode())
        time.sleep(2)

    def close(self):
        self.ser.close()
        print('Serial port closed.')


def main():
    app_id = '64120543'
    api_key = 'jB79TAegVjEYYFwzJP95fHCJ'
    secret_key = 'pxZPDUf8VARMzKYIxyyM5AEl1SuYBwgb'

    recognizer = SpeechRecognition(app_id, api_key, secret_key)
    tts = TextToSpeech(app_id, api_key, secret_key)
    # car = CarControl("COM8", 115200)

    try:
        # 录音
        recognizer.record_audio()

        # 将录音文件转换为文本
        prompt_text = recognizer.listen()
        if prompt_text == "完成机械操作。":
            tts.speak_text("好的")
            distance = 1
            tts.speak_text(f"水杯距离{distance}米")
            # car.backward(2)
            # car.forward(2)
    finally:
        car.close()


if __name__ == "__main__":
    main()
