// Running light on the eight LEDs. With SW7 up, the LEDs show the switches instead.

#include "pipeRV.h"

#ifndef DELAY
#define DELAY 1000000          // loop iterations per step, about 0.2 s at 50 MHz
#endif

static void wait(uint32_t n)
{
    for (volatile uint32_t i = 0; i < n; i++)
        ;
}

int main(void)
{
    uint32_t pattern = 1;
    int left = 1;

    for (;;) {
        uint32_t sw = SWITCHES;

        if (sw & 0x80) {
            LEDS = sw;                          // mirror mode
        } else {
            LEDS = pattern;                     // running light
            pattern = left ? pattern << 1 : pattern >> 1;
            if (pattern == 0x80) left = 0;
            if (pattern == 0x01) left = 1;
        }

        wait(DELAY);
    }
}