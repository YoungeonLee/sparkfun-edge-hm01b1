// Reference
// https://github.com/sparkfun/SparkFun_HM01B0_Camera_ArduinoLibrary/blob/master/examples/Example1_StopMotion/Example1_StopMotion.ino

#include "hm01b0_arduino.h"
#include "String.h"

#define SERIAL_PORT Serial
#define BAUD_RATE   230400

HM01B0 myCamera;            // Declare an HM01B0 object called 'myCamera'
                            // The camera will try to specialize for the host architecture 
                            // however it will fall back to a slow generic interface if no
                            // specialization is available. 
                            // The default is not guaranteed to work due to the high amount 
                            // of data the camera needs to transfer

// Forward declarations
void printWord(uint32_t num);
void printByte(uint8_t num);

void setup() {
  // Start up serial monitor
  SERIAL_PORT.begin(BAUD_RATE);
  do {
    delay(500);
  }while(!SERIAL_PORT);

  // Turn on camera regulator if using Edge board
#if defined (ARDUINO_SFE_EDGE)
  pinMode(AM_BSP_GPIO_CAMERA_HM01B0_DVDDEN, OUTPUT);
  digitalWrite(AM_BSP_GPIO_CAMERA_HM01B0_DVDDEN, HIGH);
  SERIAL_PORT.println("Turned on Edge camera regulator");
#endif

  // Start the camera
  if(myCamera.begin() != HM01B0_ERR_OK){
    SERIAL_PORT.print("Camera.begin() failed with code: " + String(myCamera.status) + "\n");
  }else{
    SERIAL_PORT.print("Camera started successfully\n");
  }

  // Calibrate Autoexposure
  SERIAL_PORT.println("Calibrating Auto Exposure..."); 
  myCamera.calibrateAutoExposure();
  if(myCamera.status != HM01B0_ERR_OK){
    SERIAL_PORT.println("\tnot converged"); 
  }else{
    SERIAL_PORT.println("\tconverged!");
  }

  SERIAL_PORT.print("Ready\n");                                                  // Newlines allow Python script to find frame start
}

void loop() {
  if (SERIAL_PORT.available() > 0) {
    int command = SERIAL_PORT.read();
    if (command == 0x55) {
      SERIAL_PORT.println("Capturing image");
      myCamera.capture();
      framebuffer_dump();
    }
  }
  // size_t size = Serial.readBytesUntil(0x55)
  // if (teststr.startsWith(String(0x55))) {
  //   SERIAL_PORT.println("Capture detected");
  // } else {
  //   SERIAL_PORT.println("Waiting");
  // }
  // SERIAL_PORT.print(size);                                                       // Newlines allow Python script to find frame start

  // Take an image
  // myCamera.capture();
  // SERIAL_PORT.print("Captured an image\n");
  // framebuffer_dump();
  // delay(1000000);
}

// Utility functions

// hex formating
// Thanks to bootsector on the Arduino forums:
// https://forum.arduino.cc/index.php?topic=38107.msg282336#msg282336
void printWord(uint32_t num) {
  char tmp[9];                  // 8 hex digits + null terminator
  sprintf(tmp, "%08X", num); 
  SERIAL_PORT.print(tmp);
}

void printByte(uint8_t num) {
  char tmp[3];                  // 2 hex digits + null terminator
  sprintf(tmp, "%02X", num); 
  SERIAL_PORT.print(tmp);
}

// frame buffer dump (formatted for python script)
void framebuffer_dump( void ){  
  SERIAL_PORT.print("+++ frame +++");                                         // Mark frame start
  for (uint32_t ui32Idx = 0; ui32Idx < myCamera.frameBufferSize; ui32Idx++){  // Process all bytes in frame
    if ((ui32Idx & 0xF) == 0x00){                                             // Print address every 16 bytes
      SERIAL_PORT.print("\n0x");
      printWord(ui32Idx);
      SERIAL_PORT.print(" ");         
    }            
    printByte(myCamera.frameBuffer[ui32Idx]);                                 // Print byte value
    SERIAL_PORT.print(" ");
  }
  SERIAL_PORT.print("\n--- frame ---\n");
  memset(myCamera.frameBuffer, 0x00, sizeof(myCamera.frameBufferSize));       // Zero out frame buffer for help identifying errors
}
