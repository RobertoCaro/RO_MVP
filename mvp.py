import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import time
import random
import os
from datetime import datetime
import re 

# ====================== CONFIGURACIÓN ======================
import LocalData
USER = LocalData.USER 
PASSWORD = LocalData.PASSWORD
BASE_URL = "https://www.atlantis-ro.info"
LOGIN_URL = f"{BASE_URL}/rocp/account/login"
LOGOUT_URL = f"{BASE_URL}/rocp/account/logout"
MVP_URL = f"{BASE_URL}/rocp/ranking/mvp/"
CSV_FILE = "mvp_log.csv"

MIN_WAIT = 30   # 30 segundos
MAX_WAIT = 60   # 60 segundos
# ==========================================================

def crear_sesion():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    })
    return session

def login(session):
    try:
        # 1. Logout previo para limpiar
        print("   → Haciendo logout previo...")
        session.get(LOGOUT_URL, timeout=15)
        time.sleep(2)

        # 2. Obtener página de login
        print("   → Cargando página de login...")
        login_page = session.get(LOGIN_URL, timeout=15)
        login_page.raise_for_status()
        
        soup = BeautifulSoup(login_page.text, "html.parser")
        form = soup.find("form")
        if not form:
            print("   ❌ No se encontró <form> en la página de login")
            return False

        # 3. Buscar token CSRF de forma flexible
        token = None
        token_input = form.find("input", {"type": "hidden"})
        if token_input:
            token_name = token_input.get("name", "")
            token_value = token_input.get("value", "")
            print(f"   → Token encontrado: {token_name} = {token_value[:20]}...")
            token = {token_name: token_value}
        else:
            print("   ⚠️ No hay input hidden - Intentando sin token")
            token = {}

        # 4. Preparar payload
        payload = {
            "username": USER,
            "password": PASSWORD,
            **token  # Agregar token si existe
        }
        print(f"   → Enviando payload: username={USER}, password=***, token={list(token.keys())}")

        # 5. POST al login (usar la action de la form si existe)
        action = form.get("action", LOGIN_URL)
        if not action.startswith("http"):
            action = BASE_URL + action if action.startswith("/") else LOGIN_URL
        
        response = session.post(action, data=payload, timeout=15, allow_redirects=True)
        response.raise_for_status()

        # 6. Verificar login exitoso (múltiples checks)
        text_lower = response.text.lower()
        if any(phrase in text_lower for phrase in ["panel de control", "logout", "bienvenido", USER.lower()]):
            print(f"   ✅ Login EXITOSO con {USER}")
            # Verificar accediendo a una página protegida rápida
            test_url = f"{BASE_URL}/rocp/account/view/"
            test_resp = session.get(test_url, timeout=10)
            if "logout" in test_resp.text.lower():
                print("   → Confirmado: Sesión activa")
                return True
            else:
                print("   ⚠️ Sesión dudosa - Probando MVP...")
        else:
            print("   ❌ Login FALLÓ - Respuesta no contiene indicadores de éxito")
            print(f"   URL final: {response.url}")
            print(f"   Snippet de respuesta: {response.text[:200]}...")

        # Fallback: Probar directamente MVP
        print("   → Probando acceso directo a MVP...")
        mvp_test = session.get(MVP_URL, timeout=10)
        if "debes iniciar sesión" not in mvp_test.text.lower() and "login" not in mvp_test.url:
            print("   ✅ Acceso a MVP OK - Login implícito exitoso")
            return True

        return False

    except requests.RequestException as e:
        print(f"   ❌ Error de red en login: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error inesperado en login: {e}")
        return False

def es_respawn(character, exp_str):
    character = str(character).strip().lower()
    exp = str(exp_str).replace(",", "").strip()
    
    if character in ["ninguno", "desconocido", "unknown", "", "n/a"]:
        return 1
    if exp in ["0", "", "n/a"]:
        return 1
    try:
        if int(exp) < 1000:  # Bajo EXP también cuenta como respawn
            return 1
    except:
        pass
    return 0
def obtener_mvps(session):
    try:
        print("   → Accediendo a ranking MVP...")
        r = session.get(MVP_URL, timeout=20)
        if "login" in r.url.lower() or "debes iniciar sesión" in r.text.lower():
            print("   Sesión expirada - Redirigiendo a login")
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            print("   No se encontró tabla en la página")
            return []

        # ====================== LECTURA FIJA POR POSICIÓN (100% FUNCIONAL) ======================
        datos = []
        filas = table.find_all("tr")

        for tr in filas[1:]:  # Saltamos la fila de títulos
            tds = tr.find_all("td")
            if len(tds) < 5:      # Algunas filas son separadores
                continue

            # Extraemos por posición exacta (esto nunca falla en Atlantis RO)
            fecha_hora   = tds[0].get_text(strip=True)
            character    = tds[1].get_text(strip=True)
            mvp_monster  = tds[2].get_text(strip=True)
            exp          = tds[3].get_text(strip=True)
            mapa         = tds[4].get_text(strip=True)

            # Filtrar filas basura
            if not mapa or mapa in ["Map", "-", ""]:
                continue
            if "Date / Time" in fecha_hora:  # es el header repetido
                continue

            # Detectar respawn
            character_lower = character.lower()
            exp_limpio = exp.replace(",", "").strip()
            es_respawn_flag = 1 if (
                character_lower in ["desconocido", "ninguno", "unknown", "", "-"] or
                exp_limpio in ["0", ""]
            ) else 0

            death = "" if es_respawn_flag else character

            datos.append({
                "Map": mapa,
                "Hora": fecha_hora,
                "Respawn": es_respawn_flag,
                "Death": death
            })

            # Mostrar solo las primeras 6 como ejemplo
            if len(datos) <= 6:
                print(f"     {mapa:15} | {fecha_hora:19} | {'RESPAWN' if es_respawn_flag else death:20}")

        print(f"   EXTRAÍDOS {len(datos)} MVPs correctamente")
        return datos

    except Exception as e:
        print(f"   Error crítico en obtener_mvps: {e}")
        return []
