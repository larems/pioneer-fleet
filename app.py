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
JSONBIN_ID = st.secrets.get("JSONBIN_ID", "6921f0ded0ea881f40f9433f")
JSONBIN_KEY = st.secrets.get("JSONBIN_KEY", "")


def normalize_db_schema(db: dict) -> dict:
    """
    Normalise la structure de la DB pour éviter les KeyError
    (ajout des clés manquantes avec valeurs par défaut).
    """
    db.setdefault("users", {})
    db.setdefault("fleet", [])

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
        ship.setdefault("Prix_aUEC", 0.0)
        ship.setdefault("Assurance", "Standard")

    return db


@st.cache_data(ttl=300, show_spinner="Chargement de la base de données...")
def load_db_from_cloud():
    """Charge la base de données depuis JSONBin.io."""
    if not JSONBIN_KEY:
        st.warning(
            "⚠️ Clé JSONBIN.io (MASTER_KEY) manquante. Utilisation d'une base de données locale temporaire."
        )
        return {"users": {}, "fleet": []}

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest"
    headers = {"X-Master-Key": JSONBIN_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json().get("record", {"users": {}, "fleet": []})
            return normalize_db_schema(data)
        else:
            st.error(f"Erreur de chargement DB: Statut {response.status_code}.")
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur réseau/timeout lors du chargement: {e}")

    return {"users": {}, "fleet": []}


def save_db_to_cloud(data):
    """Sauvegarde la base de données sur JSONBin.io."""
    if not JSONBIN_KEY:
        st.error("Impossible de sauvegarder : Clé JSONBIN.io (MASTER_KEY) manquante.")
        return False

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
    headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_KEY}

    try:
        response = requests.put(url, json=data, headers=headers, timeout=10)
        if response.status_code not in (200, 204):
            st.error(f"Erreur de sauvegarde DB: Statut {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur réseau/timeout lors de la sauvegarde: {e}")
        return False

    load_db_from_cloud.clear()
    return True


# DB dans la session
if "db" not in st.session_state:
    st.session_state.db = normalize_db_schema(load_db_from_cloud())
else:
    st.session_state.db = normalize_db_schema(st.session_state.db)


# --- 3. FONCTIONS UTILITAIRES & ACTIONS ---


@st.cache_data(show_spinner=False)
def get_local_img_as_base64(path):
    """Convertit une image locale en Base64."""
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            encoded = base64.b64encode(data).decode()
            mime_type = "image/png" if path.lower().endswith(".png") else "image/jpeg"
            return f"data:{mime_type};base64,{encoded}"
        except Exception:
            pass
    # fallback
    return (
        "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDov"
        "L3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdo"
        "dD0iNDAwIiB2aWV3Qm94PSIwIDAgODAwIDQwMCI+PHJlY3Qgd2lkdG"
        "g9IjgwMCIgaGVpZ2h0PSI0MDAiIGZpbGw9IiMwYjBlMTIiLz48dGV4"
        "dCB4PSI0MDAiIHk9IjIwMCIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRs"
        "ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9ImFyaWFs"
        "IiBmb250LXNpemU9IjUwIiBmaWxsPSIjMDBkNGZmIj5JTUFHRSBNSVNT"
        "SU5HPC90ZXh0Pjwvc3ZnPg=="
    )


def select_ship(ship_name, source, insurance):
    """Met à jour l'état de la session pour le vaisseau sélectionné dans le catalogue."""
    st.session_state.selected_ship_name = ship_name
    st.session_state.selected_source = source
    st.session_state.selected_insurance = insurance


