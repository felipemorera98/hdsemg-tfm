#pragma once
#include <Arduino.h>

void init_emg();
void construir_trama_emg(uint8_t* tx_buf);

extern float tiempo;