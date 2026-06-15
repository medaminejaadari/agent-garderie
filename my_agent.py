#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
import random
from functions import (
    creer_outil_observations_csv,
    creer_outil_observations_sql,
    creer_outil_observations_api,
    obtenir_parent_info,
    envoyer_email,
    envoyer_whatsapp_textmebot
)

def generate_summary_and_fun(raw_observations, prenom):
    """Analyse la liste brute des observations et produit un résumé et un élément amusant."""
    lines = [line.strip() for line in raw_observations.split('\n') if line.strip().startswith('-')]
    if not lines:
        return "Résumé non disponible", "😊 Profitez de chaque instant avec votre enfant !", "⭐ Continuez à encourager votre enfant."

    # Extraire les données
    repas_list = []
    sieste_list = []
    humeur_list = []
    remarque_list = []
    for line in lines:
        parts = line.split(',')
        for part in parts:
            if 'Repas =' in part:
                repas_list.append(part.split('=')[1].strip())
            if 'Sieste =' in part:
                minutes = part.split('=')[1].strip().split()[0]
                sieste_list.append(int(minutes))
            if 'Humeur =' in part:
                humeur_list.append(part.split('=')[1].strip())
            if 'Remarque =' in part:
                remarque_list.append(part.split('=')[1].strip())

    # Résumé appétit
    if all(r == 'tout mangé' for r in repas_list):
        app_text = f"{prenom} a très bien mangé tous les jours !"
    elif 'refusé' in repas_list:
        app_text = f"{prenom} a eu un petit creux un jour, mais sinon l'appétit était bon."
    else:
        app_text = f"{prenom} a bien mangé la plupart des jours."

    # Résumé sommeil
    avg_sleep = sum(sieste_list) // len(sieste_list) if sieste_list else 0
    sleep_text = f"Le sommeil était régulier, avec une moyenne de {avg_sleep} minutes de sieste par jour."

    # Résumé humeur
    happy_days = humeur_list.count('joyeux')
    sad_days = humeur_list.count('triste')
    if happy_days > sad_days:
        mood_text = f"{prenom} a été joyeux la plupart du temps, avec beaucoup de sourires 😊."
    elif sad_days > 0:
        mood_text = f"{prenom} a eu quelques moments de tristesse, mais toujours bien accompagné."
    else:
        mood_text = f"{prenom} était calme et participant."

    # Conseil
    if 'refusé' in repas_list:
        advice = "Continuez à varier les repas pour éveiller sa curiosité gustative."
    elif avg_sleep < 60:
        advice = "Veillez à un bon rituel du coucher pour optimiser son énergie."
    else:
        advice = "Félicitez-le pour son bon comportement et encouragez ses découvertes."

    summary = f"""
    <h3>📊 Résumé de la semaine</h3>
    <ul>
        <li>🍽️ {app_text}</li>
        <li>😴 {sleep_text}</li>
        <li>😊 {mood_text}</li>
        <li>💡 {advice}</li>
    </ul>
    """

    # Élément amusant
    fun_moments = [r for r in remarque_list if any(word in r for word in ['partagé', 'construit', 'peint', 'mélangé', 'rire', 'sourire'])]
    if fun_moments:
        fun_text = random.choice(fun_moments)
        fun_html = f"<h3>😄 Un moment qui a fait sourire</h3><p>✨ {fun_text} ✨</p>"
    else:
        fun_html = f"<h3>😄 Un moment qui a fait sourire</h3><p>🌟 Chaque jour est une nouvelle aventure avec {prenom} ! 🌟</p>"

    # Étoile de la semaine
    star_html = f"<h3>⭐ Étoile de la semaine</h3><p>Bravo {prenom} pour ta belle énergie et ta participation ! Continues comme ça 🌈</p>"

    return summary, fun_html, star_html

def build_html_report(raw_observations, config, prenom):
    """Convertit la liste brute en HTML complet (carte stylisée + résumé + amusant + détails)."""
    lines = [line.strip() for line in raw_observations.split('\n') if line.strip().startswith('-')]
    if not lines:
        bullets_html = f"<p>{raw_observations}</p>"
    else:
        items = ''.join([f'<li>{line[2:]}</li>' for line in lines])  # enlève le '- ' initial
        bullets_html = f'<ul>{items}</ul>'

    # Générer les sections supplémentaires
    summary, fun, star = generate_summary_and_fun(raw_observations, prenom)

    nom = config.get("nom", "Garderie")
    slogan = config.get("slogan", "")
    telephone = config.get("telephone", "01 23 45 67 89")
    email_contact = config.get("email_expediteur") or config.get("email", "contact@example.fr")
    site_web = config.get("site_web", "")
    style_bg = config.get("style_background", "linear-gradient(145deg, #f6f0ff 0%, #fdfaff 100%)")
    couleur_principale = config.get("couleur_principale", "#6d28d9")
    couleur_secondaire = config.get("couleur_secondaire", "#c084fc")

    full_html = f'''<div style="background: {style_bg}; background-image: radial-gradient(circle at 10% 20%, rgba(139,92,246,0.03) 2px, transparent 2px); background-size: 20px 20px; border-radius: 32px; padding: 10px;">
  <div style="background: rgba(255,255,255,0.96); border-radius: 28px; box-shadow: 0 20px 35px -12px rgba(0,0,0,0.15); overflow: hidden;">
    <div style="background: linear-gradient(95deg, {couleur_principale}, {couleur_secondaire}); padding: 24px 28px; text-align: center; border-bottom: 3px solid #fbbf24;">
      <h1 style="color: white; font-family: 'Segoe UI', sans-serif; font-weight: 600; font-size: 1.9rem; margin: 0;">🏫 {nom}</h1>
      <p style="color: #f3e8ff; margin: 8px 0 0 0; font-style: italic;">{slogan}</p>
    </div>
    <div style="padding: 28px 30px 20px 30px; font-family: 'Segoe UI', sans-serif; color: #1e1b2f; line-height: 1.5;">
      <h2 style="color:#2c3e50;">🏫 {nom}</h2>
      <h3 style="color:#2980b9;">📅 Rapport de la semaine pour {prenom}</h3>
      {summary}
      {fun}
      {star}
      <h3>📋 Détail jour par jour</h3>
      {bullets_html}
    </div>
    <div style="background: #faf9fe; padding: 18px 28px 24px 28px; border-top: 1px solid #e9e4f5; text-align: center;">
      <p style="margin: 0; color: #5b4b8c;">📞 {telephone} | ✉️ <a href="mailto:{email_contact}" style="color:{couleur_principale};">{email_contact}</a>{f" | 🌐 {site_web}" if site_web else ""}</p>
      <p style="margin: 12px 0 0 0; font-size: 0.75rem;">Ce compte-rendu est généré automatiquement. Pour toute question, répondez à cet email.</p>
    </div>
  </div>
</div>'''
    return full_html

