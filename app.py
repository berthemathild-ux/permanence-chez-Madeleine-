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
        # Ajout automatique des colonnes d'emails si absentes
        if "Bénévole 1 Email" not in df.columns:
            df["Bénévole 1 Email"] = ""
        if "Bénévole 2 Email" not in df.columns:
            df["Bénévole 2 Email"] = ""
        return df
    return generer_dates_planning()

def sauvegarder_donnees(df):
    """Enregistre le planning sur le disque."""
    df.to_csv(DATA_FILE, index=False)

# Initialisation de l'application
st.set_page_config(page_title="Permanences Association", page_icon="🗓️", layout="wide")
st.title("🗓️ Gestion des Permanences - Planning de l'Association")

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

# On choisit les colonnes visibles publiquement pour ne pas encombrer l'écran avec les emails
colonnes_visibles = ["Date", "Créneau", "Activité", "Bénévole Référent", "Bénévole 1", "Bénévole 2"]
st.dataframe(df_affiche[colonnes_visibles], use_container_width=True, hide_index=True)

st.markdown("---")

# --- PARTIE 2 : FORMULAIRE D'INSCRIPTION EN LIGNE (BÉNÉVOLES) ---
st.subheader("✍️ S'inscrire à un créneau (Espace Bénévole)")

creneaux_disponibles = []
for index, row in df_planning.iterrows():
    if row["Bénévole 1"] == "Disponible" or row["Bénévole 2"] == "Disponible":
        texte_choix = f"{row['Date']} ({row['Créneau']}) - {row['Activité']}"
        creneaux_disponibles.append((texte_choix, index))

if not creneaux_disponibles:
    st.success("🎉 Tous les créneaux sont complets ! Merci pour votre engagement.")
else:
    with st.form("form_inscription", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            prenom = st.text_input("Votre Prénom :").strip()
            nom = st.text_input("Votre Nom :").strip()
        with col2:
            email = st.text_input("Votre Adresse Mail :").strip()
            
        options_options = [c for c in creneaux_disponibles]
        choix_selectionne = st.selectbox("Choisissez votre date et créneau :", options_options)
        
        bouton_valider = st.form_submit_button("Valider mon inscription")
        
        if bouton_valider:
            if not nom or not prenom or not email:
                st.error("⚠️ Veuillez remplir tous les champs (Nom, Prénom et Adresse Mail) avant de valider.")
            elif "@" not in email or "." not in email:
                st.error("⚠️ Veuillez entrer une adresse mail valide.")
            else:
                idx_choix = creneaux_disponibles[options_options.index(choix_selectionne)]
                identite_complete = f"{prenom} {nom.upper()}"
                
                if df_planning.at[idx_choix, "Bénévole 1"] == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 1"] = identite_complete
                    df_planning.at[idx_choix, "Bénévole 1 Email"] = email
                    st.success(f"✅ Merci {prenom} ! Inscription validée (Place 1).")
                elif df_planning.at[idx_choix, "Bénévole 2"] == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 2"] = identite_complete
                    df_planning.at[idx_choix, "Bénévole 2 Email"] = email
                    st.success(f"✅ Merci {prenom} ! Inscription validée (Place 2).")
                
                sauvegarder_donnees(df_planning)
                st.rerun()

# --- PARTIE 3 : ZONE D'ADMINISTRATION SECURISEE ---
st.markdown("---")
with st.expander("🛠️ Zone Administrateur (Gestion & Export des données)"):
    
    code_saisi = st.text_input("Entrez le code secret admin pour déverrouiller :", type="password")
    
    if code_saisi == CODE_SECRET_ADMIN:
        st.success("🔓 Accès administrateur autorisé.")
        
        # Section 1 : Voir la liste complète avec les adresses mails cachées du public
        st.markdown("### 📧 Liste complète des permanences (avec adresses mails)")
        st.dataframe(df_planning, use_container_width=True, hide_index=True)
        
        # Section 2 : Modification des activités et référents
        st.markdown("### 📝 Assigner une Activité ou un Référent")
        tous_les_creneaux = [(f"{row['Date']} ({row['Créneau']})", index) for index, row in df_planning.iterrows()]
        options_admin = [c for c in tous_les_creneaux]
        choix_admin = st.selectbox("Sélectionnez le créneau à modifier :", options_admin)
        idx_admin = tous_les_creneaux[options_admin.index(choix_admin)]
        
        nouvelle_activite = st.text_input("Nom de l'activité :", value=df_planning.at[idx_admin, "Activité"])
        nouveau_referent = st.text_input("Bénévole Référent :", value=df_planning.at[idx_admin, "Bénévole Référent"])
        
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
