import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

DATA_FILE = "inscriptions_permanence.csv"
CODE_SECRET_ADMIN = "1234"

@st.cache_data
def generer_dates_planning_fixe():
    date_debut = datetime(2026, 11, 11)
    date_fin = date_debut + timedelta(days=90)
    jours_vises = {2: "Mercredi", 3: "Jeudi", 4: "Vendredi"}
    planning = []
    date_courante = date_debut
    while date_courante <= date_fin:
        num_jour = date_courante.weekday()
        if num_jour in jours_vises:
            nom_jour = jours_vises[num_jour]
            date_formatee = date_courante.strftime("%d/%m/%Y")
            label_date = f"{nom_jour} {date_formatee}"
            creneaux = ["10h - 14h", "14h - 18h", "18h - 22h"] if nom_jour == "Mercredi" else ["18h - 22h"]
            for creneau in creneaux:
                planning.append({
                    "Date": label_date, "Créneau": creneau, "Activité": "Non définie",
                    "Bénévole Référent": "Non assigné", "Bénévole 1": "Disponible",
                    "Bénévole 1 Email": "", "Bénévole 2": "Disponible", "Bénévole 2 Email": ""
                })
        date_courante += timedelta(days=1)
    return pd.DataFrame(planning).astype(str)

def charger_donnees():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE).fillna("")
        return df.astype(str)
    return generer_dates_planning_fixe()

def sauvegarder_donnees(df):
    df.to_csv(DATA_FILE, index=False)

st.set_page_config(page_title="Chez Madeleine", page_icon="🗓️", layout="centered") # Mode centré plus rapide à charger
st.title("🗓️ Permanences \"Chez Madeleine\"")

df_planning = charger_donnees()

# FORMULAIRE
st.subheader("✍️ Inscription rapide")
options_creneaux = {}
for idx, row in df_planning.iterrows():
    if str(row["Bénévole 1"]) == "Disponible" or str(row["Bénévole 2"]) == "Disponible":
        texte_choix = f"{row['Date']} ({row['Créneau']}) - {row['Activité']}"
        options_creneaux[texte_choix] = idx

if not options_creneaux:
    st.success("🎉 Tous les créneaux sont complets !")
else:
    with st.form("form_inscription", clear_on_submit=True):
        prenom = st.text_input("Prénom :").strip()
        nom = st.text_input("Nom :").strip()
        email = st.text_input("Adresse Mail :").strip()
        choix_selectionne = st.selectbox("Créneau :", list(options_creneaux.keys()))
        if st.form_submit_button("Valider mon inscription"):
            if not nom or not prenom or not email:
                st.error("⚠️ Tous les champs sont obligatoires.")
            elif "@" not in email:
                st.error("⚠️ Email invalide.")
            else:
                idx_choix = options_creneaux[choix_selectionne]
                identite = f"{prenom} {nom.upper()}"
                if str(df_planning.at[idx_choix, "Bénévole 1"]) == "Disponible":
                    df_planning.at[idx_choix, "Bénévole 1"] = identite
                    df_planning.at[idx_choix, "Bénévole 1 Email"] = email
                else:
                    df_planning.at[idx_choix, "Bénévole 2"] = identite
                    df_planning.at[idx_choix, "Bénévole 2 Email"] = email
                sauvegarder_donnees(df_planning)
                st.success("✅ Inscription réussie !")
                st.rerun()

st.markdown("---")

# TABLEAU ALLÉGÉ
st.subheader("📊 Voir les créneaux occupés")
recherche = st.text_input("🔍 Filtrer par date (ex: 11/11/2026, Décembre) :").strip()
df_visuel = df_planning[["Date", "Créneau", "Activité", "Bénévole Référent", "Bénévole 1", "Bénévole 2"]]

if recherche:
    df_visuel = df_visuel[df_visuel["Date"].str.contains(recherche, case=False)]
else:
    # N'affiche que les 15 prochains créneaux par défaut pour économiser la mémoire du téléphone
    df_visuel = df_visuel.head(15)

st.table(df_visuel) # Utilisation de st.table (génère du HTML simple, beaucoup plus rapide que st.dataframe)

# ADMIN
with st.expander("🛠️ Zone Administrateur"):
    code_saisi = st.text_input("Code secret :", type="password")
    if code_saisi == CODE_SECRET_ADMIN:
        st.dataframe(df_planning)
        options_admin = {f"{row['Date']} ({row['Créneau']})": idx for idx, row in df_planning.iterrows()}
        choix_admin = st.selectbox("Modifier créneau :", list(options_admin.keys()))
        idx_admin = options_admin[choix_admin]
        act = st.text_input("Activité :", value=str(df_planning.at[idx_admin, "Activité"]))
        ref = st.text_input("Référent :", value=str(df_planning.at[idx_admin, "Bénévole Référent"]))
        b1 = st.text_input("Bénévole 1 :", value=str(df_planning.at[idx_admin, "Bénévole 1"]))
        b2 = st.text_input("Bénévole 2 :", value=str(df_planning.at[idx_admin, "Bénévole 2"]))
        if st.button("💾 Sauvegarder Admin"):
            df_planning.at[idx_admin, "Activité"] = act
            df_planning.at[idx_admin, "Bénévole Référent"] = ref
            df_planning.at[idx_admin, "Bénévole 1"] = b1
            df_planning.at[idx_admin, "Bénévole 2"] = b2
            sauvegarder_donnees(df_planning)
            st.rerun()
