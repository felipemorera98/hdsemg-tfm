#include "registros.h"

uint8_t registros[NUM_ADCS][NUM_REGISTROS];

void init_registros() {
    for (int adc = 0; adc < NUM_ADCS; adc++) {
        memset(registros[adc], 0, NUM_REGISTROS);
        registros[adc][REG_ID]      = 0x92;   // ID ADS1298
        registros[adc][REG_CONFIG1] = 0x05;   // 1000 SPS
        registros[adc][REG_CONFIG3] = 0x40;   // VREF interno ON
        for (int ch = 0; ch < 8; ch++)
            registros[adc][REG_CH1SET + ch] = 0x60;  // ganancia 12
    }
}

uint32_t get_periodo_us() {
    switch (registros[0][REG_CONFIG1] & 0x07) {
        case 0x00: return 1000000 / 32000;
        case 0x01: return 1000000 / 16000;
        case 0x02: return 1000000 / 8000;
        case 0x03: return 1000000 / 4000;
        case 0x04: return 1000000 / 2000;
        case 0x05: return 1000000 / 1000;
        case 0x06: return 1000000 / 500;
        default:   return 1000000 / 250;
    }
}