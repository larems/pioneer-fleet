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
    db.setdefault("admin_code", "9999") 
    db.setdefault("corpo_code", "APQ8M3")
    
    db.setdefault("users", {})
    db.setdefault("fleet", [])
    db.setdefault("user_data", {}) 

    for i, ship in enumerate(db["fleet"]):
        ship.setdefault("id", int(time.time() * 1_000_000) + i)
        ship.setdefault("Propriétaire", "INCONNU")
        ship.setdefault("Vaisseau", "Inconnu")
        ship.setdefault("Marque", "N/A")
        ship.setdefault("Rôle", "Inconnu")
        
        # FlightReady remplace Dispo
        ship.setdefault("FlightReady", False) 
        if "Dispo" in ship:
            ship["FlightReady"] = ship.pop("Dispo")
            
        ship.setdefault("Image", "")
        ship.setdefault("Visuel", "")
        ship.setdefault("Source", "STORE")
        ship.setdefault("Prix_USD", 0.0)
        ship.setdefault("Prix_aUEC", 0.0)
        ship.setdefault("Assurance", "Standard")
        ship.setdefault("Prix", None)
        ship.setdefault("crew_max", 1)
        
        # NeedCrew
        ship.setdefault("NeedCrew", False)
        ship.setdefault("CrewList", [])
    
    for pilot in db.get("users", {}).keys():
        db["user_data"].setdefault(pilot, {"auec_balance": 0, "acquisition_target": None})
    
    return db

@st.cache_data(ttl=300, show_spinner="Chargement de la base de données...")
def load_db_from_cloud():
    if not JSONBIN_KEY:
        st.warning("⚠️ Clé JSONBin.io manquante. Mode hors ligne.")
        return {"users": {}, "fleet": [], "admin_code": "9999", "corpo_code": "APQ8M3"}
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest"
    headers = {"X-Master-Key": JSONBIN_KEY}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return normalize_db_schema(response.json().get("record", {}))
    except Exception as e:
        st.error(f"Erreur DB: {e}")
    return {"users": {}, "fleet": [], "admin_code": "9999", "corpo_code": "APQ8M3"}

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
    info = SHIPS_DB.get(ship_name, {})
    if price_type == 'USD':
        return float(info.get('price', 0) or 0)
    elif price_type == 'aUEC':
        val = info.get('auec_price', 0)
        return float(val) if isinstance(val, (int, float)) else 0.0
    return 0.0

def check_is_high_value(ship_name):
    if ship_name in FLAGSHIPS_LIST: return True
    usd_price = get_current_ship_price(ship_name, 'USD')
    if usd_price >= 800: return True
    return False

def update_ship_attributes(pilot, ship_name, source, old_ins, old_ready, old_need, new_ins, new_ready, new_need):
    updated = False
    for s in st.session_state.db["fleet"]:
        if (s["Propriétaire"] == pilot and 
            s["Vaisseau"] == ship_name and 
            s["Source"] == source and 
            s["Assurance"] == old_ins and
            s.get("FlightReady", False) == old_ready and
            s.get("NeedCrew", False) == old_need):
            
            s["Assurance"] = new_ins
            s["FlightReady"] = bool(new_ready)
            s["NeedCrew"] = bool(new_need)
            updated = True
    
    if updated:
        save_db_to_cloud(st.session_state.db)
        st.toast("Vaisseau mis à jour !", icon="✅")
        time.sleep(0.5)
        st.rerun()

def toggle_crew_signup(ship_id, pilot_name, max_slots):
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
                    st.error("Vaisseau complet !")
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
            "FlightReady": False, 
            "NeedCrew": False,    
            "CrewList": [],
            "Image": info.get("img", ""),
            "Visuel": "",
            "Source": source,
            "Prix_USD": float(info.get("price", 0) or 0),
            "Prix_aUEC": float(info.get("auec_price", 0) if isinstance(info.get("auec_price"), (int, float)) else 0),
            "Assurance": insurance,
            "Prix": None,
            "crew_max": info.get("crew_max", 1),
        }
        new_entries.append(entry)

    st.session_state.db["fleet"].extend(new_entries)
    
    if save_db_to_cloud(st.session_state.db):
        st.balloons()
        st.toast(f"✅ {len(new_entries)} vaisseaux ajoutés au hangar !", icon="🚀")
        st.session_state.cart = []
        time.sleep(1)
        st.rerun()

