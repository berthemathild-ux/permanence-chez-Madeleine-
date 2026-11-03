import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. Configuration du fichier de sauvegarde des données
DATA_FILE = "inscriptions_permanence.csv"

def generer_dates_planning():
    """Génère la liste exacte des dates du mercredi, jeudi et vendredi sur 3 mois à partir du 11 nov 2026."""
    date_debut = datetime(2026, 11, 11)
    date_fin = date_debut + timedelta(days=90) # ~ 3 mois
    
    jours_vises = {2: "Mercredi", 3: "Jeudi", 4: "Vendredi"} # 2=Mercredi, 3=Jeudi, 4=Vendredi en Python
    
    planning = []
    date_courante = date_debut
    
    while date_courante <= date_fin:
        num_jour = date_courante.weekday() # Détermine le jour de la semaine
        
        if num_jour in jours_vises:
            nom_jour = jours_vises[num_jour]
            date_formatee = date_courante.strftime("%d/%m/%Y")
            label_date = f"{nom_jour} {date_formatee}"
            
            # Application de vos créneaux spécifiques par jour
            if nom_jour == "Mercredi":
                creneaux = ["10h - 14h", "14h - 18h", "18h - 22h"]
            else: # Jeudi et Vendredi
                creneaux = ["18h - 22h"]
                
            for creneau in creneaux:
                planning.append({
                    "Date": label_date,
                    "Créneau": creneau,
                    "Bénévole 1": "Disponible",
                    "Bénévole 2": "Disponible"
                })
                
        date_courante += timedelta(days=1)
        
    return pd.DataFrame(planning)

def charger_donnees():
    """Charge les inscriptions existantes ou initialise le calendrier sur 3 mois."""
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return generer_dates_planning()

def sauvegarder_donnees(df):
    """Enregistre le planning sur le disque."""
    df.to_csv(DATA_FILE, index=False)

# Initialisation de l'application
st.set_page_config(page_title="Permanences Association", page_icon="🗓️", layout="wide")
st.title("🗓️ Gestion des Permanences - Planning sur 3 mois")
st.write("Sélectionnez une date et inscrivez-vous. Maximum 2 bénévoles par créneau.")

# Chargement du planning actuel
df_planning = charger_donnees()

# --- PARTIE 1 : FILTRES VISUELS POUR LES BÉNÉVOLES ---
st.subheader("📊 État actuel du planning")

# Optionnel : un filtre par date pour éviter que le tableau soit trop long à parcourir
recherche = st.text_input("🔍 Rechercher une date spécifique (ex: 11/11/2026 ou Décembre) :")
df_affiche = df_planning
if recherche:
    df_affiche = df_planning[df_planning["Date"].str.contains(recherche, case=False)]

st.dataframe(df_affiche, use_container_width=True, hide_index=True)

st.markdown("---")

# --- PARTIE 2 : FORMULAIRE D'INSCRIPTION EN LIGNE ---
st.subheader("✍️ S'inscrire à un créneau")

# Filtrer les créneaux qui ont encore au moins une place libre
creneaux_disponibles = []
for index, row in df_planning.iterrows():
    if row["Bénévole 1"] == "Disponible" or row["Bénévole 2"] == "Disponible":
        texte_choix = f"{row['Date']} de {row['Créneau']}"
        creneaux_disponibles.append((texte_choix, index))

if not creneaux_disponibles:
    st.success("🎉 Tous les créneaux sont complets ! Merci pour votre engagement.")
else:
    with st.form("form_inscription", clear_on_submit=True):
        nom_benevole = st.text_input("Votre Nom et Prénom :").strip()
        
        # Liste déroulante avec toutes les dates réelles sur 3 mois
        options_options = [c for c in creneaux_disponibles]
        choix_selectionne = st.selectbox("Choisissez votre date et créneau :", options_options)
        
        bouton_valider = st.form_submit_button("Valider mon inscription")
        
        if bouton_valider:
            if not nom_benevole:
                st.error("⚠️ Veuillez entrer votre nom avant de valider.")
            else:
                # Retrouver l'index de la ligne choisie
                idx_choix = creneaux_disponibles[options_options.index(choix_selectionne)][1]
                
                # Assigner la place disponible
                if df_planning.at[idx_choix, "Bénévole 1"] == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 1"] = nom_benevole
                    st.success(f"✅ Merci {nom_benevole} ! Inscrit(e) le {choix_selectionne[0]} (Place 1).")
                elif df_planning.at[idx_choix, "Bénévole 2"] == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 2"] = nom_benevole
                    st.success(f"✅ Merci {nom_benevole} ! Inscrit(e) le {choix_selectionne[0]} (Place 2).")
                
                sauvegarder_donnees(df_planning)
                st.rerun()

# --- PARTIE 3 : ZONE D'ADMINISTRATION ---
st.markdown("---")
with st.expander("🛠️ Zone Administrateur (Masquée par défaut)"):
    st.warning("Attention : cette action effacera toutes les inscriptions de ces 3 mois.")
    if st.button("🔄 Réinitialiser tout le planning"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.success("Le calendrier de 3 mois a été remis à zéro !")
        st.rerun()
