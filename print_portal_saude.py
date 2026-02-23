import time
import smtplib
import hashlib
import os
import requests
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime
import unicodedata
import traceback
from dotenv import load_dotenv

# ==================================================
# CONFIGURAÇÕES
# ==================================================

load_dotenv()

URL = "https://portaldatransparencia.saude.sp.gov.br/convocacoes.php"
INTERVALO = 5 * 60  # 5 minutos

# ----- Gmail -----
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE")
EMAIL_SENHA = os.getenv("EMAIL_SENHA")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO")

# ----- Telegram ALERTAS -----
TELEGRAM_ALERT_TOKEN = os.getenv("TELEGRAM_ALERT_TOKEN")
TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID")

# ----- Telegram LOG -----
TELEGRAM_LOG_TOKEN = os.getenv("TELEGRAM_LOG_TOKEN")
TELEGRAM_LOG_CHAT_ID = os.getenv("TELEGRAM_LOG_CHAT_ID")

# ----- Arquivos -----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_PRINTS = os.path.join(BASE_DIR, "prints")
ARQ_HASH = os.path.join(BASE_DIR, "hash_tabela.txt")
ARQ_LOG = os.path.join(BASE_DIR, "monitor.log")

PALAVRA_CHAVE = "SEDI"

os.makedirs(PASTA_PRINTS, exist_ok=True)

# ==================================================
# VALIDAÇÃO DE AMBIENTE (IMPORTANTE)
# ==================================================

def validar_env():
    variaveis = {
        "EMAIL_REMETENTE": EMAIL_REMETENTE,
        "EMAIL_SENHA": EMAIL_SENHA,
        "EMAIL_DESTINO": EMAIL_DESTINO,
        "TELEGRAM_ALERT_TOKEN": TELEGRAM_ALERT_TOKEN,
        "TELEGRAM_ALERT_CHAT_ID": TELEGRAM_ALERT_CHAT_ID,
        "TELEGRAM_LOG_TOKEN": TELEGRAM_LOG_TOKEN,
        "TELEGRAM_LOG_CHAT_ID": TELEGRAM_LOG_CHAT_ID,
    }

    faltando = [k for k, v in variaveis.items() if not v]
    if faltando:
        raise EnvironmentError(
            f"Variáveis de ambiente ausentes: {', '.join(faltando)}"
        )

validar_env()
# ================================================== # FUNÇÕES AUXILIARES # ================================================== 

def log(msg): 
    with open(ARQ_LOG, "a", encoding="utf-8") as f: 
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n") 
    
def normalizar_texto(texto): 
    texto = texto.lower() 
    texto = unicodedata.normalize("NFKD", texto) 
    return texto.encode("ascii", "ignore").decode("utf-8")

PALAVRA_CHAVE = normalizar_texto(PALAVRA_CHAVE)

def enviar_log_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_LOG_TOKEN}/sendMessage"
        requests.post(
            url,
            data={"chat_id": TELEGRAM_LOG_CHAT_ID, "text": mensagem},
            timeout=10
        )
    except Exception:
        pass


def obter_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,3000")
    return webdriver.Chrome(options=options)


def extrair_tabela(driver):
    tabela = driver.find_element(By.TAG_NAME, "table")
    return tabela, tabela.text


def calcular_hash(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hash_mudou(hash_atual):
    if not os.path.exists(ARQ_HASH):
        return True
    return open(ARQ_HASH, "r", encoding="utf-8").read().strip() != hash_atual


def salvar_hash(hash_atual):
    with open(ARQ_HASH, "w", encoding="utf-8") as f:
        f.write(hash_atual)


def tirar_print_tabela(tabela):
    nome = f"convocacoes_{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    caminho = os.path.join(PASTA_PRINTS, nome)
    tabela.screenshot(caminho)
    return caminho


def enviar_email(arquivo):
    msg = EmailMessage()
    msg["Subject"] = "Convocação detectada – Saúde SP"
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINO
    msg.set_content("Convocação relevante detectada. Segue print.")

    with open(arquivo, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="image",
            subtype="png",
            filename=os.path.basename(arquivo)
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_REMETENTE, EMAIL_SENHA)
        smtp.send_message(msg)


def enviar_alerta(arquivo):
    url = f"https://api.telegram.org/bot{TELEGRAM_ALERT_TOKEN}/sendPhoto"
    with open(arquivo, "rb") as img:
        requests.post(
            url,
            data={
                "chat_id": TELEGRAM_ALERT_CHAT_ID,
                "caption": (
                    "🚨 Palavra-chave detectada – Convocações OSS\n"
                    f"🔎 Palavra encontrada: {PALAVRA_CHAVE.upper()}"
                )
            },
            files={"photo": img},
            timeout=15
        )


# ==================================================
# LOOP PRINCIPAL
# ==================================================

log("Monitoramento iniciado.")
enviar_log_telegram("🟢 Monitor iniciado")

while True:
    driver = None
    try:
        # === INÍCIO DA VERIFICAÇÃO ===
        enviar_log_telegram(
            f"🔄 Verificação iniciada às {datetime.now():%H:%M:%S}"
        )

        driver = obter_driver()
        driver.get(URL)
        time.sleep(5)

        tabela, texto = extrair_tabela(driver)
        texto_norm = normalizar_texto(texto)

        log(f"Tamanho do texto analisado: {len(texto_norm)}")

        if PALAVRA_CHAVE not in texto_norm:
            enviar_log_telegram("ℹ️ Palavra-chave não encontrada")
        else:
            enviar_log_telegram("🚨 Palavra-chave ENCONTRADA")

            hash_atual = calcular_hash(texto_norm)
            if hash_mudou(hash_atual):
                arquivo = tirar_print_tabela(tabela)

                enviar_alerta(arquivo)
                enviar_email(arquivo)
                salvar_hash(hash_atual)

                enviar_log_telegram("✅ Alerta enviado com sucesso")
                log("Alerta enviado.")
            else:
                enviar_log_telegram("↩️ Palavra já notificada anteriormente")

    except Exception as e:
        enviar_log_telegram(
            f"❌ Erro no monitor ({type(e).__name__})"
        )
        log("ERRO:")
        log(traceback.format_exc())

    finally:
        if driver:
            driver.quit()

    # === ESPERA REAL ENTRE CICLOS ===
    enviar_log_telegram(
        f"⏱️ Aguardando próximo ciclo ({INTERVALO // 60} min)"
    )
    time.sleep(INTERVALO)