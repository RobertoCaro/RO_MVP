# anotar_yolo.py
import os
import cv2
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

# ------------------- CONFIGURACIÓN -------------------
CLASS_LIST = []  # se llenará la primera vez que pongas una clase
CURRENT_CLASS = 0

def draw_bbox(event, x, y, flags, param):
    global ix, iy, drawing, img, img_copy, bbox_list

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img = img_copy.copy()
            cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 2)
        bbox_list.append((ix, iy, x, y))

def save_labels_and_next():
    global img_path, bbox_list, img, CLASS_LIST, CURRENT_CLASS

    if not bbox_list:
        if not messagebox.askyesno("Sin etiquetas", "¿Guardar imagen sin etiquetas?"):
            return
        label_content = ""
    else:
        h, w = img.shape[:2]
        label_lines = []
        for (x1, y1, x2, y2) in bbox_list:
            class_id = CURRENT_CLASS
            x_center = (x1 + x2) / 2 / w
            y_center = (y1 + y2) / 2 / h
            width = (x2 - x1) / w
            height = (y2 - y1) / h
            label_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
        label_content = "\n".join(label_lines)

    # Guardar .txt
    label_path = os.path.splitext(img_path)[0] + ".txt"
    with open(label_path, "w") as f:
        f.write(label_content)

    print(f"Guardado: {os.path.basename(img_path)} → {len(bbox_list)} objetos")

    # Pasar a la siguiente imagen
    next_image()

def choose_class():
    global CURRENT_CLASS, CLASS_LIST
    class_name = simpledialog.askstring("Clase", "Nombre de la clase (ej: botella, caja, persona):")
    if class_name:
        class_name = class_name.strip()
        if class_name not in CLASS_LIST:
            CLASS_LIST.append(class_name)
            print(f"Nueva clase añadida: {class_name} → id {len(CLASS_LIST)-1}")
        CURRENT_CLASS = CLASS_LIST.index(class_name)
        root.title(f"Anotando YOLO - Clase actual: {class_name} (id {CURRENT_CLASS})")

def next_image():
    global img_path, img, img_copy, bbox_list, index, image_list

    index += 1
    bbox_list = []
    if index >= len(image_list):
        messagebox.showinfo("¡Terminado!", "Has etiquetado todas las imágenes")
        cv2.destroyAllWindows()
        root.quit()
        return

    load_image(image_list[index])

def load_image(path):
    global img_path, img, img_copy
    img_path = path
    img = cv2.imread(path)
    if img is None:
        print(f"No se pudo cargar: {path}")
        next_image()
        return
    img_copy = img.copy()
    cv2.imshow("Anotador YOLO - Pulsa S para guardar y siguiente | N para nueva clase", img)
    root.title(f"Anotando: {os.path.basename(path)} ({index+1}/{len(image_list)}) - Clase actual: {CLASS_LIST[CURRENT_CLASS] if CLASS_LIST else 'NINGUNA'}")

# ------------------- INICIO -------------------
root = tk.Tk()
root.withdraw()  # ocultar ventana principal

folder = filedialog.askdirectory(title="Selecciona la carpeta con tus imágenes")
if not folder:
    exit()

image_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".tiff")
image_list = sorted([os.path.join(folder, f) for f in os.listdir(folder) 
                    if f.lower().endswith(image_extensions)])

if not image_list:
    messagebox.showerror("Error", "No se encontraron imágenes en esa carpeta")
    exit()

# Crear carpetas de salida (misma carpeta que las imágenes)
labels_folder = os.path.join(folder, "labels")
os.makedirs(labels_folder, exist_ok=True)

# Mover .txt a la carpeta labels (opcional, pero limpio)
def mover_txt():
    for txt in [f for f in os.listdir(folder) if f.endswith(".txt")]:
        os.rename(os.path.join(folder, txt), os.path.join(labels_folder, txt))

# Variables globales
index = -1
bbox_list = []
drawing = False
ix, iy = -1, -1

# Primera clase
choose_class()

cv2.namedWindow("Anotador YOLO - Pulsa S para guardar y siguiente | N para nueva clase")
cv2.setMouseCallback("Anotador YOLO - Pulsa S para guardar y siguiente | N para nueva clase", draw_bbox)

print("\nINSTRUCCIONES:")
print("→ Dibuja rectángulos con el mouse")
print("→ Pulsa 's' para guardar y pasar a la siguiente")
print("→ Pulsa 'n' para añadir/cambiar clase")
print("→ Pulsa 'q' o ESC para salir\n")

next_image()

while True:
    key = cv2.waitKey(1) & 0xFF
    if key == ord('s') or key == ord('S'):
        save_labels_and_next()
    elif key == ord('n') or key == ord('N'):
        choose_class()
    elif key == 27 or key == ord('q'):  # ESC o q
        mover_txt()
        break

mover_txt()
cv2.destroyAllWindows()
messagebox.showinfo("¡Listo!", f"Terminado!\nEtiquetas guardadas en: {labels_folder}")
print(f"\n¡Todo listo! Carpeta labels creada con {len(os.listdir(labels_folder))} archivos")