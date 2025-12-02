import os
import random
from PIL import Image

# Rutas de carpetas
BASE_DIR = "dataset/imagenes_base"
TRAIN_DIR = "dataset/images/train"
TEST_DIR = "dataset/images/test"

# Crear carpetas destino si no existen
os.makedirs(TRAIN_DIR, exist_ok=True)
os.makedirs(TEST_DIR, exist_ok=True)

# Obtener todas las imágenes JPEG
imagenes = [f for f in os.listdir(BASE_DIR) 
            if f.lower().endswith((".jpg", ".jpeg"))]

# Mezclar aleatoriamente
random.shuffle(imagenes)

# Calcular 70% / 30%
split_index = int(len(imagenes) * 0.7)

train_imgs = imagenes[:split_index]
test_imgs = imagenes[split_index:]

def convertir_y_guardar(lista_imgs, destino):
    for nombre in lista_imgs:
        ruta = os.path.join(BASE_DIR, nombre)

        # Abrir imagen
        img = Image.open(ruta).convert("RGB")

        # Nombre sin extensión
        nombre_png = os.path.splitext(nombre)[0] + ".png"

        # Ruta destino
        save_path = os.path.join(destino, nombre_png)

        # Guardar en PNG
        img.save(save_path, "PNG")

        print(f"Convertida: {save_path}")

# Procesar
convertir_y_guardar(train_imgs, TRAIN_DIR)
convertir_y_guardar(test_imgs, TEST_DIR)

print("Proceso completado.")
