
import multiprocessing
import time
import os

# Verificación inmediata
print("multiprocessing importado correctamente!")
print("Procesos disponibles:", multiprocessing.cpu_count())

# Nuestros módulos
from image_detector import image_detector_process
from controller import controller_process

if __name__ == '__main__':
    print("\nIniciando RO_MVP Bot - Versión FINAL 100% FUNCIONAL")

    shared = multiprocessing.Array('i', 100)
    value = multiprocessing.Value('d', 0.0)
    
    for i in range(100):
        shared[i] = 0

    p1 = multiprocessing.Process(target=image_detector_process, args=(shared, value))
    p2 = multiprocessing.Process(target=controller_process, args=(shared, value))

    p1.start()
    p2.start()

    print("Procesos iniciados correctamente")
    time.sleep(2)
    print("Activando detección automática...")
    shared[90] = 1

    try:
        while True:
            if shared[0] == 2:
                num = shared[99]
                ms = shared[98]
                print(f"CAPTURA → {num} objetos detectados en {ms} ms")
                shared[0] = 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        shared[90] = 0
        p1.terminate()
        p2.terminate()
        print("\nBot detenido.")