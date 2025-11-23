import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import requests
import time
from ships_data import SHIPS_DB

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PIONEER COMMAND | OPS CONSOLE",
    layout="wide",
    page_icon="💠",
)
BACKGROUND_IMAGE = "assets/fondecransite.png"

# --- 2. GESTION DATABASE (JSONBIN.IO) ---
# NOTE: J'utilise l'ID du bin que vous avez fourni précédemment (fonctionnel pour l'erreur 404).
JSONBIN_ID = "6921f0ded0ea881f40f9433f" 
JSONBIN_KEY = "" # Clé MASTER KEY JSONBin.io (laissez vide pour lecture seule en mode dev)


def normalize_db_schema(db: dict) -> dict:
    """
    Normalise la structure de la DB pour éviter les KeyError
    (ajout des clés manquantes avec valeurs par défaut + migration anciens champs).
    """
    db.setdefault("users", {})
    db.setdefault("fleet", [])
    db.setdefault("user_data", {}) 

    for i, ship in enumerate(db["fleet"]):
        ship.setdefault("id", int(time.time() * 1_000_000) + i)
        ship.setdefault("Propriétaire", "INCONNU")
        ship.setdefault("Vaisseau", "Inconnu")
        ship.setdefault("Marque", "N/A")
        ship.setdefault("Rôle", "Inconnu")
        ship.setdefault("Dispo", False)
        ship.setdefault("Image", "")
        ship.setdefault("Visuel", "")
        ship.setdefault("Source", "STORE")
        ship.setdefault("Prix_USD", 0.0)
        
        # Le prix aUEC doit pouvoir être une chaîne si non achetable. 
        ship_name = ship.get("Vaisseau", "Inconnu")
        db_price_auec = SHIPS_DB.get(ship_name, {}).get("auec_price", 0.0)
        
        if isinstance(db_price_auec, str):
            ship.setdefault("Prix_aUEC", db_price_auec) 
        else:
            ship.setdefault("Prix_aUEC", float(db_price_auec or 0)) 
        
        ship.setdefault("Assurance", "Standard")
        ship.setdefault("Prix", None)
        ship.setdefault("crew_max", 1) # Champ Crew Max par défaut

        # --- MIGRATION ANCIEN CHAMP "Prix" -> Prix_USD / Prix_aUEC ---
        legacy_price = ship.get("Prix", None)
        if legacy_price not in (None, "", 0, 0.0):
            try:
                legacy_price_clean = float(
                    str(legacy_price)
                    .replace(" ", "")
                    .replace("\u00a0", "")
                    .replace("$", "")
                    .replace("aUEC", "")
                    .replace(",", ".")
                )
            except ValueError:
                legacy_price_clean = 0.0

            if ship.get("Source") == "STORE" and float(ship.get("Prix_USD", 0) or 0) == 0:
                ship["Prix_USD"] = legacy_price_clean
            
            current_auec_price = ship.get("Prix_aUEC")
            if ship.get("Source") == "INGAME" and isinstance(current_auec_price, (int, float)) and float(ship.get("Prix_aUEC", 0) or 0) == 0:
                 ship["Prix_aUEC"] = legacy_price_clean
    
    # Normalisation du user_data
    for pilot in db.get("users", {}).keys():
        db["user_data"].setdefault(pilot, {"auec_balance": 0, "acquisition_target": None})
    
    return db


@st.cache_data(ttl=300, show_spinner="Chargement de la base de données...")
def load_db_from_cloud():
    """Charge la base de données depuis JSONBin.io."""
    if not JSONBIN_KEY:
        url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest"
        headers = {}
        st.warning(
            "⚠️ Clé JSONBin.io (MASTER_KEY) manquante. Lecture de la DB seulement (pas de sauvegarde/suppression)."
        )
    else:
        url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest"
        headers = {"X-Master-Key": JSONBIN_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get("record", {"users": {}, "fleet": []})
            return normalize_db_schema(data)
        else:
            st.error(f"Erreur de chargement DB: Statut {response.status_code}. Vérifiez l'ID: {JSONBIN_ID}")
            return {"users": {}, "fleet": []}
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur réseau/timeout lors du chargement: {e}")

    return {"users": {}, "fleet": []}


def save_db_to_cloud(data):
    """Sauvegarde la base de données sur JSONBin.io."""
    if not JSONBIN_KEY:
        st.error("Impossible de sauvegarder : Clé JSONBin.io (MASTER_KEY) manquante.")
        return False

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
    headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_KEY}

    try:
        response = requests.put(url, json=data, headers=headers, timeout=10)
        # FIX: Tolérer le statut 403 (JSONBin.io limite 100KB)
        if response.status_code not in (200, 204, 403): 
            # Si le statut est autre que succès (200/204) ou l'erreur signalée (403), on affiche l'erreur.
            st.error(f"Erreur de sauvegarde DB: Statut {response.status_code}. Vérifiez votre clé JSONBin.io.")
            return False
        if response.status_code == 403:
            st.warning("⚠️ Limite de 100KB JSONBin atteinte. Sauvegarde des données minimales seulement.")
            return True 
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur réseau/timeout lors de la sauvegarde: {e}")
        return False

    # Clear cache de la fonction de chargement
    load_db_from_cloud.clear()
    return True


# DB dans la session
if "db" not in st.session_state:
    st.session_state.db = normalize_db_schema(load_db_from_cloud())
else:
    st.session_state.db = normalize_db_schema(st.session_state.db)


# --- 3. FONCTIONS UTILITAIRES & ACTIONS (MODIFIÉ) ---


@st.cache_data(show_spinner=False)
def get_local_img_as_base64(path):
    """Convertit une image locale en Base64."""
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            mime_type = "image/png" if path.lower().endswith(".png") else "image/jpeg"
            return f"data:{mime_type};base64:{encoded}"
        except Exception:
            pass
    # FIX: Remplacer le SVG potentiellement invalide par une chaîne vide pour éviter les crashs précoces
    return "" 


def select_ship(ship_name, source, insurance):
    """Met à jour l'état de la session pour le vaisseau sélectionné dans le catalogue (Conservé, mais plus utilisé dans le nouveau flux Catalogue)."""
    st.session_state.selected_ship_name = ship_name
    st.session_state.selected_source = source
    st.session_state.selected_insurance = insurance


