/**

my_custom_radar.ino written by Cameron Rulten ©2026

**/

#include <Servo.h>
#include "SR04.h"

const int buzzer_pin = 8;
const int servo_pin = 9;
const int echo_pin = 11;
const int trigger_pin = 12;


SR04 mysensor = SR04(echo_pin,trigger_pin);
Servo myservo;

long distance;

int printDistance(int distance){
  Serial.print(distance);
  Serial.println("cm");
}

void beepBuzzer(int beep_interval){
  //activate the active buzzer
  digitalWrite(buzzer_pin, HIGH);
  delay(beep_interval);//wait for beep_interval ms
  //deactivate the active buzzer
  digitalWrite(buzzer_pin, LOW);
  delay(1);//we don't want to wait long here as the sensor is scanning quite quickly!!!
}

void setup() {

  pinMode(buzzer_pin, OUTPUT); //initialize the buzzer pin as an output
  myservo.attach(servo_pin); //initialize servo motor
  Serial.begin(9600); // initialize sensor data rate
  //delay(1000);

}

void loop() {
  // put your main code here, to run repeatedly:
  for(int i=0;i<=180;i++)
  {
    myservo.write(i); //start servo motor scanning
    delay(20);
    distance=mysensor.Distance(); //get distance from sensor
    printDistance(distance); //print distance value to screen

    if(distance < 40){
      int beep_interval = map(distance, 40, 0, 50, 1); //set the beeping interval
      beepBuzzer(beep_interval); //beep according to beep interval if object in range
    }
  }
  for(int i=180;i>=0;i--)
  {
    myservo.write(i);
    delay(20);
    distance=mysensor.Distance();
    printDistance(distance);

    if(distance < 40){
      int beep_interval = map(distance, 40, 0, 50, 1); //set the beeping interval
      beepBuzzer(beep_interval); //beep according to beep interval if object in range
    }
  }
}