def add_ship_action():
    """Ajoute le vaisseau sélectionné à la flotte (enregistrement de possession)."""
    ship_name = st.session_state.selected_ship_name
    owner = st.session_state.current_pilot
    source = st.session_state.selected_source
    insurance = st.session_state.selected_insurance

    if ship_name is None or ship_name not in SHIPS_DB or not owner:
        st.toast(
            "Erreur d'ajout. Veuillez vous connecter et sélectionner un vaisseau.",
            icon="❌",
        )
        return

    info = SHIPS_DB[ship_name]
    new_id = int(time.time() * 1_000_000)

    # Vérification anti-doublon
    is_duplicate = any(
        s["Propriétaire"] == owner
        and s["Vaisseau"] == ship_name
        and s["Source"] == source
        and s.get("Assurance") == insurance
        for s in st.session_state.db["fleet"]
    )

    if is_duplicate:
        st.toast(
            f"🛑 {ship_name} est déjà enregistré avec cette configuration d'assurance/source.",
            icon="🛑",
        )
        return

    img_b64 = get_local_img_as_base64(info.get("img", ""))
    price_usd = info.get("price", 0.0)
    price_aUEC = info.get("auec_price", 0.0)

    new_entry = {
        "id": new_id,
        "Propriétaire": owner,
        "Vaisseau": ship_name,
        "Marque": info.get("brand", "N/A"),
        "Rôle": info.get("role", "Inconnu"),
        "Dispo": False,
        "Image": info.get("img", ""),
        "Visuel": img_b64,
        "Source": source,
        "Prix_USD": float(price_usd or 0),
        "Prix_aUEC": float(price_aUEC or 0),
        "Assurance": insurance,
    }

    st.session_state.db["fleet"].append(new_entry)
    st.session_state.db = normalize_db_schema(st.session_state.db)

    if save_db_to_cloud(st.session_state.db):
        st.session_state.session_log.append(f"+ {ship_name} enregistré ({insurance})")
        st.toast(f"✅ {ship_name} ENREGISTRÉ DANS HANGAR!", icon="🚀")
        st.session_state.selected_ship_name = None
        time.sleep(0.4)
        st.rerun()


def process_fleet_updates(edited_df: pd.DataFrame):
    """Met à jour les entrées de la flotte (disponibilité, suppression, assurance) et sauvegarde."""
    if edited_df.empty:
        st.info("Aucune modification à synchroniser.")
        return

    current_db = st.session_state.db
    current_fleet = current_db["fleet"]
    needs_save = False

    # Suppression
    if "Supprimer" in edited_df.columns:
        ids_to_delete = edited_df[edited_df["Supprimer"] == True]["id"].tolist()
    else:
        ids_to_delete = []

    if ids_to_delete:
        current_fleet[:] = [
            s for s in current_fleet if s.get("id") not in ids_to_delete
        ]
        needs_save = True
        st.toast(f"🗑️ {len(ids_to_delete)} vaisseaux supprimés.", icon="🗑️")

    # Mise à jour dispo / assurance
    update_df = edited_df[~edited_df["id"].isin(ids_to_delete)].copy()
    if not update_df.empty:
        for ship in current_fleet:
            sid = ship.get("id")
            row = update_df[update_df["id"] == sid]
            if not row.empty:
                row = row.iloc[0]
                if "Dispo" in row and ship["Dispo"] != row["Dispo"]:
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
    color: #e0e8f0;
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

