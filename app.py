import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import json
import requests
import time
from ships_data import SHIPS_DB

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="PIONEER COMMAND", layout="wide", page_icon="💠")
BACKGROUND_IMAGE = "assets/fondecransite.png"

# --- 2. GESTION DATABASE ---
try:
    JSONBIN_ID = st.secrets["JSONBIN_ID"]
    JSONBIN_KEY = st.secrets["JSONBIN_KEY"]
except:
    JSONBIN_ID = ""
    JSONBIN_KEY = ""

def load_db_from_cloud():
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest"
    headers = {"X-Master-Key": JSONBIN_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['record']
    except:
        pass
    return {"users": {}, "fleet": []}

def save_db_to_cloud(data):
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
    headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_KEY}
    requests.put(url, json=data, headers=headers)

if 'db' not in st.session_state:
    st.session_state.db = load_db_from_cloud()

# --- 3. FONCTIONS ---
@st.cache_data(show_spinner=False)
def get_local_img_as_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()
        return f"data:image/jpeg;base64,{encoded}"
    return "https://via.placeholder.com/400x200/0b0e11/00d4ff?text=IMG+ERROR"

def add_ship_action(ship_name, owner):
    info = SHIPS_DB[ship_name]
    new_id = int(time.time() * 1000)
    
    img_b64 = get_local_img_as_base64(info['img'])
    
    new_entry = {
        "id": new_id,
        "Propriétaire": owner,
        "Vaisseau": ship_name,
        "Marque": info['brand'],
        "Rôle": info['role'],
        "Prix": info['price'],
        "Dispo": False,
        "Image": info['img'],
        "Visuel": img_b64
    }
    
    st.session_state.db["fleet"].append(new_entry)
    st.session_state.session_log.append(f"+ {ship_name}")
    save_db_to_cloud(st.session_state.db)
    
    st.toast(f"✅ {ship_name} AJOUTÉ !", icon="🚀")
    time.sleep(0.5)
    st.rerun()

def process_fleet_updates(edited_df):
    needs_save = False
    current_db = st.session_state.db
    
    if "Supprimer" in edited_df.columns:
        ids_to_delete = edited_df[edited_df["Supprimer"] == True]["id"].tolist()
        if ids_to_delete:
            current_db["fleet"] = [s for s in current_db["fleet"] if s["id"] not in ids_to_delete]
            needs_save = True
            st.toast(f"🗑️ {len(ids_to_delete)} supprimés.", icon="🗑️")

    fleet_map = {s["id"]: s for s in current_db["fleet"]}
    for index, row in edited_df.iterrows():
        ship_id = row["id"]
        if ship_id in fleet_map:
            if fleet_map[ship_id]["Dispo"] != row["Dispo"]:
                fleet_map[ship_id]["Dispo"] = row["Dispo"]
                needs_save = True
    
    if needs_save:
        st.session_state.db = current_db
        save_db_to_cloud(current_db)
        st.success("✅ Synchronisation terminée")
        time.sleep(1)
        st.rerun()

