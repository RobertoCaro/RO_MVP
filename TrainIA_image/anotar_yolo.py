# anotar_yolo_pro.py
# Anotador YOLO con estructura perfecta: images/ + labels/ (train/val/test)

import os
import cv2
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

# ============= CONFIGURACIÓN =============
CLASS_LIST = []           # se llena automáticamente
CURRENT_CLASS = 0
DRAWING = False
IX, IY = -1, -1
BBOX_LIST = []
IMG = None
IMG_COPY = None
IMG_PATH = ""
INDEX = 0
IMAGE_LIST = []

def draw_bbox(event, x, y, flags, param):
    global IX, IY, DRAWING, IMG, IMG_COPY, BBOX_LIST

    if event == cv2.EVENT_LBUTTONDOWN:
        DRAWING = True
        IX, IY = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if DRAWING:
            IMG = IMG_COPY.copy()
            cv2.rectangle(IMG, (IX, IY), (x, y), (0, 255, 0), 2)
            cv2.imshow(WINDOW_NAME, IMG)

    elif event == cv2.EVENT_LBUTTONUP:
        DRAWING = False
        x2, y2 = x, y
        if abs(x2 - IX) > 5 and abs(y2 - IY) > 5:  # evitar clics accidentales
            cv2.rectangle(IMG, (IX, IY), (x2, y2), (0, 255, 0), 2)
            BBOX_LIST.append((min(IX, x2), min(IY, y2), max(IX, x2), max(IY, y2)))
            cv2.imshow(WINDOW_NAME, IMG)

def get_split_from_path(img_path):
    # Detecta si está en train, val o test
    rel = os.path.relpath(img_path, DATASET_ROOT)
    part = rel.split(os.sep)[1]  # images/train → "train"
    if part in ["train", "val", "test"]:
        return part
    return "train"  # por defecto

def save_labels():
    global IMG_PATH, BBOX_LIST

    if not BBOX_LIST and not messagebox.askyesno("Sin etiquetas", "Esta imagen no tiene objetos. ¿Guardar vacía?"):
        return False

    h, w = IMG.shape[:2]
    lines = []
    for (x1, y1, x2, y2) in BBOX_LIST:
        xc = (x1 + x2) / 2 / w
        yc = (y1 + y2) / 2 / h
        bw = (x2 - x1) / w
        bh = (y2 - y1) / h
        lines.append(f"{CURRENT_CLASS} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

    # Ruta del label
    split = get_split_from_path(IMG_PATH)
    label_dir = os.path.join(DATASET_ROOT, "labels", split)
    os.makedirs(label_dir, exist_ok=True)
    label_path = os.path.join(label_dir, os.path.splitext(os.path.basename(IMG_PATH))[0] + ".txt")

    with open(label_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Guardado → {os.path.basename(IMG_PATH)} ({len(BBOX_LIST)} objetos) → labels/{split}/")
    return True

def next_image():
    global INDEX, IMAGE_LIST, IMG_PATH, IMG, IMG_COPY, BBOX_LIST

    INDEX += 1
    BBOX_LIST = []

    if INDEX >= len(IMAGE_LIST):
        messagebox.showinfo("¡TERMINADO!", "Has etiquetado todas las imágenes")
        cv2.destroyAllWindows()
        root.quit()
        return

    load_image(IMAGE_LIST[INDEX])

def load_image(path):
    global IMG_PATH, IMG, IMG_COPY, BBOX_LIST

    IMG_PATH = path
    IMG = cv2.imread(path)
    if IMG is None:
        print(f"No se pudo cargar: {path}")
        next_image()
        return

    IMG_COPY = IMG.copy()
    BBOX_LIST = []
    split = get_split_from_path(path)
    clase_actual = CLASS_LIST[CURRENT_CLASS] if CLASS_LIST else "NINGUNA"

    cv2.imshow(WINDOW_NAME, IMG)
    root.title(f"Anotando YOLO | {split.upper()} | {INDEX+1}/{len(IMAGE_LIST)} | {os.path.basename(path)} | Clase: {clase_actual}")

# ============= INICIO =============
root = tk.Tk()
root.withdraw()

WINDOW_NAME = "Anotador YOLO Pro - S=Guardar y siguiente | N=Cambiar clase | Q=Salir"

# 1. Seleccionar carpeta raíz del dataset (la que tiene "images" dentro)
messagebox.showinfo("Seleccionar carpeta", "Selecciona la carpeta que contiene la subcarpeta 'images'")
dataset_root = filedialog.askdirectory(title="Carpeta raíz del dataset (con carpeta 'images' dentro)")
if not dataset_root:
    exit()

DATASET_ROOT = dataset_root
images_path = os.path.join(DATASET_ROOT, "images")

if not os.path.exists(images_path):
    messagebox.showerror("Error", "No encontré la carpeta 'images' dentro de la seleccionada")
    exit()

# Recolectar todas las imágenes
extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")
IMAGE_LIST = []
for split in ["train", "val", "test"]:
    split_path = os.path.join(images_path, split)
    if os.path.exists(split_path):
        imgs = [os.path.join(split_path, f) for f in os.listdir(split_path) if f.lower().endswith(extensions)]
        IMAGE_LIST.extend(sorted(imgs))

if not IMAGE_LIST:
    messagebox.showerror("Error", "No se encontraron imágenes en images/train, val o test")
    exit()

# Crear carpetas labels si no existen
for split in ["train", "val", "test"]:
    os.makedirs(os.path.join(DATASET_ROOT, "labels", split), exist_ok=True)

# Primera clase
def choose_class():
    global CURRENT_CLASS, CLASS_LIST
    clase = simpledialog.askstring("Clase", "Nombre de la clase (ej: botella, persona, caja):")
    if clase:
        clase = clase.strip().lower()
        if clase not in [c.lower() for c in CLASS_LIST]:
            CLASS_LIST.append(clase.capitalize())
        CURRENT_CLASS = [c.lower() for c in CLASS_LIST].index(clase.lower())
        print(f"Clase actual → {CLASS_LIST[CURRENT_CLASS]} (id {CURRENT_CLASS})")

choose_class()

cv2.namedWindow(WINDOW_NAME)
cv2.setMouseCallback(WINDOW_NAME, draw_bbox)

print("\n" + "="*60)
print("   ANOTADOR YOLO PRO LISTO")
print("="*60)
print("→ Dibuja rectángulos con el mouse")
print("→ S       → Guardar y siguiente")
print("→ N       → Cambiar clase")
print("→ Q o ESC → Salir")
print("→ Las etiquetas se guardan automáticamente en labels/train, val, test")
print("="*60 + "\n")

next_image()

while True:
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s') or key == ord('S'):
        if save_labels():
            next_image()
    elif key == ord('n') or key == ord('N'):
        choose_class()
    elif key == ord('q') or key == 27:  # q o ESC
        if messagebox.askyesno("Salir", "¿Seguro que quieres salir?"):
            break

cv2.destroyAllWindows()
messagebox.showinfo("¡Todo listo!", f"Etiquetado completado!\nTotal imágenes: {len(IMAGE_LIST)}\nCarpetas labels creadas correctamente")
print(f"\n¡Perfecto! Ya puedes entrenar con Ultralytics")