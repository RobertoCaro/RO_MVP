import os
import cv2
import numpy as np
import mss
import time
from ultralytics import YOLO
from pathlib import Path
import screeninfo  # pip install screeninfo

# ======================================================
#   CARGA AUTOMÁTICA DEL MODELO MÁS RECIENTE
# ======================================================
def obtener_ultimo_modelo():
    carpeta_runs = Path(__file__).parent.parent / "TrainIA_image" / "runs" / "detect"
    if not carpeta_runs.exists():
        raise FileNotFoundError(f"No existe la carpeta: {carpeta_runs}")

    modelos = list(carpeta_runs.rglob("best.pt"))
    if not modelos:
        raise FileNotFoundError("No hay best.pt → primero entrena un modelo.")

    ultimo = max(modelos, key=lambda p: p.stat().st_mtime)
    print(f"[YOLO] Modelo cargado → {ultimo.parent.parent.name}/{ultimo.name}")
    return ultimo

MODEL_PATH = obtener_ultimo_modelo()
CONF_THRESHOLD = 0.65
DISTANCIA_MIN = 70

model = YOLO(MODEL_PATH)
model.to('cpu')
print("[YOLO] Modelo listo")


# ======================================================
#   PANTALLA Y ÁREA INICIAL
# ======================================================
monitor = screeninfo.get_monitors()[0]
SCREEN_W, SCREEN_H = monitor.width, monitor.height

WINDOW_NAME = "YOLO - Configurar Área"
MINI_WINDOW = "YOLO Live"

pts_src = np.array([[0, 30], [1024, 30], [1024, 798], [0, 798]], dtype=np.float32)

dragging_point = -1
AREA_ACTIVA = True


# ======================================================
#   CALLBACK PARA EDITAR EL ÁREA A MANO
# ======================================================
def mouse_callback(event, x, y, flags, param):
    global dragging_point, pts_src
    if event == cv2.EVENT_LBUTTONDOWN:
        for i, pt in enumerate(pts_src):
            if np.hypot(x - pt[0], y - pt[1]) < 30:
                dragging_point = i
                break

    elif event == cv2.EVENT_MOUSEMOVE and dragging_point != -1:
        pts_src[dragging_point] = [x, y]

    elif event == cv2.EVENT_LBUTTONUP:
        dragging_point = -1


# ======================================================
#   RECORTAR/FILTRAR ÁREA DE INTERÉS
# ======================================================
def recortar_a_area(img):
    # puntos: top-left, top-right, bottom-right, bottom-left
    x1, y1 = int(pts_src[0][0]), int(pts_src[0][1])
    x2, y2 = int(pts_src[2][0]), int(pts_src[2][1])

    # corregir coordenadas fuera de rango
    x1 = max(0, min(x1, img.shape[1]-1))
    x2 = max(0, min(x2, img.shape[1]-1))
    y1 = max(0, min(y1, img.shape[0]-1))
    y2 = max(0, min(y2, img.shape[0]-1))

    # recorte rectangular simple (sin perspectiva)
    return img[y1:y2, x1:x2].copy(), None


# ======================================================
#   SUPRESIÓN NMS POR DISTANCIA (simple)
# ======================================================
def nms_yolo(dets):
    if not dets:
        return []
    ordenado = sorted(dets, key=lambda x: x['conf'], reverse=True)
    final = []
    for d in ordenado:
        if all(np.hypot(d['x'] - f['x'], d['y'] - f['y']) >= DISTANCIA_MIN for f in final):
            final.append(d)
    return final


