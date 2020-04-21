#-*- coding:utf-8 -*-
# 최신 pyserial에 적용되어 있는 스레드 시리얼의 코드
# 아두이노의 Serial 대신 HC-06 블루투스 모듈을 이용한다.
# 이 코드는... 참고용으로만 가지고있자.

import sys
import time
import serial
import threading
import queue

class Protocol(object):
    """
    ReaderThread에서 호출됨
    어플리케이션에 따른 구현 필요
    """

    def __init__(self):
        self._received_data = []
        self._test_flag = False
        self._MAXBUFFER = 100

    # 이게 되네???
    # ReaderThread 에서 호출할때는 이렇게만 하는데???
    # self.protocol.connection_made(self)
    def connection_made(self, transport):
        """Called when reader thread is started"""
        self.transport = transport
        self.running = True

    def connection_lost(self, exc):
        """\
        Called when the serial port is closed or the reader loop terminated
        otherwise.
        """
        self.transport = None
        if isinstance(exc, Exception):
            raise exc

    def data_received(self, data):
        """Called with snippets received from the serial port"""
        self._received_data.append(data)
        # 수신된 데이터가 MAXBUFFER 보다 많으면 이전 데이터 버리기
        if len(self._received_data) > self._MAXBUFFER:
            self._received_data.pop(0)
        if self._test_flag:
            print("DEBUG Read: ", data)

    #################################################3
    def data_available(self):
        # 현재 buffer 의 Data 개수
        return len(self._received_data)

    def get_data(self):
        # Data를 읽음
        return self._received_data.pop(0)

    def write(self,data):
        # 데이터 보내기
        if self._test_flag:
            print("DEBUG Write:", data)
        self.transport.write(data)

    def isDone(self):
        # 종료 체크
        return self.running

    def set_test(self, flag=False):
        self._test_flag = flag


class ReaderThread(threading.Thread):
    """
    Serial Port Read Loop와 Protocal Instance로 전달하는 클래스(Thread 이용)
    Implement a serial port read loop and dispatch to a Protocol instance (like
    the asyncio.Protocol) but do it with threads.
    Calls to close() will close the serial port but it is also possible to just
    stop() this thread and continue the serial port instance otherwise.
    """

    def __init__(self, serial_instance, protocol_factory):
        """\
        Initialize thread.
        Note that the serial_instance' timeout is set to one second!
        Other settings are not changed.
        """
        super(ReaderThread, self).__init__()
        self.daemon = True
        self.serial = serial_instance               # Serial 객체
        self.protocol_factory = protocol_factory    # 사용할 프로토콜(데이터 수신 처리)
        self.alive = True
        self._lock = threading.Lock()
        self._connection_made = threading.Event()
        self.protocol = None

    def stop(self):
        """Stop the reader thread"""
        self.alive = False
        if hasattr(self.serial, 'cancel_read'):
            self.serial.cancel_read()
        self.join(2)

    def run(self):
        """Reader loop"""
        if not hasattr(self.serial, 'cancel_read'):
            self.serial.timeout = 1
        self.protocol = self.protocol_factory()
        try:
            # Serial Connection 연결시 호출
            self.protocol.connection_made(self)
        except Exception as e:
            self.alive = False
            # Serial Connection이 끊긴 경우 호출
            self.protocol.connection_lost(e)
            self._connection_made.set()
            return
        error = None
        self._connection_made.set()
        # serial이 연결되어 있는 동안 반복
        while self.alive and self.serial.is_open:
            try:
                # read all that is there or wait for one byte (blocking)
                # data = self.serial.read(self.serial.in_waiting or 1)
                while not ser.readable():
                    pass
                data = ser.readline()
            except serial.SerialException as e:
                # probably some I/O problem such as disconnected USB serial
                # adapters -> exit
                error = e
                break
            else:
                if data:
                    # make a separated try-except for called used code
                    try:
                        ###############################
                        # 수신된 데이터 전달
                        ###############################
                        self.protocol.data_received(data)
                    except Exception as e:
                        error = e
                        break
        # Serial Connection이 끊긴 경우
        self.alive = False
        self.protocol.connection_lost(error)
        self.protocol = None

    def write(self, data):
        # Data 전송
        """Thread safe writing (uses lock)"""
        with self._lock:
            print("DEBUG Write(Thread):", data)
            self.serial.write(data)

    def close(self):
        """Close the serial port and exit reader thread (uses lock)"""
        # use the lock to let other threads finish writing
        with self._lock:
            # first stop reading, so that closing can be done on idle port
            self.stop()
            self.serial.close()

    def connect(self):
        """
        Wait until connection is set up and return the transport and protocol
        instances.
        """
        if self.alive:
            self._connection_made.wait()
            if not self.alive:
                raise RuntimeError('connection_lost already called')
            return (self, self.protocol)
        else:
            raise RuntimeError('already stopped')

    # - -  context manager, returns protocol

    def __enter__(self):
        """\
        Enter context handler. May raise RuntimeError in case the connection
        could not be created.
        """
        self.start()
        self._connection_made.wait()
        if not self.alive:
            raise RuntimeError('connection_lost already called')
        return self.protocol

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Leave context: close port"""
        self.close()

if __name__ == '__main__':
    ser = serial.Serial(port="COM4", baudrate=115200)

    # 쓰레드 시작
    with ReaderThread(ser, Protocol) as p:
        while p.isDone():
            # Test Flag setting(안해도 관계 없다)
            p.set_test(False)

            # Data 쓰기
            temp1 = input("write1: ")
            # temp2 = input("write2: ")
            # 숫자의 경우
            # val = [int(temp1), int(temp2)]
            # p.write(bytearray(val))
            # 문자의 경우
            str = temp1
            #############################
            # 디버깅중
            # V값E의 형태
            #################
            p.write(str.encode())

            time.sleep(2)

            # Data 읽기
            while p.data_available():
                new_data = p.get_data()
                # new_data = b'abc\r\n'
                # new_data[:-1] = b'abc\r'
                try:
                    print("Result:", new_data.decode()[:-1])
                except:
                    print("Error")
