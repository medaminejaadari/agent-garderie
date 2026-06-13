#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import json
import re
import requests
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# ---------- Chargement des variables d'environnement ----------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY manquante dans .env")

# ---------- LLM global (une seule instance) ----------
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.3,
)

# ---------- 1. Outil dynamique (lecture CSV) ----------
def creer_outil_observations(garderie_dir):
    observations_path = os.path.join(garderie_dir, "observations.csv")
    @tool
    def obtenir_observations(prenom: str) -> str:
        """Récupère toutes les observations d'un enfant dans cette garderie."""
        try:
            with open(observations_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                lignes = [l for l in reader if l["prenom"].lower() == prenom.lower()]
            if not lignes:
                return f"Aucune observation trouvée pour {prenom}."
            lignes.sort(key=lambda x: x["date"])
            resultats = []
            for l in lignes:
                resultats.append(
                    f"- {l['date']} : Repas = {l['repas']}, Sieste = {l['sieste_minutes']} min, "
                    f"Humeur = {l['humeur']}, Activité = {l['activite_principale']}, Remarque = {l['remarque']}"
                )
            return "\n".join(resultats)
        except Exception as e:
            return f"Erreur : {e}"
    return obtenir_observations

# ---------- 2. Récupération email/téléphone d'un parent ----------
def obtenir_parent_info(garderie_dir, prenom, champ):
    parents_path = os.path.join(garderie_dir, "parents.csv")
    try:
        with open(parents_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["prenom"].lower() == prenom.lower():
                    return row.get(champ)
        return None
    except:
        return None

# ---------- 3. Génération du prompt personnalisé (avec HTML) ----------
def generer_prompt_personnalise(config):
    nom = config.get("nom", "Garderie")
    slogan = config.get("slogan", "")
    telephone = config.get("telephone", "01 23 45 67 89")
    email_contact = config.get("email_expediteur") or config.get("email", "contact@example.fr")
    site_web = config.get("site_web", "")
    style_bg = config.get("style_background", "linear-gradient(145deg, #f6f0ff 0%, #fdfaff 100%)")
    couleur_principale = config.get("couleur_principale", "#6d28d9")
    couleur_secondaire = config.get("couleur_secondaire", "#c084fc")

    prompt_system = f"""Tu es un assistant éducatif. Génére un rapport HTML structuré selon le modèle ci-dessous.
Utilise l'outil 'obtenir_observations' pour obtenir les données réelles.

Modèle HTML (à suivre exactement) :

<div style="background: {style_bg}; border-radius: 32px; padding: 10px;">
  <div style="background: rgba(255,255,255,0.96); border-radius: 28px; box-shadow: 0 20px 35px -12px rgba(0,0,0,0.15); overflow: hidden;">
    <div style="background: linear-gradient(95deg, {couleur_principale}, {couleur_secondaire}); padding: 24px 28px; text-align: center;">
      <h1 style="color: white;">🏫 {nom}</h1>
      <p style="color: #f3e8ff;">{slogan}</p>
    </div>
    <div style="padding: 28px;">
      <h2>🏫 {nom}</h2>
      <h3>📅 Rapport de la semaine pour [PRÉNOM]</h3>
      <h3>🍽️ Alimentation</h3>
      <ul><li>...</li></ul>
      <h3>😴 Sommeil</h3>
      <ul><li>...</li></ul>
      <h3>😊 Humeur</h3>
      <ul><li>...</li></ul>
      <h3>🎨 Activités</h3>
      <ul><li>...</li></ul>
      <h3>💡 Conseils</h3>
      <ul><li>...</li></ul>
      <h3>👋 Conclusion</h3>
      <p>...</p>
    </div>
    <div style="background: #faf9fe; padding: 18px; text-align: center;">
      📞 {telephone} | ✉️ {email_contact} {f"| 🌐 {site_web}" if site_web else ""}
    </div>
  </div>
</div>
Sois bienveillant. N'invente pas de données.
"""
    return prompt_system

# ---------- 4. Création de l'executor (agent) pour une garderie ----------
def creer_executor(garderie_dir, config):
    outil = creer_outil_observations(garderie_dir)
    system_prompt = generer_prompt_personnalise(config)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, [outil], prompt)
    return AgentExecutor(agent=agent, tools=[outil], verbose=False, handle_parsing_errors=True)

# ---------- 5. Envoi d'email ----------
def envoyer_email(destinataire, sujet, contenu_html, reply_to=None):
    expediteur = os.getenv("SENDER_EMAIL")
    mot_de_passe = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    if not expediteur or not mot_de_passe:
        return False, "Identifiants email manquants"
    msg = EmailMessage()
    msg["From"] = expediteur
    msg["To"] = destinataire
    msg["Subject"] = sujet
    if reply_to:
        msg["Reply-To"] = reply_to
    texte_brut = re.sub('<[^<]+?>', '', contenu_html)
    msg.set_content(texte_brut)
    html_complet = f"<html><body>{contenu_html}</body></html>"
    msg.add_alternative(html_complet, subtype="html")
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(expediteur, mot_de_passe)
            server.send_message(msg)
        return True, "Email envoyé"
    except Exception as e:
        return False, str(e)

# ---------- 6. Envoi WhatsApp via TextMeBot ----------
def envoyer_whatsapp_textmebot(destinataire: str, contenu_texte: str) -> tuple:
    api_key = os.getenv("TEXTMEBOT_API_KEY")
    if not api_key:
        return False, "Clé API TextMeBot manquante dans .env"
    numero = destinataire.strip().replace(" ", "").replace("-", "")
    if not numero.startswith("+"):
        return False, "Le numéro doit être au format international (+216...)"
    url = f"https://api.textmebot.com/send.php?recipient={numero}&apikey={api_key}&text={contenu_texte}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return True, f"WhatsApp envoyé à {destinataire}"
        else:
            return False, f"Erreur API: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Erreur réseau : {e}"