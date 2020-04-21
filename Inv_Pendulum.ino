// step motor 결선 및 코드 참고
// http://blog.naver.com/ubicomputing/220517587523
// Bluetooth 결선 및 코드 참고
// https://blog.naver.com/PostView.nhn?blogId=eduino&logNo=221121406317
// AccelStepper 함수
// https://makernambo.com/66
// http://www.airspayce.com/mikem/arduino/AccelStepper/classAccelStepper.html

/////////////////////////////////////
// << Protocol >>
// $N# : Center 위치로 이동
// $CXXX# : XXX 위치로 이동
// $RXXX# : RPM을 XXX로 지정(+ 정방향(RIGHT), - 역방향(LEFT))
// //////////////////////////////////

#include <SoftwareSerial.h>
#include <AccelStepper.h>

#define MAX_BUFF 10

#define BAUD_RATE 115200

#define MAX_SPEED 300 //rpm 
#define MIN_SPEED -300 //rpm
 
#define MAX_RIGHT 1500
#define CENTER    750
#define MIN_LEFT  20

#define LEFT_EDGE 13

#define BT_TXD 7
#define BT_RXD 6

#define DEBUG Serial.println

// HW 연결
// Pin8-IN1, Pin9-IN2, Pin10-IN3, Pin11-IN4, 
// ENA, ENB의 Jumper 연결
AccelStepper myStepper(AccelStepper::FULL4WIRE, 8, 9, 10, 11);

// HW 연결
// Pin7 - TX, Pin6 - RX
// Pin6은 저항을 이용해서 분압(3.3V)해야 한다
SoftwareSerial bluetooth(BT_TXD,BT_RXD); //rxPin, txPin

char char_buff[MAX_BUFF];
int index = 0;
int send_msg = 1;
int rpm = 0;

// RPM을 Step으로 변환
// AccelStepper는 step 단위로 이동함
int rpm2step(int rpm)
{
  int step;
  // rpm = (step/200.0) * 60.0;   //200setp/round, 60sec/min
  step = (rpm/60.0) * 200.0;
  return step;
}
  
void  move_to_center(void)
{
  // 좌측 끝에 도착할때까지 이동
  while (digitalRead(LEFT_EDGE) == HIGH)
  {
    myStepper.setSpeed(rpm2step(-100));  // 좌측으로 이동
    myStepper.runSpeed();
  }
  // 정지하고 현재 위치를 좌측 끝으로 지정
  myStepper.stop();
  myStepper.setCurrentPosition(0);
  delay(500);

  // 중앙으로 이동
  myStepper.runToNewPosition(CENTER);   // 중심 위치로 이동(Block됨)
  myStepper.disableOutputs();           // 모터 전원 Off

  // 현재 위치를 Serial로 전송
  bluetooth.write("$N750#");
  DEBUG("$N750#");
}
  
void setup() {
  // Serial 설정
  Serial.begin(115200);
  bluetooth.begin(9600);

  // 좌측 끝 판단을 위한 Pin 설정
  pinMode(LEFT_EDGE, INPUT_PULLUP);

  // stepper 초기화
  myStepper.setMaxSpeed(rpm2step(300));
  myStepper.setAcceleration(rpm2step(300));
}

void loop() {
  /* 블루투스 테스트 코드
  if (bluetooth.available())  Serial.write(bluetooth.read());
  if (Serial.available())     bluetooth.write(Serial.read());
  */

  ////////////////////////////
  // 블루투스 명령 수신
  ////////////////////////////
  if (bluetooth.available() > 0)
  {
    // 한 문자 받기
    char_buff[index] = bluetooth.read();
    // 첫문자는 S로 시작
    if (char_buff[index] == '$')
    {
      // Buffer 초기화
      for(int i = 0; i<MAX_BUFF ; i++)
        char_buff[i] = '\0';
      // index를 처음 값으로 이동하고, 초기 buffer에 S 저장
      index = 0;
      char_buff[index] = '$';
    }
    
    // 초기 문자는 S로 시작되고, 끝문자는 E로 종료
    if ((char_buff[0] == '$') && (char_buff[index] == '#'))    
    {
      ///////////////////////////////////
      // RPM 변경
      ///////////////////////////////////
      if (char_buff[1] == 'R')  
      {
        String str_buff = "";
        String str_rpm = "";

        // RPM 추출
        str_buff = String(char_buff);
        str_rpm = str_buff.substring(2, index);

        // 기본 RPM
        rpm = str_rpm.toInt();
        rpm = min(MAX_SPEED, rpm);
        rpm = max(MIN_SPEED, rpm);

        // 모터 설정
        myStepper.setSpeed(rpm2step(rpm));
        DEBUG(String("New Speed(RPM): ") + String(rpm));
      }
      ///////////////////////////////////
      // 모터 출력 제어
      ///////////////////////////////////
      else if (char_buff[1] == 'A')
      {
        // 모터 활성화/비활성화
        if(char_buff[2] == 'E')
        {
          myStepper.enableOutputs();
          DEBUG("Enable Outputs");
        }
        else if (char_buff[2] == 'D')
        {
          myStepper.disableOutputs();
          DEBUG("Disable Outputs");
        }
      }
      ///////////////////////////////////
      // 지정 위치로 이동
      ///////////////////////////////////
      else if (char_buff[1] == 'C')
      {
        String str_buff, str_position, temp;
        char char_temp[32] = {0};
        int dest_position;
        
        str_buff = String(char_buff);
        str_position = str_buff.substring(2, index);

        // 목표 위치
        dest_position = str_position.toInt();
        dest_position = min(MAX_RIGHT, dest_position);
        dest_position = max(MIN_LEFT, dest_position);
        
        // 이동
        myStepper.runToNewPosition(dest_position);
        
        // 이동 완료를 알림
        temp = String("$C") + String(dest_position) + String("#");
        temp.toCharArray(char_temp, temp.length()+1);
        bluetooth.write(char_temp);
        DEBUG(char_temp);
      }
      ///////////////////////////////////
      // 중심 위치로 이동
      ///////////////////////////////////
      else if (char_buff[1] == 'N')
      {
        move_to_center();   // 중심 위치로 이동
      }
      // Buffer Clear
      for(int i = 0; i<MAX_BUFF ; i++)
        char_buff[i] = '\0';
      index = 0;
    }
    
    // 다음 문자 위치로 이동
    index = index + 1;
    
    // buffer 용량을 초과하면 Clear
    if (index >= MAX_BUFF)
    {
      for(int i = 0; i<MAX_BUFF ; i++)
        char_buff[i] = '\0';
      index = 0;
    }
  }

  ////////////////////////////
  // 모터 구동
  ////////////////////////////
  if (rpm > 0)  // 정방향
  {
    if (myStepper.currentPosition() < MAX_RIGHT)
    {
      myStepper.runSpeed();
      send_msg = 1;
    }
    else if (send_msg == 1)
    {  
      bluetooth.write("$R#");
      DEBUG("$R#");
      send_msg = 0;
    }
  }
  else if (rpm < 0)  // 역방향
  {
    if (myStepper.currentPosition() > MIN_LEFT)
    {
      myStepper.runSpeed();
      send_msg = 1;
    }
    else if (send_msg == 1)
    {
      bluetooth.write("$L#");
      DEBUG("$L#");
      send_msg = 0;
    }
  }
  else  // 정지(rpm == 0)
  {
    myStepper.disableOutputs();
  }
}
