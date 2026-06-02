#pragma once
#include <Arduino.h>

#define NUM_REGISTROS  0x1A
#define NUM_ADCS       4

#define REG_ID         0x00
#define REG_CONFIG1    0x01
#define REG_CONFIG2    0x02
#define REG_CONFIG3    0x03
#define REG_LOFF       0x04
#define REG_CH1SET     0x05
#define REG_CH8SET     0x0C
#define REG_LOFF_STATP 0x12
#define REG_LOFF_STATN 0x13
#define REG_GPIO       0x14
#define REG_CONFIG4    0x17

extern uint8_t registros[NUM_ADCS][NUM_REGISTROS];

void     init_registros();
uint32_t get_periodo_us();