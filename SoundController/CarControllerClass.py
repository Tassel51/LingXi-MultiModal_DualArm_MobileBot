import serial
import time


class CarControl:
    def __init__(self, port, baudrate, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)

    def backward(self, forward_time):
        time.sleep(2)
        self.ser.write('w'.encode())  # w 2
        time.sleep(forward_time)
        self.ser.write('u'.encode())
        time.sleep(2)

    def forward(self, backward_time):
        time.sleep(2)
        self.ser.write('s'.encode())  # s 2
        time.sleep(backward_time)
        self.ser.write('u'.encode())
        time.sleep(2)

    def only_backward(self, obstacle=False):
        time.sleep(2)
        self.ser.write('w'.encode())

    def only_forward(self, obstacle=False):
        time.sleep(2)
        self.ser.write('s'.encode())
        if obstacle:
            time.sleep(2.25)
        else:
            time.sleep(3.2)
        # 60+30:3.2s
        self.ser.write('x'.encode())
        # time.sleep(0.5)

    def only_backward(self):
        time.sleep(2)
        self.ser.write('w'.encode())
        time.sleep(3.2)
        self.ser.write('r'.encode())
        time.sleep(0.5)

    def only_stop(self):
        self.ser.write('u'.encode())
        time.sleep(2)

    def close(self):
        self.ser.close()
        print('Serial port closed.')
if __name__ == '__main__':
    carController = CarControl('COM12',115200)
    time.sleep(2)
    carController.only_stop()