# Las funciones actualizar_csv y el bucle principal permanecen IGUALES que en la versión anterior
# (Cópialas de ahí para no repetir código)

def actualizar_csv(datos_nuevos):
    if not datos_nuevos:
        return

    df_nuevo = pd.DataFrame(datos_nuevos)
    
    if os.path.exists(CSV_FILE):
        df_antiguo = pd.read_csv(CSV_FILE)
        if df_antiguo.empty:
            df_antiguo = pd.DataFrame(columns=["Map", "Hora", "Respawn", "Death"])
    else:
        df_antiguo = pd.DataFrame(columns=["Map", "Hora", "Respawn", "Death"])

    cambios = 0
    for _, row in df_nuevo.iterrows():
        mask = (
            (df_antiguo["Map"] == row["Map"]) & 
            (df_antiguo["Respawn"] == row["Respawn"])
        )
        if mask.any():
            idx = df_antiguo[mask].index[0]
            old_hora = df_antiguo.loc[idx, "Hora"]
            if old_hora != row["Hora"] or df_antiguo.loc[idx, "Death"] != row["Death"]:
                df_antiguo.loc[idx, "Hora"] = row["Hora"]
                df_antiguo.loc[idx, "Death"] = row["Death"]
                cambios += 1
                print(f"   ↻ Actualizado {row['Map']} (Respawn={row['Respawn']}) → {row['Hora'][:16]}")
        else:
            nueva_fila = pd.DataFrame([{**row}])
            df_antiguo = pd.concat([df_antiguo, nueva_fila], ignore_index=True)
            cambios += 1
            print(f"   ➕ Nuevo: {row['Map']} | Respawn={row['Respawn']} | {row['Hora'][:16]}")

    if cambios > 0:
        df_antiguo = df_antiguo.sort_values("Map").reset_index(drop=True)
        df_antiguo.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")
        print(f"   💾 CSV actualizado: {len(df_antiguo)} mapas únicos\n")
    else:
        print("   ℹ️ Sin cambios en esta iteración\n")

# ====================== BUCLE PRINCIPAL ======================
if __name__ == "__main__":
    print("=== MONITOR MVP ATLANTIS RO v3.1 (con DEBUG tabla) ===\n")
    os.makedirs(os.path.dirname(CSV_FILE) or ".", exist_ok=True)
    
    session = crear_sesion()
    
    # Login inicial
    if not login(session):
        print("\n❌ No se pudo loguear. Posibles causas:")
        print("   - Usuario/contraseña incorrectos (verifica MCH3 / Cc123456)")
        print("   - Sitio bloqueado temporalmente (prueba en navegador manual)")
        print("   - Cambios en el sitio (revisa el DEBUG arriba)")
        print("\n💡 Prueba manual: Abre https://www.atlantis-ro.info/rocp/account/login en tu navegador y confirma que funciona.")
        exit(1)

    print(f"\n🚀 Monitor iniciado. Archivo: {CSV_FILE}")
    print("   Presiona Ctrl+C para detener.\n")
    
    while True:
        try:
            ahora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{ahora}] 🔍 Consultando ranking MVP...")
            
            datos = obtener_mvps(session)
            
            if datos is None:
                print("   ⚠️ Sesión perdida → Relogueando...")
                if not login(session):
                    print("   ❌ Relogin falló → Esperando 10 min antes de reintento...")
                    time.sleep(6000)
                    continue
            elif datos:
                actualizar_csv(datos)
            else:
                print("   ℹ️ No se obtuvieron datos (tabla vacía o error)")

            # Relogin aleatorio cada 10-20 ciclos para mantener sesión
            if random.randint(1, 20) <= 2:
                print("   🔄 Relogin preventivo...")
                login(session)

            espera = random.randint(MIN_WAIT, MAX_WAIT)
            mins, secs = divmod(espera, 60)
            print(f"   ⏳ Esperando {mins} min {secs} seg...\n")
            time.sleep(espera)

        except KeyboardInterrupt:
            print("\n\n🛑 Detenido por el usuario. ¡Hasta la próxima!")
            break
        except Exception as e:
            print(f"   ❌ Error general: {e}")
            time.sleep(60)