def main():
    print("=" * 60)
    print("📋 Agent de rapports pour garderie (Email / WhatsApp)")
    print("=" * 60)

    base_dir = "garderies"
    if not os.path.isdir(base_dir):
        print(f"❌ Dossier '{base_dir}' introuvable.")
        return
    garderies = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    if not garderies:
        print("❌ Aucune garderie trouvée.")
        return

    print("\nGarderies disponibles :")
    for i, g in enumerate(garderies, 1):
        print(f"  {i}. {g}")
    choix = input("\nChoisissez le numéro de la garderie : ").strip()
    try:
        idx = int(choix) - 1
        garderie_nom = garderies[idx]
    except:
        print("Choix invalide.")
        return

    garderie_dir = os.path.join(base_dir, garderie_nom)
    config_path = os.path.join(garderie_dir, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {"nom": garderie_nom, "slogan": "", "telephone": "01 23 45 67 89", "email_expediteur": "contact@example.fr"}

    # --- Choix de la source de données (CSV, SQL, API) ---
    print("\n🔍 Choisissez la source des données :")
    print("  1. CSV (fichier observations.csv)")
    print("  2. SQL (base de données garderie.db)")
    print("  3. API externe (fournir l'URL)")
    source = input("Votre choix (1/2/3) : ").strip()

    if source == "1":
        outil_obs = creer_outil_observations_csv(garderie_dir)
        source_name = "CSV"
    elif source == "2":
        outil_obs = creer_outil_observations_sql(garderie_dir)
        source_name = "SQL"
    elif source == "3":
        api_url = input("URL de l'API (ex: https://api.exemple.com/observations) : ").strip()
        api_key = input("Clé API (optionnelle, laisser vide si non nécessaire) : ").strip() or None
        outil_obs = creer_outil_observations_api(api_url, api_key)
        source_name = f"API ({api_url})"
    else:
        print("Choix invalide. Utilisation du CSV par défaut.")
        outil_obs = creer_outil_observations_csv(garderie_dir)
        source_name = "CSV"

    print(f"\n✅ Garderie sélectionnée : {config.get('nom', garderie_nom)}")
    print(f"📁 Source des données : {source_name}\n")

    # --- Boucle principale ---
    while True:
        prenom = input("Prénom de l'enfant (ou 'quit') : ").strip()
        if prenom.lower() in ["quit", "exit", "q"]:
            break
        if not prenom:
            continue

        print("🔍 Récupération des observations...")
        raw_report = outil_obs.invoke({"prenom": prenom})

        if "Aucune observation" in raw_report or "Erreur" in raw_report:
            print(raw_report)
            continue

        # Construction du rapport HTML complet
        rapport_html = build_html_report(raw_report, config, prenom)

        # Aperçu (texte)
        preview = re.sub('<[^<]+?>', '', rapport_html)[:300]
        print("\n--- APERÇU (HTML converti) ---")
        print(preview + ("..." if len(preview) >= 300 else ""))
        print("--- FIN APERÇU ---\n")

        canal = input("Envoyer par (email / whatsapp / aucun) ? ").strip().lower()
        if canal == "email":
            email_parent = obtenir_parent_info(garderie_dir, prenom, "email_parent")
            if not email_parent:
                print("❌ Aucun email trouvé pour cet enfant.")
                continue
            sujet = f"Rapport hebdomadaire pour {prenom} - {config.get('nom', garderie_nom)}"
            reply_to = config.get("email_expediteur")
            success, msg = envoyer_email(email_parent, sujet, rapport_html, reply_to)
            print(msg)
        elif canal == "whatsapp":
            telephone_parent = obtenir_parent_info(garderie_dir, prenom, "telephone")
            if not telephone_parent:
                print("❌ Aucun téléphone trouvé pour cet enfant.")
                continue
            # WhatsApp reçoit le texte brut
            raw_text = re.sub('<[^<]+?>', '', rapport_html)
            success, msg = envoyer_whatsapp_textmebot(telephone_parent, raw_text)
            print(msg)
        else:
            print("Envoi annulé.")

if __name__ == "__main__":
    main()

    