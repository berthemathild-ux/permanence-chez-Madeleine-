import streamlit as st
import pandas as pd
import os

# 1. Configuration du fichier de sauvegarde des données
DATA_FILE = "inscriptions_permanence.csv"

def charger_donnees():
    """Charge les inscriptions existantes ou crée le planning avec les créneaux spécifiques."""
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    
    # Configuration précise de vos créneaux par jour
    planning_initial = [
        {"Jour": "Mercredi", "Créneau": "10h - 14h", "Bénévole 1": "Disponible", "Bénévole 2": "Disponible"},
        {"Jour": "Mercredi", "Créneau": "14h - 18h", "Bénévole 1": "Disponible", "Bénévole 2": "Disponible"},
        {"Jour": "Mercredi", "Créneau": "18h - 22h", "Bénévole 1": "Disponible", "Bénévole 2": "Disponible"},
        {"Jour": "Jeudi", "Créneau": "18h - 22h", "Bénévole 1": "Disponible", "Bénévole 2": "Disponible"},
        {"Jour": "Vendredi", "Créneau": "18h - 22h", "Bénévole 1": "Disponible", "Bénévole 2": "Disponible"}
    ]
    return pd.DataFrame(planning_initial)

def sauvegarder_donnees(df):
    """Enregistre le planning sur le disque."""
    df.to_csv(DATA_FILE, index=False)

# Initialisation de l'application
st.set_page_config(page_title="Permanences Association", page_icon="🗓️", layout="wide")
st.title("🗓️ Gestion des Permanences de l'Association")
st.write("Inscrivez-vous sur les créneaux disponibles. Maximum 2 bénévoles par créneau.")

# Chargement du planning actuel
df_planning = charger_donnees()

# --- PARTIE 1 : AFFICHAGE DU PLANNING ACTUEL ---
st.subheader("📊 État actuel du planning")
st.dataframe(df_planning, use_container_width=True, hide_index=True)

st.markdown("---")

# --- PARTIE 2 : FORMULAIRE D'INSCRIPTION EN LIGNE ---
st.subheader("✍️ S'inscrire à un créneau")

# Filtrer les créneaux qui ont encore au moins une place libre
creneaux_disponibles = []
for index, row in df_planning.iterrows():
    if row["Bénévole 1"] == "Disponible" or row["Bénévole 2"] == "Disponible":
        texte_choix = f"{row['Jour']} de {row['Créneau']}"
        creneaux_disponibles.append((texte_choix, index))

if not creneaux_disponibles:
    st.success("🎉 Tous les créneaux sont complets ! Merci pour votre engagement.")
else:
    # Création du formulaire d'inscription
    with st.form("form_inscription", clear_on_submit=True):
        nom_benevole = st.text_input("Votre Nom et Prénom :").strip()
        
        # Liste déroulante dynamique contenant uniquement les créneaux avec de la place
        options_options = [c for c in creneaux_disponibles]
        choix_selectionne = st.selectbox("Choisissez votre créneau :", options_options)
        
        bouton_valider = st.form_submit_button("Valider mon inscription")
        
        if bouton_valider:
            if not nom_benevole:
                st.error("⚠️ Veuillez entrer votre nom avant de valider.")
            else:
                # Retrouver l'index de la ligne choisie dans le tableau original
                idx_choix = creneaux_disponibles[options_options.index(choix_selectionne)][1]
                
                # Assigner la place disponible (priorité au Bénévole 1, puis Bénévole 2)
                if df_planning.at[idx_choix, "Bénévole 1"] == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 1"] = nom_benevole
                    st.success(f"✅ Merci {nom_benevole} ! Vous êtes inscrit pour le {choix_selectionne[0]} (Place 1).")
                elif df_planning.at[idx_choix, "Bénévole 2"] == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 2"] = nom_benevole
                    st.success(f"✅ Merci {nom_benevole} ! Vous êtes inscrit pour le {choix_selectionne[0]} (Place 2).")
                
                # Sauvegarde immédiate des données et rechargement visuel
                sauvegarder_donnees(df_planning)
                st.rerun()

# --- PARTIE 3 : ZONE D'ADMINISTRATION (POUR RÉINITIALISER) ---
st.markdown("---")
with st.expander("🛠️ Zone Administrateur (Masquée par défaut)"):
    st.warning("Attention : cette action videra toutes les inscriptions actuelles.")
    if st.button("🔄 Réinitialiser tout le planning"):
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        st.success("Le planning a été remis à zéro avec succès !")
        st.rerun()
