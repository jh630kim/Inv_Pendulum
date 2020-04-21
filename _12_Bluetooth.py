# -*- coding: utf-8 -*-
# BT 이용: http://pages.iu.edu/~rwisman/c490/html/pythonandbluetooth.htm
#          https://people.csail.mit.edu/albert/bluez-intro/x232.html

import bluetooth        # pip3 install pybluez 로 설치 필요.
                        # 이걸... from bluetooth import *로 하면 폭망
import time
import threading


class Comm_BT:
    def __init__(self, address):
        self.sock = 0
        self.addr = address
        self.port = 1

        # 상태
        self.newline = False
        self.command = ''

        self.BT_Init()

    # BT 초기화
    def BT_Init(self):
        print("Wating BT connection...")
        # client 소켓 연결(to HC-06)
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.connect((self.addr, self.port))
        print("BT Connected...")

    # 데이터 수신 Thread 시작
    def start_comm_thread(self):
        commThread = threading.Thread(target=self.data_receiving_BT)
        commThread.start()

    # 데이터 수신 쓰레드
    def data_receiving_BT(self):
        data = ''
        # "$L#"-왼쪽 끝 or "$R#"-오른쪽 끝, "$C#"-중앙, 시작준비 완료
        while True:
            incomingStr = self.sock.recv(1024)  # byte array
            data = data + incomingStr.decode()  # string
            # 첫번째 바이트는 '$'
            if (data[-1] == '$'):
                data = '$'

            # $로 시작해서 #으로 끝나면(한 패킷이 완성되었으면)
            if (data[0] == '$') & (data[-1] == '#'):
                self.command = data[1:-1]
                self.newline = True
                data = ''

            # 데이터가 너무 길면 초기화
            if (len(data) > 10):
                data = ''

            time.sleep(0.01)

    # 새로운 명령이 있는지 확인 및 초기화
    def get_command(self):
        return self.newline, self.command

    def clear_command(self):
        self.newline = False
        self.command = ''

    # 외부에서 직접 메시지를 보낼 경우
    def msg_send(self, msg):
        self.sock.send(msg)


if __name__ == '__main__':
    temp = 0

    # 쓰레드 객체 생성 및 쓰레드 시작
    bt = Comm_BT("00:18:E5:04:23:38")
    bt.start_comm_thread()

    while True:
        try:
            # 쓰기
            speed = input("speed(rpm): ")
            bt.msg_send("$" + str(speed) + "#")

            time.sleep(1)

            # 새로운 명령이 있는지 확인
            status, command = bt.get_command()
            if status:
                print("command = ", command)
                bt.clear_command()

        except:
            bt.sock.close()
            print("Bluetooth Error, Socket Close")
            exit()