#include <FastLED.h>
#include "fire_data.h"

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
unsigned long interval = 40;          

void setup() {
  FastLED.addLeds<WS2811, LEDS1_PIN, RGB>(leds1, NUM_LEDS1);
  FastLED.addLeds<WS2811, LEDS2_PIN, RGB>(leds2, NUM_LEDS2);
  pinMode(BOARD_LED_PIN, OUTPUT);
  // Light the LED on the Teensy board to show the board
  // is working
  digitalWrite(BOARD_LED_PIN, HIGH);
}

int i = 0;
int r , g, b, ofs;
int n = 0;

void loop() {

  unsigned long currentMillis = millis();

  if(currentMillis - previousMillis > interval) {

    ofs = n*86;
    // Set LEDs
    for(i = 0; i < NUM_LEDS1; i++) {
      r = r_data[ofs + i];
      g = g_data[ofs + i];
      b = b_data[ofs + i];
      leds1[i].setRGB(r, g, b);
    }
    for(i = 0; i < NUM_LEDS2; i++) {
      r = r_data[ofs + NUM_LEDS1 + i];
      g = g_data[ofs + NUM_LEDS1 + i];
      b = b_data[ofs + NUM_LEDS1 + i];
      leds2[i].setRGB(r, g, b);
    }
    n = (n + 1) % N_SEQ;
    
    FastLED.show();

    previousMillis = currentMillis;
  }
}
