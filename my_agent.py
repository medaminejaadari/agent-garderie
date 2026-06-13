#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
from functions import creer_executor, obtenir_parent_info, envoyer_email, envoyer_whatsapp_textmebot

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
    choix = input("\nChoisissez le numéro : ").strip()
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

    executor = creer_executor(garderie_dir, config)
    print(f"\n✅ Garderie sélectionnée : {config.get('nom', garderie_nom)}")

    while True:
        prenom = input("\nPrénom de l'enfant (ou 'quit') : ").strip()
        if prenom.lower() in ["quit", "exit", "q"]:
            break
        if not prenom:
            continue

        print("🔍 Génération du rapport...")
        try:
            result = executor.invoke({"input": prenom})
            rapport_html = result["output"]
        except Exception as e:
            print(f"❌ Erreur génération : {e}")
            continue

        # Aperçu
        rapport_texte = re.sub('<[^<]+?>', '', rapport_html)
        print("\n--- APERÇU (texte) ---")
        print(rapport_texte[:500] + ("..." if len(rapport_texte) > 500 else ""))
        print("--- FIN APERÇU ---\n")

        canal = input("Envoyer par (email / whatsapp / aucun) ? ").strip().lower()
        if canal == "email":
            email_parent = obtenir_parent_info(garderie_dir, prenom, "email_parent")
            if not email_parent:
                print("❌ Aucun email trouvé.")
                continue
            sujet = f"Rapport pour {prenom} - {config.get('nom', garderie_nom)}"
            reply_to = config.get("email_expediteur")
            success, msg = envoyer_email(email_parent, sujet, rapport_html, reply_to)
            print(msg)
        elif canal == "whatsapp":
            telephone_parent = obtenir_parent_info(garderie_dir, prenom, "telephone")
            if not telephone_parent:
                print("❌ Aucun téléphone trouvé.")
                continue
            rapport_texte = re.sub('<[^<]+?>', '', rapport_html)
            success, msg = envoyer_whatsapp_textmebot(telephone_parent, rapport_texte)
            print(msg)
        else:
            print("Envoi annulé.")

if __name__ == "__main__":
    main()