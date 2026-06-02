#include "spi_parser.h"
#include "registros.h"

bool rdatac_activo = false;  
bool adc_iniciado  = false;
EstadoSPI estado        = MODO_COMANDO;

static uint8_t reg_addr_actual    = 0;
static uint8_t reg_count_restante = 0;

void procesar_comando(uint8_t* rx, int len, uint8_t* tx_buf) {

    // Si hay una respuesta RREG pendiente de la transacción anterior,
    // cargarla en tx_buf ANTES de procesar el nuevo byte
    if (estado == MODO_RREG_DATA) {
        for (int r = 0; r < reg_count_restante; r++) {
            uint8_t addr = reg_addr_actual + r;
            tx_buf[r] = (addr < NUM_REGISTROS) ? registros[0][addr] : 0x00;
        }
        estado = MODO_COMANDO;
        return;  // Esta transacción solo carga la respuesta
    }

    for (int i = 0; i < len; i++) {
        uint8_t byte = rx[i];

        switch (estado) {
            case MODO_COMANDO:
                if      (byte == CMD_RDATAC) { rdatac_activo = true;  }
                else if (byte == CMD_SDATAC) { rdatac_activo = false; }
                else if (byte == CMD_START)  { adc_iniciado  = true;  }
                else if (byte == CMD_STOP)   { adc_iniciado  = false; }
                else if (byte == CMD_RESET)  {
                    init_registros();
                    rdatac_activo = false;   // ← solo añadir estas dos líneas
                    adc_iniciado  = false;   // ← dentro del bloque del RESET
                }
                else if ((byte & 0xE0) == CMD_RREG) {
                    reg_addr_actual = byte & 0x1F;
                    estado = MODO_RREG_N;
                }
                else if ((byte & 0xE0) == CMD_WREG) {
                    reg_addr_actual = byte & 0x1F;
                    estado = MODO_WREG_N;
                }
                break;

            case MODO_RREG_N:
                reg_count_restante = (byte & 0x1F) + 1;
                estado = MODO_RREG_DATA;  // Responder en siguiente transacción
                break;

            case MODO_WREG_N:
                reg_count_restante = (byte & 0x1F) + 1;
                estado = MODO_WREG_DATA;
                break;

            case MODO_WREG_DATA: {
                bool read_only = (reg_addr_actual == REG_ID         ||
                                  reg_addr_actual == REG_LOFF_STATP ||
                                  reg_addr_actual == REG_LOFF_STATN);
                if (reg_addr_actual < NUM_REGISTROS && !read_only) {
                    for (int adc = 0; adc < NUM_ADCS; adc++)
                        registros[adc][reg_addr_actual] = byte;
                }
                reg_addr_actual++;
                if (--reg_count_restante == 0)
                    estado = MODO_COMANDO;
                break;
            }

            default:
                estado = MODO_COMANDO;
        }
    }
}