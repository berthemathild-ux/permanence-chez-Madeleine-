import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. Configuration du fichier de sauvegarde des données
DATA_FILE = "inscriptions_permanence.csv"
CODE_SECRET_ADMIN = "1234"  # Pensez à modifier ce code secret pour plus de sécurité

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
                    "Bénévole 1 Email": "",
                    "Bénévole 2": "Disponible",
                    "Bénévole 2 Email": ""
                })
                
        date_courante += timedelta(days=1)
        
    return pd.DataFrame(planning)

def charger_donnees():
    """Charge les inscriptions existantes ou initialise le calendrier."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Assurer la présence des bonnes colonnes
        for col in ["Activité", "Bénévole Référent", "Bénévole 1", "Bénévole 1 Email", "Bénévole 2", "Bénévole 2 Email"]:
            if col not in df.columns:
                df[col] = "" if "Email" in col else "Disponible"
        return df
    return generer_dates_planning()

def sauvegarder_donnees(df):
    """Enregistre le planning sur le disque."""
    df.to_csv(DATA_FILE, index=False)

# Initialisation de l'application
st.set_page_config(page_title="Permanences Chez Madeleine", page_icon="🗓️", layout="wide")
st.title("🗓️ Gestion des permanences \"Chez Madeleine\"")

# Chargement du planning actuel
df_planning = charger_donnees()

# --- PARTIE 1 : FORMULAIRE D'INSCRIPTION EN LIGNE (BÉNÉVOLES EN HAUT) ---
st.subheader("✍️ S'inscrire à un créneau (Espace Bénévole)")

# Construire la liste des choix disponibles avec leur index réel
options_creneaux = {}
for idx, row in df_planning.iterrows():
    if str(row["Bénévole 1"]) == "Disponible" or str(row["Bénévole 2"]) == "Disponible":
        texte_choix = f"{row['Date']} ({row['Créneau']}) - Activité : {row['Activité']}"
        options_creneaux[texte_choix] = idx

if not options_creneaux:
    st.success("🎉 Tous les créneaux sont complets ! Merci pour votre engagement.")
else:
    with st.form("form_inscription", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            prenom = st.text_input("Votre Prénom :").strip()
            nom = st.text_input("Votre Nom :").strip()
        with col2:
            email = st.text_input("Votre Adresse Mail :").strip()
            
        choix_selectionne = st.selectbox("Choisissez votre date et créneau :", list(options_creneaux.keys()))
        bouton_valider = st.form_submit_button("Valider mon inscription")
        
        if bouton_valider:
            if not nom or not prenom or not email:
                st.error("⚠️ Veuillez remplir tous les champs (Nom, Prénom et Adresse Mail) avant de valider.")
            elif "@" not in email or "." not in email:
                st.error("⚠️ Veuillez entrer une adresse mail valide.")
            else:
                idx_choix = options_creneaux[choix_selectionne]
                identite_complete = f"{prenom} {nom.upper()}"
                
                if str(df_planning.at[idx_choix, "Bénévole 1"]) == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 1"] = identite_complete
                    df_planning.at[idx_choix, "Bénévole 1 Email"] = email
                    st.success(f"✅ Merci {prenom} ! Inscription validée (Place 1).")
                elif str(df_planning.at[idx_choix, "Bénévole 2"]) == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 2"] = identite_complete
                    df_planning.at[idx_choix, "Bénévole 2 Email"] = email
                    st.success(f"✅ Merci {prenom} ! Inscription validée (Place 2).")
                
                sauvegarder_donnees(df_planning)
                st.rerun()

st.markdown("---")

# --- PARTIE 2 : AFFICHAGE DU PLANNING ACTUEL (EN DESSOUS) ---
st.subheader("📊 État actuel du planning")

recherche = st.text_input("🔍 Rechercher une date ou une activité dans le tableau (ex: 11/11/2026, Décembre, Atelier...) :")
df_affiche = df_planning
if recherche:
    df_affiche = df_planning[
        df_planning["Date"].str.contains(recherche, case=False) | 
        df_planning["Activité"].str.contains(recherche, case=False)
    ]

colonnes_visibles = ["Date", "Créneau", "Activité", "Bénévole Référent", "Bénévole 1", "Bénévole 2"]
st.dataframe(df_affiche[colonnes_visibles], use_container_width=True, hide_index=True)

# --- PARTIE 3 : ZONE D'ADMINISTRATION SECURISEE ---
st.markdown("---")
with st.expander("🛠️ Zone Administrateur (Gestion & Export des données)"):
    
    code_saisi = st.text_input("Entrez le code secret admin pour déverrouiller :", type="password")
    
    if code_saisi == CODE_SECRET_ADMIN:
        st.success("🔓 Accès administrateur autorisé.")
        
        st.markdown("### 📧 Liste complète des permanences (avec adresses mails)")
        st.dataframe(df_planning, use_container_width=True, hide_index=True)
        
        st.markdown("### 📝 Assigner une Activité ou un Référent")
        options_admin = {f"{row['Date']} ({row['Créneau']})": idx for idx, row in df_planning.iterrows()}
        choix_admin = st.selectbox("Sélectionnez le créneau à modifier :", list(options_admin.keys()))
        idx_admin = options_admin[choix_admin]
        
        nouvelle_activite = st.text_input("Nom de l'activité :", value=str(df_planning.at[idx_admin, "Activité"]))
        nouveau_referent = st.text_input("Bénévole Référent :", value=str(df_planning.at[idx_admin, "Bénévole Référent"]))
        
        if st.button("💾 Enregistrer les modifications admin"):
            df_planning.at[idx_admin, "Activité"] = nouvelle_activite if nouvelle_activite else "Non définie"
            df_planning.at[idx_admin, "Bénévole Référent"] = nouveau_referent if nouveau_referent else "Non assigné"
            sauvegarder_donnees(df_planning)
            st.success("Mise à jour enregistrée avec succès !")
            st.rerun()
            
        st.markdown("---")
        st.markdown("### ⚠️ Réinitialisation globale")
        if st.button("🔄 Réinitialiser tout le planning"):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.success("Le calendrier a été intégralement remis à zéro !")
            st.rerun()
    elif code_saisi != "":
        st.error("Code secret incorrect.")