/* Bouton de sélection sous la carte */
.card-footer-button {{
    margin-top: 0;
}}
div.card-footer-button > div.stButton > button {{
    width: 100%;
    border-radius: 0 0 8px 8px;
    background: linear-gradient(90deg, #00d4ff, #30e8ff);
    color: #041623;
    font-family: 'Orbitron', sans-serif;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 8px 0;
    font-weight: 700;
}}
div.stButton > button:hover {{
    filter: brightness(1.05);
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.75);
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
</style>
""",
    unsafe_allow_html=True,
)

# --- 5. SESSION STATE ---
if "current_pilot" not in st.session_state:
    st.session_state.current_pilot = None
if "catalog_page" not in st.session_state:
    st.session_state.catalog_page = 0
if "menu_nav" not in st.session_state:
    st.session_state.menu_nav = "CATALOGUE"
if "session_log" not in st.session_state:
    st.session_state.session_log = []
if "selected_ship_name" not in st.session_state:
    st.session_state.selected_ship_name = None
if "selected_source" not in st.session_state:
    st.session_state.selected_source = "STORE"
if "selected_insurance" not in st.session_state:
    st.session_state.selected_insurance = "LTI"


# --- 6. SIDEBAR ---
def render_sidebar():
    with st.sidebar:
        st.markdown(
            "<h2 style='text-align: left; color: #fff !important; font-size: 1.5em; border:none;'>💠 PIONEER</h2>",
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        if st.session_state.current_pilot:
            st.markdown(
                f"<div style='color:#00d4ff; font-weight:bold; margin-bottom:10px;'>PILOTE: {st.session_state.current_pilot}</div>",
                unsafe_allow_html=True,
            )

            if st.button("DÉCONNEXION", use_container_width=True):
                st.session_state.current_pilot = None
                st.session_state.session_log = []
                st.session_state.menu_nav = "CATALOGUE"
                st.rerun()

            st.markdown("---")

            if st.session_state.session_log:
                st.caption("JOURNAL D'OPÉRATIONS:")
                for log in reversed(st.session_state.session_log[-5:]):
                    st.markdown(
                        f"<span style='color:#30E8FF; font-size:0.8em;'>{log}</span>",
                        unsafe_allow_html=True,
                    )
                st.markdown("---")

            selected_menu = st.radio(
                "NAVIGATION CONSOLE",
                ["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"],
                index=["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"].index(
                    st.session_state.menu_nav
                ),
                label_visibility="collapsed",
                key="nav_radio",
            )

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
    st.markdown(
        "<div style='margin-top:40px;'></div>",
        unsafe_allow_html=True,
    )
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
            st.markdown(
                "<div style='height:12px;'></div>",
                unsafe_allow_html=True,
            )
            st.subheader("CONNEXION PILOTE", divider="gray")
            pseudo = st.text_input("Identifiant de pilote", key="landing_pseudo")
            pin = st.text_input(
                "PIN (4 chiffres)", type="password", max_chars=4, key="landing_pin"
            )
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

        st.markdown(
            """
<p style="text-align:center; font-size:0.8rem; color:#76869a; margin-top:6px;">
  Astuce : votre flotte restera sauvegardée tant que vous utilisez le même ID + PIN.
</p>
""",
            unsafe_allow_html=True,
        )


def catalogue_page():
    col_filters, col_main_catalogue, col_commander = st.columns([1, 3.5, 1.5])

    # --- COLONNE 1: FILTRES & COMMANDES D'AJOUT ---
    with col_filters:
        st.subheader("PARAMÈTRES")

        purchase_source = st.radio(
            "SOURCE DE POSSESSION",
            ["STORE", "INGAME"],
            captions=["(Achat USD)", "(Achat aUEC)"],
            index=0 if st.session_state.selected_source == "STORE" else 1,
            horizontal=False,
            key="purchase_source_radio",
        )
        st.session_state.selected_source = purchase_source

        insurance_options = ["LTI", "10 Ans", "6 Mois", "2 Mois", "Standard"]
        selected_insurance = st.selectbox(
            "ASSURANCE ACQUISE",
            insurance_options,
            index=insurance_options.index(st.session_state.selected_insurance),
            key="insurance_selectbox",
        )
        st.session_state.selected_insurance = selected_insurance

        st.markdown("---")

        brand_filter = st.selectbox(
            "CONSTRUCTEUR",
            ["Tous"]
            + sorted(
                list(
                    set(
                        d.get("brand")
                        for d in SHIPS_DB.values()
                        if d.get("brand") is not None
                    )
                )
            ),
        )

        all_ships = sorted(list(SHIPS_DB.keys()))
        search_selection = st.multiselect(
            "RECHERCHE", all_ships, placeholder="Tapez le nom..."
        )

    # --- LOGIQUE DE FILTRAGE ---
    filtered = {}
    for name, data in SHIPS_DB.items():
        if purchase_source == "INGAME" and not data.get("ingame", False):
            continue

        match_brand = (brand_filter == "Tous") or (data.get("brand") == brand_filter)
        match_search = (not search_selection) or (name in search_selection)

        if match_brand and match_search:
            filtered[name] = data

    items = list(filtered.items())

    # Pagination
    ITEMS_PER_PAGE = 8
    total_items = len(items)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    if st.session_state.catalog_page >= total_pages:
        st.session_state.catalog_page = 0
    if st.session_state.catalog_page < 0:
        st.session_state.catalog_page = 0

    start = st.session_state.catalog_page * ITEMS_PER_PAGE
    current_items = items[start : start + ITEMS_PER_PAGE]

    # --- COLONNE 2: AFFICHAGE DU CATALOGUE ---
    with col_main_catalogue:
        st.subheader("REGISTRE DES VAISSEAUX")

        # Contrôles de Pagination
        c_prev, c_txt, c_next = st.columns([1, 4, 1])
        if total_pages > 1:
            with c_prev:
                if st.button(
                    "◄ PRÉC.",
                    key="p1",
                    disabled=(st.session_state.catalog_page == 0),
                ):
                    st.session_state.catalog_page -= 1
                    st.rerun()
            with c_txt:
                st.markdown(
                    f"<div class='pagination-info'>PAGE {st.session_state.catalog_page + 1} / {total_pages} ({total_items} modèles)</div>",
                    unsafe_allow_html=True,
                )
            with c_next:
                if st.button(
                    "SUIV. ►",
                    key="n1",
                    disabled=(st.session_state.catalog_page == total_pages - 1),
                ):
                    st.session_state.catalog_page += 1
                    st.rerun()

        st.markdown("---")

        if not current_items:
            st.info("Aucun vaisseau ne correspond aux filtres sélectionnés.")
        else:
            # 2 cartes par ligne
            cols = st.columns(2)
            for i, (name, data) in enumerate(current_items):
                with cols[i % 2]:
                    img_b64 = get_local_img_as_base64(data.get("img", ""))

                    if purchase_source == "STORE":
                        price_display = f"${data.get('price', 0):,.2f} USD"
                        price_class = "usd-price"
                    else:
                        price_display = f"{data.get('auec_price', 0):,.0f} aUEC"
                        price_class = "auec-price"

                    role = data.get("role", "Inconnu")
                    brand = data.get("brand", "N/A")

                    is_selected = st.session_state.selected_ship_name == name
                    selected_class = "selected-card" if is_selected else ""

                    card_html = f"""
<div class="catalog-card-wrapper">
  <div class="catalog-card {selected_class}">
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
"""
                    st.markdown(card_html, unsafe_allow_html=True)

                    st.markdown(
                        "<div class='card-footer-button'>", unsafe_allow_html=True
                    )
                    if st.button(
                        "Sélectionner ce vaisseau",
                        key=f"select_{name}",
                        use_container_width=True,
                    ):
                        select_ship(name, purchase_source, selected_insurance)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

    # --- COLONNE 3: ZONE D'ENREGISTREMENT DYNAMIQUE ---
    with col_commander:
        st.subheader("ACQUISITION LOGISTIQUE")

        selected_name = st.session_state.selected_ship_name

        if selected_name and selected_name in SHIPS_DB:
            info = SHIPS_DB[selected_name]

            st.markdown("**VAISSEAU SÉLECTIONNÉ :**")
            st.markdown(
                f"<div class='ships-name'>{selected_name}</div>", unsafe_allow_html=True
            )
            st.markdown(
                f"<div class='card-brand'>{info.get('brand', 'N/A')} | Rôle : {info.get('role', 'Inconnu')}</div>",
                unsafe_allow_html=True,
            )

            img_path = info.get("img", "")
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
            else:
                st.warning("Visuel non trouvé.")

            st.markdown(
                f"**SOURCE :** <span style='color:#FFF;'>{st.session_state.selected_source}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"**ASSURANCE :** <span style='color:#FFF;'>{st.session_state.selected_insurance}</span>",
                unsafe_allow_html=True,
            )

            if st.session_state.selected_source == "STORE":
                price_value = f"${info.get('price', 0):,.0f} USD (Valeur)"
                price_style = "color:#00d4ff;"
            else:
                price_value = f"{info.get('auec_price', 0):,.0f} aUEC (Coût)"
                price_style = "color:#30E8FF;"

            st.markdown(
                f"<h4 style='{price_style}'>ENREGISTREMENT : {price_value}</h4>",
                unsafe_allow_html=True,
            )

            if st.session_state.current_pilot:
                if st.button(
                    f"✅ ENREGISTRER {selected_name} DANS MON HANGAR",
                    type="primary",
                    use_container_width=True,
                ):
                    add_ship_action()
            else:
                st.info("Connectez-vous pour enregistrer ce vaisseau dans votre hangar.")
        else:
            if st.session_state.current_pilot:
                st.info(
                    "Sélectionnez un vaisseau dans le registre pour afficher les options d'enregistrement."
                )
            else:
                st.info("Connectez-vous pour enregistrer un vaisseau.")

            st.markdown("---")
            st.caption("Instructions:")
            st.markdown("* Choisissez la source et l'assurance à gauche.")
            st.markdown("* Cliquez sur le bouton sous la carte pour le sélectionner.")
            if st.session_state.current_pilot:
                st.markdown("* Confirmez l'enregistrement ici.")


def my_hangar_page():
    """Affiche et permet la modification de la flotte personnelle, séparée par source."""
    st.subheader(f"HANGAR LOGISTIQUE | PILOTE: {st.session_state.current_pilot}")
    st.markdown("---")

    my_fleet = [
        s
        for s in st.session_state.db["fleet"]
        if s["Propriétaire"] == st.session_state.current_pilot
    ]

    if not my_fleet:
        st.info("Hangar vide. Ajoutez des vaisseaux depuis le CATALOGUE.")
        return

    df_my = pd.DataFrame(my_fleet)
    df_my["Supprimer"] = False

    if "Source" not in df_my.columns:
        st.error(
            "Données de flotte incomplètes (colonne 'Source' manquante). "
            "Ajoutez un nouveau vaisseau depuis le catalogue pour régénérer la structure."
        )
        return

    if "id" not in df_my.columns:
        df_my["id"] = range(1, len(df_my) + 1)
    df_my["id"] = df_my["id"].astype(int)

    # CORRECTION DES PRIX: Assurer la conversion des colonnes en numérique au début
    df_my["Prix_USD"] = pd.to_numeric(df_my["Prix_USD"], errors="coerce").fillna(0)
    df_my["Prix_aUEC"] = pd.to_numeric(df_my["Prix_aUEC"], errors="coerce").fillna(0)
    
    # AJOUT DE L'ANCIENNE COLONNE 'Prix' À LA SUPPRESSION
    columns_to_drop = ["id", "Image", "Propriétaire", "Prix"]
    
    st.caption(
        "❗ Utilisez **ACTUALISER** pour synchroniser les changements (Disponibilité / Suppression / Assurance) avec la base de données centrale."
    )

    # --- HANGAR STORE ---
    df_store = df_my[df_my["Source"] == "STORE"].reset_index(drop=True).copy()
    df_store_display = df_store.drop(columns=columns_to_drop, errors="ignore")
    
    # Configuration spécifique pour le Store: USD actif (vert)
    editable_columns_store = {
        "Dispo": st.column_config.CheckboxColumn("OPÉRATIONNEL ?", width="small"),
        "Supprimer": st.column_config.CheckboxColumn("SUPPRIMER", width="small"),
        "Visuel": st.column_config.ImageColumn("APERÇU", width="small"),
        "Assurance": st.column_config.SelectboxColumn(
            "ASSURANCE",
            options=["LTI", "10 Ans", "6 Mois", "2 Mois", "Standard"],
            width="medium",
        ),
        "Prix_USD": st.column_config.NumberColumn(
            "VALEUR USD", 
            format="$%,.0f", 
            # Conditionnel : Si la valeur est > 0 (valeur réelle), colore en vert
            help="Valeur en dollars réels.",
            background="rgba(0, 255, 0, 0.15)", # Vert très léger
            text_color="#00ff00" # Vert
        ),
        "Prix_aUEC": st.column_config.NumberColumn(
            "COÛT aUEC", 
            format="%,.0f",
        ),
    }

    st.markdown("## 💰 HANGAR STORE (Propriété USD)")
    # RETRAIT DU ST.MARKDOWN QUI CAUSAIT LE '$0' RÉSIDUEL
    
    if not df_store.empty:
        total_usd = df_store["Prix_USD"].sum()
        col_usd, col_toggle_usd = st.columns([3, 1])
        show_usd = col_toggle_usd.toggle(
            "Afficher Valorisation Totale (USD)", value=False, key="toggle_usd"
        )
        col_usd.metric(
            "VALORISATION STORE", f"${total_usd:,.0f}" if show_usd else "---"
        )

        edited_store_display = st.data_editor(
            df_store_display,
            column_config=editable_columns_store,
            disabled=[
                "Vaisseau",
                "Marque",
                "Rôle",
                "Visuel",
                "Source",
                # Seul le prix USD devrait être visible, mais on désactive la modification des deux
                "Prix_aUEC", 
                "Prix_USD",
            ],
            hide_index=True,
            use_container_width=True,
            key="store_hangar_editor",
        )
        edited_store = edited_store_display.copy()
        edited_store["id"] = df_store["id"]
    else:
        st.info("Aucun vaisseau provenant du Store dans votre hangar.")
        edited_store = pd.DataFrame()

    st.markdown("---")

    # --- HANGAR INGAME ---
    df_ingame = df_my[df_my["Source"] == "INGAME"].reset_index(drop=True).copy()
    df_ingame_display = df_ingame.drop(columns=columns_to_drop, errors="ignore")
    
    # Configuration spécifique pour Ingame: aUEC actif (turquoise)
    editable_columns_ingame = {
        "Dispo": st.column_config.CheckboxColumn("OPÉRATIONNEL ?", width="small"),
        "Supprimer": st.column_config.CheckboxColumn("SUPPRIMER", width="small"),
        "Visuel": st.column_config.ImageColumn("APERÇU", width="small"),
        "Assurance": st.column_config.SelectboxColumn(
            "ASSURANCE",
            options=["LTI", "10 Ans", "6 Mois", "2 Mois", "Standard"],
            width="medium",
        ),
        "Prix_USD": st.column_config.NumberColumn(
            "VALEUR USD", 
            format="$%,.0f", 
        ),
        "Prix_aUEC": st.column_config.NumberColumn(
            "COÛT aUEC", 
            format="%,.0f",
            # Conditionnel : Si la valeur est > 0 (coût réel), colore en turquoise
            help="Coût en aUEC pour l'achat en jeu.",
            background="rgba(48, 232, 255, 0.15)", # Turquoise très léger
            text_color="#30e8ff" # Turquoise
        ),
    }


    st.markdown("## 💸 HANGAR INGAME (Acquisition aUEC)")

    if not df_ingame.empty:
        total_aUEC = df_ingame["Prix_aUEC"].sum()
        col_aUEC, col_toggle_aUEC = st.columns([3, 1])
        show_aUEC = col_toggle_aUEC.toggle(
            "Afficher Coût Total (aUEC)", value=False, key="toggle_aUEC"
        )
        col_aUEC.metric(
            "COÛT ACQUISITION", f"{total_aUEC:,.0f} aUEC" if show_aUEC else "---"
        )

        edited_ingame_display = st.data_editor(
            df_ingame_display,
            column_config=editable_columns_ingame,
            disabled=[
                "Vaisseau",
                "Marque",
                "Rôle",
                "Visuel",
                "Source",
                "Prix_aUEC",
                "Prix_USD",
            ],
            hide_index=True,
            use_container_width=True,
            key="ingame_hangar_editor",
        )
        edited_ingame = edited_ingame_display.copy()
        edited_ingame["id"] = df_ingame["id"]
    else:
        st.info("Aucun vaisseau acheté en jeu dans votre hangar.")
        edited_ingame = pd.DataFrame()

    # --- SAUVEGARDE GLOBALE ---
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

    # CORRECTION DES PRIX: Assurer la conversion des colonnes en numérique au début
    df_global["Prix_USD"] = pd.to_numeric(df_global["Prix_USD"], errors="coerce").fillna(0)
    df_global["Prix_aUEC"] = pd.to_numeric(df_global["Prix_aUEC"], errors="coerce").fillna(0)
    
    # KPI principaux
    total_ships = len(df_global)
    total_dispo = int(df_global["Dispo"].sum())
    total_pilots = len(st.session_state.db["users"])

    total_value_usd = df_global[df_global["Source"] == "STORE"]["Prix_USD"].sum()
    total_value_aUEC = df_global[df_global["Source"] == "INGAME"]["Prix_aUEC"].sum()

    st.markdown("---")
    
    # AFFICHAGE DES KPI AVEC TOGGLE
    col_kpi, col_toggle = st.columns([4, 1])
    
    with col_toggle:
        show_value_kpi = st.toggle(
            "Afficher Valorisation Totale", 
            value=False, 
            key="toggle_corpo_kpi"
        )

    with col_kpi:
        c1, c2, c3, c4, c5 = st.columns(5)
        
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
    summary_df = (
        df_global.groupby(["Vaisseau", "Marque", "Rôle"])
        .agg(Quantité=("Vaisseau", "count"), Dispo=("Dispo", "sum"))
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
        },
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # === LISTE DÉTAILLÉE + VUE TACTIQUE ===
    st.markdown("### 📋 LISTE DÉTAILLÉE DES UNITÉS")

    show_only_dispo = st.checkbox(
        "✅ Afficher uniquement les vaisseaux opérationnels", value=False
    )

    display_df = df_global.copy()
    if show_only_dispo:
        display_df = display_df[display_df["Dispo"] == True].copy()

    display_df["Statut"] = display_df["Dispo"].apply(
        lambda x: "✅ DISPONIBLE" if x else "⛔ NON ASSIGNÉ"
    )
    # Prix d'acquisition propre (un seul prix affiché selon la source)
    display_df["Prix_Acquisition"] = display_df.apply(
        lambda row: (
            f"{row['Prix_aUEC']:,.0f} aUEC"
            if row["Source"] == "INGAME" and row["Prix_aUEC"] > 0
            else f"${row['Prix_USD']:,.0f} USD"
            if row["Source"] == "STORE" and row["Prix_USD"] > 0
            else "N/A"
        ),
        axis=1,
    )

    selection = st.dataframe(
        display_df,
        column_config={
            "Visuel": st.column_config.ImageColumn("Vaisseau", width="small"),
            "Propriétaire": st.column_config.TextColumn("Pilote", width="medium"),
            "Source": st.column_config.TextColumn("Source", width="small"),
            "Assurance": st.column_config.TextColumn("Assurance", width="small"),
            "Statut": st.column_config.TextColumn("Prêt ?", width="medium"),
            "Vaisseau": st.column_config.TextColumn("Modèle", width="medium"),
            "Rôle": st.column_config.TextColumn("Classification", width="medium"),
            "Prix_Acquisition": st.column_config.TextColumn("Prix", width="medium"),
            "Image": None,
            "Prix_USD": None,
            "Prix_aUEC": None,
            "id": None,
            "Marque": None,
            "Dispo": None,
        },
        use_container_width=True,
        hide_index=True,
        height=400,
        selection_mode="single-row",
        key="global_fleet_detail",
    )

    # VUE TACTIQUE (Logique corrigée et SÉCURISÉE)
    try:
        selection_data = selection.get("selection", {})
        selected_indices = selection_data.get("rows", [])
    except Exception:
        selected_indices = []

    if selected_indices:
        idx = selected_indices[0]
        selected_row = display_df.iloc[idx]

        st.markdown("---")
        st.markdown(f"### 🔎 VUE TACTIQUE : {selected_row['Vaisseau']}")

        col_img, col_details = st.columns([1, 1])

        with col_img:
            image_path = selected_row.get("Image")
            if image_path and os.path.exists(image_path):
                st.image(
                    image_path,
                    use_container_width=True,
                    caption=f"{selected_row['Marque']} {selected_row['Vaisseau']}",
                )
            else:
                st.warning("Visuel non disponible localement.")

        # Prix propres : on masque les 0 / valeurs vides
        prix_usd = selected_row.get("Prix_USD", 0.0)
        prix_aUEC = selected_row.get("Prix_aUEC", 0.0)

        prix_usd_format = (
            f"${prix_usd:,.0f}" if prix_usd > 0 and selected_row["Source"] == "STORE" else "N/A"
        )
        prix_aUEC_format = (
            f"{prix_aUEC:,.0f} aUEC"
            if prix_aUEC > 0 and selected_row["Source"] == "INGAME"
            else "N/A"
        )

        with col_details:
            st.markdown(
                f"""
<div style="background:rgba(0,0,0,0.5); padding:20px; border-radius:10px; border:1px solid #333;">
  <h4>PILOTE : <span style="color:#fff">{selected_row['Propriétaire']}</span></h4>
  <h4>RÔLE : <span style="color:#fff">{selected_row['Rôle']}</span></h4>
  <h4>CONSTRUCTEUR : <span style="color:#fff">{selected_row['Marque']}</span></h4>
  <br>
  <h4>SOURCE D'ACHAT : <span style="color:#fff">{selected_row['Source']}</span></h4>
  <h4 style="color:#00d4ff;">ASSURANCE : <span style="color:#fff">{selected_row['Assurance']}</span></h4>
  <br>
  <h4>PRIX STORE : <span style="color:#00d4ff">{prix_usd_format}</span></h4>
  <h4>PRIX INGAME : <span class="auec-price">{prix_aUEC_format}</span></h4>
  <br>
  <h2 style="color:{'#00ff00' if selected_row['Dispo'] else '#ff4b4b'} !important">
    {selected_row['Statut']}
  </h2>
</div>
""",
                unsafe_allow_html=True,
            )


# --- 8. APP PRINCIPALE ---

render_sidebar()

if not st.session_state.current_pilot:
    # Page d'accueil sans gros titre global
    home_page()
else:
    # Titre global uniquement après connexion
    st.markdown(
        "<h1>PIONEER COMMAND | CONSOLE D'OPÉRATIONS</h1>",
        unsafe_allow_html=True,
    )

    if st.session_state.menu_nav == "CATALOGUE":
        catalogue_page()
    elif st.session_state.menu_nav == "MON HANGAR":
        my_hangar_page()
    elif st.session_state.menu_nav == "FLOTTE CORPO":
        corpo_fleet_page()