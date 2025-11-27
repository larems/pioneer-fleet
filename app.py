import streamlit as st
import pandas as pd
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
    initial_sidebar_state="expanded"
)
BACKGROUND_IMAGE = "assets/fondecransite.png"

# Liste des vaisseaux considérés comme "Majeurs"
FLAGSHIPS_LIST = [
    "Javelin", "Idris-M", "Idris-P", "Kraken", "Kraken Privateer", 
    "890 Jump", "Polaris", "Nautilus", "Hammerhead", "Perseus", "Carrack", "Carrack Expedition",
    "Pioneer", "Orion", "Reclaimer", "Arrastra", "Hull E", "Hull D", "BMM", "Merchantman", "Endeavor", "Odyssey"
]

# --- 2. GESTION DATABASE (JSONBIN.IO) ---
JSONBIN_ID = st.secrets.get("JSONBIN_ID", "6921f0ded0ea881f40f9933f")
JSONBIN_KEY = st.secrets.get("JSONBIN_KEY", "")

def normalize_db_schema(db: dict) -> dict:
    """Normalise la structure de la DB."""
    db.setdefault("users", {})
    db.setdefault("fleet", [])
    db.setdefault("user_data", {}) 

    for i, ship in enumerate(db["fleet"]):
        ship.setdefault("id", int(time.time() * 1_000_000) + i)
        ship.setdefault("Propriétaire", "INCONNU")
        ship.setdefault("Vaisseau", "Inconnu")
        ship.setdefault("Marque", "N/A")
        ship.setdefault("Rôle", "Inconnu")
        
        # MODIF: FlightReady remplace Dispo
        ship.setdefault("FlightReady", False) 
        if "Dispo" in ship: # Migration auto
            ship["FlightReady"] = ship.pop("Dispo")
            
        ship.setdefault("Image", "")
        ship.setdefault("Visuel", "")
        ship.setdefault("Source", "STORE")
        ship.setdefault("Prix_USD", 0.0)
        ship.setdefault("Prix_aUEC", 0.0)
        ship.setdefault("Assurance", "Standard")
        ship.setdefault("Prix", None)
        ship.setdefault("crew_max", 1)
        
        # AJOUT: Gestion Crew
        ship.setdefault("NeedCrew", False)
        ship.setdefault("CrewList", [])
    
    for pilot in db.get("users", {}).keys():
        db["user_data"].setdefault(pilot, {"auec_balance": 0, "acquisition_target": None})
    
    return db

@st.cache_data(ttl=300, show_spinner="Chargement de la base de données...")
def load_db_from_cloud():
    if not JSONBIN_KEY:
        st.warning("⚠️ Clé JSONBin.io manquante. Mode hors ligne.")
        return {"users": {}, "fleet": []}
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest"
    headers = {"X-Master-Key": JSONBIN_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return normalize_db_schema(response.json().get("record", {}))
    except Exception as e:
        st.error(f"Erreur DB: {e}")
    return {"users": {}, "fleet": []}

def save_db_to_cloud(data):
    if not JSONBIN_KEY: return False
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
    headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_KEY}
    try:
        response = requests.put(url, json=data, headers=headers, timeout=10)
        if response.status_code in (200, 204): return True
        if response.status_code == 403: 
            st.warning("⚠️ Limite taille JSON atteinte.")
            return True
    except Exception as e:
        st.error(f"Erreur Sauvegarde: {e}")
    load_db_from_cloud.clear()
    return False

# Session State DB
if "db" not in st.session_state:
    st.session_state.db = normalize_db_schema(load_db_from_cloud())
else:
    st.session_state.db = normalize_db_schema(st.session_state.db)

# --- 3. FONCTIONS UTILITAIRES & ACTIONS ---

