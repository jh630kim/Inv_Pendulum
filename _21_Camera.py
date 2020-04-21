import cv2
import time

class Image(object):
    def __init__(self, cam_id=0):
        self.cam_id = cam_id
        self.cam = ''

        self.width = 0
        self.height = 0
        self.x_center = 0
        self.y_center = 0

        self.dir_name = './img/'
        self.base_img = self.dir_name + 'base.jpg'
        self.list_name = self.dir_name + \
                         str(int(time.time() * 1000)) + \
                         '.csv'

        self.img_init()

    def img_init(self):
        # 웹캠 연결
        self.cam = cv2.VideoCapture(self.cam_id)
        if self.cam.isOpened() == False:
            print('Fail to open the cam (%d)' % self.cam_id)

        # 웹캠의 width와 height
        self.width = self.cam.get(3)
        self.height = self.cam.get(4)
        print('width :%d, height : %d' % (self.width, self.height))

        # gray 이미지[imgray = (400,500)] 생성
        self.base_gray = cv2.cvtColor(cv2.imread('./base.jpg'), cv2.COLOR_BGR2GRAY)

    def img_close(self):
        self.cam.release()
        cv2.destroyAllWindows()

    def img_read(self):
        result, frame = self.cam.read()  # result: 수행결과(T/F), frame: 이미지
        # 그레이 스케일로 변환
        imgray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # gray 이미지[imgray = (400,500)] 생성
        return result, imgray

    def save_img(self, img, value='NA'):
        # 파일 이름
        file_name = str(int(time.time() * 1000)) + '.jpg'

        # jpg로 저장
        cv2.imwrite(self.dir_name + file_name, img,
                    params=[cv2.IMWRITE_JPEG_QUALITY, 95])  # default = 95

        # 파일 이름 기록
        file = open(self.list_name, 'a')
        file.write(file_name + ',' + value + '\n')
        file.close()

    def find_circle(self, src_img):
        # 그레이 스케일로 변환
        # imgray = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)  # gray 이미지[imgray = (400,500)] 생성

        # circle 검색 및 중심 찾기
        # circles = [1,N,3], 3=x,y,r(중심점 및 반지름) 검색
        circles = cv2.HoughCircles(image=src_img,  # 검출이미지(Grayscale)
                                   method=cv2.HOUGH_GRADIENT,  # 검출 방법
                                   dp=1,  # 해상도 비율(?)
                                   minDist=50,  # 검출 원 간의 최소 거리
                                   param1=40, param2=20,
                                   # param1: Canny Edeg에 전달되는 인자
                                   # param2: 작으면 오류가 많고, 높은면 검출률이 낮아짐.
                                   minRadius=10,
                                   maxRadius=20)

        try:
            # imgray에 흰색으로 원 그리기
            for i in circles[0]:
                cv2.circle(src_img, (i[0], i[1]), i[2], (255, 255, 255), 3)
                x = i[0]
                y = i[1]
                if (0 < x < 640) and (320 < y < 480):
                    print('x: ', x, ', y: ', y, '-> OK')
                    result = True
                    break
                else:
                    print('x: ', x, ', y: ', y, '-> Fail')
                    result = False
        except:
            x = y = 0
            print("Fail to find circles.")
            result = False

        # 이미지 그리기
        cv2.imshow('Find Circle', src_img)  # 컬러 화면 출력
        return result, x, y

    def scaled_img(self, src_img):
        # circle 찾기
        result, x, y = self.find_circle(src_img)

        # scaled img의 base
        base = self.base_gray.copy()

        if result:
            # 이미지 변환을 위한 상수
            SRC_HEIGHT = self.height     #480
            SRC_WITDH = self.width      #640

            # scaled img의 크기: 500 x 400
            # 원의 위치: (350, 250)
            DST_HEIGHT = 400
            DST_HEIGHT_L = 350
            DST_HEIGHT_H = DST_HEIGHT - DST_HEIGHT_L
            DST_WIDTH = 500

            # 이미지 좌측 윗쪽이 (0,0)
            y_low = int(max(y - DST_HEIGHT_L, 0))
            y_high = int(min(y + DST_HEIGHT_H, SRC_HEIGHT))

            x_left = int(max(x-DST_WIDTH/2.0, 0))
            x_right = int(min(x+DST_WIDTH/2.0, SRC_WITDH))

            # 사용할 Img 자르기
            # 단, roi는 500x400이 아닐 수 있다.
            roi = src_img[y_low:y_high, x_left:x_right]

            if(y < DST_HEIGHT_L):
                new_y_low = DST_HEIGHT - y_high
                new_y_high = DST_HEIGHT
            else:
                new_y_low = 0
                new_y_high = y_high - y_low

            if (x < DST_WIDTH/2.0):
                new_x_left = DST_WIDTH - x_right
                new_x_right = DST_WIDTH
            else:
                new_x_left = 0
                new_x_right = x_right - x_left

            # roi를 base로 copy
            base[new_y_low:new_y_high, new_x_left:new_x_right] = roi

            cv2.imshow('Scaled Img', base)

        return result, base


if __name__ == '__main__':
    CAM_ID = 0  # 0: 내장 카메라, 1: 추가 카메라

    # 1) 클래스 객체 생성
    cap = Image(CAM_ID)

    while(True):
        # 2) 웹캠  읽기
        ret, frame = cap.img_read()    # ret: 수행결과(T/F), frame: 흑백 이미지

        key = cv2.waitKey(1)

        if (ret) :
            # 3) capture한 화면 출력
            cv2.imshow('Captured Img', frame)
            # q버튼으로 종료
            if key == ord('q'):
                print("quit")
                break
            # s버튼으로 circle 찾고, 이미지 전처리하고, 저장하기
            elif key == ord('s'):
                # 4) circle 찾고, 이미지 전처리
                rst, img = cap.scaled_img(frame)
                #5) 이미지 저장, '-'대신 각도 등 원하는 상태 또는 action의 저장 가능
                if rst:
                    cap.save_img(img,'-,3')

    cap.img_close()
