import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="KaMela Finance", page_icon="💰", layout="wide")

# --- STYLE PERSONNALISÉ (Pour faire "Pro") ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

st.title("📂 KaMela Finance")
st.caption("Synchronisé avec votre Google Sheet")

# --- CONNEXION AU CLOUD ---
# Cette ligne utilise les identifiants que tu as mis dans secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

# Fonction pour charger les données
def load_data():
    flux = conn.read(worksheet="Flux")
    dettes = conn.read(worksheet="Dettes")
    return flux, dettes

df_flux, df_dettes = load_data()

# --- NAVIGATION ---
menu = st.tabs(["📊 Tableau de Bord", "💸 Mouvements", "🤝 Dettes & Prêts"])

# --- 1. DASHBOARD (Vue d'ensemble) ---
with menu[0]:
    solde = df_flux["Montant"].sum() if not df_flux.empty else 0
    
    col1, col2 = st.columns(2)
    col1.metric("Solde Total", f"{solde:,.2f} $")
    
    # Calcul des dettes en cours uniquement
    if not df_dettes.empty:
        a_payer = df_dettes[df_dettes["Statut"] == "En cours"]["Montant"].sum()
        col2.metric("Dettes à régler", f"{a_payer:,.2f} $", delta="- Attention", delta_color="inverse")

    st.subheader("Historique récent")
    st.dataframe(df_flux.tail(10), use_container_width=True)

# --- 2. MOUVEMENTS (Entrées/Sorties) ---
with menu[1]:
    st.subheader("Ajouter une transaction")
    with st.form("ajout_flux"):
        f_date = st.date_input("Date", datetime.now())
        f_desc = st.text_input("Description (ex: Salaire, Achat téléphone...)")
        f_mt = st.number_input("Montant (Négatif pour dépense, Positif pour gain)")
        f_cat = st.selectbox("Catégorie", ["Salaire", "Nourriture", "Loyer", "Loisirs", "Business", "Cadeau"])
        
        if st.form_submit_button("Enregistrer sur le Cloud"):
            # Préparation de la nouvelle ligne
            nouvelle_ligne = pd.DataFrame([[str(f_date), f_desc, f_mt, f_cat]], columns=df_flux.columns)
            # Mise à jour du Google Sheet
            updated_df = pd.concat([df_flux, nouvelle_ligne], ignore_index=True)
            conn.update(worksheet="Flux", data=updated_df)
            st.success("Données sauvegardées !")
            st.rerun()

# --- 3. DETTES & PRÊTS (Gestion avancée) ---
with menu[2]:
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("Nouvel Engagement")
        with st.form("ajout_dette"):
            nom = st.text_input("Nom du contact")
            tel = st.text_input("N° de Téléphone")
            tp = st.selectbox("Type", ["Dette (Je dois)", "Prêt (On me doit)"])
            mt = st.number_input("Montant", min_value=0.0)
            ech = st.date_input("Échéance")
            if st.form_submit_button("Ajouter l'engagement"):
                nouvelle_dette = pd.DataFrame([[nom, tel, tp, mt, str(ech), "En cours"]], columns=df_dettes.columns)
                updated_dettes = pd.concat([df_dettes, nouvelle_dette], ignore_index=True)
                conn.update(worksheet="Dettes", data=updated_dettes)
                st.success("Engagement noté !")
                st.rerun()

    with col_b:
        st.subheader("Suivi des paiements")
        # Affichage interactif pour payer
        for i, row in df_dettes.iterrows():
            if row["Statut"] == "En cours":
                c1, c2, c3 = st.columns([2, 2, 1])
                c1.write(f"**{row['Contact']}** ({row['Type']})")
                c2.write(f"{row['Montant']}$ | 📅 {row['Echeance']}")
                if c3.button("Payer", key=f"pay_{i}"):
                    # 1. Marquer comme payé dans Dettes
                    df_dettes.at[i, "Statut"] = "✅ Payé"
                    conn.update(worksheet="Dettes", data=df_dettes)
                    
                    # 2. Créer l'impact financier automatique dans Flux
                    impact = -row['Montant'] if "Dette" in row['Type'] else row['Montant']
                    nouvelle_ligne_flux = pd.DataFrame([[str(datetime.now().date()), f"Remboursement {row['Contact']}", impact, "Dettes"]], columns=df_flux.columns)
                    updated_flux = pd.concat([df_flux, nouvelle_ligne_flux], ignore_index=True)
                    conn.update(worksheet="Flux", data=updated_flux)
                    
                    st.rerun()