@st.cache_data(show_spinner=False)
def get_local_img_as_base64(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        except: pass
    return "" 

def get_current_ship_price(ship_name, price_type):
    """Récupère le prix actuel depuis le catalogue."""
    info = SHIPS_DB.get(ship_name, {})
    if price_type == 'USD':
        return float(info.get('price', 0) or 0)
    elif price_type == 'aUEC':
        val = info.get('auec_price', 0)
        return float(val) if isinstance(val, (int, float)) else 0.0
    return 0.0

def check_is_high_value(ship_name):
    """Détermine si un vaisseau doit être dans la section Amirale."""
    if ship_name in FLAGSHIPS_LIST: return True
    usd_price = get_current_ship_price(ship_name, 'USD')
    if usd_price >= 800: return True
    return False

def update_ship_attributes(pilot, ship_name, source, old_insurance, old_ready, old_need, new_insurance, new_ready, new_need):
    """Met à jour l'assurance, FlightReady et NeedCrew."""
    updated = False
    for s in st.session_state.db["fleet"]:
        if (s["Propriétaire"] == pilot and 
            s["Vaisseau"] == ship_name and 
            s["Source"] == source and 
            s["Assurance"] == old_insurance and
            s.get("FlightReady", False) == old_ready and
            s.get("NeedCrew", False) == old_need):
            
            s["Assurance"] = new_insurance
            s["FlightReady"] = bool(new_ready)
            s["NeedCrew"] = bool(new_need)
            updated = True
    
    if updated:
        save_db_to_cloud(st.session_state.db)
        st.toast("Vaisseau mis à jour !", icon="✅")
        time.sleep(0.5)
        st.rerun()

def toggle_crew_signup(ship_id, pilot_name, max_slots):
    """Gère l'inscription au Crew avec limite max."""
    for s in st.session_state.db["fleet"]:
        if s["id"] == ship_id:
            current_crew = s.get("CrewList", [])
            if pilot_name in current_crew:
                s["CrewList"].remove(pilot_name)
                st.toast("Vous avez quitté l'équipage.", icon="👋")
            else:
                if len(current_crew) < max_slots:
                    s["CrewList"].append(pilot_name)
                    st.toast("Bienvenue à bord !", icon="🚀")
                else:
                    st.error("Le vaisseau est complet !")
                    return
            save_db_to_cloud(st.session_state.db)
            time.sleep(0.5)
            st.rerun()
            return

def submit_cart_batch():
    if not st.session_state.current_pilot:
        st.error("Vous devez être connecté.")
        return

    if not st.session_state.cart:
        st.warning("Votre panier est vide.")
        return

    new_entries = []
    pilot = st.session_state.current_pilot
    
    for item in st.session_state.cart:
        ship_name = item['name']
        source = item['source']
        insurance = item['insurance']
        
        info = SHIPS_DB.get(ship_name)
        if not info: continue

        new_id = int(time.time() * 1_000_000) + len(new_entries)
        
        entry = {
            "id": new_id,
            "Propriétaire": pilot,
            "Vaisseau": ship_name,
            "Marque": info.get("brand", "N/A"),
            "Rôle": info.get("role", "Inconnu"),
            "FlightReady": False, # Nouveau
            "Image": info.get("img", ""),
            "Visuel": "",
            "Source": source,
            "Prix_USD": float(info.get("price", 0) or 0),
            "Prix_aUEC": float(info.get("auec_price", 0) if isinstance(info.get("auec_price"), (int, float)) else 0),
            "Assurance": insurance,
            "Prix": None,
            "crew_max": info.get("crew_max", 1),
            "NeedCrew": False,
            "CrewList": []
        }
        new_entries.append(entry)

    st.session_state.db["fleet"].extend(new_entries)
    
    if save_db_to_cloud(st.session_state.db):
        st.balloons()
        st.toast(f"✅ {len(new_entries)} vaisseaux ajoutés au hangar !", icon="🚀")
        st.session_state.cart = []
        time.sleep(1)
        st.rerun()

# --- 4. CSS ---
bg_img_code = get_local_img_as_base64(BACKGROUND_IMAGE)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500&display=swap');
.stApp {{ background-image: url("{bg_img_code}"); background-size: cover; background-attachment: fixed; }}
.stApp::before {{ content: ""; position: absolute; inset: 0; background: radial-gradient(circle at top left, rgba(0, 20, 40, 0.95), rgba(0, 0, 0, 0.98)); z-index: -1; }}
section[data-testid="stSidebar"] {{ background-color: rgba(5, 10, 18, 0.98); border-right: 1px solid #123; }}

/* POLICES (SAFE MODE) */
h1, h2, h3, h4, h5, h6, p, label, button, .stMarkdown, .stRadio {{ 
    font-family: 'Rajdhani', sans-serif !important; 
}}
h1, h2, h3 {{ 
    font-family: 'Orbitron', sans-serif !important; 
    color: #fff !important; 
    text-transform: uppercase; 
    border-bottom: 2px solid rgba(0, 212, 255, 0.2); 
}}

/* LOCK SIDEBAR */
section[data-testid="stSidebar"] button {{ display: none !important; }}
[data-testid="collapsedControl"] {{ display: none !important; }}
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: #020408; }}
::-webkit-scrollbar-thumb {{ background: #163347; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: #00d4ff; }}

/* NAV */
div[data-testid="stRadio"] > label {{ display: none; }}
div[data-testid="stRadio"] div[role="radiogroup"] > label {{
    background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; border: 1px solid transparent; margin-bottom: 5px; transition: all 0.3s;
}}
div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {{ border-color: #00d4ff; background: rgba(0, 212, 255, 0.1); }}
div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {{
    background: linear-gradient(90deg, rgba(0, 212, 255, 0.2), transparent); border-left: 4px solid #00d4ff; color: #00d4ff !important;
}}

/* CARDS */
.corpo-card {{
    background: linear-gradient(135deg, rgba(4,20,35,0.95), rgba(0,0,0,0.95));
    border: 1px solid #163347;
    border-radius: 12px;
    padding: 0;
    overflow: hidden;
    margin-bottom: 10px;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.corpo-card:hover {{ transform: translateY(-4px); border-color: #00d4ff; box-shadow: 0 0 15px rgba(0, 212, 255, 0.15); }}
.corpo-card-img {{ width: 100%; height: 200px; object-fit: cover; border-bottom: 1px solid #163347; }} 
.corpo-card-header {{ padding: 10px 14px; background: rgba(0,0,0,0.4); display:flex; justify-content:space-between; align-items:center; }}
.corpo-card-title {{ font-family: 'Orbitron'; font-size: 1.2em; color: white; font-weight: bold; text-shadow: 0 2px 4px black; }}
.corpo-card-count {{ background: #00d4ff; color: #000; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'Orbitron'; box-shadow: 0 0 10px rgba(0,212,255,0.4); }}
.corpo-card-body {{ padding: 12px 14px; font-size: 0.9em; color: #aaa; background: rgba(0,0,0,0.2); }}
.corpo-pilot-tag {{ display: inline-block; background: rgba(22, 51, 71, 0.8); color: #e0e0e0; padding: 4px 8px; border-radius: 4px; margin: 3px; font-size: 0.85em; border: 1px solid rgba(255,255,255,0.1); }}

.flagship-card {{ border: 2px solid #ffaa00; box-shadow: 0 0 25px rgba(255, 170, 0, 0.15); }}
.flagship-card .corpo-card-img {{ height: 350px; }}
.flagship-count {{ background: #ffaa00; }}

.crew-card {{ border: 1px solid #ff0055 !important; box-shadow: 0 0 15px rgba(255, 0, 85, 0.2); }}
.crew-tag {{ background: #ff0055; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 5px; }}

div[data-testid="stTextInput"] input {{ text-align: center; font-family: 'Orbitron'; border: 1px solid #333; background-color: #020408; }}
div[data-testid="stSelectbox"] > div > div {{ background-color: rgba(0,0,0,0.5); border: 1px solid #333; }}
</style>""", unsafe_allow_html=True)

# --- 5. SESSION STATE ---
if "current_pilot" not in st.session_state: st.session_state.current_pilot = None
if "catalog_page" not in st.session_state: st.session_state.catalog_page = 0
if "menu_nav" not in st.session_state: st.session_state.menu_nav = "CATALOGUE"
if "selected_source" not in st.session_state: st.session_state.selected_source = "STORE"
if "selected_insurance" not in st.session_state: st.session_state.selected_insurance = "LTI"
if "cart" not in st.session_state: st.session_state.cart = [] 

# --- 6. SIDEBAR ---
def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='border:none;'>💠 PIONEER</h2>", unsafe_allow_html=True)
        if st.session_state.current_pilot:
            st.markdown(f"<div style='color:#00d4ff; font-weight:bold; margin-bottom:10px;'>PILOTE: {st.session_state.current_pilot}</div>", unsafe_allow_html=True)
            if st.button("DÉCONNEXION", use_container_width=True):
                st.session_state.current_pilot = None; st.session_state.cart = []; st.rerun()
            st.markdown("---")
            
            # AJOUT DE "NEED CREW" EN DERNIER
            nav_opts = ["CATALOGUE", "MON HANGAR", "FLOTTE CORPO", "NEED CREW"]
            
            curr_idx = 0
            if st.session_state.menu_nav in nav_opts:
                curr_idx = nav_opts.index(st.session_state.menu_nav)
            else:
                st.session_state.menu_nav = "CATALOGUE"
            
            nav = st.radio("NAVIGATION", nav_opts, index=curr_idx, label_visibility="collapsed")
            
            if nav != st.session_state.menu_nav:
                st.session_state.menu_nav = nav; st.session_state.catalog_page = 0; st.rerun()
        else:
            st.caption("Connexion requise.")

# --- 7. PAGES ---

def home_page():
    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        st.markdown("""<div style="background: rgba(4, 20, 35, 0.9); border: 1px solid #163347; padding: 30px; border-radius: 14px;">
        <h2 style="border:none;">PIONEER COMMAND</h2><p>Console logistique • Accès restreint</p></div>""", unsafe_allow_html=True)
        with st.form("login"):
            st.subheader("CONNEXION")
            pseudo = st.text_input("Identifiant")
            pin = st.text_input("PIN (4 chiffres)", type="password", max_chars=4)
            if st.form_submit_button("SE CONNECTER", type="primary"):
                if not pseudo or not pin.isdigit(): st.error("Format invalide.")
                else:
                    users = st.session_state.db["users"]
                    if pseudo in users and users[pseudo] != pin: st.error("PIN incorrect.")
                    else:
                        if pseudo not in users:
                            users[pseudo] = pin
                            save_db_to_cloud(st.session_state.db)
                        st.session_state.current_pilot = pseudo
                        st.rerun()

def catalogue_page():
    col_filters, col_main, col_cart = st.columns([1, 3.5, 1.5])
    
    # --- 1. FILTRES (GAUCHE) ---
    with col_filters:
        st.subheader("PARAMÈTRES")
        p_source = st.radio("SOURCE", ["STORE", "INGAME"], index=0 if st.session_state.selected_source == "STORE" else 1)
        st.session_state.selected_source = p_source
        
        ins_opts = ["LTI", "10 Ans", "2 ans", "6 Mois", "2 Mois", "Standard"]
        p_ins = st.selectbox("ASSURANCE", ins_opts, index=0)
        st.session_state.selected_insurance = p_ins
        
        st.markdown("---")
        
        # CONSTRUCTEUR
        brands = ["Tous"] + sorted(list(set(d.get("brand") for d in SHIPS_DB.values() if d.get("brand"))))
        f_brand = st.selectbox("CONSTRUCTEUR", brands)

        # RÔLE
        all_roles = sorted(list(set(d.get("role", "Inconnu") for d in SHIPS_DB.values() if d.get("role"))))
        f_role = st.selectbox("RÔLE", ["Tous"] + all_roles)
        
    # --- 2. ZONE CENTRALE ---
    with col_main:
        st.subheader(f"REGISTRE ({len(st.session_state.cart)} SÉLECTIONNÉS)")
        
        # BARRE DE RECHERCHE CENTRALE
        search_list = sorted(list(SHIPS_DB.keys()))
        search = st.multiselect("RECHERCHE", search_list, placeholder="🔍 Rechercher un vaisseau...", label_visibility="collapsed")

        # LOGIQUE DE FILTRAGE
        filtered = {}
        for name, data in SHIPS_DB.items():
            # Filtres
            if f_brand != "Tous" and data.get("brand") != f_brand: continue
            if f_role != "Tous" and data.get("role") != f_role: continue
            if search and name not in search: continue
            filtered[name] = data

        items = list(filtered.items())
        PER_PAGE = 8
        total_pages = max(1, (len(items) + PER_PAGE - 1) // PER_PAGE)
        if st.session_state.catalog_page >= total_pages: st.session_state.catalog_page = 0

        # PAGINATION
        c1, c2, c3 = st.columns([1, 4, 1])
        with c1: 
            if st.button("◄", disabled=(st.session_state.catalog_page==0)): st.session_state.catalog_page -= 1; st.rerun()
        with c2: st.markdown(f"<div style='text-align:center'>PAGE {st.session_state.catalog_page+1}/{total_pages}</div>", unsafe_allow_html=True)
        with c3: 
            if st.button("►", disabled=(st.session_state.catalog_page==total_pages-1)): st.session_state.catalog_page += 1; st.rerun()

        start = st.session_state.catalog_page * PER_PAGE
        current_batch = items[start : start + PER_PAGE]
        
        if not current_batch: st.info("Aucun vaisseau.")
        
        # GRILLE D'AFFICHAGE
        cols = st.columns(2)
        for i, (name, data) in enumerate(current_batch):
            with cols[i % 2]:
                img_b64 = get_local_img_as_base64(data.get("img", ""))
                
                count_in_cart = sum(1 for item in st.session_state.cart if item['name'] == name)
                border = "2px solid #00d4ff" if count_in_cart > 0 else "1px solid #163347"
                shadow = "0 0 15px rgba(0, 212, 255, 0.4)" if count_in_cart > 0 else "none"
                opacity = "1.0"

                if p_source == "STORE":
                    pv = data.get('price', 0)
                    price_str = f"${pv:,.0f} USD" if isinstance(pv, (int, float)) else str(pv)
                    price_col = "#00d4ff"
                else:
                    pv = data.get('auec_price', 0)
                    price_str = f"{pv:,.0f} aUEC" if isinstance(pv, (int, float)) and pv > 0 else "N/A"
                    price_col = "#30e8ff"

                # HTML Card Compact
                badge_html = f"<div style='background:#00d4ff; color:black; font-weight:bold; padding:0 6px; border-radius:4px;'>x{count_in_cart}</div>" if count_in_cart > 0 else ""
                card_html = f"<div style='background:#041623; border-radius:8px; border:{border}; box-shadow:{shadow}; overflow:hidden; margin-bottom:8px; transition:0.2s;'><div style='height:150px; background:#000;'><img src='{img_b64}' style='width:100%; height:100%; object-fit:cover; opacity:{opacity}'></div><div style='padding:10px;'><div style='display:flex; justify-content:space-between; align-items:center;'><div style='font-weight:bold; color:#fff; font-size:1.1em;'>{name}</div>{badge_html}</div><div style='display:flex; justify-content:space-between; font-size:0.9em; color:#ccc; margin-top:4px;'><span>{data.get('role','N/A')}</span><span style='color:{price_col}; font-weight:bold;'>{price_str}</span></div></div></div>"
                
                st.markdown(card_html, unsafe_allow_html=True)

                cb1, cb2 = st.columns(2)
                with cb1:
                    if st.button(f"➖", key=f"min_{name}", use_container_width=True):
                        for idx, item in enumerate(st.session_state.cart):
                            if item['name'] == name:
                                st.session_state.cart.pop(idx)
                                st.rerun()
                                break
                with cb2:
                    if st.button(f"➕", key=f"pls_{name}", use_container_width=True, type="primary"):
                        st.session_state.cart.append({
                            'name': name,
                            'source': p_source,
                            'insurance': p_ins,
                            'price_disp': price_str
                        })
                        st.rerun()

    with col_cart:
        st.subheader("VALIDATION")
        if st.session_state.current_pilot:
            p_data = st.session_state.db.get("user_data", {}).get(st.session_state.current_pilot, {})
            st.markdown(f"💳 Solde : <span style='color:#30e8ff'>{p_data.get('auec_balance', 0):,.0f} aUEC</span>", unsafe_allow_html=True)
        st.markdown("---")

        if not st.session_state.cart:
            st.info("Panier vide.")
        else:
            st.markdown(f"### 🛒 PANIER ({len(st.session_state.cart)})")
            cart_counts = {}
            for item in st.session_state.cart:
                key = (item['name'], item['source'], item['insurance'], item['price_disp'])
                cart_counts[key] = cart_counts.get(key, 0) + 1
            
            for (c_name, c_src, c_ins, c_prc), count in cart_counts.items():
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.05); padding:6px; border-radius:4px; margin-bottom:4px; border-left:3px solid #00d4ff; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <b>{c_name}</b> <span style="background:#333; padding:1px 5px; border-radius:3px;">x{count}</span><br>
                        <span style="font-size:0.8em; color:#aaa;">{c_src} | {c_ins} | {c_prc}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
            
            st.markdown("---")
            if st.button(f"💾 ENREGISTRER TOUT ({len(st.session_state.cart)})", type="primary", use_container_width=True):
                submit_cart_batch()
            if st.button("🗑️ Vider", use_container_width=True):
                st.session_state.cart = []; st.rerun()

def my_hangar_page():
    st.subheader(f"HANGAR LOGISTIQUE | {st.session_state.current_pilot}")
    
    # CHARGEMENT DONNEES
    pilot_data = st.session_state.db.get("user_data", {}).get(st.session_state.current_pilot, {})
    current_auec = pilot_data.get("auec_balance", 0)
    target = pilot_data.get("acquisition_target", None)
    my_fleet = [s for s in st.session_state.db["fleet"] if s["Propriétaire"] == st.session_state.current_pilot]

    # --- ONGLET 1 : MA FLOTTE VISUELLE ---
    tab_fleet, tab_acq = st.tabs(["🚀 MA FLOTTE", "🎯 OBJECTIF D'ACHAT"])

    with tab_fleet:
        # BARRE DE RECHERCHE HANGAR
        search_hangar = st.text_input("🔍 Rechercher un vaisseau dans mon hangar...", "")

        if my_fleet:
            df = pd.DataFrame(my_fleet)
            
            # CALCUL TOTAL (USD & aUEC) SUR LA FLOTTE FILTRÉE
            total_usd_personal = 0
            total_auec_personal = 0
            for _, row in df.iterrows():
                if row['Source'] == 'STORE':
                    total_usd_personal += get_current_ship_price(row['Vaisseau'], 'USD')
                elif row['Source'] == 'INGAME':
                    total_auec_personal += get_current_ship_price(row['Vaisseau'], 'aUEC')

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("VALEUR PLEDGE (USD)", f"${total_usd_personal:,.0f}")
            col_m2.metric("VALEUR IN-GAME (aUEC)", f"{total_auec_personal:,.0f}")
            col_m3.metric("VAISSEAUX", len(df))
            st.markdown("---")

            # FILTRE DE RECHERCHE
            if search_hangar:
                m = search_hangar.lower()
                df = df[df["Vaisseau"].str.lower().str.contains(m) | 
                        df["Rôle"].str.lower().str.contains(m) | 
                        df["Source"].str.lower().str.contains(m)]

            if df.empty:
                st.info("Aucun vaisseau trouvé avec cette recherche.")
            else:
                # --- SEPARATION (FLAGSHIPS / STANDARD) + TRI PAR PRIX ---
                df['is_flagship'] = df['Vaisseau'].apply(check_is_high_value)
                
                df_flags = df[df['is_flagship'] == True].copy()
                df_std = df[df['is_flagship'] == False].copy()

                df_flags['Sort_Price'] = df_flags['Vaisseau'].apply(lambda x: get_current_ship_price(x, 'USD'))
                df_flags = df_flags.sort_values(by='Sort_Price', ascending=False)
                
                df_std['Sort_Price'] = df_std['Vaisseau'].apply(lambda x: get_current_ship_price(x, 'USD'))
                df_std = df_std.sort_values(by='Sort_Price', ascending=False)

                # FONCTION D'AFFICHAGE AVEC MODIFICATION
                def render_fleet_grid_editable(dataframe, is_flagship=False):
                    if dataframe.empty: return
                    
                    # AJOUT : FlightReady et NeedCrew dans le groupement
                    grp = dataframe.groupby(['Vaisseau', 'Source', 'Assurance', 'FlightReady', 'NeedCrew']).agg({
                        'id': 'count',
                        'Image': 'first',
                        'crew_max': 'max'
                    }).reset_index().rename(columns={'id': 'Quantité'})
                    
                    grp['Sort_Price'] = grp['Vaisseau'].apply(lambda x: get_current_ship_price(x, 'USD'))
                    grp = grp.sort_values(by='Sort_Price', ascending=False)

                    cols = st.columns(3)
                    for i, row in grp.iterrows():
                        with cols[i % 3]:
                            name = row['Vaisseau']
                            source = row['Source']
                            insurance = row['Assurance']
                            is_ready = row['FlightReady']
                            need_crew = row['NeedCrew']
                            count = row['Quantité']
                            max_slots = int(row['crew_max']) if row['crew_max'] else 1
                            
                            img_path = SHIPS_DB.get(name, {}).get('img', '')
                            img_b64 = get_local_img_as_base64(img_path)

                            info = SHIPS_DB.get(name, {})
                            if source == 'STORE':
                                p_display = f"${info.get('price', 0):,.0f} USD"
                                p_col = "#00d4ff"
                            else:
                                p_display = f"{info.get('auec_price', 0):,.0f} aUEC"
                                p_col = "#30e8ff"
                            
                            card_class = "corpo-card flagship-card" if is_flagship else "corpo-card"
                            if need_crew: card_class += " crew-card"
                            
                            count_class = "corpo-card-count flagship-count" if is_flagship else "corpo-card-count"
                            img_style = "height:350px;" if is_flagship else "height:200px;"
                            
                            crew_badge = f"<span class='crew-tag'>CREW MAX: {max_slots}</span>" if need_crew else ""

                            # 1. CARTE VISUELLE
                            st.markdown(f"""
                            <div class="{card_class}">
                                <img src="{img_b64}" class="corpo-card-img" style="{img_style}">
                                <div class="corpo-card-header">
                                    <span class="corpo-card-title">{name}</span>
                                    <span class="{count_class}">x{count}</span>
                                </div>
                                <div class="corpo-card-body">
                                    <div style="display:flex; justify-content:space-between;">
                                        <span>{source}</span>
                                        <span style="color:{p_col}; font-weight:bold;">{p_display}</span>
                                    </div>
                                    <div style="margin-top:5px;">{crew_badge}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 2. CONTROLES DE GESTION SOUS LA CARTE
                            c_edit, c_del = st.columns([3, 1])
                            
                            with c_edit:
                                ins_opts = ["LTI", "10 Ans", "2 ans", "6 Mois", "2 Mois", "Standard"]
                                new_ins = st.selectbox("Assurance", ins_opts, index=ins_opts.index(insurance) if insurance in ins_opts else 5, key=f"ins_{i}_{name}_{source}_{is_ready}", label_visibility="collapsed")
                                
                                c_t1, c_t2 = st.columns(2)
                                with c_t1:
                                    new_ready = st.toggle("🚀 Flight Ready", value=is_ready, key=f"ready_{i}_{name}_{source}")
                                with c_t2:
                                    new_need = st.toggle("📢 Search Crew", value=need_crew, key=f"need_{i}_{name}_{source}")

                                if new_ins != insurance or new_ready != is_ready or new_need != need_crew:
                                    update_ship_attributes(st.session_state.current_pilot, name, source, insurance, is_ready, need_crew, new_ins, new_ready, new_need)

                            with c_del:
                                if st.button("🗑️", key=f"del_{i}_{name}_{source}_{is_ready}", help="Retirer un exemplaire"):
                                    to_remove_id = None
                                    for s in st.session_state.db["fleet"]:
                                        if (s["Propriétaire"] == st.session_state.current_pilot and 
                                            s["Vaisseau"] == name and 
                                            s["Source"] == source and 
                                            s["Assurance"] == insurance and
                                            s.get("FlightReady", False) == is_ready):
                                            to_remove_id = s["id"]
                                            break
                                    if to_remove_id:
                                        st.session_state.db["fleet"] = [s for s in st.session_state.db["fleet"] if s["id"] != to_remove_id]
                                        save_db_to_cloud(st.session_state.db)
                                        st.rerun()

                # AFFICHAGE
                if not df_flags.empty:
                    st.markdown("""
                    <div style="text-align:center; margin: 30px 0 10px 0;">
                        <div style="font-size: 30px; color: #ffaa00; margin-bottom: -10px;">▼</div>
                        <h2 style="color: #ffaa00; border-bottom: 2px solid #ffaa00; display: inline-block; padding: 0 20px 10px 20px;">
                            FLOTTE AMIRALE
                        </h2>
                    </div>
                    """, unsafe_allow_html=True)
                    render_fleet_grid_editable(df_flags, is_flagship=True)

                st.markdown("### 🚀 FLOTTE STANDARD")
                render_fleet_grid_editable(df_std, is_flagship=False)

        else:
            st.info("Hangar vide. Allez au catalogue pour ajouter des vaisseaux.")

    # --- ONGLET 2 : ACQUISITION ---
    with tab_acq:
        st.markdown("### 🎯 CALCULATEUR D'OBJECTIF")
        
        opts = ["—"] + sorted([n for n, d in SHIPS_DB.items() if d.get('ingame')])
        idx = opts.index(target) if target in opts else 0
        
        new_tgt = st.selectbox("Sélectionner le vaisseau cible", opts, index=idx, key="h_target_sel")
        current_selection = new_tgt
        
        if "calc_balance" not in st.session_state:
            st.session_state.calc_balance = int(current_auec)

        def update_balance_slider():
            st.session_state.calc_balance = st.session_state.h_slider
        def update_balance_num():
            st.session_state.calc_balance = st.session_state.h_num

        c1, c2 = st.columns([1, 2])
        
        target_cost = 0
        if current_selection != "—" and current_selection in SHIPS_DB:
            t_price = SHIPS_DB[current_selection].get('auec_price', 0)
            if isinstance(t_price, (int, float)) and t_price > 0:
                target_cost = t_price
        
        slider_max = max(100_000, int(target_cost * 1.2)) if target_cost > 0 else 10_000_000

        with c1:
            st.markdown(f"**💰 Mon Solde Actuel**")
            st.number_input("Montant", value=st.session_state.calc_balance, step=10000, key="h_num", on_change=update_balance_num, label_visibility="collapsed")
            st.slider("Jauge", 0, slider_max, key="h_slider", on_change=update_balance_slider, label_visibility="collapsed")
            
            if st.button("💾 ENREGISTRER OBJECTIF", type="primary", use_container_width=True):
                st.session_state.db["user_data"][st.session_state.current_pilot] = {
                    "auec_balance": st.session_state.calc_balance,
                    "acquisition_target": new_tgt if new_tgt != "—" else None
                }
                save_db_to_cloud(st.session_state.db)
                st.success("Sauvegardé !")
                time.sleep(1)
                st.rerun()

        with c2:
            st.markdown(f"**📊 Progression vers : {current_selection}**")
            if target_cost > 0:
                bal = st.session_state.calc_balance
                pct = min(1.0, bal/target_cost)
                
                st.markdown(f"""
                <div style="background:#163347; border-radius:10px; padding:20px; text-align:center; border:1px solid #00d4ff;">
                    <h2 style="margin:0; color:#fff;">{int(pct*100)}%</h2>
                    <p style="color:#aaa;">{bal:,.0f} / <span style="color:#00d4ff; font-weight:bold;">{target_cost:,.0f} aUEC</span></p>
                </div>
                """, unsafe_allow_html=True)
                st.progress(pct)
                
                if bal >= target_cost:
                    st.markdown("""<div style="background:rgba(0,255,0,0.2); border:1px solid #0f0; color:#fff; padding:10px; border-radius:5px; text-align:center; margin-top:10px;">
                    🚀 FONDS SUFFISANTS POUR L'ACHAT !
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"*Il manque {target_cost - bal:,.0f} aUEC*")
            else:
                st.info("Sélectionnez un vaisseau achetable en jeu pour voir la progression.")

# --- NOUVELLE PAGE : NEED CREW ---
def need_crew_page():
    st.subheader("📢 OFFRES D'ÉQUIPAGE (NEED CREW)")
    st.markdown("Rejoignez les équipages formés par les membres de la corporation.")
    
    crew_ships = [s for s in st.session_state.db["fleet"] if s.get("NeedCrew") == True]
    
    if not crew_ships:
        st.info("Aucune offre d'équipage pour le moment.")
        return

    cols = st.columns(3)
    for i, ship in enumerate(crew_ships):
        with cols[i % 3]:
            img = get_local_img_as_base64(ship.get("Image", ""))
            owner = ship["Propriétaire"]
            crew_list = ship.get("CrewList", [])
            current_user = st.session_state.current_pilot
            max_slots = ship.get("crew_max", 1)
            
            header_info = f"CAPITAINE: {owner}"
            members_html = "".join([f"<span class='corpo-pilot-tag'>👨‍🚀 {m}</span>" for m in crew_list]) if crew_list else "<span style='color:#666; font-style:italic;'>Aucun membre inscrit</span>"
            
            st.markdown(f"""
            <div class="corpo-card crew-card">
                <img src="{img}" class="corpo-card-img">
                <div class="corpo-card-header" style="background:rgba(255,0,85,0.15);">
                    <span class="corpo-card-title">{ship['Vaisseau']}</span>
                    <span class="crew-tag">{header_info}</span>
                </div>
                <div class="corpo-card-body">
                    <div style="display:flex; justify-content:space-between; color:#00d4ff; font-weight:bold; margin-bottom:5px;">
                        <span>ÉQUIPAGE</span>
                        <span>{len(crew_list)} / {max_slots}</span>
                    </div>
                    <div style="margin-bottom:10px;">{members_html}</div>
                </div>
            </div>""", unsafe_allow_html=True)
            
            if owner == current_user:
                st.button("👑 C'est votre vaisseau", key=f"own_{i}", disabled=True, use_container_width=True)
            else:
                if current_user in crew_list:
                    if st.button(f"❌ QUITTER LE POSTE", key=f"leave_{ship['id']}", use_container_width=True):
                        toggle_crew_signup(ship['id'], current_user, max_slots)
                else:
                    if len(crew_list) < max_slots:
                        if st.button(f"✋ M'ENRÔLER", key=f"join_{ship['id']}", type="primary", use_container_width=True):
                            toggle_crew_signup(ship['id'], current_user, max_slots)
                    else:
                        st.button("COMPLET", key=f"full_{ship['id']}", disabled=True, use_container_width=True)

def corpo_fleet_page():
    st.subheader("FLOTTE CORPORATIVE")
    df = pd.DataFrame(st.session_state.db["fleet"])
    if df.empty: st.info("Aucune donnée."); return

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    total_usd_global = 0
    total_auec_global = 0
    for _, row in df.iterrows():
        if row['Source'] == 'STORE':
            total_usd_global += get_current_ship_price(row['Vaisseau'], 'USD')
        elif row['Source'] == 'INGAME':
            total_auec_global += get_current_ship_price(row['Vaisseau'], 'aUEC')

    c1.metric("VAISSEAUX", len(df))
    c2.metric("VALEUR FLOTTE (USD)", f"${total_usd_global:,.0f}")
    c3.metric("VALEUR FLOTTE (aUEC)", f"{total_auec_global:,.0f}")
    c4.metric("FLIGHT READY", df['FlightReady'].sum() if 'FlightReady' in df.columns else 0)

    st.markdown("---")
    
    # --- 3 ONGLETS : VUE / REGISTRE / MEMBRES ---
    tab_visu, tab_table, tab_members = st.tabs(["🚀 VUE FLOTTE", "📋 REGISTRE COMPLET", "👥 MEMBRES"])
    
    with tab_visu:
        # --- SECTION FLAGSHIPS & HIGH VALUE ---
        st.markdown("""
        <div style="text-align:center; margin: 30px 0 10px 0;">
            <div style="font-size: 30px; color: #ffaa00; margin-bottom: -10px;">▼</div>
            <h2 style="color: #ffaa00; border-bottom: 2px solid #ffaa00; display: inline-block; padding: 0 20px 10px 20px;">
                FLOTTE AMIRALE
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        df['is_flagship'] = df['Vaisseau'].apply(check_is_high_value)
        
        df_flagships = df[df['is_flagship'] == True]
        df_standard = df[df['is_flagship'] == False]
        
        if not df_flagships.empty:
            grp_flags = df_flagships.groupby(['Vaisseau', 'Source']).agg({
                'Propriétaire': lambda x: sorted(x.unique()),
                'id': 'count',
                'Image': 'first'
            }).reset_index()

            cols = st.columns(3)
            for i, row in grp_flags.iterrows():
                with cols[i % 3]:
                    img_b64 = get_local_img_as_base64(row['Image'])
                    pilots_html = "".join([f"<span class='corpo-pilot-tag'>{p}</span>" for p in row['Propriétaire']])
                    
                    st.markdown(f"""
                    <div class="corpo-card flagship-card">
                        <img src="{img_b64}" class="corpo-card-img">
                        <div class="corpo-card-header">
                            <span class="corpo-card-title">{row['Vaisseau']}</span>
                            <span class="corpo-card-count flagship-count">x{row['id']}</span>
                        </div>
                        <div class="corpo-card-body">
                            <div>{pilots_html}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Aucun vaisseau majeur détecté.")

        st.markdown("---")
        st.markdown("### 🚀 FLOTTE STANDARD")

        if not df_standard.empty:
            all_roles = sorted(df_standard["Rôle"].unique())
            
            selected_role_view = st.selectbox("📂 Filtrer par Rôle", ["Tout afficher"] + all_roles)
            
            if selected_role_view == "Tout afficher":
                df_to_show = df_standard
            else:
                df_to_show = df_standard[df_standard["Rôle"] == selected_role_view]
                
            grp_role = df_to_show.groupby(['Vaisseau']).agg({
                'Propriétaire': lambda x: sorted(x.unique()),
                'id': 'count',
                'Image': 'first'
            }).reset_index()

            cols_role = st.columns(3) 
            for j, row in grp_role.iterrows():
                with cols_role[j % 3]:
                    img_b64 = get_local_img_as_base64(row['Image'])
                    pilots_html = "".join([f"<span class='corpo-pilot-tag'>{p}</span>" for p in row['Propriétaire']])
                    
                    st.markdown(f"""
                    <div class="corpo-card">
                        <img src="{img_b64}" class="corpo-card-img">
                        <div class="corpo-card-header">
                            <span class="corpo-card-title">{row['Vaisseau']}</span>
                            <span class="corpo-card-count">x{row['id']}</span>
                        </div>
                        <div class="corpo-card-body">
                            <div>{pilots_html}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    with tab_table:
        st.subheader("📋 DÉTAIL GLOBAL")
        
        # BARRE DE RECHERCHE ET TABLEAU
        c_search, c_void = st.columns([2, 1])
        with c_search:
            search = st.text_input("🔍 Filtrer la liste globale (Vaisseau, Pilote, Rôle)", "")

        df_filtered = df.copy()
        if search:
            m = search.lower()
            df_filtered = df_filtered[df_filtered["Vaisseau"].str.lower().str.contains(m) | 
                    df_filtered["Propriétaire"].str.lower().str.contains(m) | 
                    df_filtered["Rôle"].str.lower().str.contains(m)]

        # Groupement pour l'affichage
        grp = df_filtered.groupby(['Vaisseau', 'Source', 'Rôle']).agg({
            'Propriétaire': lambda x: ', '.join(sorted(x.unique())),
            'id': 'count',
            'Image': 'first'
        }).reset_index().rename(columns={'id': 'Quantité'})
        
        grp['Visuel'] = grp['Image'].apply(get_local_img_as_base64)

        def get_price_display(row):
            name = row['Vaisseau']
            source = row['Source']
            info = SHIPS_DB.get(name)
            if not info: return "N/A"
            if source == "STORE":
                p = info.get("price", 0)
                return f"${p:,.0f}" if p else "N/A"
            else:
                p = info.get("auec_price", 0)
                return f"{p:,.0f} aUEC" if isinstance(p, (int, float)) else "N/A"

        grp['Valeur Unitaire'] = grp.apply(get_price_display, axis=1)
        final_view = grp[["Visuel", "Vaisseau", "Rôle", "Source", "Propriétaire", "Quantité", "Valeur Unitaire"]]

        st.dataframe(
            final_view,
            column_config={
                "Visuel": st.column_config.ImageColumn("Aperçu", width=150), # FIXE
                "Propriétaire": st.column_config.TextColumn("Pilotes"),
                "Quantité": st.column_config.ProgressColumn("Stock", max_value=int(grp["Quantité"].max())),
                "Valeur Unitaire": st.column_config.TextColumn("Valeur (Unité)")
            },
            use_container_width=True,
            hide_index=True,
            height=800
        )

    with tab_members:
        st.subheader("👥 LISTE DES MEMBRES")
        
        all_users = set(st.session_state.db["users"].keys())
        all_owners = set(df["Propriétaire"].unique())
        all_pilots = sorted(list(all_users | all_owners))
        
        if "INCONNU" in all_pilots: all_pilots.remove("INCONNU")
        
        data_members = []
        for p in all_pilots:
            p_ships = df[df["Propriétaire"] == p]
            target_p = st.session_state.db["user_data"].get(p, {}).get("acquisition_target", "Aucun")
            
            # CONFIDENTIALITÉ : PAS DE PRIX
            data_members.append({
                "Pilote": p,
                "Vaisseaux": len(p_ships),
                "Objectif Actuel": target_p
            })
        
        st.dataframe(pd.DataFrame(data_members), use_container_width=True, hide_index=True)

# --- MAIN LOOP ---
render_sidebar()
if not st.session_state.current_pilot:
    home_page()
else:
    if st.session_state.menu_nav == "CATALOGUE": catalogue_page()
    elif st.session_state.menu_nav == "MON HANGAR": my_hangar_page()
    elif st.session_state.menu_nav == "FLOTTE CORPO": corpo_fleet_page()
    elif st.session_state.menu_nav == "NEED CREW": need_crew_page()