from ultralytics import YOLO

model = YOLO("yolov11s.pt")  # o yolov8s.pt
model.train(data="data.yaml", epochs=100, imgsz=640, batch=16)