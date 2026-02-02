/*
 * Rufus Servo Executor
 * Receives servo commands from Pi via serial
 * All gesture logic is on Pi, Arduino just executes
 *
 * SERIAL COMMAND FORMAT: "pin:angle"
 * Examples:
 *   2:90   - Move pan servo to 90 degrees
 *   4:120  - Move left arm to 120 degrees
 *   5:60   - Move right arm to 60 degrees
 *
 * SERVO PINS:
 * - Pin 2: Pan servo (head side-to-side)  [0-180°, Rest: 90°]
 * - Pin 4: Left Arm                     [50-180°, Rest: 90°]
 * - Pin 5: Right Arm                    [50-180°, Rest: 90°]
 */

#include <Servo.h>

Servo panServo;
Servo leftArm;
Servo rightArm;

int panPos = 90;
int leftArmPos = 90;
int rightArmPos = 90;

void setup() {
  Serial.begin(9600);

  panServo.attach(2);
  leftArm.attach(4);
  rightArm.attach(5);

  // Start at rest positions
  panServo.write(90);
  leftArm.write(90);
  rightArm.write(90);

  delay(500);

  Serial.println("READY");  // Tell Pi we're ready
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    // Parse "pin:angle" format
    int colonIndex = command.indexOf(':');
    if (colonIndex > 0) {
      int pin = command.substring(0, colonIndex).toInt();
      int angle = command.substring(colonIndex + 1).toInt();

      // Execute servo movement
      moveServo(pin, angle);
    }
  }
}

void moveServo(int pin, int angle) {
  // Constrain angle to safe range
  angle = constrain(angle, 0, 180);

  switch (pin) {
    case 2:
      panServo.write(angle);
      panPos = angle;
      break;
    case 4:
      leftArm.write(angle);
      leftArmPos = angle;
      break;
    case 5:
      rightArm.write(angle);
      rightArmPos = angle;
      break;
  }

  // Send acknowledgment back to Pi
  Serial.print("OK:");
  Serial.print(pin);
  Serial.print(":");
  Serial.println(angle);
}
