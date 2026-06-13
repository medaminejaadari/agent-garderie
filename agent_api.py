#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from functions import creer_executor, obtenir_parent_info, envoyer_email, envoyer_whatsapp_textmebot

load_dotenv()

app = Flask(__name__)
CORS(app)  # Permet les appels depuis n'importe quelle origine (site web, mobile)

# Chargement des clés API des garderies
with open("cles_api.json", "r", encoding="utf-8") as f:
    CLES_API = json.load(f)

# ---------- Endpoint 1 : Générer le rapport (HTML) ----------
@app.route("/generer_rapport", methods=["POST"])
def api_generer_rapport():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON requis"}), 400

    garderie_id = data.get("garderie_id")
    api_key = data.get("api_key")
    prenom = data.get("prenom")

    if not garderie_id or not api_key or not prenom:
        return jsonify({"error": "garderie_id, api_key et prenom sont requis"}), 400

    # Vérification de la clé API
    if CLES_API.get(garderie_id) != api_key:
        return jsonify({"error": "Clé API invalide"}), 403

    garderie_dir = os.path.join("garderies", garderie_id)
    if not os.path.isdir(garderie_dir):
        return jsonify({"error": "Garderie inconnue"}), 404

    # Chargement de la configuration de la garderie
    config_path = os.path.join(garderie_dir, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {"nom": garderie_id, "slogan": "", "telephone": "01 23 45 67 89"}

    try:
        executor = creer_executor(garderie_dir, config)
        result = executor.invoke({"input": prenom})
        rapport_html = result["output"]
        return jsonify({"status": "success", "rapport": rapport_html})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------- Endpoint 2 : Envoyer un rapport (email ou WhatsApp) ----------
@app.route("/envoyer_rapport", methods=["POST"])
def api_envoyer_rapport():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON requis"}), 400

    garderie_id = data.get("garderie_id")
    api_key = data.get("api_key")
    prenom = data.get("prenom")
    canal = data.get("canal")          # "email" ou "whatsapp"
    contenu = data.get("contenu")      # HTML pour email, texte pour WhatsApp

    if not all([garderie_id, api_key, prenom, canal, contenu]):
        return jsonify({"error": "garderie_id, api_key, prenom, canal, contenu requis"}), 400

    if CLES_API.get(garderie_id) != api_key:
        return jsonify({"error": "Clé API invalide"}), 403

    garderie_dir = os.path.join("garderies", garderie_id)
    if not os.path.isdir(garderie_dir):
        return jsonify({"error": "Garderie inconnue"}), 404

    if canal == "email":
        coordonnee = obtenir_parent_info(garderie_dir, prenom, "email_parent")
        if not coordonnee:
            return jsonify({"error": "Email parent introuvable"}), 404
        config_path = os.path.join(garderie_dir, "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}
        sujet = f"Rapport pour {prenom} - {config.get('nom', garderie_id)}"
        reply_to = config.get("email_expediteur")
        success, msg = envoyer_email(coordonnee, sujet, contenu, reply_to)
    elif canal == "whatsapp":
        coordonnee = obtenir_parent_info(garderie_dir, prenom, "telephone")
        if not coordonnee:
            return jsonify({"error": "Téléphone parent introuvable"}), 404
        success, msg = envoyer_whatsapp_textmebot(coordonnee, contenu)
    else:
        return jsonify({"error": "canal doit être 'email' ou 'whatsapp'"}), 400

    if success:
        return jsonify({"status": "success", "message": msg})
    else:
        return jsonify({"error": msg}), 500

# ---------- Lancement du serveur ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)