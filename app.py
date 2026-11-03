import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. Configuration du fichier de sauvegarde des données
DATA_FILE = "inscriptions_permanence.csv"
CODE_SECRET_ADMIN = "1234"  # Vous pouvez changer ce code secret ici

def generer_dates_planning():
    """Génère la liste exacte des dates du mercredi, jeudi et vendredi sur 3 mois à partir du 11 nov 2026."""
    date_debut = datetime(2026, 11, 11)
    date_fin = date_debut + timedelta(days=90) # ~ 3 mois
    
    jours_vises = {2: "Mercredi", 3: "Jeudi", 4: "Vendredi"}
    
    planning = []
    date_courante = date_debut
    
    while date_courante <= date_fin:
        num_jour = date_courante.weekday()
        
        if num_jour in jours_vises:
            nom_jour = jours_vises[num_jour]
            date_formatee = date_courante.strftime("%d/%m/%Y")
            label_date = f"{nom_jour} {date_formatee}"
            
            if nom_jour == "Mercredi":
                creneaux = ["10h - 14h", "14h - 18h", "18h - 22h"]
            else:
                creneaux = ["18h - 22h"]
                
            for creneau in creneaux:
                planning.append({
                    "Date": label_date,
                    "Créneau": creneau,
                    "Activité": "Non définie",
                    "Bénévole Référent": "Non assigné",
                    "Bénévole 1": "Disponible",
                    "Bénévole 2": "Disponible"
                })
                
        date_courante += timedelta(days=1)
        
    return pd.DataFrame(planning)

def charger_donnees():
    """Charge les inscriptions existantes ou initialise le calendrier."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Sécurité si les colonnes n'existent pas dans un ancien fichier
        if "Activité" not in df.columns:
            df["Activité"] = "Non définie"
        if "Bénévole Référent" not in df.columns:
            df["Bénévole Référent"] = "Non assigné"
        return df
    return generer_dates_planning()

def sauvegarder_donnees(df):
    """Enregistre le planning sur le disque."""
    df.to_csv(DATA_FILE, index=False)

# Initialisation de l'application
st.set_page_config(page_title="Permanences Association", page_icon="🗓️", layout="wide")
st.title("🗓️ Gestion des Permanences - Planning de l'Association")
st.write("Bénévoles : inscrivez-vous ci-dessous. Administrateurs : gérez les activités et référents en bas de page.")

# Chargement du planning actuel
df_planning = charger_donnees()

# --- PARTIE 1 : FILTRES VISUELS ET AFFICHAGE ---
st.subheader("📊 État actuel du planning")

recherche = st.text_input("🔍 Rechercher une date ou une activité (ex: 11/11/2026, Décembre, Atelier...) :")
df_affiche = df_planning
if recherche:
    df_affiche = df_planning[
        df_planning["Date"].str.contains(recherche, case=False) | 
        df_planning["Activité"].str.contains(recherche, case=False)
    ]

st.dataframe(df_affiche, use_container_width=True, hide_index=True)

st.markdown("---")

# --- PARTIE 2 : FORMULAIRE D'INSCRIPTION EN LIGNE (BÉNÉVOLES) ---
st.subheader("✍️ S'inscrire à un créneau (Espace Bénévole)")

creneaux_disponibles = []
for index, row in df_planning.iterrows():
    if row["Bénévole 1"] == "Disponible" or row["Bénévole 2"] == "Disponible":
        texte_choix = f"{row['Date']} ({row['Créneau']}) - Activité : {row['Activité']}"
        creneaux_disponibles.append((texte_choix, index))

if not creneaux_disponibles:
    st.success("🎉 Tous les créneaux sont complets ! Merci pour votre engagement.")
else:
    with st.form("form_inscription", clear_on_submit=True):
        nom_benevole = st.text_input("Votre Nom et Prénom :").strip()
        options_options = [c for c in creneaux_disponibles]
        choix_selectionne = st.selectbox("Choisissez votre date et créneau :", options_options)
        bouton_valider = st.form_submit_button("Valider mon inscription")
        
        if bouton_valider:
            if not nom_benevole:
                st.error("⚠️ Veuillez entrer votre nom avant de valider.")
            else:
                idx_choix = creneaux_disponibles[options_options.index(choix_selectionne)][1]
                
                if df_planning.at[idx_choix, "Bénévole 1"] == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 1"] = nom_benevole
                    st.success(f"✅ Merci {nom_benevole} ! Inscrit(e) sur le créneau (Place 1).")
                elif df_planning.at[idx_choix, "Bénévole 2"] == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 2"] = nom_benevole
                    st.success(f"✅ Merci {nom_benevole} ! Inscrit(e) sur le créneau (Place 2).")
                
                sauvegarder_donnees(df_planning)
                st.rerun()

# --- PARTIE 3 : ZONE D'ADMINISTRATION SECURISEE ---
st.markdown("---")
with st.expander("🛠️ Zone Administrateur (Gestion des Activités & Référents)"):
    
    code_saisi = st.text_input("Entrez le code secret admin pour déverrouiller :", type="password")
    
    if code_saisi == CODE_SECRET_ADMIN:
        st.success("🔓 Accès administrateur autorisé.")
        
        # Formulaire de modification d'un créneau
        st.markdown("### 📝 Assigner une Activité ou un Référent")
        
        tous_les_creneaux = [
            (f"{row['Date']} ({row['Créneau']})", index) 
            for index, row in df_planning.iterrows()
        ]
        
        options_admin = [c for c in tous_les_creneaux]
        choix_admin = st.selectbox("Sélectionnez le créneau à modifier :", options_admin)
        idx_admin = tous_les_creneaux[options_admin.index(choix_admin)][1]
        
        # Pré-remplir les champs avec les valeurs actuelles
        activite_actuelle = df_planning.at[idx_admin, "Activité"]
        referent_actuel = df_planning.at[idx_admin, "Bénévole Référent"]
        
        nouvelle_activite = st.text_input("Nom de l'activité / Description :", value=activite_actuelle)
        nouveau_referent = st.text_input("Bénévole Référent désigné :", value=referent_actuel)
        
        if st.button("💾 Enregistrer les modifications admin"):
            df_planning.at[idx_admin, "Activité"] = nouvelle_activite if nouvelle_activite else "Non définie"
            df_planning.at[idx_admin, "Bénévole Référent"] = nouveau_referent if nouveau_referent else "Non assigné"
            sauvegarder_donnees(df_planning)
            st.success("Mise à jour enregistrée avec succès !")
            st.rerun()
            
        st.markdown("---")
        st.markdown("### ⚠️ Réinitialisation globale")
        st.warning("Cette action effacera absolument toutes les données et recréera un calendrier vierge.")
        if st.button("🔄 Réinitialiser tout le planning"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.success("Le calendrier a été intégralement remis à zéro !")
            st.rerun()
    elif code_saisi != "":
        st.error("Code secret incorrect.")
