# controller.py
import time

def controller_process(SharedArray, SharedValue):
    print("[Controller] Iniciado - Captura automática cada 1 segundo")
    ultimo = 0

    while True:
        if SharedArray[90] == 1:  # Sistema activado
            ahora = time.time()
            if ahora - ultimo >= 1.0 and SharedArray[0] != 1:  # No está procesando
                SharedArray[0] = 1  # Disparar captura
                ultimo = ahora
        else:
            ultimo = 0
        time.sleep(0.05)