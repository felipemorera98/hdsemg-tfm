#pragma once
#include <Arduino.h>

// Opcodes ADS1298
#define CMD_WAKEUP  0x02
#define CMD_STANDBY 0x04
#define CMD_RESET   0x06
#define CMD_START   0x08
#define CMD_STOP    0x0A
#define CMD_RDATAC  0x10
#define CMD_SDATAC  0x11
#define CMD_RDATA   0x12
#define CMD_RREG    0x20
#define CMD_WREG    0x40

typedef enum {
    MODO_COMANDO,
    MODO_RREG_N,
    MODO_RREG_DATA,
    MODO_WREG_N,
    MODO_WREG_DATA
} EstadoSPI;

extern bool     rdatac_activo;
extern bool     adc_iniciado;
extern EstadoSPI estado;

void procesar_comando(uint8_t* rx, int len, uint8_t* tx_buf);