# ======================================================
#   DETECCIÓN + VISUALIZACIÓN
# ======================================================
def detectar_yolo_con_area(pantalla_bgr):

    # --------------------------------------------------
    # Crear mini-ventana solo si no existe
    # --------------------------------------------------
    if cv2.getWindowProperty(MINI_WINDOW, cv2.WND_PROP_VISIBLE) < 0:
        cv2.namedWindow(MINI_WINDOW, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(MINI_WINDOW, 500, 320)
        cv2.moveWindow(MINI_WINDOW, SCREEN_W - 500, 0)

    # --------------------------------------------------
    # Recorte del área si está activada
    # --------------------------------------------------
    if AREA_ACTIVA:
        img_yolo, _ = recortar_a_area(pantalla_bgr)
    else:
        img_yolo = pantalla_bgr.copy()

    # --------------------------------------------------
    # Reducir resolución para procesar más rápido
    # --------------------------------------------------
    small = cv2.resize(img_yolo, (0,0), fx=0.8, fy=0.8)
    scale = 1 / 0.8  # corrección de coordenadas

    results = model(small, conf=CONF_THRESHOLD, iou=0.4, verbose=False, device='cpu')[0]

    detecciones = []

    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        conf = float(box.conf.cpu())
        nombre = results.names[int(box.cls.cpu())]
        # centro del bounding box (en imagen reducida)
        cx_small = (x1 + x2) / 2
        cy_small = (y1 + y2) / 2

        # escalar de vuelta al tamaño del ROI original
        cx_roi = int(cx_small * scale)
        cy_roi = int(cy_small * scale)

        # si el ROI está recortado dentro de la pantalla
        # convertir coordenadas de ROI → pantalla completa
        if AREA_ACTIVA:
            x_off = int(pts_src[0][0])
            y_off = int(pts_src[0][1])
        else:
            x_off = 0
            y_off = 0

        cx = cx_roi + x_off
        cy = cy_roi + y_off

        detecciones.append({
            'nombre': nombre,
            'x': cx,
            'y': cy,
            'conf': conf
        })

    # --------------------------------------------------
    # Dibujar detecciones correctamente escaladas
    # --------------------------------------------------
    mini = img_yolo.copy()

    for d in detecciones:
        cv2.circle(mini, (d['x'], d['y']), 12, (0,255,0), -1)
        cv2.putText(
            mini,
            f"{d['nombre']} {d['conf']:.2f}",
            (d['x'] + 18, d['y'] + 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55, (0,255,0), 2
        )

    # --------------------------------------------------
    # Mostrar mini-ventana (la imagen corregida)
    # --------------------------------------------------
    cv2.imshow(MINI_WINDOW, mini)
    cv2.waitKey(1)

    return nms_yolo(detecciones)


# ======================================================
#   PROCESO PRINCIPAL (multiprocessing)
# ======================================================
def image_detector_process(SharedArray, SharedValue):
    print("[YOLO Detector] Iniciado → Mini ventana + Área configurada")

    with mss.mss() as sct:
        monitor = sct.monitors[1]

        while True:
            if SharedArray[90] == 0:  # pausa
                time.sleep(0.1)
                continue

            if SharedArray[0] == 1:  # pedir frame
                inicio = time.time()

                img = sct.grab(monitor)
                pantalla = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)

                resultados = detectar_yolo_con_area(pantalla)

                SharedArray[98] = int((time.time() - inicio) * 1000)

                # limpiar
                for i in range(1, 90):
                    SharedArray[i] = 0

                # enviar detecciones al shared array
                for i, r in enumerate(resultados[:15]):
                    base = 1 + i * 4
                    SharedArray[base]   = abs(hash(r['nombre'])) % 10000
                    SharedArray[base+1] = r['x']
                    SharedArray[base+2] = r['y']
                    SharedArray[base+3] = int(r['conf'] * 1000)

                SharedArray[99] = len(resultados)
                SharedArray[0] = 2  # listo

                # Debug
                if resultados:
                    print(f"\n[YOLO] {len(resultados)} objetos detectados")
                    for r in resultados[:6]:
                        print(f"  → {r['nombre']} @ ({r['x']},{r['y']})   conf={r['conf']:.3f}")
                else:
                    print("[YOLO] — Nada detectado")

            time.sleep(0.02)

    cv2.destroyAllWindows()
