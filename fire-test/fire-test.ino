#include <FastLED.h>

// Number of leds in each strip
#define NUM_LEDS1 40
#define NUM_LEDS2 46

// For led chips like WS2812, which have a data line, ground, and power, you just
// need to define DATA_PIN.  For led chipsets that are SPI based (four wires - data, clock,
// ground, and power), like the LPD8806 define both DATA_PIN and CLOCK_PIN
// Clock pin only needed for SPI based chipsets when not using hardware SPI
#define LEDS1_PIN 2
#define LEDS2_PIN 3
#define BOARD_LED_PIN 13

// Define the array of leds
CRGB leds1[NUM_LEDS1];
CRGB leds2[NUM_LEDS2];

// To store last time LED was updated
long previousMillis = 0;
// Sample time (milliseconds)
unsigned long interval = 2000;          

void setup() {
  FastLED.addLeds<WS2811, LEDS1_PIN, RGB>(leds1, NUM_LEDS1);
  FastLED.addLeds<WS2811, LEDS2_PIN, RGB>(leds2, NUM_LEDS2);
  pinMode(BOARD_LED_PIN, OUTPUT);
  // Light the LED on the Teensy board to show the board
  // is working
  digitalWrite(BOARD_LED_PIN, HIGH);
}

int i = 0;
int i_prev = NUM_LEDS1 + NUM_LEDS2 - 1;

void loop() {

  unsigned long currentMillis = millis();

  if(currentMillis - previousMillis > interval) {

    // Set LEDs
    if(i < NUM_LEDS1) {
      leds1[i_prev].setRGB(0, 0, 0);
      leds1[i].setRGB(64, 64, 0);
      i_prev = i;
    }
    else if(i < (NUM_LEDS1 + NUM_LEDS2)) {
      leds1[i_prev].setRGB(0, 0, 0);
      leds2[i - NUM_LEDS1].setRGB(64, 64, 0);
      i_prev = i;
    }
    i++;
    if(i >= 100) {
      i = 0;
    }
    FastLED.show();

    previousMillis = currentMillis;
  }
}