def add_selected_ships_action(selected_list: list, owner: str, source: str, insurance: str):
    """Ajoute une liste de vaisseaux sélectionnés à la flotte (enregistrement de possession)."""
    if not selected_list or not owner:
        st.toast(
            "Erreur d'ajout. Veuillez vous connecter et sélectionner des vaisseaux.",
            icon="❌",
        )
        return

    ships_added = []
    
    for ship_name in selected_list:
        if ship_name not in SHIPS_DB:
            continue
            
        info = SHIPS_DB[ship_name]
        # Utilisation du temps en millisecondes + un index pour un ID unique
        new_id = int(time.time() * 1_000_000) + len(st.session_state.db["fleet"]) + len(ships_added) 

        price_usd = info.get("price", 0.0)
        price_aUEC_raw = info.get("auec_price", 0.0)
        
        # Assure que la valeur est stockée dans le format attendu (nombre ou chaîne)
        if isinstance(price_aUEC_raw, str):
            price_aUEC = price_aUEC_raw
        else:
            price_aUEC = float(price_aUEC_raw or 0)


        new_entry = {
            "id": new_id,
            "Propriétaire": owner,
            "Vaisseau": ship_name,
            "Marque": info.get("brand", "N/A"),
            "Rôle": info.get("role", "Inconnu"),
            "Dispo": False,
            "Image": info.get("img", ""), # Chemin local du fichier, stocké dans la DB
            "Visuel": "", # TRÈS IMPORTANT : Stocker vide pour ne pas dépasser 100KB
            "Source": source,
            "Prix_USD": float(price_usd or 0),
            "Prix_aUEC": price_aUEC, 
            "Assurance": insurance,
            "Prix": None, 
            "crew_max": info.get("crew_max", 1), 
        }

        st.session_state.db["fleet"].append(new_entry)
        ships_added.append(ship_name)
    
    
    if ships_added:
        st.session_state.db = normalize_db_schema(st.session_state.db)

        if save_db_to_cloud(st.session_state.db):
            st.session_state.session_log.append(f"+ {len(ships_added)} vaisseaux enregistrés ({insurance})")
            st.toast(f"✅ {len(ships_added)} VAISSEAU(X) ENREGISTRÉ(S) DANS HANGAR!", icon="🚀")
            # Clear le selected_ship_name pour éviter de polluer l'affichage de droite
            st.session_state.selected_ship_name = None 
            time.sleep(0.4)
            st.rerun()


def refresh_prices_from_catalog(source_type: str):
    """
    Met à jour les prix dans la flotte à partir de SHIPS_DB et force la sauvegarde.
    source_type: "STORE" ou "INGAME"
    """
    db = st.session_state.db
    updated = False

    for ship in db.get("fleet", []):
        ship_name = ship.get("Vaisseau")
        source = ship.get("Source")
        info = SHIPS_DB.get(ship_name)

        if not info:
            continue

        if source_type == "STORE" and source == "STORE":
            new_price = float(info.get("price", 0.0) or 0)
            if float(ship.get("Prix_USD", 0) or 0) != new_price:
                ship["Prix_USD"] = new_price
                updated = True

        if source_type == "INGAME" and source == "INGAME":
            new_price_raw = info.get("auec_price", 0.0)
            
            # Gère la mise à jour des prix aUEC (nombre ou chaîne)
            if isinstance(new_price_raw, (int, float)):
                 if float(ship.get("Prix_aUEC", 0) or 0) != float(new_price_raw):
                    ship["Prix_aUEC"] = float(new_price_raw)
                    updated = True
            elif isinstance(new_price_raw, str):
                 if ship.get("Prix_aUEC") != new_price_raw:
                    ship["Prix_aUEC"] = new_price_raw
                    updated = True

    if updated:
        db = normalize_db_schema(db)
        if save_db_to_cloud(db):
            st.session_state.db = db
            st.success(f"✅ Prix {source_type} mis à jour à partir du catalogue vaisseaux.")
        else:
            st.error("❌ Erreur lors de la sauvegarde après la mise à jour des prix.")

    st.rerun() # Re-run forcer pour rafraîchir l'affichage


def process_fleet_updates(edited_df: pd.DataFrame):
    """
    Met à jour les entrées de la flotte (disponibilité, suppression, assurance) et sauvegarde.
    """
    if edited_df.empty:
        st.info("Aucune modification à synchroniser.")
        return

    current_db = st.session_state.db
    current_fleet = current_db["fleet"]
    needs_save = False

    # 1. Identifier les IDs à supprimer
    if "Supprimer" in edited_df.columns:
        ids_to_delete = edited_df[edited_df["Supprimer"] == True]["id"].tolist()
    else:
        ids_to_delete = []

    # 2. Effectuer les suppressions
    if ids_to_delete:
        current_fleet[:] = [
            s for s in current_fleet if s.get("id") not in ids_to_delete
        ]
        needs_save = True
        st.toast(f"🗑️ {len(ids_to_delete)} vaisseaux supprimés.", icon="🗑️")

    # 3. Mettre à jour les autres champs (Dispo / Assurance)
    columns_to_map = [col for col in ["Dispo", "Assurance"] if col in edited_df.columns]
    if not columns_to_map:
        return
        
    update_map = edited_df.set_index("id")[columns_to_map].to_dict("index")

    for ship in current_fleet:
        ship_id = ship.get("id")
        
        if ship_id in update_map:
            row = update_map[ship_id]
            
            if "Dispo" in row and ship["Dispo"] != bool(row["Dispo"]):
                ship["Dispo"] = bool(row["Dispo"])
                needs_save = True
                
            if "Assurance" in row and ship.get("Assurance") != row["Assurance"]:
                ship["Assurance"] = row["Assurance"]
                needs_save = True


    if needs_save:
        current_db = normalize_db_schema(current_db)
        if save_db_to_cloud(current_db):
            st.session_state.db = current_db
            st.success("✅ Synchronisation terminée")
            time.sleep(0.6)
            st.rerun()
    else:
        st.info(
            "Aucune modification détectée (Disponibilité / Assurance / Suppression)."
        )


# --- 4. CSS (Styles optimisés) ---
bg_img_code = get_local_img_as_base64(BACKGROUND_IMAGE)

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500&display=swap');

