/**

my_custom_radar.ino written by Cameron Rulten ©2026

**/

#include <Servo.h>
#include "SR04.h"

const int servo_pin = 9;
const int echo_pin = 11;
const int trigger_pin = 12;

SR04 mysensor = SR04(echo_pin, trigger_pin);
Servo myservo;

long distance;
int angle = 0;
int direction = 1;
bool scanning = false;

void printAngle(int angle) {
  Serial.print(angle);
  Serial.println(" degrees");
}

void printDistance(int distance) {
  Serial.print(distance);
  Serial.println(" cm");
}

// Checks for a "START" or "STOP" command from the GUI. Called once per
// sweep step (every ~20ms) so a Stop request takes effect almost immediately
// instead of waiting for a full 0-180-0 sweep to finish.
void handleSerialCommand() {
  if (!Serial.available()) {
    return;
  }
  String command = Serial.readStringUntil('\n');
  command.trim();
  if (command == "START") {
    scanning = true;
  } else if (command == "STOP") {
    scanning = false;
  }
}

void setup() {
  myservo.attach(servo_pin); // initialize servo motor
  myservo.write(angle);
  Serial.begin(9600); // initialize sensor data rate
}

void loop() {
  handleSerialCommand();

  if (!scanning) {
    delay(20); // idle - keep polling for a START command without sweeping
    return;
  }

  myservo.write(angle);
  printAngle(angle);
  delay(20);

  distance = mysensor.Distance(); // get distance from sensor
  printDistance(distance); // print distance value to screen

  angle += direction;
  if (angle >= 180) {
    angle = 180;
    direction = -1;
  } else if (angle <= 0) {
    angle = 0;
    direction = 1;
  }
}
