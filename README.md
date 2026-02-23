# 📡 Monitor de Convocações – Saúde SP

Script em Python para **monitorar automaticamente** a página de convocações do Portal da Transparência da Saúde do Estado de São Paulo, detectando alterações relevantes em uma tabela específica e disparando **alertas por Telegram e e-mail** quando uma palavra-chave é encontrada.

---

## 🚀 Funcionalidades

- 🔄 Monitoramento periódico da página
- 🔍 Busca por palavra-chave na tabela de convocações
- 🧠 Detecção de mudanças via hash (evita alertas duplicados)
- 📸 Captura de print da tabela quando há alteração
- 🚨 Alerta via Telegram (com imagem)
- ✉️ Envio de e-mail automático com anexo
- 📝 Log local + log no Telegram
- 🔐 Segredos protegidos via `.env`

---

## 🌐 Página monitorada
https://portaldatransparencia.saude.sp.gov.br/convocacoes.php


---

## 🛠️ Tecnologias utilizadas

- Python 3
- Selenium (Chrome Headless)
- Requests
- SMTP (Gmail)
- Telegram Bot API
- python-dotenv