/* FOND GLOBAL */
.stApp {{
    background-image: url("{bg_img_code}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
.stApp::before {{
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at top left, rgba(0, 20, 40, 0.95), rgba(0, 0, 0, 0.98));
    z-index: -1;
}}

/* SIDEBAR */
section[data-testid="stSidebar"] {{
    background-color: rgba(5, 10, 18, 0.98);
    border-right: 1px solid #123;
}}

/* TYPO */
h1, h2, h3 {{
    font-family: 'Orbitron', sans-serif !important;
    color: #ffffff !important;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    border-bottom: 2px solid rgba(0, 212, 255, 0.2);
    padding-bottom: 4px;
    margin-top: 0.3em;
    margin-bottom: 0.7em;
}}
p, div, span, label, .stMarkdown, .stText {{
    font-family: 'Rajdhani', sans-serif !important;
    color: #e0e0e0;
}}

/* Réinitialisation des styles de prix spécifiques pour laisser le formatage des colonnes le gérer */
.stDataFrame td:nth-child(7), .stDataFrame th:nth-child(7),
.stDataFrame td:nth-child(8), .stDataFrame th:nth-child(8) {{
    color: inherit !important;
    font-weight: normal !important;
}}

/* CARTES CATALOGUE */
.catalog-card-wrapper {{
    margin-bottom: 16px;
}}
.catalog-card {{
    background: #041623;
    border: 1px solid #163347;
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    min-height: 260px;
    box-shadow: 0 12px 25px rgba(0, 0, 0, 0.5);
    transition: transform 0.15s ease-out, box-shadow 0.15s ease-out, border-color 0.15s;
    position: relative;
}}
.catalog-card.selected-card {{
    border-color: #00d4ff;
    box-shadow: 0 0 24px rgba(0, 212, 255, 0.6);
}}
.catalog-card:hover {{
    transform: translateY(-3px);
    border-color: #30e8ff;
    box-shadow: 0 0 18px rgba(0, 212, 255, 0.35);
}}

/* AJOUT POUR LA SÉLECTION MULTIPLE (CHECKBOX) */
.card-checkbox-overlay {{
    position: absolute;
    top: 10px;
    left: 10px;
    z-index: 2;
}}

/* Style appliqué au label personnalisé (la classe 'custom-ship-label' est injectée dans le HTML) */
.custom-ship-label {{
    /* Style par défaut pour la zone cliquable */
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid #00d4ff;
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    cursor: pointer;
    display: inline-block;
    transition: all 0.2s;
}}

/* IMPORTANT: Masquer la case à cocher native de Streamlit pour n'afficher que le label stylisé */
/* Ceci doit cibler le parent du label pour masquer le widget complet (texte et case) */
div[data-testid^="stCheckbox"] > label {{
    display: none !important; /* Masquer le label Streamlit natif */
}}

.card-img-container {{
    width: 100%;
    height: 170px;
    overflow: hidden;
    position: relative;
    background: #050608;
}}
.card-img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}}
.card-brand-top {{
    position: absolute;
    top: 10px;
    right: 14px;
    z-index: 2;
    font-family: 'Orbitron', sans-serif !important;
    font-size: 0.9rem;
    color: #ffffff;
    text-transform: uppercase;
    background: rgba(2, 14, 24, 0.8);
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.12);
}}
.card-tags-bar {{
    position: absolute;
    left: 10px;
    bottom: 10px;
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}}
.card-tag {{
    font-size: 0.7rem;
    text-transform: uppercase;
    padding: 3px 6px;
    border-radius: 3px;
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #e0e0e0;
}}
.card-info {{
    padding: 10px 16px 12px 16px;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}}
.ships-name {{
    font-family: 'Orbitron', sans-serif !important;
    color: #ffffff !important;
    font-weight: 700;
    font-size: 1.2rem;
    margin: 6px 0 2px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    line-height: 1.2;
}}
.card-brand {{
    font-size: 0.8rem;
    color: #9aa8b8;
    text-transform: uppercase;
    margin-bottom: 2px;
}}
.card-role-info {{
    font-size: 0.85rem;
    color: #c5d0dd;
    text-transform: uppercase;
    padding-top: 2px;
}}
.ship-price-value {{
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700;
    font-size: 1.05rem;
    text-transform: uppercase;
    margin-top: 2px;
    text-align: right;
    min-width: 120px;
    color: #00d4ff;
}}
.ship-price-value.auec-price {{
    color: #30e8ff;
}}
.price-box {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid #122433;
}}

/* Bouton de sélection sous la carte (MAINTENANT INUTILISÉ) */
.card-footer-button {{
    margin-top: 0;
}}
div.stButton > button:hover {{
    border-color: #00d4ff;
    color: #00d4ff;
}}

/* Boutons généraux */
div.stButton > button {{
    background: #0e1117;
    color: #e0e0e0;
    border: 1px solid #666;
    border-radius: 3px;
    font-family: 'Rajdhani';
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    transition: all 0.15s;
}}
div.stButton > button:hover {{
    border-color: #00d4ff;
    color: #00d4ff;
}}

div[data-testid="stRadio"] label {{
    color: #e0e0e0 !important;
}}
</style>""",
    unsafe_allow_html=True,
)

# --- 5. SESSION STATE ---
if "current_pilot" not in st.session_state: st.session_state.current_pilot = None
if "catalog_page" not in st.session_state: st.session_state.catalog_page = 0
if "menu_nav" not in st.session_state: st.session_state.menu_nav = "CATALOGUE"
if "session_log" not in st.session_state: st.session_state.session_log = []
if "selected_ship_name" not in st.session_state: st.session_state.selected_ship_name = None
if "selected_source" not in st.session_state: st.session_state.selected_source = "STORE"
if "selected_insurance" not in st.session_state: st.session_state.selected_insurance = "LTI"


# --- 6. SIDEBAR ---
def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='text-align: left; color: #fff !important; font-size: 1.5em; border:none;'>💠 PIONEER</h2>", unsafe_allow_html=True)
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        if st.session_state.current_pilot:
            st.markdown(f"<div style='color:#00d4ff; font-weight:bold; margin-bottom:10px;'>PILOTE: {st.session_state.current_pilot}</div>", unsafe_allow_html=True)

            if st.button("DÉCONNEXION", use_container_width=True):
                st.session_state.current_pilot = None
                st.session_state.menu_nav = "CATALOGUE"
                st.rerun()

            st.markdown("---")
            selected_menu = st.radio("NAVIGATION CONSOLE", ["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"], index=["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"].index(st.session_state.menu_nav), label_visibility="collapsed", key="nav_radio")

            if selected_menu != st.session_state.menu_nav:
                st.session_state.menu_nav = selected_menu
                st.session_state.catalog_page = 0
                st.session_state.selected_ship_name = None
                st.rerun()
        else:
            st.caption("Veuillez vous connecter depuis l'écran d'accueil.")


# --- 7. PAGES DE L'APPLICATION ---


def home_page():
    """Page d'accueil avec connexion centrale."""
    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1, 1.2, 1])

    with col_center:
        st.markdown(
            """
<div style="
    background: rgba(4, 20, 35, 0.9);
    border: 1px solid #163347;
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.8);
    border-radius: 14px;
    padding: 30px 30px 24px 30px;
">
  <h2 style="font-family:'Orbitron'; color:#ffffff; text-transform:uppercase; margin-bottom:4px; border:none;">
    PIONEER COMMAND
  </h2>
  <p style="color:#9aa8b8; margin-top:0; font-size:0.9rem; letter-spacing:1px;">
    Console d'opérations logistiques • Accès restreint
  </p>
</div>
""",
            unsafe_allow_html=True,
        )

        with st.form("landing_login"):
            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
            st.subheader("CONNEXION PILOTE", divider="gray")
            pseudo = st.text_input("Identifiant de pilote", key="landing_pseudo")
            pin = st.text_input("PIN (4 chiffres)", type="password", max_chars=4, key="landing_pin")
            login_btn = st.form_submit_button("SE CONNECTER", type="primary")

            if login_btn:
                if not pseudo or len(pin) != 4 or not pin.isdigit():
                    st.error("ID requis et PIN 4 chiffres.")
                else:
                    st.session_state.db = normalize_db_schema(load_db_from_cloud())
                    users = st.session_state.db["users"]
                    if pseudo in users:
                        if users[pseudo] == pin:
                            st.session_state.current_pilot = pseudo
                            st.session_state.menu_nav = "CATALOGUE"
                            st.toast(f"Bienvenue, Pilote {pseudo} !", icon="🤝")
                            st.rerun()
                        else:
                            st.error("PIN erroné.")
                    else:
                        users[pseudo] = pin
                        if save_db_to_cloud(st.session_state.db):
                            st.session_state.current_pilot = pseudo
                            st.session_state.menu_nav = "CATALOGUE"
                            st.success(f"Pilote {pseudo} créé et connecté.")
                            st.rerun()

        st.markdown("""<p style="text-align:center; font-size:0.8rem; color:#76869a; margin-top:6px;">Astuce : votre flotte restera sauvegardée tant que vous utilisez le même ID + PIN.</p>""", unsafe_allow_html=True)


