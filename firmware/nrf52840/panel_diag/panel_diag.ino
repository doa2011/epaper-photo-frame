// SPDX-License-Identifier: GPL-3.0-or-later
// Diagnostic only: external 3.3 V supply and verified panel adapter required.
// No automatic refresh on startup. Send uppercase R via USB serial.
#include <Arduino.h>
#include <SPI.h>

#ifndef EPD_PANEL
#error "Select EPD_PANEL: 1=GDEM0397F81, 2=GDEY116F51, 3=GDEM0213B74"
#endif
#if !defined(ARDUINO_NRF52840_PCA10056)
#error "This diagnostic is for the PCA10056 DK Arduino BSP only"
#endif

#if EPD_PANEL == 1
#include <GxEPD2_4C.h>
using Panel = GxEPD2_397c_GDEM0397F81;
using Display = GxEPD2_4C<Panel, 8>;
#define PANEL_NAME "GDEM0397F81"
#define PANEL_FOUR_COLOR 1
#elif EPD_PANEL == 2
#include <GxEPD2_4C.h>
using Panel = GxEPD2_1160c_GDEY116F51;
using Display = GxEPD2_4C<Panel, 8>;
#define PANEL_NAME "GDEY116F51"
#define PANEL_FOUR_COLOR 1
#elif EPD_PANEL == 3
#include <GxEPD2_BW.h>
using Panel = GxEPD2_213_B74;
using Display = GxEPD2_BW<Panel, 8>;
#define PANEL_NAME "GDEM0213B74"
#define PANEL_FOUR_COLOR 0
#else
#error "Unknown panel: refusing to build"
#endif

// Arduino BSP 1.7.0 PCA10056 variant: SS=P1.12, MOSI=P1.13,
// SCK=P1.15. A0=P0.03, A1=P0.04, A2=P0.28.
// Keep NFC P0.09/P0.10 free. Bare FPC requires correct adapter.
Display display(Panel(SS, A0, A1, A2));

void setup() {
  Serial.begin(115200);
}
void loop() {
  static bool announced = false;
  if (Serial && !announced) {
    Serial.print("External-power panel diagnostic: ");
    Serial.println(PANEL_NAME);
    Serial.println("Verify adapter and supply, then send R for one refresh.");
    announced = true;
  }
  if (!Serial.available() || Serial.read() != 'R') {
    delay(20);
    return;
  }
  display.init(115200);
  display.setRotation(0);
  display.setFullWindow();
  const uint16_t colors[] = {
    GxEPD_WHITE, GxEPD_BLACK,
#if PANEL_FOUR_COLOR
    GxEPD_RED, GxEPD_YELLOW
#endif
  };
  constexpr uint8_t count = sizeof(colors) / sizeof(colors[0]);
  display.firstPage();
  do {
    for (uint8_t i = 0; i < count; ++i) {
      const int16_t x0 = (int32_t)display.width() * i / count;
      const int16_t x1 = (int32_t)display.width() * (i + 1) / count;
      display.fillRect(x0, 0, x1 - x0, display.height(), colors[i]);
    }
  } while (display.nextPage());
  display.hibernate();
  // Driver return does not prove physical display or absence of timeout.
  Serial.println("Driver returned; inspect physical display and BUSY log.");
}
