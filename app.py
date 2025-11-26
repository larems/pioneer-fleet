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

        legacy_price = ship.get("Prix", None)
        if legacy_price not in (None, "", 0, 0.0):
            try:
                legacy_price_clean = float(str(legacy_price).replace(" ", "").replace("\u00a0", "").replace("$", "").replace("aUEC", "").replace(",", "."))
            except ValueError:
                legacy_price_clean = 0.0
            if ship.get("Source") == "STORE" and float(ship.get("Prix_USD", 0) or 0) == 0:
                ship["Prix_USD"] = legacy_price_clean
            if ship.get("Source") == "INGAME" and float(ship.get("Prix_aUEC", 0) or 0) == 0:
                ship["Prix_aUEC"] = legacy_price_clean
    
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

def process_fleet_updates(edited_df: pd.DataFrame):
    if edited_df.empty: return
    current_fleet = st.session_state.db["fleet"]
    needs_save = False

    if "Supprimer" in edited_df.columns:
        ids_to_del = edited_df[edited_df["Supprimer"] == True]["id"].tolist()
        if ids_to_del:
            st.session_state.db["fleet"] = [s for s in current_fleet if s.get("id") not in ids_to_del]
            needs_save = True

    update_map = edited_df.set_index("id")[["Dispo", "Assurance"]].to_dict("index")
    for ship in st.session_state.db["fleet"]:
        sid = ship.get("id")
        if sid in update_map:
            row = update_map[sid]
            if ship["Dispo"] != bool(row["Dispo"]):
                ship["Dispo"] = bool(row["Dispo"])
                needs_save = True
            if ship.get("Assurance") != row["Assurance"]:
                ship["Assurance"] = row["Assurance"]
                needs_save = True

    if needs_save:
        if save_db_to_cloud(st.session_state.db):
            st.success("✅ Synchronisation terminée")
            time.sleep(0.5); st.rerun()

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
                in_cart = any(item['name'] == name for item in st.session_state.cart)
                
                border = "2px solid #00d4ff" if in_cart else "1px solid #163347"
                shadow = "0 0 15px rgba(0, 212, 255, 0.4)" if in_cart else "none"
                opacity = "0.7" if in_cart else "1.0"
                btn_txt = "✅ DANS LE PANIER" if in_cart else "AJOUTER AU PANIER"
                btn_type = "primary" if in_cart else "secondary"

                if p_source == "STORE":
                    pv = data.get('price', 0)
                    price_str = f"${pv:,.0f} USD" if isinstance(pv, (int, float)) else str(pv)
                    price_col = "#00d4ff"
                else:
                    pv = data.get('auec_price', 0)
                    price_str = f"{pv:,.0f} aUEC" if isinstance(pv, (int, float)) and pv > 0 else "N/A"
                    price_col = "#30e8ff"

                st.markdown(f"""
                <div style="background:#041623; border-radius:8px; border:{border}; box-shadow:{shadow}; overflow:hidden; margin-bottom:8px; transition:0.2s;">
                    <div style="height:150px; background:#000;">
                        <img src="{img_b64}" style="width:100%; height:100%; object-fit:cover; opacity:{opacity}">
                    </div>
                    <div style="padding:10px;">
                        <div style="font-weight:bold; color:#fff; font-size:1.1em;">{name}</div>
                        <div style="display:flex; justify-content:space-between; font-size:0.9em; color:#ccc;">
                            <span>{data.get('role','N/A')}</span>
                            <span style="color:{price_col}; font-weight:bold;">{price_str}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(btn_txt, key=f"btn_{name}", use_container_width=True, type=btn_type):
                    if in_cart:
                        st.session_state.cart = [x for x in st.session_state.cart if x['name'] != name]
                    else:
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
            for idx, item in enumerate(st.session_state.cart):
                c_a, c_b = st.columns([5, 1])
                with c_a:
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.05); padding:6px; border-radius:4px; margin-bottom:4px; border-left:3px solid #00d4ff;">
                        <b>{item['name']}</b><br>
                        <span style="font-size:0.8em; color:#aaa;">{item['source']} | {item['insurance']} | {item['price_disp']}</span>
                    </div>""", unsafe_allow_html=True)
                with c_b:
                    if st.button("❌", key=f"del_{idx}_{item['name']}"):
                        st.session_state.cart.pop(idx); st.rerun()
            
            st.markdown("---")
            if st.button(f"💾 ENREGISTRER TOUT ({len(st.session_state.cart)})", type="primary", use_container_width=True):
                submit_cart_batch()
            if st.button("🗑️ Vider", use_container_width=True):
                st.session_state.cart = []; st.rerun()