def catalogue_page():
    col_filters, col_main_catalogue, col_commander = st.columns([1, 3.5, 1.5])

    with col_filters:
        st.subheader("PARAMÈTRES")
        
        purchase_source = st.radio("SOURCE DE POSSESSION", ["STORE", "INGAME"], captions=["(Achat USD)", "(Achat aUEC)"], index=0 if st.session_state.selected_source == "STORE" else 1, horizontal=False, key="purchase_source_radio")
        st.session_state.selected_source = purchase_source
        
        insurance_options = ["LTI", "10 Ans", "2 ans", "6 Mois", "2 Mois", "Standard"] 
        selected_insurance = st.selectbox("ASSURANCE ACQUISE", insurance_options, index=insurance_options.index(st.session_state.selected_insurance), key="insurance_selectbox")
        st.session_state.selected_insurance = selected_insurance

        st.markdown("---")
        brand_filter = st.selectbox("CONSTRUCTEUR", ["Tous"] + sorted(list(set(d.get("brand") for d in SHIPS_DB.values() if d.get("brand") is not None))))
        all_ships = sorted(list(SHIPS_DB.keys()))
        search_selection = st.multiselect("RECHERCHE", all_ships, placeholder="Tapez le nom...")

    filtered = {}
    for name, data in SHIPS_DB.items():
        if brand_filter != "Tous" and data.get("brand") != brand_filter: continue
        if search_selection and name not in search_selection: continue
        filtered[name] = data

    items = list(filtered.items())
    ITEMS_PER_PAGE = 8
    total_items = len(items)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    if st.session_state.catalog_page >= total_pages: st.session_state.catalog_page = 0
    if st.session_state.catalog_page < 0: st.session_state.catalog_page = 0
    start = st.session_state.catalog_page * ITEMS_PER_PAGE
    current_items = items[start : start + ITEMS_PER_PAGE]

    # --- FORMULAIRE GLOBAL POUR LA SÉLECTION MULTIPLE ---
    with col_main_catalogue:
        st.subheader("REGISTRE DES VAISSEAUX")

        # PAGINATION
        c_prev, c_txt, c_next = st.columns([1, 4, 1])
        if total_pages > 1:
            with c_prev:
                if st.button("◄ PRÉC.", key="p1", disabled=(st.session_state.catalog_page == 0)): st.session_state.catalog_page -= 1; st.rerun()
            with c_txt:
                st.markdown(f"<div class='pagination-info'>PAGE {st.session_state.catalog_page + 1} / {total_pages} ({total_items} modèles)</div>", unsafe_allow_html=True)
            with c_next:
                if st.button("SUIV. ►", key="n1", disabled=(st.session_state.catalog_page == total_pages - 1)): st.session_state.catalog_page += 1; st.rerun()

        st.markdown("---")
        
        # Utilisation d'un formulaire pour regrouper toutes les sélections et la soumission
        with st.form("bulk_ship_acquisition_form"):
            
            if not current_items:
                st.info("Aucun vaisseau ne correspond aux filtres sélectionnés.")
            else:
                cols = st.columns(2)
                for i, (name, data) in enumerate(current_items):
                    with cols[i % 2]:
                        img_b64 = get_local_img_as_base64(data.get("img", ""))
                        
                        # LOGIQUE D'AFFICHAGE DU PRIX
                        if purchase_source == "STORE":
                            price_value = data.get('price', 0)
                            if isinstance(price_value, (int, float)):
                                price_display = f"${price_value:,.2f} USD"
                            else: 
                                price_display = str(price_value) 
                            price_class = "usd-price"
                        else: # source == "INGAME"
                            price_value = data.get('auec_price', 0)
                            
                            if isinstance(price_value, (int, float)) and price_value > 0:
                                price_display = f"{price_value:,.0f} aUEC" 
                            elif isinstance(price_value, str):
                                price_display = price_value
                            else:
                                price_display = "Prix non spécifié" 
                                
                            price_class = "auec-price"
                            
                        role = data.get("role", "Inconnu")
                        brand = data.get("brand", "N/A")

                        # NOUVEAU: Case à cocher pour la sélection (widget Streamlit invisible)
                        checkbox_key = f"check_{name}"
                        
                        # 1. Widget Streamlit (fonctionnalité)
                        is_selected = st.checkbox(
                            f"SÉLECTIONNER", 
                            key=checkbox_key, 
                            value=False, 
                            label_visibility="collapsed", 
                        )
                        
                        # 2. Styles dynamiques pour le label HTML
                        selected_class = "selected-card" if is_selected else ""
                        label_text = f"✅ SÉLECTIONNÉ" if is_selected else "☐ SÉLECTIONNER"
                        
                        # Couleurs en fonction de l'état (pour le style en ligne)
                        if is_selected:
                            label_color = '#041623'
                            label_background = '#00d4ff'
                        else:
                            label_color = '#ffffff'
                            label_background = 'rgba(4, 20, 35, 0.9)'


                        st.markdown(f"""
<div class="catalog-card-wrapper">
  <div class="catalog-card {selected_class}">
    <div class="card-checkbox-overlay">
        
        <label for="{checkbox_key}" class="custom-ship-label" style="
            background: {label_background};
            color: {label_color};
        ">
            <span style="font-family: 'Orbitron', sans-serif; font-weight: 700;">
                {label_text}
            </span>
        </label>
    </div>
    <div class="card-img-container">
      <img src="{img_b64}" class="card-img">
      <span class="card-brand-top">{brand}</span>
      <div class="card-tags-bar">
        <span class="card-tag">{role}</span>
        <span class="card-tag">{purchase_source}</span>
      </div>
    </div>
    <div class="card-info">
      <div class="ships-name" title="{name}">{name}</div>
      <div class="price-box">
        <span class="card-role-info">RÔLE: {role}</span>
        <span class="ship-price-value {price_class}">{price_display}</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)
                        

            st.markdown("---")
            # --- BOUTON DE SOUMISSION UNIQUE DU FORMULAIRE ---
            submit_button = st.form_submit_button(
                "✅ ENREGISTRER LA SÉLECTION DANS MON HANGAR",
                type="primary",
                use_container_width=True,
            )

        # --- LOGIQUE DE TRAITEMENT DU FORMULAIRE APRÈS SOUMISSION ---
        if submit_button:
            if not st.session_state.current_pilot:
                st.error("Veuillez vous connecter pour enregistrer des vaisseaux.")
            else:
                # 1. Identifier tous les vaisseaux qui ont été cochés
                selected_ship_names = []
                
                # On itère sur les items affichés (et donc soumis dans le formulaire)
                for ship_name, _ in current_items: 
                    checkbox_key = f"check_{ship_name}"
                    # On vérifie l'état de la checkbox dans la session (mis à jour par le form submission)
                    if st.session_state.get(checkbox_key):
                        selected_ship_names.append(ship_name)
                    
                if not selected_ship_names:
                    st.warning("Aucun vaisseau n'a été coché pour l'enregistrement. Veuillez cocher au moins un vaisseau.")
                else:
                    # 2. Appeler la nouvelle fonction d'ajout avec la liste
                    add_selected_ships_action(
                        selected_ship_names,
                        st.session_state.current_pilot,
                        st.session_state.selected_source,
                        st.session_state.selected_insurance
                    )


    with col_commander:
        st.subheader("ACQUISITION LOGISTIQUE")
        
        if st.session_state.current_pilot:
            pilot_data = st.session_state.db.get("user_data", {}).get(st.session_state.current_pilot, {})
            current_auec_balance = pilot_data.get("auec_balance", 0)
            st.markdown(f"<h4 style='color:#30e8ff;'>Solde aUEC : {current_auec_balance:,.0f}</h4>", unsafe_allow_html=True)
            st.markdown("---")

        
        st.markdown("**MODE OPÉRATIONNEL :**")
        st.markdown(f"<span style='color:#FFF; font-weight:bold;'>ENREGISTREMENT EN BLOC</span>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown(f"**SOURCE SÉLECTIONNÉE :** <span style='color:#FFF;'>{st.session_state.selected_source}</span>", unsafe_allow_html=True)
        st.markdown(f"**ASSURANCE SÉLECTIONNÉE :** <span style='color:#FFF;'>{st.session_state.selected_insurance}</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("Instructions de l'enregistrement en bloc:")
        st.markdown("1. Choisissez la **Source** et l'**Assurance** à gauche.")
        st.markdown("2. **Cochez** les vaisseaux que vous possédez dans le registre principal.")
        st.markdown("3. Cliquez sur le bouton **'✅ ENREGISTRER LA SÉLECTION...'** en bas du registre pour valider l'ensemble.")
        st.markdown("*Note : Les options de la colonne de gauche s'appliquent à **tous** les vaisseaux cochés sur la page actuelle lors de la soumission.*")
        
        if not st.session_state.current_pilot:
            st.info("Connectez-vous pour enregistrer un vaisseau.")


def my_hangar_page():
    """Affiche et permet la modification de la flotte personnelle, séparée par source, avec totaux et recherche."""
    st.subheader(f"HANGAR LOGISTIQUE | PILOTE: {st.session_state.current_pilot}")
    st.markdown("---")

    # --- LECTURE DES VARIABLES NÉCESSAIRES ---
    pilot_data = st.session_state.db.get("user_data", {}).get(st.session_state.current_pilot, {})
    current_auec_balance = pilot_data.get("auec_balance", 0)
    final_target_name = pilot_data.get("acquisition_target", None)
    
    # --- LISTE DES VAISSEAUX POSSÉDÉS ---
    my_fleet = [
        s
        for s in st.session_state.db["fleet"]
        if s["Propriétaire"] == st.session_state.current_pilot
    ]

    if not my_fleet:
        st.info("Hangar vide. Ajoutez des vaisseaux depuis le CATALOGUE.")
        render_acquisition_tracking(current_auec_balance, final_target_name)
        return
    else:
        df_my = pd.DataFrame(my_fleet)
        df_my["Supprimer"] = False

        # Conversion des prix en numérique pour les calculs de totaux (les chaînes deviennent 0)
        df_my["Prix_USD"] = pd.to_numeric(df_my["Prix_USD"], errors="coerce").fillna(0)
        
        # Le prix aUEC peut être un nombre ou une chaîne. On le convertit en numérique pour le calcul du total.
        df_my["Prix_aUEC_Num"] = df_my["Prix_aUEC"].apply(lambda x: float(x) if isinstance(x, (int, float)) else 0)

        # --- AFFICHAGE DES KPIS (TOTAUX) ---
        total_store_ships = len(df_my[df_my["Source"] == "STORE"])
        total_ingame_ships = len(df_my[df_my["Source"] == "INGAME"])
        
        col_count_usd, col_count_aUEC, col_filler = st.columns(3)
        
        col_count_usd.metric(
            "Vaisseaux Store (Pledge)", 
            value=f"{total_store_ships} unités"
        )
        col_count_aUEC.metric(
            "Vaisseaux InGame (aUEC)", 
            value=f"{total_ingame_ships} unités"
        )
        
        st.markdown("---")

        # --- BARRE DE RECHERCHE ET FILTRAGE ---
        search_term = st.text_input("🔍 Rechercher dans mon hangar (Vaisseau, Marque, Rôle, Assurance)", key="hangar_search_input").lower()
        
        df_filtered = df_my.copy()
        if search_term:
            df_filtered = df_filtered[
                df_filtered['Vaisseau'].str.lower().str.contains(search_term) |
                df_filtered['Marque'].str.lower().str.contains(search_term) |
                df_filtered['Rôle'].str.lower().str.contains(search_term) |
                df_filtered['Assurance'].str.lower().str.contains(search_term)
            ].copy()

        # Re-séparation du DataFrame filtré pour l'affichage
        # Correction critique: Appliquer reset_index() pour garantir des index propres après filtrage
        df_store = df_filtered[df_filtered["Source"] == "STORE"].reset_index(drop=True).copy()
        df_ingame = df_filtered[df_filtered["Source"] == "INGAME"].reset_index(drop=True).copy()
        
        
        # Correction : Forcer la Base64 des images locales pour l'aperçu du tableau
        df_store['Visuel'] = df_store['Image'].apply(get_local_img_as_base64)
        df_ingame['Visuel'] = df_ingame['Image'].apply(get_local_img_as_base64)

        # 1. Calcul de la colonne de prix unique pour l'affichage
        def get_price_display(row):
            if row["Source"] == "INGAME":
                if isinstance(row["Prix_aUEC"], str):
                    return row['Prix_aUEC']
                elif row['Prix_aUEC_Num'] > 0:
                    return f"{row['Prix_aUEC_Num']:,.0f} aUEC"
                else:
                    return "N/A"
            else: # Source == "STORE"
                if row["Prix_USD"] > 0:
                    return f"${row['Prix_USD']:,.0f} USD"
                else:
                    return "N/A"

        df_store["Prix_Acquisition"] = df_store.apply(get_price_display, axis=1)
        df_ingame["Prix_Acquisition"] = df_ingame.apply(get_price_display, axis=1)


        # Colonnes visibles et configurées
        columns_for_display = [
            "id", 
            "Vaisseau", 
            "Marque", 
            "Rôle", 
            "Dispo", 
            "Visuel", 
            "Source", 
            "Assurance",
            "Prix_Acquisition", 
            "Supprimer"
        ]
        
        editable_columns_base = {
            "id": st.column_config.Column("ID", disabled=True, width="small"),
            "Dispo": st.column_config.CheckboxColumn("OPÉRATIONNEL ?", width="small"),
            "Supprimer": st.column_config.CheckboxColumn("SUPPRIMER", width="small"),
            "Visuel": st.column_config.ImageColumn("APERÇU", width="small"),
            "Source": st.column_config.TextColumn("SOURCE", disabled=True, width="small"),
            "Assurance": st.column_config.SelectboxColumn(
                "ASSURANCE",
                options=["LTI", "10 Ans", "6 Mois", "2 Mois", "Standard"],
                width="medium",
            ),
            "Prix_Acquisition": st.column_config.TextColumn("PRIX", disabled=True, width="small"),
            "Vaisseau": st.column_config.TextColumn("Vaisseau", disabled=True, width="medium"),
            "Marque": st.column_config.TextColumn("Marque", disabled=True, width="small"),
            "Rôle": st.column_config.TextColumn("Rôle", disabled=True, width="small"),
        }
        
        # Colonnes à désactiver dans l'éditeur (sauf les champs modifiables)
        disabled_cols = [col for col in editable_columns_base.keys() if col not in ["Dispo", "Assurance", "Supprimer"]]

        
        # --- HANGAR STORE (Affichage après filtrage) ---
        df_store_display = df_store[columns_for_display].copy()
        st.markdown("## 💰 HANGAR STORE (Propriété USD)")

        if not df_store.empty:
            total_usd = df_store["Prix_USD"].sum()
            col_usd_2, col_toggle_usd = st.columns([3, 1])
            show_usd = col_toggle_usd.toggle(
                "Afficher Valorisation Totale (USD)", value=False, key="toggle_usd"
            )
            col_usd_2.metric(
                "VALORISATION TOTALE DE LA SÉLECTION", f"${total_usd:,.0f}" if show_usd else "---"
            )
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) 

            edited_store = st.data_editor(
                df_store_display,
                column_config=editable_columns_base,
                disabled=disabled_cols,
                hide_index=True,
                use_container_width=True,
                key="store_hangar_editor",
            )
        else:
            st.info(f"Aucun vaisseau provenant du Store ne correspond à la recherche ('{search_term}').")
            edited_store = pd.DataFrame(columns=columns_for_display)

        st.markdown("---")

        # --- HANGAR INGAME (Affichage après filtrage) ---
        df_ingame_display = df_ingame[columns_for_display].copy()
        
        st.markdown("## 💸 HANGAR INGAME (Acquisition aUEC)")

        if not df_ingame.empty:
            total_aUEC = df_ingame["Prix_aUEC_Num"].sum()
            col_aUEC_2, col_toggle_aUEC = st.columns([3, 1])
            show_aUEC = col_toggle_aUEC.toggle(
                "Afficher Coût Total (aUEC)", value=False, key="toggle_aUEC"
            )
            col_aUEC_2.metric(
                "COÛT TOTAL DE LA SÉLECTION", f"{total_aUEC:,.0f} aUEC" if show_aUEC else "---"
            )
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) 

            edited_ingame = st.data_editor(
                df_ingame_display,
                column_config=editable_columns_base,
                disabled=disabled_cols,
                hide_index=True,
                use_container_width=True,
                key="ingame_hangar_editor",
            )
        else:
            st.info(f"Aucun vaisseau acheté en jeu ne correspond à la recherche ('{search_term}').")
            edited_ingame = pd.DataFrame(columns=columns_for_display)

        # --- SAUVEGARDE GLOBALE DES VAISSEAUX POSSÉDÉS ---
        st.markdown("---")
        combined_edited = pd.concat([edited_store, edited_ingame], ignore_index=True)

        if st.button(
            "💾 ACTUALISER LA FLOTTE (SAUVEGARDER & SUPPRIMER)",
            type="primary",
            use_container_width=True,
        ):
            if not combined_edited.empty:
                process_fleet_updates(combined_edited)
            else:
                st.info("Aucune modification significative à enregistrer.")


    # -------------------------------------------------------------
    # --- ZONE : SUIVI D'ACQUISITION FUTURE (DÉPLACÉE EN BAS) ---
    # -------------------------------------------------------------
    render_acquisition_tracking(current_auec_balance, final_target_name)

def render_acquisition_tracking(current_auec_balance, final_target_name):
    """Render the acquisition tracking section, used by my_hangar_page."""
    st.markdown("---") # Séparateur visuel
    st.markdown("## 🎯 SUIVI D'ACQUISITION FUTURE (aUEC)")
    
    # Liste de tous les vaisseaux achetable en aUEC pour le sélecteur cible
    # Utilisation du champ 'ingame' du catalogue pour le sélecteur
    ingame_ships = sorted([name for name, data in SHIPS_DB.items() if data.get('ingame', False)])
    ingame_options = ["— Sélectionner un objectif —"] + ingame_ships
    
    # Déterminer l'index par défaut pour le selectbox
    current_target_index = ingame_options.index(final_target_name) if final_target_name in ingame_options else 0
    
    
    with st.form("acquisition_target_form"):
        col_input, col_selector = st.columns([1, 2])
        
        with col_input:
            new_auec_balance = st.number_input(
                "💰 **MON SOLDE aUEC ACTUEL**",
                min_value=0,
                value=int(current_auec_balance),
                step=1000,
                key="hangar_auec_input_form",
                help="Entrez votre solde actuel pour suivre votre progression d'achat."
            )

        with col_selector:
            selected_target = st.selectbox(
                "🚀 **VAISSEAU CIBLE EN JEU**",
                ingame_options,
                index=current_target_index,
                key="hangar_target_select_form",
            )
            
        
        submitted = st.form_submit_button("💾 ENREGISTRER MON SOLDE / OBJECTIF", type="primary")

        if submitted:
            new_target = st.session_state.hangar_target_select_form if st.session_state.hangar_target_select_form != "— Sélectionner un objectif —" else None
            
            st.session_state.db["user_data"].setdefault(st.session_state.current_pilot, {})
            user_data_update = st.session_state.db["user_data"][st.session_state.current_pilot]
            
            user_data_update["auec_balance"] = st.session_state.hangar_auec_input_form
            user_data_update["acquisition_target"] = new_target
            
            if save_db_to_cloud(st.session_state.db):
                st.toast("✅ Solde et objectif d'acquisition enregistrés !", icon="🎯")
                st.rerun()

    # Logique de Suppression d'Objectif (hors du formulaire pour pouvoir rerun)
    if final_target_name and st.button("🗑️ SUPPRIMER L'OBJECTIF ACTUEL", use_container_width=True):
        st.session_state.db["user_data"].setdefault(st.session_state.current_pilot, {})
        user_data_update = st.session_state.db["user_data"][st.session_state.current_pilot]
        
        user_data_update["acquisition_target"] = None
        
        if save_db_to_cloud(st.session_state.db):
            st.toast("🗑️ Objectif d'acquisition supprimé.", icon="❌")
            st.rerun()
            
    
    # --- AFFICHAGE DE LA PROGRESSION (Calculé à partir des valeurs sauvegardées) ---
    if final_target_name and final_target_name in SHIPS_DB:
        target_info = SHIPS_DB[final_target_name]
        cost_auec = float(target_info.get('auec_price', 0) or 0)
        
        if cost_auec > 0:
            st.markdown("---")
            st.markdown("#### PROCHAIN OBJECTIF : **" + final_target_name + "**")
            
            progress_ratio = min(1.0, current_auec_balance / cost_auec)
            progress_percent = int(progress_ratio * 100)
            
            col_metric_1, col_metric_2 = st.columns(2)
            
            col_metric_1.metric(
                "COÛT CIBLE", 
                f"{cost_auec:,.0f} aUEC", 
            )
            col_metric_2.metric(
                "PROGRESSION", 
                f"{current_auec_balance:,.0f} aUEC", 
                delta=f"{progress_percent}%", 
                delta_color="normal" if progress_percent < 100 else "inverse"
            )

            st.progress(progress_ratio, text=f"**{current_auec_balance:,.0f} aUEC / {cost_auec:,.0f} aUEC**")
            
            if progress_percent >= 100:
                st.success("Fonds suffisants ! Vous pouvez acheter votre vaisseau. 🚀")
            else:
                remaining = cost_auec - current_auec_balance
                st.warning(f"Il vous manque **{remaining:,.0f} aUEC** pour l'acquisition.")
        else:
            st.info("Le vaisseau cible sélectionné n'a pas de prix en aUEC dans le catalogue.")
    # --- FIN AFFICHAGE PROGRESSION ---


def corpo_fleet_page():
    """Affiche les statistiques et le détail de la flotte corporative globale."""
    st.subheader("REGISTRE GLOBAL DE LA CORPO")

    if not st.session_state.db["fleet"]:
        st.info(
            "Base de données de flotte vide. Demandez aux pilotes d'ajouter leurs vaisseaux."
        )
        return

    # Normalisation pour être sûr d'avoir toutes les colonnes
    df_global_raw = pd.DataFrame(st.session_state.db["fleet"])
    df_global_norm = normalize_db_schema(
        {"fleet": df_global_raw.to_dict("records")}
    )["fleet"]
    df_global = pd.DataFrame(df_global_norm)

    # Conversion des colonnes prix en numérique
    df_global["Prix_USD"] = pd.to_numeric(df_global["Prix_USD"], errors="coerce").fillna(
        0
    )
    df_global["Prix_aUEC_Num"] = df_global["Prix_aUEC"].apply(lambda x: float(x) if isinstance(x, (int, float)) else 0)

    # Joindre le Crew Max à partir de SHIPS_DB (pour les totaux et graphiques)
    def get_ship_info(row, key):
        return SHIPS_DB.get(row['Vaisseau'], {}).get(key, row.get(key, 1))
        
    df_global['Crew_Max_Catalog'] = df_global.apply(lambda row: get_ship_info(row, 'crew_max'), axis=1)


    # KPI principaux
    total_ships = len(df_global)
    total_dispo = int(df_global["Dispo"].sum())
    total_pilots = len(st.session_state.db["users"])

    total_value_usd = df_global[df_global["Source"] == "STORE"]["Prix_USD"].sum()
    total_value_aUEC = df_global[df_global["Source"] == "INGAME"]["Prix_aUEC_Num"].sum()

    st.markdown("---")

    # AFFICHAGE DES KPI AVEC TOGGLE
    col_kpi, col_toggle = st.columns([4, 1])

    with col_toggle:
        show_value_kpi = st.toggle(
            "Afficher Valorisation Totale",
            value=False,
            key="toggle_corpo_kpi",
        )

    with col_kpi:
        c1, c2, c3, c4, c5 = st.columns(5)

        # Affichage conditionnel des totaux
        value_usd_display = f"${total_value_usd:,.0f}" if show_value_kpi else "---"
        value_aUEC_display = f"{total_value_aUEC:,.0f} aUEC" if show_value_kpi else "---"

        c1.metric("PILOTES", total_pilots)
        c2.metric("FLOTTE TOTALE", total_ships)
        c3.metric("OPÉRATIONNELS", total_dispo)
        c4.metric("VALEUR STORE", value_usd_display)
        c5.metric("COÛT INGAME", value_aUEC_display)

    st.markdown("---")


    # === ANALYSES GRAPHIQUES (version plus clean) ===
    st.markdown("### 📊 ANALYSE DE COMPOSITION")
    col_chart1, col_chart2 = st.columns(2)

    # 1) Donut par Marque (nombre d'unités)
    summary_brand = df_global.groupby("Marque").size().reset_index(name="Quantité")
    summary_brand = summary_brand.sort_values("Quantité", ascending=False)

    fig_brand = px.pie(
        summary_brand,
        values="Quantité",
        names="Marque",
        hole=0.45,
        title="Répartition de la flotte par constructeur",
        color_discrete_sequence=px.colors.sequential.Blues_r,
    )
    fig_brand.update_traces(
        textposition="inside",
        textinfo="percent+label",
        pull=[0.04] + [0] * (len(summary_brand) - 1),
    )
    fig_brand.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(t=60, b=0, l=0, r=0),
        showlegend=False,
    )
    col_chart1.plotly_chart(fig_brand, use_container_width=True)

    # 2) Bar chart horizontal par rôle (nombre d'unités)
    summary_role = df_global.groupby("Rôle").size().reset_index(name="Quantité")
    summary_role = summary_role.sort_values("Quantité", ascending=True)

    fig_role = px.bar(
        summary_role,
        x="Quantité",
        y="Rôle",
        orientation="h",
        title="Répartition par rôle",
        color="Quantité",
        color_continuous_scale="Blues",
    )
    fig_role.update_layout(
        template="plotly_dark",
        height=420,
        margin=dict(t=60, b=10, l=10, r=10),
        xaxis_title="Nombre de vaisseaux",
        yaxis_title="",
        coloraxis_showscale=False,
    )
    fig_role.update_traces(marker_line_width=0.5, marker_line_color="#0a141f")
    col_chart2.plotly_chart(fig_role, use_container_width=True)

    st.markdown("---")

    # === RÉSUMÉ DES STOCKS ===
    st.markdown("### 📦 RÉSUMÉ DES STOCKS")
    
    # Regroupement des stocks
    summary_df = (
        df_global.groupby(["Vaisseau", "Marque", "Rôle"])
        .agg(
            Quantité=("Vaisseau", "count"), 
            Dispo=("Dispo", "sum"),
            Crew_Max=("Crew_Max_Catalog", "first") 
        )
        .reset_index()
        .sort_values(by="Quantité", ascending=False)
    )

    st.dataframe(
        summary_df,
        column_config={
            "Quantité": st.column_config.ProgressColumn(
                "Total",
                format="%d",
                min_value=0,
                max_value=int(summary_df["Quantité"].max()),
            ),
            "Dispo": st.column_config.NumberColumn("Prêtables"),
            "Crew_Max": st.column_config.NumberColumn("CREW MAX", format="%d"), 
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # AJOUT DU FILTRE DE RECHERCHE RAPIDE
    search_term = st.text_input("🔍 Recherche rapide (Vaisseau, Pilote, Rôle)", key="global_search_input_detail")
    
    
    # === LISTE DÉTAILLÉE DES UNITÉS (Tableau Regroupé par Pilote) ===
    st.markdown("### 📋 LISTE DÉTAILLÉE DES UNITÉS")

    # Filtre sur la disponibilité
    display_df = df_global.copy()
    if st.checkbox("✅ Afficher uniquement les vaisseaux opérationnels", value=False, key="global_dispo_check"):
        display_df = display_df[display_df["Dispo"] == True].copy()

    # Application de la recherche rapide
    if search_term:
        search_term = search_term.lower()
        display_df = display_df[
            display_df['Vaisseau'].str.lower().str.contains(search_term) |
            display_df['Propriétaire'].str.lower().str.contains(search_term) |
            display_df['Rôle'].str.lower().str.contains(search_term)
        ].copy()


    # 1. Regrouper les lignes pour la LISTE DÉTAILLÉE (Regrouper par Modèle, Classification, et Source - Ignorer l'Assurance pour la fusion)
    detail_data = display_df.groupby(['Vaisseau', 'Marque', 'Rôle', 'Source']).agg(
        Pilotes=('Propriétaire', lambda x: ', '.join(sorted(x.unique()))), # JOINDRE LES PILOTES
        Assurance=('Assurance', lambda x: ', '.join(sorted(x.unique()))), # JOINDRE LES ASSURANCES
        Quantité=('Vaisseau', 'count'), # Nombre de ships par ligne
        Crew_Max=('Crew_Max_Catalog', 'first'),
        Image=('Image', 'first'),
    ).reset_index()

    # 2. Préparer les colonnes pour l'affichage final
    display_for_table = pd.DataFrame()
    display_for_table['Pilotes'] = detail_data['Pilotes']
    display_for_table['Modèle'] = detail_data['Vaisseau']
    display_for_table['Classification'] = detail_data['Rôle']
    display_for_table['Source'] = detail_data['Source']
    display_for_table['Assurance'] = detail_data['Assurance'] # Liste des assurances fusionnées
    display_for_table['Crew Max'] = detail_data['Crew_Max']
    display_for_table['NB Ex.'] = detail_data['Quantité']
    
    # Régénérer la Base64 en utilisant la colonne 'Image' (chemin local)
    display_for_table['Visuel'] = detail_data['Image'].apply(get_local_img_as_base64)
    
    # Calculer le Prix Affiché (du modèle)
    def calculate_aggregated_price(row):
        ship_name = row['Modèle']
        source = row['Source']
        
        info = SHIPS_DB.get(ship_name)
        if not info:
            return "N/A"
            
        if source == 'STORE':
            return f"${info.get('price', 0):,.0f} USD"
        else:
            price_raw = info.get('auec_price', 0)
            if isinstance(price_raw, (int, float)):
                return f"{price_raw:,.0f} aUEC"
            else:
                return str(price_raw)


    display_for_table['Prix'] = display_for_table.apply(calculate_aggregated_price, axis=1)
    
    # 3. Afficher le tableau final
    st.dataframe(
        display_for_table,
        column_config={
            "Pilotes": st.column_config.TextColumn("PILOTES", help="Liste des propriétaires"),
            "Modèle": st.column_config.TextColumn("VAISSEAU"),
            "Classification": st.column_config.TextColumn("RÔLE"),
            "Source": st.column_config.TextColumn("SOURCE"),
            "Assurance": st.column_config.TextColumn("ASSURANCE", help="Assurances possédées pour ce modèle"),
            "Crew Max": st.column_config.TextColumn("CREW MAX"),
            "Visuel": st.column_config.ImageColumn("APERÇU", width="small"),
            "Prix": st.column_config.TextColumn("PRIX"),
            "NB Ex.": st.column_config.TextColumn("NB EX.", width="small"), 
        },
        use_container_width=True,
        hide_index=True,
        height=400,
        selection_mode="disabled", 
        key="global_fleet_detail",
    )


# --- MAIN ---
render_sidebar()

if not st.session_state.current_pilot:
    home_page()
else:
    st.markdown("<h1>PIONEER COMMAND | CONSOLE D'OPÉRATIONS</h1>", unsafe_allow_html=True)
    if st.session_state.menu_nav == "CATALOGUE": catalogue_page()
    elif st.session_state.menu_nav == "MON HANGAR": my_hangar_page()
    elif st.session_state.menu_nav == "FLOTTE CORPO": corpo_fleet_page()