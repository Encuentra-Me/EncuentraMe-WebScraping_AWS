import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from pathlib import Path

# Configuración general
BASE_URL = "https://desaparecidosenperu.policia.gob.pe/Desaparecidos/"
LIST_URLS = {
    "adultos": BASE_URL + "mujer_desaparecido",
    "menores": BASE_URL + "menor_desaparecido"
}

# Configuración del backend
BACKEND_URL = "http://localhost:8080/api/v1/reports/index"
COLLECTION_ID = "personas-desaparecidas-Peru"

def create_driver():
    chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(executable_path=chromedriver_path)
    return webdriver.Chrome(service=service, options=options)

def get_alert_note_links(driver, url, max_links=10):
    driver.get(url)
    time.sleep(3)
    links = []
    buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Nota de alerta')]")
    for button in buttons:
        try:
            parent = button.find_element(By.XPATH, "./..")
            href = parent.get_attribute("href")
            if href and "nota_alerta_menor" in href:
                links.append(href)
            if len(links) >= max_links:
                break
        except:
            continue
    return links

def extract_report_data(driver, url):
    driver.get(url)
    time.sleep(1)
    try:
        def get_text_after_label(label):
            element = driver.find_element(By.XPATH, f"//b[contains(text(), '{label}')]")
            return element.find_element(By.XPATH, "following-sibling::b").text.strip()

        def get_trait_by_table(label):
            try:
                cell = driver.find_element(By.XPATH, f"//tr/td[b[text()='{label}']]/following-sibling::td[1]/b")
                return cell.text.strip()
            except:
                return None

        last_name = get_text_after_label("APELLIDOS")
        name = get_text_after_label("NOMBRES")
        age_text = get_text_after_label("EDAD")
        age = int(''.join(filter(str.isdigit, age_text)))
        born_country = get_text_after_label("PAIS DE NACIMIENTO")
        last_seen = get_text_after_label("FECHA DEL HECHO")
        place_last_seen = get_text_after_label("LUGAR DEL HECHO")

        tez = get_trait_by_table("TEZ :")
        sangre = get_trait_by_table("SANGRE :")
        contextura = get_trait_by_table("CONTEXTURA :")
        estatura = get_trait_by_table("ESTATURA :")
        cabello = get_trait_by_table("CABELLO :")
        boca = get_trait_by_table("BOCA :")
        ojos = get_trait_by_table("OJOS :")
        nariz = get_trait_by_table("NARIZ :")

        try:
            image_element = driver.find_element(By.XPATH, "//img[contains(@src, 'fotos_desaparecidos')]")
            image_url = image_element.get_attribute("src")
        except:
            image_url = None

        return {
            "name": name,
            "lastName": last_name,
            "age": age,
            "bornCountry": born_country,
            "lastSeen": last_seen,
            "placeLastSeen": place_last_seen,
            "tez": tez,
            "sangre": sangre,
            "contextura": contextura,
            "estatura": estatura,
            "cabello": cabello,
            "boca": boca,
            "ojos": ojos,
            "nariz": nariz,
            "alertNoteUrl": url,
            "image1Url": image_url,
            "collectionId": COLLECTION_ID
        }
    except Exception as e:
        print(f"❌ Error extrayendo datos de {url}: {e}")
        return None

def post_report_to_backend(report_data):
    try:
        response = requests.post(BACKEND_URL, json=report_data)
        if response.status_code == 200:
            print(f"✅ Reporte enviado con éxito: {report_data['name']} {report_data['lastName']}")
        else:
            print(f"❌ Error al enviar reporte: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Excepción al enviar reporte: {e}")

def run_scraper():
    driver = create_driver()
    try:
        for label, list_url in LIST_URLS.items():
            print(f"\n🔍 Procesando {label.upper()}...")
            links = get_alert_note_links(driver, list_url, max_links=10)
            print(f"✅ Se encontraron {len(links)} links.")
            for url in links:
                report = extract_report_data(driver, url)
                if report:
                    post_report_to_backend(report)
    finally:
        driver.quit()

if __name__ == "__main__":
    run_scraper()