# --- FONCTION SUPPRESSION ADMIN ---
def admin_delete_user(target_pilot):
    """Supprime toutes les traces d'un utilisateur."""
    db = st.session_state.db
    
    # 1. Supprimer le login
    if target_pilot in db["users"]:
        del db["users"][target_pilot]
    
    # 2. Supprimer les données perso
    if target_pilot in db["user_data"]:
        del db["user_data"][target_pilot]
    
    # 3. Supprimer les vaisseaux
    initial_len = len(db["fleet"])
    db["fleet"] = [s for s in db["fleet"] if s["Propriétaire"] != target_pilot]
    deleted_count = initial_len - len(db["fleet"])
    
    # 4. Retirer des équipages
    for s in db["fleet"]:
        if target_pilot in s.get("CrewList", []):
            s["CrewList"].remove(target_pilot)
            
    if save_db_to_cloud(db):
        st.success(f"Utilisateur {target_pilot} totalement supprimé ({deleted_count} vaisseaux).")
        time.sleep(2)
        st.rerun()

# --- 4. CSS ---
bg_img_code = get_local_img_as_base64(BACKGROUND_IMAGE)
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500&display=swap');
.stApp {{ background-image: url("{bg_img_code}"); background-size: cover; background-attachment: fixed; }}
.stApp::before {{ content: ""; position: absolute; inset: 0; background: radial-gradient(circle at top left, rgba(0, 20, 40, 0.95), rgba(0, 0, 0, 0.98)); z-index: -1; }}
section[data-testid="stSidebar"] {{ background-color: rgba(5, 10, 18, 0.98); border-right: 1px solid #123; }}

h1, h2, h3 {{ font-family: 'Orbitron', sans-serif !important; color: #fff !important; text-transform: uppercase; border-bottom: 2px solid rgba(0, 212, 255, 0.2); }}
p, div, span, label, button {{ font-family: 'Rajdhani', sans-serif !important; }}
::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: #020408; }}
::-webkit-scrollbar-thumb {{ background: #163347; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: #00d4ff; }}

/* LOCK SIDEBAR */
section[data-testid="stSidebar"] button {{ display: none !important; }}
[data-testid="collapsedControl"] {{ display: none !important; }}
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

/* CORPO CARD STYLE */
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

/* FLAGSHIP STYLE */
.flagship-card {{ border: 2px solid #ffaa00; box-shadow: 0 0 25px rgba(255, 170, 0, 0.15); }}
.flagship-card .corpo-card-img {{ height: 350px; }}
.flagship-count {{ background: #ffaa00; }}

/* CREW CARD STYLE */
.crew-card {{ border: 1px solid #ff0055 !important; box-shadow: 0 0 15px rgba(255, 0, 85, 0.2); }}
.crew-tag {{ background: #ff0055; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; margin-left: 5px; }}

/* SEARCH BAR STYLE */
div[data-testid="stTextInput"] input {{
    text-align: center;
    font-family: 'Orbitron';
    border: 1px solid #333;
    background-color: #020408;
}}
div[data-testid="stTextInput"] input:focus {{
    border-color: #00d4ff;
    box-shadow: 0 0 10px rgba(0,212,255,0.3);
}}

/* CUSTOM SELECTBOX IN CARDS */
div[data-testid="stSelectbox"] > div > div {{
    background-color: rgba(0,0,0,0.5);
    border: 1px solid #333;
}}

/* NAVIGATION STYLE */
div[data-testid="stRadio"] > label {{ display: none; }}
div[data-testid="stRadio"] div[role="radiogroup"] > label {{
    background: rgba(255,255,255,0.05);
    padding: 10px;
    border-radius: 6px;
    border: 1px solid transparent;
    margin-bottom: 5px;
    transition: all 0.3s;
}}
div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {{ border-color: #00d4ff; background: rgba(0, 212, 255, 0.1); }}
div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] {{
    background: linear-gradient(90deg, rgba(0, 212, 255, 0.2), transparent);
    border-left: 4px solid #00d4ff;
    color: #00d4ff !important;
}}
</style>""", unsafe_allow_html=True)

# --- 5. SESSION STATE ---
if "current_pilot" not in st.session_state: st.session_state.current_pilot = None
if "catalog_page" not in st.session_state: st.session_state.catalog_page = 0
if "menu_nav" not in st.session_state: st.session_state.menu_nav = "CATALOGUE"
if "selected_source" not in st.session_state: st.session_state.selected_source = "STORE"
if "selected_insurance" not in st.session_state: st.session_state.selected_insurance = "LTI"
if "cart" not in st.session_state: st.session_state.cart = [] 
if "admin_unlocked" not in st.session_state: st.session_state.admin_unlocked = False

# --- 6. SIDEBAR ---
def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='border:none;'>💠 PIONEER</h2>", unsafe_allow_html=True)
        if st.session_state.current_pilot:
            st.markdown(f"<div style='color:#00d4ff; font-weight:bold; margin-bottom:10px;'>PILOTE: {st.session_state.current_pilot}</div>", unsafe_allow_html=True)
            if st.button("DÉCONNEXION", use_container_width=True):
                st.session_state.current_pilot = None; st.session_state.cart = []; st.session_state.admin_unlocked = False; st.rerun()
            st.markdown("---")
            
            nav_opts = ["CATALOGUE", "MON HANGAR", "FLOTTE CORPO", "NEED CREW", "ADMINISTRATION"]
            curr_idx = nav_opts.index(st.session_state.menu_nav) if st.session_state.menu_nav in nav_opts else 0
            
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
            corpo_pass = st.text_input("Code Corporation", type="password")
            
            if st.form_submit_button("SE CONNECTER", type="primary"):
                real_corpo = st.session_state.db.get("corpo_code", "APQ8M3")
                if corpo_pass != real_corpo:
                    st.error("Code Corporation incorrect.")
                    st.stop()
                
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
    with col_filters:
        st.subheader("PARAMÈTRES")
        p_source = st.radio("SOURCE", ["STORE", "INGAME"], index=0 if st.session_state.selected_source == "STORE" else 1)
        st.session_state.selected_source = p_source
        p_ins = st.selectbox("ASSURANCE", ["LTI", "10 Ans", "2 ans", "6 Mois", "2 Mois", "Standard"], index=0)
        st.markdown("---")
        brands = ["Tous"] + sorted(list(set(d.get("brand") for d in SHIPS_DB.values() if d.get("brand"))))
        f_brand = st.selectbox("CONSTRUCTEUR", brands)
        all_roles = sorted(list(set(d.get("role", "Inconnu") for d in SHIPS_DB.values() if d.get("role"))))
        f_role = st.selectbox("RÔLE", ["Tous"] + all_roles)
        
    with col_main:
        st.subheader(f"REGISTRE ({len(st.session_state.cart)} SÉLECTIONNÉS)")
        search = st.multiselect("RECHERCHE", sorted(list(SHIPS_DB.keys())), placeholder="🔍 Vaisseau...", label_visibility="collapsed")
        filtered = {}
        for name, data in SHIPS_DB.items():
            if f_brand != "Tous" and data.get("brand") != f_brand: continue
            if f_role != "Tous" and data.get("role") != f_role: continue
            if search and name not in search: continue
            filtered[name] = data

        items = list(filtered.items())
        PER_PAGE = 8
        total_pages = max(1, (len(items) + PER_PAGE - 1) // PER_PAGE)
        if st.session_state.catalog_page >= total_pages: st.session_state.catalog_page = 0

        c1, c2, c3 = st.columns([1, 4, 1])
        if c1.button("◄", disabled=(st.session_state.catalog_page==0)): st.session_state.catalog_page -= 1; st.rerun()
        c2.markdown(f"<div style='text-align:center'>PAGE {st.session_state.catalog_page+1}/{total_pages}</div>", unsafe_allow_html=True)
        if c3.button("►", disabled=(st.session_state.catalog_page==total_pages-1)): st.session_state.catalog_page += 1; st.rerun()

        start = st.session_state.catalog_page * PER_PAGE
        current_batch = items[start : start + PER_PAGE]
        
        if not current_batch: st.info("Aucun vaisseau.")
        
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
                        st.session_state.cart.append({'name': name, 'source': p_source, 'insurance': p_ins, 'price_disp': price_str})
                        st.rerun()

    with col_cart:
        st.subheader("PANIER")
        if not st.session_state.cart: st.info("Vide")
        else:
            for item in st.session_state.cart:
                p_disp = item.get('price_disp', 'N/A')
                st.markdown(f"<div style='border-left:2px solid #00d4ff; padding-left:5px; margin-bottom:5px;'>{item['name']} <br><span style='font-size:0.8em; color:#888'>{item['source']}</span></div>", unsafe_allow_html=True)
            if st.button("VALIDER TOUT", type="primary", use_container_width=True): submit_cart_batch()
            if st.button("VIDER", use_container_width=True): st.session_state.cart = []; st.rerun()

def my_hangar_page():
    st.subheader(f"HANGAR LOGISTIQUE | {st.session_state.current_pilot}")
    pilot_data = st.session_state.db.get("user_data", {}).get(st.session_state.current_pilot, {})
    current_auec = pilot_data.get("auec_balance", 0)
    target = pilot_data.get("acquisition_target", None)
    my_fleet = [s for s in st.session_state.db["fleet"] if s["Propriétaire"] == st.session_state.current_pilot]

    tab_fleet, tab_acq = st.tabs(["🚀 MA FLOTTE", "🎯 OBJECTIF D'ACHAT"])

    with tab_fleet:
        search_hangar = st.text_input("🔍 Rechercher un vaisseau dans mon hangar...", "")
        if not my_fleet:
            st.info("Hangar vide.")
        else:
            df = pd.DataFrame(my_fleet)
            total_usd_personal = 0
            total_auec_personal = 0
            for _, row in df.iterrows():
                if row['Source'] == 'STORE': total_usd_personal += get_current_ship_price(row['Vaisseau'], 'USD')
                elif row['Source'] == 'INGAME': total_auec_personal += get_current_ship_price(row['Vaisseau'], 'aUEC')

            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("VALEUR PLEDGE (USD)", f"${total_usd_personal:,.0f}")
            col_m2.metric("VALEUR IN-GAME (aUEC)", f"{total_auec_personal:,.0f}")
            col_m3.metric("VAISSEAUX", len(df))
            st.markdown("---")

            if search_hangar:
                m = search_hangar.lower()
                df = df[df["Vaisseau"].str.lower().str.contains(m) | df["Rôle"].str.lower().str.contains(m) | df["Source"].str.lower().str.contains(m)]

            if df.empty:
                st.info("Aucun vaisseau trouvé avec cette recherche.")
            else:
                df['is_flagship'] = df['Vaisseau'].apply(check_is_high_value)
                
                df_flags = df[df['is_flagship'] == True].copy()
                df_std = df[df['is_flagship'] == False].copy()

                df_flags['Sort_Price'] = df_flags['Vaisseau'].apply(lambda x: get_current_ship_price(x, 'USD'))
                df_flags = df_flags.sort_values(by='Sort_Price', ascending=False)
                
                df_std['Sort_Price'] = df_std['Vaisseau'].apply(lambda x: get_current_ship_price(x, 'USD'))
                df_std = df_std.sort_values(by='Sort_Price', ascending=False)

                def render_fleet_grid_editable(dataframe, is_flagship=False):
                    if dataframe.empty: return
                    
                    # RESTAURÉ : Gestion + et - (2-colonnes)
                    grp = dataframe.groupby(['Vaisseau', 'Source', 'Assurance', 'FlightReady', 'NeedCrew']).agg({
                        'id': 'count', 'Image': 'first', 'crew_max': 'max'
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
                            p_display = f"${info.get('price', 0):,.0f} USD" if source == 'STORE' else f"{info.get('auec_price', 0):,.0f} aUEC"
                            p_col = "#00d4ff" if source == 'STORE' else "#30e8ff"
                            
                            card_class = "corpo-card flagship-card" if is_flagship else "corpo-card"
                            if need_crew: card_class += " crew-card"
                            img_style = "height:350px;" if is_flagship else "height:200px;"
                            crew_badge = f"<span class='crew-tag'>CREW MAX: {max_slots}</span>" if need_crew else ""

                            st.markdown(f"""
                            <div class="{card_class}">
                                <img src="{img_b64}" class="corpo-card-img" style="{img_style}">
                                <div class="corpo-card-header">
                                    <span class="corpo-card-title">{name}</span>
                                    <span class="corpo-card-count">x{count}</span>
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
                                if st.button("🗑️", key=f"del_{i}_{name}_{source}_{is_ready}", help="Retirer"):
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

                if not df_flags.empty:
                    st.markdown("""<div style="text-align:center; margin: 30px 0 10px 0;"><div style="font-size: 30px; color: #ffaa00; margin-bottom: -10px;">▼</div><h2 style="color: #ffaa00; border-bottom: 2px solid #ffaa00; display: inline-block; padding: 0 20px 10px 20px;">FLOTTE AMIRALE</h2></div>""", unsafe_allow_html=True)
                    render_fleet_grid_editable(df_flags, is_flagship=True)

                st.markdown("### 🚀 FLOTTE STANDARD")
                render_fleet_grid_editable(df_std, is_flagship=False)

        else:
            st.info("Hangar vide. Allez au catalogue pour ajouter des vaisseaux.")

    with tab_acq:
        st.markdown("### 🎯 CALCULATEUR D'OBJECTIF")
        opts = ["—"] + sorted([n for n, d in SHIPS_DB.items() if d.get('ingame')])
        idx = opts.index(target) if target in opts else 0
        new_tgt = st.selectbox("Cible", opts, index=idx)
        
        c1, c2 = st.columns([1, 2])
        if "calc_balance" not in st.session_state: st.session_state.calc_balance = int(current_auec)
        
        with c1:
            tgt_price = SHIPS_DB[new_tgt].get('auec_price', 0) if new_tgt != "—" else 0
            sl_max = max(1000000, int(tgt_price * 1.2))
            def update_sl(): st.session_state.calc_balance = st.session_state.sl_val
            def update_nm(): st.session_state.calc_balance = st.session_state.nm_val
            st.number_input("Solde", value=st.session_state.calc_balance, step=10000, key="nm_val", on_change=update_nm)
            st.slider("Jauge", 0, sl_max, value=st.session_state.calc_balance, key="sl_val", on_change=update_sl)
            
            if st.button("💾 ENREGISTRER", type="primary", use_container_width=True):
                st.session_state.db["user_data"][st.session_state.current_pilot] = {"auec_balance": st.session_state.calc_balance, "acquisition_target": new_tgt}
                save_db_to_cloud(st.session_state.db)
                st.success("Sauvegardé !")
                time.sleep(0.5); st.rerun()
                
        with c2:
            if tgt_price > 0:
                pct = min(1.0, st.session_state.calc_balance / tgt_price)
                st.markdown(f"""<div style="background:#163347; border-radius:10px; padding:20px; text-align:center; border:1px solid #00d4ff;"><h2 style="margin:0; color:#fff;">{int(pct*100)}%</h2><p style="color:#aaa;">{st.session_state.calc_balance:,.0f} / <span style="color:#00d4ff; font-weight:bold;">{tgt_price:,.0f} aUEC</span></p></div>""", unsafe_allow_html=True)
                st.progress(pct)

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

    c1, c2, c3, c4 = st.columns(4)
    usd = df[df['Source']=='STORE']['Prix_USD'].sum()
    auec = df[df['Source']=='INGAME']['Prix_aUEC'].sum()
    c1.metric("VAISSEAUX", len(df))
    c2.metric("VALEUR FLOTTE (USD)", f"${usd:,.0f}")
    c3.metric("VALEUR FLOTTE (aUEC)", f"{auec:,.0f}")
    c4.metric("FLIGHT READY", df['FlightReady'].sum() if 'FlightReady' in df.columns else 0)

    st.markdown("---")
    
    tab_visu, tab_table, tab_members = st.tabs(["🚀 VUE FLOTTE", "📋 REGISTRE COMPLET", "👥 MEMBRES"])
    
    with tab_visu:
        st.markdown("""<div style="text-align:center; margin: 30px 0 10px 0;"><div style="font-size: 30px; color: #ffaa00; margin-bottom: -10px;">▼</div><h2 style="color: #ffaa00; border-bottom: 2px solid #ffaa00; display: inline-block; padding: 0 20px 10px 20px;">FLOTTE AMIRALE</h2></div>""", unsafe_allow_html=True)
        
        df['is_flagship'] = df['Vaisseau'].apply(check_is_high_value)
        df_flagships = df[df['is_flagship'] == True]
        df_standard = df[df['is_flagship'] == False]
        
        if not df_flagships.empty:
            grp_flags = df_flagships.groupby(['Vaisseau', 'Source']).agg({'Propriétaire': lambda x: sorted(x.unique()), 'id': 'count', 'Image': 'first'}).reset_index()
            cols = st.columns(3)
            for i, row in grp_flags.iterrows():
                with cols[i % 3]:
                    img_b64 = get_local_img_as_base64(row['Image'])
                    pilots_html = "".join([f"<span class='corpo-pilot-tag'>{p}</span>" for p in row['Propriétaire']])
                    st.markdown(f"""<div class="corpo-card flagship-card"><img src="{img_b64}" class="corpo-card-img"><div class="corpo-card-header"><span>{row['Vaisseau']}</span></div><div class="corpo-card-body">{pilots_html}</div></div>""", unsafe_allow_html=True)
        
        st.markdown("#### 🚀 FLOTTE STANDARD")
        if not df_standard.empty:
            roles = sorted(df_standard["Rôle"].unique())
            sel_role = st.selectbox("📂 Filtrer par Rôle", ["Tout afficher"] + roles)
            if sel_role != "Tout afficher": df_standard = df_standard[df_standard["Rôle"] == selected_role_view]
                
            grp_role = df_standard.groupby(['Vaisseau']).agg({'Propriétaire': lambda x: sorted(x.unique()), 'id': 'count', 'Image': 'first'}).reset_index()
            cols_role = st.columns(3) 
            for j, row in grp_role.iterrows():
                with cols_role[j % 3]:
                    img_b64 = get_local_img_as_base64(row['Image'])
                    pilots_html = "".join([f"<span class='corpo-pilot-tag'>{p}</span>" for p in row['Propriétaire']])
                    st.markdown(f"""<div class="corpo-card"><img src="{img_b64}" class="corpo-card-img"><div class="corpo-card-header"><span class="corpo-card-title">{row['Vaisseau']}</span><span class="corpo-card-count">x{row['id']}</span></div><div class="corpo-card-body"><div>{pilots_html}</div></div></div>""", unsafe_allow_html=True)

    with tab_table:
        st.subheader("📋 DÉTAIL GLOBAL")
        c_search, c_void = st.columns([2, 1])
        with c_search: search = st.text_input("🔍 Filtrer...", "")
        df_disp = df.copy()
        if search:
            m = search.lower()
            df_disp = df_disp[df_disp["Vaisseau"].str.lower().str.contains(m) | df_disp["Propriétaire"].str.lower().str.contains(m) | df_disp["Rôle"].str.lower().str.contains(m)]

        grp = df_disp.groupby(['Vaisseau', 'Source', 'Rôle']).agg({'Propriétaire': lambda x: ', '.join(sorted(x.unique())), 'id': 'count', 'Image': 'first'}).reset_index().rename(columns={'id': 'Quantité'})
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
        
        st.dataframe(grp[['Visuel', 'Vaisseau', 'Rôle', 'Source', 'Propriétaire', 'Quantité', 'Valeur Unitaire']], column_config={"Visuel": st.column_config.ImageColumn("Aperçu", width=150)}, use_container_width=True, hide_index=True, height=800)

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
            data_members.append({"Pilote": p, "Vaisseaux": len(p_ships), "Objectif Actuel": target_p})
        st.dataframe(pd.DataFrame(data_members), use_container_width=True, hide_index=True)

def admin_page():
    st.subheader("🔧 ADMINISTRATION")
    admin_code_db = st.session_state.db.get("admin_code", "9999")

    if not st.session_state.get("admin_unlocked", False):
        pwd = st.text_input("Code d'accès Admin", type="password")
        if st.button("ACCÉDER"):
            if pwd == admin_code_db:
                st.session_state.admin_unlocked = True
                st.rerun()
            else:
                st.error("Code incorrect.")
    else:
        st.warning("⚠️ ZONE DANGEREUSE")
        users_list = list(st.session_state.db["users"].keys())
        target_user = st.selectbox("Supprimer un membre", ["-- Choisir --"] + users_list)
        
        if target_user != "-- Choisir --":
            st.error(f"Supprimer {target_user} ?")
            if st.button("CONFIRMER SUPPRESSION", type="primary"):
                admin_delete_user(target_user)

        st.markdown("---")
        st.markdown("### 🔐 Code Corporation")
        new_code = st.text_input("Nouveau Code Corpo")
        if st.button("METTRE À JOUR LE CODE"):
            if new_code:
                st.session_state.db["corpo_code"] = new_code
                if save_db_to_cloud(st.session_state.db):
                    st.success(f"Code Corpo changé : {new_code}")
        
        st.markdown("---")
        if st.button("Se déconnecter"):
            st.session_state.admin_unlocked = False
            st.rerun()

# --- MAIN LOOP ---
render_sidebar()

if not st.session_state.current_pilot:
    home_page()
else:
    if st.session_state.menu_nav == "CATALOGUE": catalogue_page()
    elif st.session_state.menu_nav == "MON HANGAR": my_hangar_page()
    elif st.session_state.menu_nav == "FLOTTE CORPO": corpo_fleet_page()
    elif st.session_state.menu_nav == "NEED CREW": need_crew_page()
    elif st.session_state.menu_nav == "ADMINISTRATION": admin_page()