def my_hangar_page():
    st.subheader(f"HANGAR | {st.session_state.current_pilot}")
    pilot_data = st.session_state.db.get("user_data", {}).get(st.session_state.current_pilot, {})
    current_auec = pilot_data.get("auec_balance", 0)
    target = pilot_data.get("acquisition_target", None)

    my_fleet = [s for s in st.session_state.db["fleet"] if s["Propriétaire"] == st.session_state.current_pilot]
    
    if my_fleet:
        df = pd.DataFrame(my_fleet)
        df["Supprimer"] = False
        df["Prix_USD"] = pd.to_numeric(df["Prix_USD"], errors="coerce").fillna(0)
        df["Prix_aUEC"] = pd.to_numeric(df["Prix_aUEC"], errors="coerce").fillna(0)
        df['Visuel'] = df['Image'].apply(get_local_img_as_base64)
        df["Affiche_Prix"] = df.apply(lambda x: f"${x['Prix_USD']:,.0f}" if x["Source"]=="STORE" else f"{x['Prix_aUEC']:,.0f} aUEC", axis=1)

        col_cfg = {
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "Visuel": st.column_config.ImageColumn("Aperçu"),
            "Dispo": st.column_config.CheckboxColumn("Prêt ?"),
            "Supprimer": st.column_config.CheckboxColumn("Suppr."),
            "Source": st.column_config.TextColumn("Source", disabled=True),
            "Assurance": st.column_config.SelectboxColumn("Assurance", options=["LTI", "10 Ans", "Standard"]),
            "Affiche_Prix": st.column_config.TextColumn("Valeur", disabled=True)
        }
        visible_cols = ["id", "Visuel", "Vaisseau", "Rôle", "Source", "Assurance", "Dispo", "Affiche_Prix", "Supprimer"]

        df_store = df[df["Source"]=="STORE"].copy()
        if not df_store.empty:
            st.markdown(f"#### 💰 STORE (${df_store['Prix_USD'].sum():,.0f})")
            edit_store = st.data_editor(df_store[visible_cols], column_config=col_cfg, use_container_width=True, hide_index=True, key="ed_store")
        else:
            edit_store = pd.DataFrame()

        df_game = df[df["Source"]=="INGAME"].copy()
        if not df_game.empty:
            st.markdown(f"#### 💸 INGAME ({df_game['Prix_aUEC'].sum():,.0f} aUEC)")
            edit_game = st.data_editor(df_game[visible_cols], column_config=col_cfg, use_container_width=True, hide_index=True, key="ed_game")
        else:
            edit_game = pd.DataFrame()

        if st.button("💾 SAUVEGARDER MODIFICATIONS HANGAR", type="primary", use_container_width=True):
            full_edit = pd.concat([edit_store, edit_game], ignore_index=True)
            process_fleet_updates(full_edit)
    else:
        st.info("Hangar vide.")

    render_acquisition_tracking(current_auec, target)

