#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import json
import re
import sqlite3
import requests
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY manquante dans .env")

llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY, temperature=0.3)

# ---------- 1. Outil CSV ----------
def creer_outil_observations_csv(garderie_dir):
    observations_path = os.path.join(garderie_dir, "observations.csv")
    @tool
    def obtenir_observations(prenom: str) -> str:
        """Récupère les observations depuis le fichier CSV."""
        try:
            with open(observations_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                lignes = [l for l in reader if l["prenom"].lower() == prenom.lower()]
            if not lignes:
                return f"Aucune observation CSV trouvée pour {prenom}."
            lignes.sort(key=lambda x: x["date"])
            resultats = []
            for l in lignes:
                resultats.append(
                    f"- {l['date']} : Repas = {l['repas']}, Sieste = {l['sieste_minutes']} min, "
                    f"Humeur = {l['humeur']}, Activité = {l['activite_principale']}, Remarque = {l['remarque']}"
                )
            return "\n".join(resultats)
        except Exception as e:
            return f"Erreur CSV : {e}"
    return obtenir_observations

# ---------- 2. Outil SQL ----------
def creer_outil_observations_sql(garderie_dir):
    db_path = os.path.join(garderie_dir, "garderie.db")
    @tool
    def obtenir_observations_sql(prenom: str) -> str:
        """Récupère les observations depuis la base de données SQLite."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, repas, sieste_minutes, humeur, activite_principale, remarque
                FROM observations
                WHERE prenom LIKE ?
                ORDER BY date
            """, (f"%{prenom}%",))
            rows = cursor.fetchall()
            conn.close()
            if not rows:
                return f"Aucune observation SQL trouvée pour {prenom}."
            resultats = []
            for row in rows:
                resultats.append(
                    f"- {row[0]} : Repas = {row[1]}, Sieste = {row[2]} min, "
                    f"Humeur = {row[3]}, Activité = {row[4]}, Remarque = {row[5]}"
                )
            return "\n".join(resultats)
        except Exception as e:
            return f"Erreur SQL : {e}"
    return obtenir_observations_sql

# ---------- 3. Récupération email/téléphone (parents.csv) ----------
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

# ---------- 4. Prompt simplifié (sans accolades non échappées) ----------
def generer_prompt_personnalise(config):
    nom = config.get("nom", "Garderie")
    prompt_system = f"""Tu es un assistant éducatif. Génére un rapport hebdomadaire pour un enfant de la garderie {nom}.
Retourne uniquement le rapport dans le format suivant (sans aucun texte avant ou après) :

#### Alimentation
- [résumé en une phrase]

#### Sommeil
- [résumé en une phrase]

#### Humeur et comportement
- [résumé en une phrase]

#### Activités et progrès
- [résumé en une phrase]

#### Conseils pour la maison
- [résumé en une phrase]

#### Conclusion
- [une phrase positive]

Utilise les données de l'outil d'observation. Sois bienveillant et concis. Ne liste pas les dates. Remplace chaque [résumé...] par le texte approprié.
"""
    return prompt_system

# ---------- 5. Création de l'executor avec choix de l'outil ----------
def creer_executor(garderie_dir, config, tool_choice="both"):
    outil_csv = creer_outil_observations_csv(garderie_dir)
    outil_sql = creer_outil_observations_sql(garderie_dir)
    
    if tool_choice == "csv":
        outils = [outil_csv]
    elif tool_choice == "sql":
        outils = [outil_sql]
    else:
        outils = [outil_csv, outil_sql]
    
    system_prompt = generer_prompt_personnalise(config)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    agent = create_tool_calling_agent(llm, outils, prompt)
    return AgentExecutor(agent=agent, tools=outils, verbose=False, handle_parsing_errors=True, max_iterations=5)

# ---------- 6. Envoi d'email ----------
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

# ---------- 7. Envoi WhatsApp ----------
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