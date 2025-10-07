#include <Wire.h>
#include <MPU6050.h>

MPU6050 mpu;

// Variables for angle calculation
float accelX, accelY, accelZ;
float gyroX, gyroY, gyroZ;
float pitchAccel, rollAccel;
float pitch = 0, roll = 0, yaw = 0;
unsigned long lastTime = 0;
float dt;

// Complementary filter constants
float alpha = 0.96;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  // Initialize MPU6050
  Serial.println("Initializing MPU6050...");
  mpu.initialize();
  
  // Verify connection
  if (mpu.testConnection()) {
    Serial.println("MPU6050 connection successful");
  } else {
    Serial.println("MPU6050 connection failed");
    while(1);
  }
  
  // Calibrate gyro
  Serial.println("Calibrating gyro...");
  delay(1000);
  calibrateGyro();
  Serial.println("Calibration complete");
  
  // Print header for debugging
  Serial.println("UNIVERSAL MPU6050 - Supports all Python visualizations");
  delay(1000);
}

void calibrateGyro() {
  long gx = 0, gy = 0, gz = 0;
  int numReadings = 100;
  
  for (int i = 0; i < numReadings; i++) {
    mpu.getRotation(&gyroX, &gyroY, &gyroZ);
    gx += gyroX;
    gy += gyroY;
    gz += gyroZ;
    delay(10);
  }
  
  gyroX = gx / numReadings;
  gyroY = gy / numReadings;
  gyroZ = gz / numReadings;
}

void calculateAngles() {
  // Read accelerometer and gyroscope data
  mpu.getAcceleration(&accelX, &accelY, &accelZ);
  mpu.getRotation(&gyroX, &gyroY, &gyroZ);
  
  // Calculate time difference
  unsigned long currentTime = micros();
  dt = (currentTime - lastTime) / 1000000.0;
  lastTime = currentTime;
  
  // Calculate angles from accelerometer (in degrees)
  pitchAccel = atan2(accelY, sqrt(accelX * accelX + accelZ * accelZ)) * 180 / PI;
  rollAccel = atan2(-accelX, sqrt(accelY * accelY + accelZ * accelZ)) * 180 / PI;
  
  // Remove gyro bias and convert to degrees/sec
  float gyroPitch = (gyroY - gyroY) / 131.0;
  float gyroRoll = (gyroX - gyroX) / 131.0;
  float gyroYaw = (gyroZ - gyroZ) / 131.0;
  
  // Complementary filter: combine accelerometer and gyroscope
  pitch = alpha * (pitch + gyroPitch * dt) + (1 - alpha) * pitchAccel;
  roll = alpha * (roll + gyroRoll * dt) + (1 - alpha) * rollAccel;
  yaw = yaw + gyroYaw * dt;  // Yaw from gyro only
  
  // Keep angles in reasonable range
  if (pitch > 180) pitch = 180;
  if (pitch < -180) pitch = -180;
  if (roll > 180) roll = 180;
  if (roll < -180) roll = -180;
  if (yaw > 180) yaw -= 360;
  if (yaw < -180) yaw += 360;
}

void loop() {
  calculateAngles();
  
  // UNIVERSAL OUTPUT - works with ALL Python scripts
  // Format: pitch,roll,yaw
  // Each Python script will parse what it needs
  
  Serial.print(pitch, 2);
  Serial.print(",");
  Serial.print(roll, 2); 
  Serial.print(",");
  Serial.println(yaw, 2);
  
  delay(30); // Match Python animation interval
}