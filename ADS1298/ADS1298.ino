#include "registros.h"
#include "spi_parser.h"
#include "emg_generator.h"

#define PIN_DRDY D9

uint8_t tx_buf[108];
uint8_t rx_buf[108];

void setup() {
    pinMode(PIN_DRDY, OUTPUT);
    digitalWrite(PIN_DRDY, HIGH);
    randomSeed(analogRead(A0));

    init_registros();
    init_emg();

    NRF_SPIS0->PSEL.MOSI = (uint32_t)digitalPinToPinName(D11);
    NRF_SPIS0->PSEL.MISO = (uint32_t)digitalPinToPinName(D12);
    NRF_SPIS0->PSEL.SCK  = (uint32_t)digitalPinToPinName(D13);
    NRF_SPIS0->PSEL.CSN  = (uint32_t)digitalPinToPinName(D10);
    NRF_SPIS0->CONFIG    = (SPIS_CONFIG_CPOL_ActiveHigh << SPIS_CONFIG_CPOL_Pos) |
                           (SPIS_CONFIG_CPHA_Trailing   << SPIS_CONFIG_CPHA_Pos);
    NRF_SPIS0->DEF       = 0x00;
    NRF_SPIS0->ORC       = 0xFF;
    NRF_SPIS0->ENABLE    = (SPIS_ENABLE_ENABLE_Enabled << SPIS_ENABLE_ENABLE_Pos);
}

void loop() {
    NRF_SPIS0->TASKS_ACQUIRE = 1;
    while (NRF_SPIS0->EVENTS_ACQUIRED == 0) {}
    NRF_SPIS0->EVENTS_ACQUIRED = 0;

    // Procesar lo que llegó en la transacción anterior
    uint32_t bytes_rx = NRF_SPIS0->AMOUNTRX;
    if (bytes_rx > 0)
        procesar_comando(rx_buf, bytes_rx, tx_buf);

    // Construir trama de salida
    if (rdatac_activo && adc_iniciado)
        construir_trama_emg(tx_buf);
    else
        memset(tx_buf, 0, 108);

    // Cargar buffers y liberar SPIS
    NRF_SPIS0->TXDPTR     = (uint32_t)tx_buf;
    NRF_SPIS0->RXDPTR     = (uint32_t)rx_buf;
    NRF_SPIS0->MAXTX      = 108;
    NRF_SPIS0->MAXRX      = 108;
    NRF_SPIS0->EVENTS_END = 0;
    NRF_SPIS0->TASKS_RELEASE = 1;  // ← PRIMERO liberar
    uint32_t periodo_us = get_periodo_us();
    if (rdatac_activo && adc_iniciado) {       

        tiempo += (float)periodo_us / 1e6f;
        if (tiempo > 1000.0f) tiempo = 0.0f;

        // DESPUÉS pulsar DRDY para que STM32 inicie la transacción
        digitalWrite(PIN_DRDY, LOW);
        uint32_t t0 = micros();
        while (NRF_SPIS0->EVENTS_END == 0 && (micros() - t0 < 2000)) {}
        digitalWrite(PIN_DRDY, HIGH);

        uint32_t elapsed = micros() - t0;
        if (elapsed < periodo_us)
            delayMicroseconds(periodo_us - elapsed);
    } else {
        delay(5);
    }
}