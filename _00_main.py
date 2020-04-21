# -*- coding: utf-8 -*-
# CV2, 원 찾기: https://m.blog.naver.com/samsjang/220592858479
#              https://076923.github.io/posts/Python-opencv-29/
# CV2, 이미지 리사이징: https://m.blog.naver.com/samsjang/220504966397
# CV2, 이미지 자르기: https://076923.github.io/posts/Python-opencv-9/

import _12_Bluetooth as c
import time

import cv2

# 쓰레드 객체 생성 및 쓰레드 시작
bt = c.Comm_BT("00:18:E5:04:23:38")
bt.start_comm_thread()

# 초기 위치로 이동
print("Move to Start Point!!!")
bt.msg_send("$N#")

# 이동 완료시까지 대기
while (command == 'N'):
    status, command = bt.get_command()
    if status:
        print("command = ", command)
        bt.clear_command()

print("Done!!!")


temp = 0
value = 100
dir = 1
cmd = "R"
command = ''

while True:
    try:
        if (dir == 1) & (value < 300):
            value = value + 1
        elif (dir == 0) & (value > 100):
            value = value - 1
        elif value >= 300:
            dir = 0
        elif value <= 100:
            dir = 1

        if cmd == "R":
            speed = -value
        elif cmd == "L":
            speed = value

        # 쓰기
        bt.msg_send("$R" + str(speed) + "#")

        time.sleep(0.01)

        # 새로운 명령이 있는지 확인
        status, command = bt.get_command()
        if status:
            print("command = ", command)
            cmd = command
            bt.clear_command()

    except:
        bt.sock.close()
        print("Bluetooth Error, Socket Close")
        exit()

