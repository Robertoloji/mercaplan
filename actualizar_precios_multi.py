import json
import re
import time
from bs4 import BeautifulSoup
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
}

# Lista de productos clave para buscar y cruzar precios en los 5 supers
PRODUCTOS_OBJETIVO = [
    "pechuga de pollo",
    "carne picada",
    "huevos",
    "arroz redondo",
    "leche semidesnatada",
    "aceite de oliva",
    "salmón",
    "tomate triturado",
    "garbanzos cocidos",
    "queso fresco batido",
    "plátano",
    "pan integral",
    "atún claro",
    "pasta macarrones",
]


def limpiar_precio(texto_precio):
  """Limpia cadenas como '3,85 €' y devuelve un float."""
  if not texto_precio:
    return None
  limpio = re.sub(r"[^\d,\.]", "", str(texto_precio)).replace(",", ".")
  try:
    return round(float(limpio), 2)
  except ValueError:
    return None


# 1. MERCADONA (API por código postal)
def extraer_mercadona(cp="28110"):
  print("🟢 Extrayendo precios reales de Mercadona...")
  resultados = []
  try:
    r = requests.get(
        "https://tienda.mercadona.es/api/categories/",
        headers=HEADERS,
        params={"postal_code": cp},
        timeout=10,
    )
    if r.status_code != 200:
      return resultados

    for cat in r.json().get("results", []):
      for sub in cat.get("categories", []):
        sub_r = requests.get(
            f"https://tienda.mercadona.es/api/categories/{sub['id']}/",
            headers=HEADERS,
            params={"postal_code": cp},
            timeout=10,
        )
        if sub_r.status_code == 200:
          for sec in sub_r.json().get("sections", []):
            for prod in sec.get("products", []):
              pi = prod.get("price_instructions", {})
              resultados.append({
                  "nombre": prod.get("display_name"),
                  "precio": limpiar_precio(pi.get("unit_price")),
                  "formato": pi.get("unit_size", ""),
              })
        time.sleep(0.05)
  except Exception as e:
    print(f"   ⚠️ Error Mercadona: {e}")
  return resultados


# 2. CARREFOUR (API de búsqueda)
def extraer_carrefour(busquedas):
  print("🔵 Extrayendo precios reales de Carrefour...")
  resultados = []
  url = "https://www.carrefour.es/search-api/query/v1/search"
  for termino in busquedas:
    try:
      r = requests.get(
          url,
          headers=HEADERS,
          params={"query": termino, "scope": "desktop", "lang": "es", "rows": 3},
          timeout=10,
      )
      if r.status_code == 200:
        for item in r.json().get("content", {}).get("docs", []):
          resultados.append({
              "nombre": item.get("display_name"),
              "precio": limpiar_precio(item.get("active_price")),
              "formato": item.get("unit_price_label", ""),
          })
      time.sleep(0.1)
    except Exception as e:
      print(f"   ⚠️ Error Carrefour ({termino}): {e}")
  return resultados


# 3. AHORRAMAS (Scraping web)
def extraer_ahorramas(busquedas):
  print("🔴 Extrayendo precios reales de Ahorramas...")
  resultados = []
  for termino in busquedas:
    try:
      r = requests.get(
          f"https://www.ahorramas.com/buscador?q={termino}",
          headers=HEADERS,
          timeout=10,
      )
      if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select(".product-tile")[:3]:
          nombre_el = card.select_one(".pdp-link a")
          precio_el = card.select_one(".sales .value")
          if nombre_el and precio_el:
            resultados.append({
                "nombre": nombre_el.get_text(strip=True),
                "precio": limpiar_precio(
                    precio_el.get("content") or precio_el.get_text()
                ),
                "formato": "",
            })
      time.sleep(0.1)
    except Exception as e:
      print(f"   ⚠️ Error Ahorramas ({termino}): {e}")
  return resultados


# 4. BM SUPERMERCADOS (Scraping web)
def extraer_bm(busquedas):
  print("🟡 Extrayendo precios reales de BM Supermercados...")
  resultados = []
  for termino in busquedas:
    try:
      r = requests.get(
          f"https://www.online.bmsupermercados.es/es/s?q={termino}",
          headers=HEADERS,
          timeout=10,
      )
      if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select(".product-item, .product-card")[:3]:
          nombre_el = card.select_one(
              ".product-title, .product-name, h2 a, h3 a"
          )
          precio_el = card.select_one(".price, .product-price")
          if nombre_el and precio_el:
            resultados.append({
                "nombre": nombre_el.get_text(strip=True),
                "precio": limpiar_precio(precio_el.get_text()),
                "formato": "",
            })
      time.sleep(0.1)
    except Exception as e:
      print(f"   ⚠️ Error BM ({termino}): {e}")
  return resultados


# 5. ALDI (Scraping web)
def extraer_aldi(busquedas):
  print("🟠 Extrayendo referencias reales de Aldi...")
  resultados = []
  for termino in busquedas:
    try:
      r = requests.get(
          f"https://www.aldi.es/busqueda.html?q={termino}",
          headers=HEADERS,
          timeout=10,
      )
      if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select(".mod-article-tile")[:3]:
          nombre_el = card.select_one(".mod-article-tile__title")
          precio_el = card.select_one(".price__wrapper")
          if nombre_el and precio_el:
            resultados.append({
                "nombre": nombre_el.get_text(strip=True),
                "precio": limpiar_precio(precio_el.get_text()),
                "formato": "",
            })
      time.sleep(0.1)
    except Exception as e:
      print(f"   ⚠️ Error Aldi ({termino}): {e}")
  return resultados


def main():
  cp = "28110"  # Tu código postal por defecto en Madrid norte
  datos = {
      "actualizado": time.strftime("%Y-%m-%d %H:%M:%S"),
      "codigo_postal": cp,
      "supermercados": {
          "mercadona": extraer_mercadona(cp),
          "carrefour": extraer_carrefour(PRODUCTOS_OBJETIVO),
          "ahorramas": extraer_ahorramas(PRODUCTOS_OBJETIVO),
          "bm": extraer_bm(PRODUCTOS_OBJETIVO),
          "aldi": extraer_aldi(PRODUCTOS_OBJETIVO),
      },
  }

  with open("precios_supermercados.json", "w", encoding="utf-8") as f:
    json.dump(datos, f, ensure_ascii=False, indent=4)

  print(
      "\n✅ ¡Fichero 'precios_supermercados.json' generado con éxito para los 5"
      " supermercados!"
  )


if __name__ == "__main__":
  main()