import time

INTERVALO = 0.0  # segundos

def controller_process(SharedArray, SharedValue):
    print(f"[Controller] Iniciado - Captura automática cada {INTERVALO} segundo(s)")
    ultimo = time.perf_counter()

    while True:
        if SharedArray[90] == 1:  # Sistema activado
            ahora = time.perf_counter()
            if ahora - ultimo >= INTERVALO and SharedArray[0] != 1:
                SharedArray[0] = 1  # Disparar captura
                ultimo = ahora
        time.sleep(0.05)