# --- 4. CSS ---
bg_img_code = get_local_img_as_base64(BACKGROUND_IMAGE)

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500&display=swap');

    .stApp {{
        background-image: url("{bg_img_code}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    .stApp::before {{
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.85); z-index: -1;
    }}

    section[data-testid="stSidebar"] {{ background-color: rgba(8, 10, 12, 0.98); border-right: 1px solid #333; }}

    h1, h2, h3 {{ font-family: 'Orbitron', sans-serif !important; color: #e0e0e0 !important; text-transform: uppercase; letter-spacing: 1px; }}
    p, div, span, label, button {{ font-family: 'Rajdhani', sans-serif !important; color: #ccc; }}

    .catalog-card {{
        background: rgba(20, 20, 20, 0.8); border: 1px solid #333; border-radius: 4px;
        overflow: hidden; margin-bottom: 15px; transition: transform 0.2s;
    }}
    .catalog-card:hover {{ border-color: #00d4ff; transform: translateY(-3px); }}
    .card-img {{ width: 100%; height: 120px; object-fit: cover; border-bottom: 1px solid #222; }}
    .card-body {{ padding: 8px; text-align: center; }}
    .card-title {{ color: #fff; font-weight: bold; font-size: 0.85rem; margin: 0; }}
    .card-sub {{ font-size: 0.65rem; color: #888; text-transform: uppercase; }}

    div.stButton > button {{
        width: 100%; background: #0e1117; color: #ccc; border: 1px solid #444;
        border-radius: 0px; font-family: 'Rajdhani'; font-weight: bold; text-transform: uppercase;
    }}
    div.stButton > button:hover {{ border-color: #00d4ff; color: #00d4ff; }}
    div.stButton > button[kind="primary"] {{ border: 1px solid #00d4ff; color: #00d4ff; }}
    div.stButton > button[kind="primary"]:hover {{ background: #00d4ff; color: #000; }}

    .stTextInput > div > div, .stSelectbox > div > div {{
        background-color: rgba(0, 0, 0, 0.6) !important; color: #fff !important;
        border: 1px solid #333 !important; border-radius: 0px !important;
    }}
    
    div[data-testid="stAlert"] {{ background-color: rgba(20,20,20,0.9); border: 1px solid #333; color: #ccc; }}
    .pagination-info {{ text-align: center; color: #666; font-size: 0.9em; margin-top: 10px; }}
    
    .stRadio > div[role="radiogroup"] > label > div:first-child {{ display: None; }}
    .stRadio > div[role="radiogroup"] > label {{
        background: transparent; padding: 8px 15px; border-left: 2px solid transparent; transition: all 0.2s;
    }}
    .stRadio > div[role="radiogroup"] > label:hover {{ border-left: 2px solid #00d4ff; color: #fff; }}
</style>
""", unsafe_allow_html=True)

# --- 5. STATE INIT ---
if 'current_pilot' not in st.session_state:
    st.session_state.current_pilot = None
if 'catalog_page' not in st.session_state:
    st.session_state.catalog_page = 0
if 'menu_nav' not in st.session_state:
    st.session_state.menu_nav = "CATALOGUE"
if 'session_log' not in st.session_state:
    st.session_state.session_log = []

db = st.session_state.db

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: left; color: #fff !important; font-size: 1.5em; border:none;'>💠 PIONEER</h2>", unsafe_allow_html=True)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    if not st.session_state.current_pilot:
        st.caption("CONNEXION")
        with st.form("auth_form"):
            pseudo = st.text_input("ID")
            pin = st.text_input("PIN", type="password", max_chars=4)
            if st.form_submit_button("INITIALISER", type="primary"):
                st.session_state.db = load_db_from_cloud()
                if pseudo and len(pin) == 4:
                    if pseudo in st.session_state.db["users"]:
                        if st.session_state.db["users"][pseudo] == pin:
                            st.session_state.current_pilot = pseudo
                            st.rerun()
                        else:
                            st.error("PIN Erroné")
                    else:
                        st.session_state.db["users"][pseudo] = pin
                        save_db_to_cloud(st.session_state.db)
                        st.session_state.current_pilot = pseudo
                        st.success("OK")
                        st.rerun()
                else:
                    st.error("Données invalides")
    else:
        st.markdown(f"<div style='color:#00d4ff; font-weight:bold; margin-bottom:10px;'>PILOTE: {st.session_state.current_pilot}</div>", unsafe_allow_html=True)
        
        if st.button("DÉCONNEXION"):
            st.session_state.current_pilot = None
            st.session_state.session_log = []
            st.rerun()
        
        st.markdown("---")
        
        if st.session_state.session_log:
            st.caption("DERNIERS AJOUTS :")
            for log in reversed(st.session_state.session_log[-5:]):
                st.markdown(f"<span style='color:#00ff00; font-size:0.8em;'>{log}</span>", unsafe_allow_html=True)
            st.markdown("---")

        selected_menu = st.radio("NAVIGATION", ["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"], 
                                 index=["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"].index(st.session_state.menu_nav),
                                 label_visibility="collapsed", key="nav_radio")
        
        if selected_menu != st.session_state.menu_nav:
            st.session_state.menu_nav = selected_menu
            st.rerun()

# --- 7. APP PRINCIPALE ---
st.title("PIONEER ORG COMMAND")

if not st.session_state.current_pilot:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: rgba(20, 20, 20, 0.8); border-top: 2px solid #ff4b4b; border-bottom: 2px solid #ff4b4b;">
        <h2 style="color: #ff4b4b !important; font-size: 1.8em;">SYSTÈME VERROUILLÉ</h2>
        <p style="color: #aaa; letter-spacing: 1px; margin-top: 10px;">IDENTIFICATION REQUISE POUR ACCÈS AUX DONNÉES LOGISTIQUES.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # === CATALOGUE ===
    if st.session_state.menu_nav == "CATALOGUE":
        st.subheader("Base de Données")
        c1, c2 = st.columns([1, 3])
        brand_filter = c1.selectbox("Constructeur", ["Tous"] + sorted(list(set(d['brand'] for d in SHIPS_DB.values()))))
        search = c2.text_input("Recherche")

        filtered = {k: v for k, v in SHIPS_DB.items() if (brand_filter == "Tous" or v['brand'] == brand_filter) and (not search or search.lower() in k.lower())}
        items = list(filtered.items())
        
        ITEMS_PER_PAGE = 20
        total_pages = max(1, (len(items) // ITEMS_PER_PAGE) + (1 if len(items) % ITEMS_PER_PAGE > 0 else 0))
        
        if st.session_state.catalog_page >= total_pages: st.session_state.catalog_page = 0
        start = st.session_state.catalog_page * ITEMS_PER_PAGE
        current_items = items[start:start + ITEMS_PER_PAGE]

        if total_pages > 1:
            c_prev, c_txt, c_next = st.columns([1, 4, 1])
            with c_prev:
                if st.button("◄", key="p1") and st.session_state.catalog_page > 0:
                    st.session_state.catalog_page -= 1
                    st.rerun()
            with c_txt:
                st.markdown(f"<div class='pagination-info'>PAGE {st.session_state.catalog_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
            with c_next:
                if st.button("►", key="n1") and st.session_state.catalog_page < total_pages - 1:
                    st.session_state.catalog_page += 1
                    st.rerun()

        cols = st.columns(5)
        for i, (name, data) in enumerate(current_items):
            with cols[i % 5]:
                img_b64 = get_local_img_as_base64(data['img'])
                st.markdown(f"""
                <div class="catalog-card">
                    <img src="{img_b64}" class="card-img">
                    <div class="card-body">
                        <div class="card-sub">{data['brand']}</div>
                        <div class="card-title" title="{name}">{name}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("AJOUTER", key=f"add_{name}"):
                    add_ship_action(name, st.session_state.current_pilot)

    # === MON HANGAR ===
    elif st.session_state.menu_nav == "MON HANGAR":
        st.subheader(f"Inventaire : {st.session_state.current_pilot}")
        
        if st.button("➕ ACQUÉRIR D'AUTRES VAISSEAUX", type="primary"):
            st.session_state.menu_nav = "CATALOGUE"
            st.rerun()
            
        st.markdown("---")
        
        my_fleet = [s for s in st.session_state.db["fleet"] if s["Propriétaire"] == st.session_state.current_pilot]
        
        if not my_fleet:
            st.info("Hangar vide.")
        else:
            df_my = pd.DataFrame(my_fleet)
            df_my["Supprimer"] = False
            
            col_kpi, col_toggle = st.columns([3, 1])
            show = col_toggle.toggle("Voir Valeur")
            col_kpi.metric("VALORISATION", f"${df_my['Prix'].sum():,.0f}" if show else "---")

            edited = st.data_editor(
                df_my,
                column_config={
                    "Dispo": st.column_config.CheckboxColumn("Dispo ?", width="small"),
                    "Supprimer": st.column_config.CheckboxColumn("Supprimer", width="small"),
                    "Visuel": st.column_config.ImageColumn("Aperçu", width="small"),
                    "Prix": None,
                    "id": None,
                    "Image": None
                },
                disabled=["Propriétaire", "Vaisseau", "Marque", "Rôle", "Prix", "Visuel"],
                hide_index=True,
                use_container_width=True
            )
            
            if st.button("💾 ACTUALISER (SAUVEGARDER / SUPPRIMER)"):
                process_fleet_updates(edited)

    # === FLOTTE CORPO ===
    elif st.session_state.menu_nav == "FLOTTE CORPO":
        st.subheader("Registre Global")
        if not st.session_state.db["fleet"]:
            st.info("Base vide.")
        else:
            df_global = pd.DataFrame(st.session_state.db["fleet"])
            if "Visuel" not in df_global.columns:
                df_global["Visuel"] = df_global["Image"].apply(get_local_img_as_base64)

            # KPIs
            total_ships = len(df_global)
            total_dispo = len(df_global[df_global["Dispo"] == True])
            total_value = df_global["Prix"].sum() # Calcul de la valeur totale
            
            # Ajout de la 4ème colonne pour le prix total
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("MEMBRES", len(st.session_state.db["users"]))
            c2.metric("FLOTTE", total_ships)
            c3.metric("OPÉRATIONNELS", total_dispo)
            c4.metric("VALEUR GLOBALE", f"${total_value:,.0f}") # Affichage du prix
            
            st.divider()
            
            # 1. TABLEAU SYNTHÈSE
            st.markdown("### 📦 RÉSUMÉ DES STOCKS")
            summary_df = df_global.groupby(["Vaisseau", "Marque", "Rôle"]).agg(
                Quantité=('Vaisseau', 'count'),
                Dispo=('Dispo', 'sum')
            ).reset_index().sort_values(by="Quantité", ascending=False)
            
            st.dataframe(
                summary_df,
                column_config={
                    "Quantité": st.column_config.ProgressColumn("Total", format="%d", min_value=0, max_value=int(summary_df["Quantité"].max())),
                    "Dispo": st.column_config.NumberColumn("Prêtables", help="Nombre de vaisseaux marqués comme disponibles")
                },
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")

            # 2. TABLEAU DÉTAILLÉ
            st.markdown("### 📋 LISTE DÉTAILLÉE DES PILOTES")
            st.markdown("💡 *Sélectionnez une ligne pour voir le détail tactique*")
            
            show_only_dispo = st.checkbox("✅ Afficher uniquement les vaisseaux disponibles")
            
            if show_only_dispo:
                display_df = df_global[df_global["Dispo"] == True]
            else:
                display_df = df_global

            display_df["Statut"] = display_df["Dispo"].apply(lambda x: "✅ DISPONIBLE" if x else "⛔ NON DISPO")

            selection = st.dataframe(
                display_df,
                column_config={
                    "Visuel": st.column_config.ImageColumn("Vaisseau", width="small"),
                    "Propriétaire": st.column_config.TextColumn("Pilote", width="medium"),
                    "Statut": st.column_config.TextColumn("Prêt ?", width="medium"),
                    "Vaisseau": st.column_config.TextColumn("Modèle", width="medium"),
                    "Rôle": st.column_config.TextColumn("Classification", width="medium"),
                    "Image": None, "Prix": None, "id": None, "Marque": None, "Dispo": None
                },
                use_container_width=True,
                hide_index=True,
                height=400,
                selection_mode="single-row",
                on_select="rerun"
            )

            if selection.selection["rows"]:
                idx = selection.selection["rows"][0]
                selected_row = display_df.iloc[idx]
                
                st.markdown("---")
                st.markdown(f"### 🔎 VUE TACTIQUE : {selected_row['Vaisseau']}")
                
                col_img, col_details = st.columns([1, 1])
                
                with col_img:
                    if os.path.exists(selected_row['Image']):
                        st.image(selected_row['Image'], use_container_width=True)
                    else:
                        st.warning("Image non disponible")
                
                with col_details:
                    st.markdown(f"""
                    <div style="background:rgba(0,0,0,0.5); padding:20px; border-radius:10px; border:1px solid #333;">
                        <h4>PILOTE : <span style="color:#fff">{selected_row['Propriétaire']}</span></h4>
                        <h4>RÔLE : <span style="color:#fff">{selected_row['Rôle']}</span></h4>
                        <h4>CONSTRUCTEUR : <span style="color:#fff">{selected_row['Marque']}</span></h4>
                        <br>
                        <h2 style="color:{'#00ff00' if selected_row['Dispo'] else '#ff4b4b'} !important">
                            {'✅ OPÉRATIONNEL' if selected_row['Dispo'] else '⛔ NON ASSIGNÉ'}
                        </h2>
                    </div>
                    """, unsafe_allow_html=True)