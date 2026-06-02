#include "emg_generator.h"
#include "registros.h"
#include <math.h>

float tiempo = 0.0;

static float freq_base[32],  freq_harm2[32], freq_harm3[32];
static float fase[32][3],    freq_env[32];

static const float VREF_V   = 2.4;
static const float GANANCIA = 12.0;
static const float LSB_UV   = (2.0*VREF_V/GANANCIA) / (float)(1<<23) * 1e6;
static const int32_t AMP_COUNTS   = (int32_t)(3000.0 / LSB_UV);
static const int32_t RUIDO_COUNTS = (int32_t)(80.0   / LSB_UV);

void init_emg() {
    for (int i = 0; i < 32; i++) {
        freq_base[i]  = random(200, 1500) / 10.0;
        freq_harm2[i] = freq_base[i] * (1.5 + random(0,100)/100.0);
        freq_harm3[i] = freq_base[i] * (2.5 + random(0,100)/100.0);
        fase[i][0]    = random(0, 628) / 100.0;
        fase[i][1]    = random(0, 628) / 100.0;
        fase[i][2]    = random(0, 628) / 100.0;
        freq_env[i]   = random(5, 30)  / 10.0;
    }
}

void construir_trama_emg(uint8_t* tx_buf) {
    for (int adc = 0; adc < NUM_ADCS; adc++) {
        int offset = adc * 27;

        // Status word correcto según datasheet
        tx_buf[offset + 0] = 0xC0;
        tx_buf[offset + 1] = 0x00;
        tx_buf[offset + 2] = 0x00;

        for (int ch = 0; ch < 8; ch++) {
            int    global_ch = (adc * 8) + ch;
            uint8_t chset    = registros[adc][REG_CH1SET + ch];
            int    bi        = offset + 3 + (ch * 3);

            // Canal apagado (bit 7 del CHnSET) → salida cero
            if (chset & 0x80) {
                tx_buf[bi] = tx_buf[bi+1] = tx_buf[bi+2] = 0;
                continue;
            }

            float env = fabsf(sinf(2.0*PI * freq_env[global_ch] * tiempo));
            float emg = ( 1.00f*sinf(2.0*PI*freq_base[global_ch] *tiempo+fase[global_ch][0])
                        + 0.50f*sinf(2.0*PI*freq_harm2[global_ch]*tiempo+fase[global_ch][1])
                        + 0.25f*sinf(2.0*PI*freq_harm3[global_ch]*tiempo+fase[global_ch][2])
                        ) / 1.75f;

            int32_t senal = (int32_t)(emg * AMP_COUNTS * env)
                          + random(-RUIDO_COUNTS, RUIDO_COUNTS);

            tx_buf[bi]   = (senal >> 16) & 0xFF;
            tx_buf[bi+1] = (senal >> 8)  & 0xFF;
            tx_buf[bi+2] =  senal         & 0xFF;
        }
    }
}