def render_acquisition_tracking(balance, target):
    st.markdown("---")
    st.markdown("### 🎯 OBJECTIF DU PILOTE")
    
    # === SYNC LOGIC POUR SLIDER & INPUT ===
    if "calc_balance" not in st.session_state:
        st.session_state.calc_balance = int(balance)

    def update_balance_slider():
        st.session_state.calc_balance = st.session_state.widget_slider
    def update_balance_num():
        st.session_state.calc_balance = st.session_state.widget_num

    # Définition de la cible et du max slider
    opts = ["—"] + sorted([n for n, d in SHIPS_DB.items() if d.get('ingame')])
    idx = opts.index(target) if target in opts else 0
    
    # Layout en 2 colonnes
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.markdown("**💰 Mon Solde aUEC**")
        # SLIDER ET INPUT SYNCHRONISÉS
        slider_max = 100_000_000
        if target and target in SHIPS_DB:
            t_price = SHIPS_DB[target].get('auec_price', 0)
            if isinstance(t_price, (int, float)) and t_price > 0:
                slider_max = int(t_price * 1.5)

        st.slider("Jauge rapide", 0, slider_max, key="widget_slider", on_change=update_balance_slider, label_visibility="collapsed")
        st.number_input("Montant précis", value=st.session_state.calc_balance, step=10000, key="widget_num", on_change=update_balance_num, label_visibility="collapsed")

    with c2:
        st.markdown("**🚀 Vaisseau Cible**")
        new_tgt = st.selectbox("Sélection", opts, index=idx, label_visibility="collapsed")
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True) # Espacement pour aligner le bouton
        
        if st.button("💾 METTRE À JOUR SOLDE & OBJECTIF", type="primary", use_container_width=True):
            st.session_state.db["user_data"][st.session_state.current_pilot] = {
                "auec_balance": st.session_state.calc_balance,
                "acquisition_target": new_tgt if new_tgt != "—" else None
            }
            save_db_to_cloud(st.session_state.db); st.rerun()

    # Barre de progression (si cible valide)
    if target and target in SHIPS_DB:
        cost = SHIPS_DB[target].get('auec_price', 0)
        if isinstance(cost, (int, float)) and cost > 0:
            bal = st.session_state.calc_balance
            pct = min(1.0, bal/cost)
            st.markdown(f"**Progression : {int(pct*100)}%** ({bal:,.0f} / {cost:,.0f} aUEC)")
            st.progress(pct)
            if bal >= cost: st.success("Fonds suffisants pour l'achat ! 🚀")

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
    
    g1, g2 = st.columns(2)
    with g1:
        v_counts = df["Marque"].value_counts().reset_index()
        v_counts.columns = ["Marque", "Count"]
        st.plotly_chart(px.pie(v_counts, values="Count", names="Marque", title="Constructeurs", hole=0.4), use_container_width=True)
    with g2:
        r_counts = df["Rôle"].value_counts().reset_index()
        r_counts.columns = ["Rôle", "Count"]
        st.plotly_chart(px.bar(r_counts, x="Count", y="Rôle", orientation='h', title="Rôles"), use_container_width=True)

    st.markdown("### 📋 DÉTAIL GLOBAL")
    search = st.text_input("🔍 Recherche globale...")
    if search:
        m = search.lower()
        df = df[df["Vaisseau"].str.lower().str.contains(m) | df["Propriétaire"].str.lower().str.contains(m)]

    grp = df.groupby(['Vaisseau', 'Source', 'Rôle']).agg({
        'Propriétaire': lambda x: ', '.join(sorted(x.unique())),
        'id': 'count',
        'Image': 'first'
    }).reset_index().rename(columns={'id': 'Quantité'})
    
    grp['Visuel'] = grp['Image'].apply(get_local_img_as_base64)
    
    # SÉLECTION DES COLONNES POUR MASQUER "Image" (le chemin texte)
    # On n'affiche que : Visuel, Vaisseau, Rôle, Source, Pilotes, Quantité
    final_view = grp[["Visuel", "Vaisseau", "Rôle", "Source", "Propriétaire", "Quantité"]]

    st.dataframe(
        final_view,
        column_config={
            "Visuel": st.column_config.ImageColumn("Aperçu", width="small"),
            "Propriétaire": st.column_config.TextColumn("Pilotes"),
            "Quantité": st.column_config.ProgressColumn("Stock", max_value=int(grp["Quantité"].max()))
        },
        use_container_width=True,
        hide_index=True
    )

# --- MAIN LOOP ---
render_sidebar()
if not st.session_state.current_pilot:
    home_page()
else:
    if st.session_state.menu_nav == "CATALOGUE": catalogue_page()
    elif st.session_state.menu_nav == "MON HANGAR": my_hangar_page()
    elif st.session_state.menu_nav == "FLOTTE CORPO": corpo_fleet_page()