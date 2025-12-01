# detector_yolo.py  → LA VERDADERA SOLUCIÓN 2025 (fondo variable = no importa)
import os
import cv2
import numpy as np
import mss
import time
from ultralytics import YOLO

# ========================= CONFIG =========================
MODEL_PATH = "modelos_yolo/best.pt"   # ← tu modelo entrenado
CONF_THRESHOLD = 0.65
DISTANCIA_MIN = 70
# =========================================================

# Cargar modelo UNA vez (muy rápido en CPU también)
model = YOLO(MODEL_PATH)  # usa YOLOv8n.pt o YOLOv10n si lo entrenaste con v10
model.to('cpu')  # funciona genial en CPU
print(f"[YOLO] Modelo cargado: {MODEL_PATH}")

def nms_yolo(detections):
    if not detections: return []
    sorted_det = sorted(detections, key=lambda x: x['conf'], reverse=True)
    final = []
    for d in sorted_det:
        if all(np.hypot(d['x'] - f['x'], d['y'] - f['y']) >= DISTANCIA_MIN for f in final):
            final.append(d)
    return final

def detectar_yolo(pantalla_bgr):
    # Opcional: reducir un poco para más velocidad (0.7–0.8 recomendado)
    scale = 0.8
    small = cv2.resize(pantalla_bgr, (0,0), fx=scale, fy=scale)
    
    results = model(small, conf=CONF_THRESHOLD, iou=0.4, verbose=False, device='cpu')[0]
    
    detecciones = []
    inv_scale = 1.0 / scale
    
    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        conf = float(box.conf.cpu())
        cls_id = int(box.cls.cpu())
        nombre = results.names[cls_id]
        
        center_x = int(((x1 + x2) / 2) * inv_scale)
        center_y = int(((y1 + y2) / 2) * inv_scale)
        
        detecciones.append({
            'nombre': nombre,
            'x': center_x,
            'y': center_y,
            'conf': conf
        })
    
    return nms_yolo(detecciones)

# =============== PROCESO PRINCIPAL (igual que antes) ===============
def image_detector_process(SharedArray, SharedValue):
    print("[YOLO Detector] Iniciado → Fondo variable? NO PROBLEM")
    
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        
        while True:
            if SharedArray[90] == 0:  # FLAG_ACTIVO
                time.sleep(0.1)
                continue
                
            if SharedArray[0] == 1:  # FLAG_TRIGGER
                inicio = time.time()
                
                img = sct.grab(monitor)
                pantalla = cv2.cvtColor(np.array(img), cv2.COLOR_BGRA2BGR)
                resultados = detectar_yolo(pantalla)
                
                tiempo = int((time.time() - inicio) * 1000)
                SharedArray[98] = tiempo  # TIEMPO_MS

                # Limpiar y escribir (mismo formato que antes)
                for i in range(1, 90): SharedArray[i] = 0
                for i, r in enumerate(resultados[:15]):
                    base = 1 + i * 4
                    SharedArray[base]   = abs(hash(r['nombre'])) % 10000
                    SharedArray[base+1] = r['x']
                    SharedArray[base+2] = r['y']
                    SharedArray[base+3] = int(r['conf'] * 1000)
                
                SharedArray[99] = len(resultados)  # NUM_DETECCIONES
                SharedArray[0] = 2  # FLAG_TRIGGER = listo

                if resultados:
                    print(f"\n[YOLO] {len(resultados)} objetos | {tiempo} ms")
                    for r in resultados[:6]:
                        print(f"   → {r['nombre']} @ ({r['x']},{r['y']}) | {r['conf']:.3f}")
                else:
                    print(f"[YOLO] — Nada | {tiempo} ms")
                    
            time.sleep(0.02)