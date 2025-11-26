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

# Liste des vaisseaux considérés comme "Majeurs/Flagships"
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
        ship.setdefault("Dispo", False)
        ship.setdefault("Image", "")
        ship.setdefault("Visuel", "")
        ship.setdefault("Source", "STORE")
        ship.setdefault("Prix_USD", 0.0)
        ship.setdefault("Prix_aUEC", 0.0)
        ship.setdefault("Assurance", "Standard")
        ship.setdefault("Prix", None)
        ship.setdefault("crew_max", 1)
    
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
            "Dispo": False,
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

# --- 4. CSS (Styles Ajustés) ---
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

/* CORPO CARD STYLE */
.corpo-card {{
    background: linear-gradient(135deg, rgba(4,20,35,0.95), rgba(0,0,0,0.95));
    border: 1px solid #163347;
    border-radius: 12px;
    padding: 0;
    overflow: hidden;
    margin-bottom: 20px;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.corpo-card:hover {{ transform: translateY(-4px); border-color: #00d4ff; box-shadow: 0 0 15px rgba(0, 212, 255, 0.15); }}
.corpo-card-img {{ width: 100%; height: 220px; object-fit: cover; border-bottom: 1px solid #163347; }} 
.corpo-card-header {{ padding: 10px 14px; background: rgba(0,0,0,0.4); display:flex; justify-content:space-between; align-items:center; }}
.corpo-card-title {{ font-family: 'Orbitron'; font-size: 1.2em; color: white; font-weight: bold; text-shadow: 0 2px 4px black; }}
.corpo-card-count {{ background: #00d4ff; color: #000; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-family: 'Orbitron'; box-shadow: 0 0 10px rgba(0,212,255,0.4); }}
.corpo-card-body {{ padding: 12px 14px; font-size: 0.9em; color: #aaa; background: rgba(0,0,0,0.2); }}
.corpo-pilot-tag {{ display: inline-block; background: rgba(22, 51, 71, 0.8); color: #e0e0e0; padding: 4px 8px; border-radius: 4px; margin: 3px; font-size: 0.85em; border: 1px solid rgba(255,255,255,0.1); }}

/* FLAGSHIP STYLE */
.flagship-card {{ border: 2px solid #ffaa00; box-shadow: 0 0 25px rgba(255, 170, 0, 0.15); }}
.flagship-card .corpo-card-img {{ height: 350px; }}
.flagship-count {{ background: #ffaa00; }}
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
            nav = st.radio("NAVIGATION", ["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"], index=["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"].index(st.session_state.menu_nav), label_visibility="collapsed")
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
    
    with col_filters:
        st.subheader("PARAMÈTRES")
        p_source = st.radio("SOURCE", ["STORE", "INGAME"], index=0 if st.session_state.selected_source == "STORE" else 1)
        st.session_state.selected_source = p_source
        ins_opts = ["LTI", "10 Ans", "2 ans", "6 Mois", "2 Mois", "Standard"]
        p_ins = st.selectbox("ASSURANCE", ins_opts, index=0)
        st.session_state.selected_insurance = p_ins
        st.markdown("---")
        brands = ["Tous"] + sorted(list(set(d.get("brand") for d in SHIPS_DB.values() if d.get("brand"))))
        f_brand = st.selectbox("CONSTRUCTEUR", brands)
        search = st.multiselect("RECHERCHE", sorted(list(SHIPS_DB.keys())))

    filtered = {}
    for name, data in SHIPS_DB.items():
        if f_brand != "Tous" and data.get("brand") != f_brand: continue
        if search and name not in search: continue
        filtered[name] = data

    items = list(filtered.items())
    PER_PAGE = 8
    total_pages = max(1, (len(items) + PER_PAGE - 1) // PER_PAGE)
    if st.session_state.catalog_page >= total_pages: st.session_state.catalog_page = 0
    
    with col_main:
        st.subheader(f"REGISTRE ({len(st.session_state.cart)} SÉLECTIONNÉS)")
        c1, c2, c3 = st.columns([1, 4, 1])
        with c1: 
            if st.button("◄", disabled=(st.session_state.catalog_page==0)): st.session_state.catalog_page -= 1; st.rerun()
        with c2: st.markdown(f"<div style='text-align:center'>PAGE {st.session_state.catalog_page+1}/{total_pages}</div>", unsafe_allow_html=True)
        with c3: 
            if st.button("►", disabled=(st.session_state.catalog_page==total_pages-1)): st.session_state.catalog_page += 1; st.rerun()

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
                
                st.markdown(f"""
                <div style="background:#041623; border-radius:8px; border:{border}; box-shadow:{shadow}; overflow:hidden; margin-bottom:8px; transition:0.2s;">
                    <div style="height:150px; background:#000;">
                        <img src="{img_b64}" style="width:100%; height:100%; object-fit:cover; opacity:{opacity}">
                    </div>
                    <div style="padding:10px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="font-weight:bold; color:#fff; font-size:1.1em;">{name}</div>
                            {badge_html}
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:0.9em; color:#ccc; margin-top:4px;">
                            <span>{data.get('role','N/A')}</span>
                            <span style="color:{price_col}; font-weight:bold;">{price_str}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

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
        if my_fleet:
            df = pd.DataFrame(my_fleet)
            
            # Groupement pour affichage carte (par Vaisseau + Source + Assurance pour éviter les confusions)
            # On veut afficher "x2" si on a 2 fois le même vaisseau exact
            grp_fleet = df.groupby(['Vaisseau', 'Source', 'Assurance']).agg({
                'id': 'count',
                'Image': 'first' # On prend l'image du premier
            }).reset_index().rename(columns={'id': 'Quantité'})

            # Affichage en grille
            cols = st.columns(3)
            for i, row in grp_fleet.iterrows():
                with cols[i % 3]:
                    name = row['Vaisseau']
                    source = row['Source']
                    insurance = row['Assurance']
                    count = row['Quantité']
                    img_path = SHIPS_DB.get(name, {}).get('img', '')
                    img_b64 = get_local_img_as_base64(img_path)

                    # Prix Reel
                    info = SHIPS_DB.get(name, {})
                    if source == 'STORE':
                        p_display = f"${info.get('price', 0):,.0f} USD"
                        p_col = "#00d4ff"
                    else:
                        p_display = f"{info.get('auec_price', 0):,.0f} aUEC"
                        p_col = "#30e8ff"
                    
                    st.markdown(f"""
                    <div class="corpo-card">
                        <img src="{img_b64}" class="corpo-card-img" style="height:200px;">
                        <div class="corpo-card-header">
                            <span class="corpo-card-title">{name}</span>
                            <span class="corpo-card-count">x{count}</span>
                        </div>
                        <div class="corpo-card-body">
                            <div style="display:flex; justify-content:space-between;">
                                <span>{source} | {insurance}</span>
                                <span style="color:{p_col}; font-weight:bold;">{p_display}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Bouton Suppression Unitaire
                    if st.button(f"🗑️ Retirer un {name}", key=f"del_h_{i}"):
                        # Trouver l'ID d'UN vaisseau correspondant
                        to_remove_id = None
                        for s in st.session_state.db["fleet"]:
                            if (s["Propriétaire"] == st.session_state.current_pilot and 
                                s["Vaisseau"] == name and 
                                s["Source"] == source and 
                                s["Assurance"] == insurance):
                                to_remove_id = s["id"]
                                break
                        
                        if to_remove_id:
                            st.session_state.db["fleet"] = [s for s in st.session_state.db["fleet"] if s["id"] != to_remove_id]
                            save_db_to_cloud(st.session_state.db)
                            st.rerun()

        else:
            st.info("Hangar vide. Allez au catalogue pour ajouter des vaisseaux.")

    # --- ONGLET 2 : ACQUISITION ---
    with tab_acq:
        st.markdown("### 🎯 CALCULATEUR D'OBJECTIF")
        
        opts = ["—"] + sorted([n for n, d in SHIPS_DB.items() if d.get('ingame')])
        idx = opts.index(target) if target in opts else 0
        
        # Selecteur principal
        new_tgt = st.selectbox("Sélectionner le vaisseau cible", opts, index=idx, key="h_target_sel")
        
        # Update session state si changement
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
                
                # Jauge visuelle custom
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

def corpo_fleet_page():
    st.subheader("FLOTTE CORPORATIVE")
    df = pd.DataFrame(st.session_state.db["fleet"])
    if df.empty: st.info("Aucune donnée."); return

    df["Prix_USD"] = pd.to_numeric(df["Prix_USD"], errors="coerce").fillna(0)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("VAISSEAUX", len(df))
    c2.metric("VALEUR USD", f"${df[df['Source']=='STORE']['Prix_USD'].sum():,.0f}")
    c3.metric("PRÊTABLES", df["Dispo"].sum())

    st.markdown("---")

    # --- SECTION FLAGSHIPS ---
    st.markdown("## ⚔️ VAISSEAUX AMIRAUX & CAPITAUX")
    
    df_flagships = df[df["Vaisseau"].isin(FLAGSHIPS_LIST)]
    
    if not df_flagships.empty:
        grp_flags = df_flagships.groupby(['Vaisseau', 'Source']).agg({
            'Propriétaire': lambda x: sorted(x.unique()),
            'id': 'count',
            'Image': 'first'
        }).reset_index()

        cols = st.columns(3) # IMAGES GEANTES
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
        st.info("Aucun vaisseau capital détecté.")

    st.markdown("---")
    st.markdown("## 🚀 FLOTTE OPÉRATIONNELLE")

    df_standard = df[~df["Vaisseau"].isin(FLAGSHIPS_LIST)]
    
    if not df_standard.empty:
        all_roles = sorted(df_standard["Rôle"].unique())
        tabs = st.tabs(all_roles)

        for i, role in enumerate(all_roles):
            with tabs[i]:
                df_role = df_standard[df_standard["Rôle"] == role]
                grp_role = df_role.groupby(['Vaisseau']).agg({
                    'Propriétaire': lambda x: sorted(x.unique()),
                    'id': 'count',
                    'Image': 'first'
                }).reset_index()

                # IMAGES PLUS GRANDES (3 COLONNES)
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

# --- MAIN LOOP ---
render_sidebar()
if not st.session_state.current_pilot:
    home_page()
else:
    if st.session_state.menu_nav == "CATALOGUE": catalogue_page()
    elif st.session_state.menu_nav == "MON HANGAR": my_hangar_page()
    elif st.session_state.menu_nav == "FLOTTE CORPO": corpo_fleet_page()