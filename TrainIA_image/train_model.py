from ultralytics import YOLO

# Estos 4 funcionan 100% seguro con internet:
model = YOLO("yolov8n.pt")   # nano  (muy rápido)
#model = YOLO("yolov8s.pt")   # small (recomendado para empezar)
#model = YOLO("yolov8m.pt")   # medium
#model = YOLO("yolov11n.pt")  # YOLOv11 nano (el más nuevo)
# model = YOLO("yolov11s.pt")  # este también funciona si tienes ultralytics >= 8.3.0

model = YOLO("yolov8s.pt")  # o yolov8s.pt
model.train(data="data.yaml", epochs=100, imgsz=640, batch=16)