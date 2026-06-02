def decodificar_24bits(b1: int, b2: int, b3: int) -> int:
    """Convierte 3 bytes big-endian en un entero con signo de 24 bits."""
    valor = (b1 << 16) | (b2 << 8) | b3
    if valor & 0x800000:
        valor -= 0x1000000
    return valor


def decodificar_paquete(paquete: bytes) -> list[int]:
    """
    Decodifica un paquete de 108 bytes y devuelve los 32 valores de canal.
    Estructura por ADC (×4): [sync(1), status(2), ch0..ch7 (3 bytes cada uno)]
    """
    valores = []
    for adc in range(4):
        offset = adc * 27
        for ch in range(8):
            ib = offset + 3 + (ch * 3)
            valores.append(
                decodificar_24bits(paquete[ib], paquete[ib + 1], paquete[ib + 2])
            )
    return valores