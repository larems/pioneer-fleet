import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import requests
import time
from ships_data import SHIPS_DB

# -------------------------------------------------------
# 1. CONFIGURATION
# -------------------------------------------------------

st.set_page_config(
    page_title="PIONEER COMMAND | OPS CONSOLE",
    layout="wide",
    page_icon="💠",
)

BACKGROUND_IMAGE = "assets/fondecransite.png"

# -------------------------------------------------------
# 2. GESTION DATABASE (JSONBIN.IO)
# -------------------------------------------------------

JSONBIN_ID = st.secrets.get("JSONBIN_ID", "6921f0ded0ea881f40f9933f")
JSONBIN_KEY = st.secrets.get("JSONBIN_KEY", "")

def normalize_db_schema(db: dict) -> dict:
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
        ship.setdefault("crew_max", 1)

        # Migration anciennes valeurs
        legacy_price = ship.get("Prix", None)
        if legacy_price not in (None, "", 0, 0.0):
            try:
                p = float(str(legacy_price)
                    .replace(" ", "")
                    .replace(",", ".")
                    .replace("$", "")
                    .replace("aUEC", ""))
            except:
                p = 0.0

            if ship["Source"] == "STORE" and ship["Prix_USD"] == 0:
                ship["Prix_USD"] = p
            if ship["Source"] == "INGAME" and ship["Prix_aUEC"] == 0:
                ship["Prix_aUEC"] = p

    # normalisation pilot data
    for pilot in db["users"].keys():
        db["user_data"].setdefault(pilot, {
            "auec_balance": 0,
            "acquisition_target": None
        })

    return db

@st.cache_data(ttl=300)
def load_db_from_cloud():
    if not JSONBIN_KEY:
        return {"users": {}, "fleet": [], "user_data": {}}

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest"
    try:
        r = requests.get(url, headers={"X-Master-Key": JSONBIN_KEY}, timeout=10)
        if r.status_code == 200:
            rec = r.json().get("record", {})
            return normalize_db_schema(rec)
    except:
        pass

    return {"users": {}, "fleet": [], "user_data": {}}

def save_db_to_cloud(data):
    if not JSONBIN_KEY:
        st.error("JSONBin.io KEY manquante — sauvegarde impossible.")
        return False

    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
    headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_KEY}

    try:
        r = requests.put(url, json=data, headers=headers, timeout=10)
        if r.status_code not in (200, 204, 403):
            st.error(f"Erreur JSONBin: {r.status_code}")
            return False
    except:
        return False

    load_db_from_cloud.clear()
    return True

# Chargement initial
if "db" not in st.session_state:
    st.session_state.db = normalize_db_schema(load_db_from_cloud())

# -------------------------------------------------------
# 3. UTILITAIRES
# -------------------------------------------------------

def get_local_img_as_base64(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
            return f"data:{mime};base64,{b64}"
        except:
            return ""
    return ""

# -------------------------------------------------------
# 4. CSS
# -------------------------------------------------------

bg_img_code = get_local_img_as_base64(BACKGROUND_IMAGE)

st.markdown(f"""
<style>
.stApp {{
    background-image: url("{bg_img_code}");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}
/* ... (tout ton CSS intact ici) ... */
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# 5. SESSION STATE
# -------------------------------------------------------

defaults = {
    "current_pilot": None,
    "catalog_page": 0,
    "menu_nav": "CATALOGUE",
    "session_log": [],
    "selected_ship_name": None,
    "selected_source": "STORE",
    "selected_insurance": "LTI",
    "pending_ships": [],            # <-- AJOUT POUR ACQUISITION MULTIPLE
}

for key, val in defaults.items():
    st.session_state.setdefault(key, val)

# -------------------------------------------------------
# 6. SIDEBAR
# -------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='color:white;'>💠 PIONEER</h2>", unsafe_allow_html=True)

        if st.session_state.current_pilot:
            st.markdown(f"**PILOTE :** {st.session_state.current_pilot}")
            if st.button("DÉCONNEXION", use_container_width=True):
                st.session_state.current_pilot = None
                st.session_state.menu_nav = "CATALOGUE"
                st.rerun()

            st.markdown("---")
            menu = st.radio(
                "Navigation",
                ["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"],
                index=["CATALOGUE","MON HANGAR","FLOTTE CORPO"].index(st.session_state.menu_nav),
            )
            if menu != st.session_state.menu_nav:
                st.session_state.menu_nav = menu
                st.session_state.catalog_page = 0
                st.session_state.selected_ship_name = None
                st.rerun()
        else:
            st.caption("Veuillez vous connecter.")

# -------------------------------------------------------
# 7. ACQUISITION MULTIPLE — FONCTION D'ENREGISTREMENT
# -------------------------------------------------------

def register_ship_batch(item):
    """Enregistre un vaisseau depuis la liste pending_ships."""
    name = item["name"]
    source = item["source"]
    insurance = item["insurance"]
    owner = st.session_state.current_pilot

    info = SHIPS_DB[name]
    new_id = int(time.time() * 1_000_000)

    price_usd = info.get("price", 0) or 0
    price_aUEC = info.get("auec_price", 0) or 0

    new_entry = {
        "id": new_id,
        "Propriétaire": owner,
        "Vaisseau": name,
        "Marque": info.get("brand", "N/A"),
        "Rôle": info.get("role", "Inconnu"),
        "Dispo": False,
        "Image": info.get("img", ""),
        "Visuel": "",
        "Source": source,
        "Prix_USD": float(price_usd if isinstance(price_usd, (int, float)) else 0),
        "Prix_aUEC": float(price_aUEC if isinstance(price_aUEC, (int, float)) else 0),
        "Assurance": insurance,
        "Prix": None,
        "crew_max": info.get("crew_max", 1),
    }

    st.session_state.db["fleet"].append(new_entry)
    st.session_state.db = normalize_db_schema(st.session_state.db)

# -------------------------------------------------------
# 8. PAGE CATALOGUE (Version Nettoyée + Sélection Multiple)
# -------------------------------------------------------

def catalogue_page():
    col_filters, col_main_catalogue, col_commander = st.columns([1.2, 3.5, 1.6])

    # -------------------------------
    # PANEL GAUCHE : FILTRES + OPTIONS
    # -------------------------------
    with col_filters:
        st.subheader("PARAMÈTRES")

        purchase_source = st.radio(
            "SOURCE",
            ["STORE", "INGAME"],
            index=0 if st.session_state.selected_source == "STORE" else 1
        )
        st.session_state.selected_source = purchase_source

        insurance_options = ["LTI", "10 Ans", "2 ans", "6 Mois", "2 Mois", "Standard"]
        selected_insurance = st.selectbox(
            "ASSURANCE",
            insurance_options,
            index=insurance_options.index(st.session_state.selected_insurance),
        )
        st.session_state.selected_insurance = selected_insurance

        st.markdown("---")

        brand_filter = st.selectbox(
            "CONSTRUCTEUR",
            ["Tous"] + sorted({d.get("brand") for d in SHIPS_DB.values() if d.get("brand")})
        )

        available_names = sorted(list(SHIPS_DB.keys()))
        search_selection = st.multiselect("RECHERCHE", available_names)

    # -------------------------------
    # FILTRAGE DES VAISSEAUX
    # -------------------------------
    filtered = {}
    for name, data in SHIPS_DB.items():
        if brand_filter != "Tous" and data.get("brand") != brand_filter:
            continue
        if search_selection and name not in search_selection:
            continue
        filtered[name] = data

    items = list(filtered.items())
    ITEMS_PER_PAGE = 8
    total_items = len(items)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    if st.session_state.catalog_page >= total_pages:
        st.session_state.catalog_page = 0

    start = st.session_state.catalog_page * ITEMS_PER_PAGE
    current_items = items[start:start + ITEMS_PER_PAGE]

    # -------------------------------
    # CATALOGUE CENTRAL
    # -------------------------------

    with col_main_catalogue:
        st.subheader("REGISTRE DES VAISSEAUX")

        # Pagination
        left, center, right = st.columns([1, 4, 1])

        if st.button("◄", disabled=st.session_state.catalog_page == 0, key="prev_btn"):
            st.session_state.catalog_page -= 1
            st.rerun()

        with center:
            st.markdown(
                f"**Page {st.session_state.catalog_page + 1}/{total_pages} — {total_items} modèles**"
            )

        if st.button("►", disabled=st.session_state.catalog_page == total_pages - 1, key="next_btn"):
            st.session_state.catalog_page += 1
            st.rerun()

        st.markdown("---")

        if not current_items:
            st.info("Aucun vaisseau ne correspond aux filtres.")
        else:
            cols = st.columns(2)

            for i, (name, data) in enumerate(current_items):
                with cols[i % 2]:

                    img64 = get_local_img_as_base64(data.get("img", ""))

                    # Prix dynamique
                    if purchase_source == "STORE":
                        p = data.get("price", 0)
                        price_display = f"${p:,.0f} USD" if isinstance(p, (int, float)) else str(p)
                    else:
                        p = data.get("auec_price", 0)
                        if isinstance(p, (int, float)):
                            price_display = f"{p:,.0f} aUEC"
                        else:
                            price_display = str(p)

                    brand = data.get("brand", "N/A")
                    role = data.get("role", "Inconnu")

                    st.markdown(f"""
<div class="catalog-card">
  <div class="card-img-container">
    <img class="card-img" src="{img64}">
    <span class="card-brand-top">{brand}</span>
    <div class="card-tags-bar">
      <span class="card-tag">{role}</span>
      <span class="card-tag">{purchase_source}</span>
    </div>
  </div>
  <div class="card-info">
    <div class="ships-name">{name}</div>
    <div class="price-box">
      <span class="card-role-info">RÔLE: {role}</span>
      <span class="ship-price-value">{price_display}</span>
    </div>
  </div>
</div>
                    """, unsafe_allow_html=True)

                    if st.button(
                        "Ajouter à la liste",
                        key=f"add_pending_{name}",
                        use_container_width=True
                    ):
                        st.session_state.pending_ships.append({
                            "name": name,
                            "source": purchase_source,
                            "insurance": selected_insurance
                        })
                        st.success(f"{name} ajouté à la pré-sélection.")
                        st.rerun()

    # -------------------------------
    # PANNEAU DROIT : VALIDATION MULTIPLE
    # -------------------------------

    with col_commander:
        st.subheader("ACQUISITIONS SÉLECTIONNÉES")

        if not st.session_state.current_pilot:
            st.info("Connectez-vous pour enregistrer des vaisseaux.")
            return

        if st.session_state.pending_ships:
            for ship in st.session_state.pending_ships:
                st.markdown(
                    f"• **{ship['name']}** — {ship['source']} — {ship['insurance']}"
                )

            st.markdown("---")

            if st.button("🚀 CONFIRMER L’ACQUISITION", type="primary", use_container_width=True):
                for ship in st.session_state.pending_ships:
                    register_ship_batch(ship)

                save_db_to_cloud(st.session_state.db)
                st.session_state.pending_ships = []
                st.success("Tous les vaisseaux ont été enregistrés.")
                st.rerun()

            if st.button("🗑️ VIDER LA LISTE", use_container_width=True):
                st.session_state.pending_ships = []
                st.warning("Sélection vidée.")
                st.rerun()

        else:
            st.info("Aucun vaisseau sélectionné.")

# -------------------------------------------------------
# 9. STYLE GLOBAL (CSS)
# -------------------------------------------------------

def load_css():
    st.markdown("""
<style>

:root {
  --color-bg: #0d0d0f;
  --color-bg-alt: #1a1a1d;
  --color-card: #131316;
  --color-accent: #3a8aff;
  --color-text: #e5e5e5;
  --color-soft: #b4b4b4;
  --radius: 12px;
  --shadow: 0 0 10px rgba(0,0,0,0.45);
}

/* Global */
body {
  background-color: var(--color-bg);
  color: var(--color-text);
}

h1, h2, h3, h4, h5 { color: var(--color-text); }
hr { border-color: #222; }

/* ----------- CATALOG CARDS ----------- */

.catalog-card {
  background: var(--color-card);
  border-radius: var(--radius);
  margin-bottom: 18px;
  overflow: hidden;
  box-shadow: var(--shadow);
  border: 1px solid #222;
}

.card-img-container {
  position: relative;
  background: #000;
}

.card-img {
  width: 100%;
  border-bottom: 1px solid #222;
}

.card-brand-top {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(0,0,0,0.6);
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 6px;
  color: #fff;
}

.card-tags-bar {
  position: absolute;
  bottom: 6px;
  left: 6px;
  display: flex;
  gap: 5px;
}

.card-tag {
  background: rgba(0,0,0,0.65);
  padding: 3px 7px;
  border-radius: 6px;
  font-size: 11px;
  color: #fff;
  border: 1px solid rgba(255,255,255,0.13);
}

.card-info {
  padding: 10px 12px;
}

.ships-name {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 4px;
}

.price-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-role-info {
  font-size: 13px;
  color: var(--color-soft);
}

.ship-price-value {
  font-weight: 700;
  color: var(--color-accent);
  font-size: 15px;
}

/* ----------- RIGHT PANEL LIST ----------- */

.selection-panel {
  background: var(--color-bg-alt);
  padding: 12px;
  border-radius: var(--radius);
  border: 1px solid #222;
  box-shadow: var(--shadow);
}

.selection-panel .ship-entry {
  padding: 6px 0;
  border-bottom: 1px solid #333;
  font-size: 13px;
}

.selection-panel .ship-entry:last-child {
  border-bottom: none;
}

/* ----------- BUTTONS ----------- */

button[kind="secondary"] {
  background-color: #222 !important;
  border: 1px solid #444 !important;
}

button {
  border-radius: 8px !important;
  font-weight: 600 !important;
}

</style>
    """, unsafe_allow_html=True)

# -------------------------------------------------------
# 10. PAGE HANGAR / FLEET MANAGEMENT
# -------------------------------------------------------

def hangar_page():

    if not st.session_state.current_pilot:
        st.warning("Connectez-vous pour voir votre hangar.")
        return

    st.header(f"Hangar de {st.session_state.current_pilot}")

    # -------------------------------------------------------
    # FILTRES
    # -------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        filter_brand = st.selectbox(
            "Constructeur",
            ["Tous"] + sorted({ship["Marque"] for ship in st.session_state.db["fleet"]}),
        )

    with col2:
        filter_role = st.selectbox(
            "Rôle",
            ["Tous"] + sorted({ship["Rôle"] for ship in st.session_state.db["fleet"]}),
        )

    with col3:
        filter_source = st.selectbox(
            "Source",
            ["Tous", "STORE", "INGAME"],
        )

    with col4:
        filter_dispo = st.selectbox(
            "Disponibilité",
            ["Tous", "Disponible", "Stocké"],
        )

    # -------------------------------------------------------
    # Filtrage des entrées du hangar
    # -------------------------------------------------------
    fleet = [
        ship for ship in st.session_state.db["fleet"]
        if ship["Propriétaire"] == st.session_state.current_pilot
    ]

    # Marque
    if filter_brand != "Tous":
        fleet = [s for s in fleet if s["Marque"] == filter_brand]

    # Rôle
    if filter_role != "Tous":
        fleet = [s for s in fleet if s["Rôle"] == filter_role]

    # Source
    if filter_source != "Tous":
        fleet = [s for s in fleet if s["Source"] == filter_source]

    # Disponibilité
    if filter_dispo != "Tous":
        want = True if filter_dispo == "Disponible" else False
        fleet = [s for s in fleet if s["Dispo"] == want]

    # -------------------------------------------------------
    # Pagination du hangar
    # -------------------------------------------------------
    ITEMS_PER_PAGE = 6
    total_items = len(fleet)
    total_pages = max(1, (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    page = st.session_state.get("hangar_page", 0)
    st.session_state.hangar_page = page

    start = page * ITEMS_PER_PAGE
    show_items = fleet[start:start + ITEMS_PER_PAGE]

    # Pagination display
    st.markdown("---")
    left, center, right = st.columns([1, 4, 1])

    if left.button("◄", disabled=page == 0):
        st.session_state.hangar_page -= 1
        st.rerun()

    with center:
        st.markdown(f"**Page {page + 1}/{total_pages} — {total_items} vaisseaux**")

    if right.button("►", disabled=page == total_pages - 1):
        st.session_state.hangar_page += 1
        st.rerun()

    st.markdown("---")

    # -------------------------------------------------------
    # AFFICHE LES CARTES DU HANGAR
    # -------------------------------------------------------

    cols = st.columns(2)

    for i, ship in enumerate(show_items):
        with cols[i % 2]:

            img = get_local_img_as_base64(ship.get("Image", ""))

            dispo_label = "🟢 DISPONIBLE" if ship["Dispo"] else "🔴 STOCKÉ"
            dispo_color = "color: #3a8aff;" if ship["Dispo"] else "color: #e86e6e;"

            st.markdown(f"""
<div class="catalog-card">
  <div class="card-img-container">
    <img class="card-img" src="{img}">
    <span class="card-brand-top">{ship["Marque"]}</span>
  </div>

  <div class="card-info">
      <div class="ships-name">{ship["Vaisseau"]}</div>

      <div class="price-box">
        <span class="card-role-info">{ship["Rôle"]}</span>
        <span class="ship-price-value">{ship['Source']}</span>
      </div>

      <div class="card-role-info" style="{dispo_color}">
        {dispo_label}
      </div>

      <div class="card-role-info">Assurance : {ship["Assurance"]}</div>
      <div class="card-role-info">ID : {ship["id"]}</div>
  </div>
</div>
            """, unsafe_allow_html=True)

            # -------------------------------------------------------
            # ACTIONS POUR CE VAISSEAU
            # -------------------------------------------------------

            b1, b2, b3 = st.columns([1, 1, 1])

            # Toggle disponibilité
            if b1.button("Toggle", key=f"toggle_{ship['id']}"):
                ship["Dispo"] = not ship["Dispo"]
                save_db_to_cloud(st.session_state.db)
                st.rerun()

            # Éditer
            if b2.button("Modifier", key=f"edit_{ship['id']}"):
                st.session_state.edit_ship_id = ship["id"]
                st.rerun()

            # Supprimer
            if b3.button("❌", key=f"del_{ship['id']}"):
                st.session_state.db["fleet"] = [
                    s for s in st.session_state.db["fleet"]
                    if s["id"] != ship["id"]
                ]
                save_db_to_cloud(st.session_state.db)
                st.rerun()

    # -------------------------------------------------------
    # POPUP D'ÉDITION D'UN VAISSEAU
    # -------------------------------------------------------
    if st.session_state.get("edit_ship_id"):
        ship_id = st.session_state.edit_ship_id
        ship = next((s for s in st.session_state.db["fleet"] if s["id"] == ship_id), None)

        if ship:
            st.markdown("---")
            st.subheader(f"Modifier : {ship['Vaisseau']}")

            c1, c2 = st.columns(2)

            with c1:
                new_insurance = st.selectbox(
                    "Assurance",
                    ["LTI", "10 Ans", "2 ans", "6 Mois", "2 Mois", "Standard"],
                    index=["LTI", "10 Ans", "2 ans", "6 Mois", "2 Mois", "Standard"].index(ship["Assurance"])
                )

            with c2:
                new_source = st.selectbox(
                    "Source",
                    ["STORE", "INGAME"],
                    index=0 if ship["Source"] == "STORE" else 1
                )

            if st.button("💾 Enregistrer les modifications"):
                ship["Assurance"] = new_insurance
                ship["Source"] = new_source
                save_db_to_cloud(st.session_state.db)
                st.success("Modifié.")
                st.session_state.edit_ship_id = None
                st.rerun()

            if st.button("Annuler"):
                st.session_state.edit_ship_id = None
                st.rerun()

# -------------------------------------------------------
# 11. PAGE CORPO – Flotte Globale
# -------------------------------------------------------

def corpo_fleet_page():

    st.header("📘 Registre Global de la Corporation")

    fleet = st.session_state.db.get("fleet", [])
    users = st.session_state.db.get("users", {})

    if not fleet:
        st.info("Aucun vaisseau enregistré dans la corporation.")
        return

    df = pd.DataFrame(fleet)

    # Normalisation minimale
    df["Prix_USD"] = pd.to_numeric(df.get("Prix_USD", 0), errors="coerce").fillna(0)
    df["Prix_aUEC"] = pd.to_numeric(df.get("Prix_aUEC", 0), errors="coerce").fillna(0)
    df["Dispo"] = df["Dispo"].astype(bool)

    # -------------------------------------------------------
    # KPI (avec toggle valeurs)
    # -------------------------------------------------------
    c_info, c_toggle = st.columns([4, 1])

    with c_toggle:
        show_val = st.toggle("Afficher valeurs", value=False)

    with c_info:
        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric("PILOTES", len(users))
        c2.metric("VAISSEAUX", len(df))
        c3.metric("OPÉRATIONNELS", int(df["Dispo"].sum()))

        usd_value = df[df["Source"] == "STORE"]["Prix_USD"].sum()
        auec_value = df[df["Source"] == "INGAME"]["Prix_aUEC"].sum()

        c4.metric("VALEUR STORE", f"${usd_value:,.0f}" if show_val else "---")
        c5.metric("VALEUR INGAME", f"{auec_value:,.0f} aUEC" if show_val else "---")

    st.markdown("---")

    # -------------------------------------------------------
    # GRAPH 1 : Donut par marque
    # -------------------------------------------------------
    st.subheader("📊 Composition globale")

    col1, col2 = st.columns(2)

    with col1:
        brand_data = df.groupby("Marque").size().reset_index(name="Quantité")

        fig_brand = px.pie(
            brand_data,
            values="Quantité",
            names="Marque",
            hole=0.45,
            title="Répartition par constructeur",
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig_brand.update_layout(template="plotly_dark")
        st.plotly_chart(fig_brand, use_container_width=True)

    # -------------------------------------------------------
    # GRAPH 2 : Bar chart rôle
    # -------------------------------------------------------
    with col2:
        role_data = df.groupby("Rôle").size().reset_index(name="Quantité")
        role_data = role_data.sort_values("Quantité")

        fig_role = px.bar(
            role_data,
            x="Quantité",
            y="Rôle",
            orientation="h",
            color="Quantité",
            color_continuous_scale="Blues",
            title="Répartition par rôle"
        )
        fig_role.update_layout(template="plotly_dark")
        st.plotly_chart(fig_role, use_container_width=True)

    st.markdown("---")

    # -------------------------------------------------------
    # STOCK PAR MODÈLE
    # -------------------------------------------------------

    st.subheader("📦 Stock par Modèle")

    stock_df = (
        df.groupby(["Vaisseau", "Marque", "Rôle"])
        .agg(
            Quantité=("Vaisseau", "count"),
            Dispo=("Dispo", "sum")
        )
        .reset_index()
        .sort_values("Quantité", ascending=False)
    )

    st.dataframe(
        stock_df,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # -------------------------------------------------------
    # RECHERCHE DÉTAILLÉE
    # -------------------------------------------------------
    st.subheader("📋 Liste détaillée des unités")

    colA, colB = st.columns([3, 1])

    with colA:
        search_term = st.text_input("🔍 Recherche (Pilote / Vaisseau / Rôle)")

    with colB:
        only_ready = st.checkbox("Afficher seulement dispos", value=False)

    detailed_df = df.copy()

    if only_ready:
        detailed_df = detailed_df[detailed_df["Dispo"]]

    if search_term:
        term = search_term.lower()
        detailed_df = detailed_df[
            detailed_df["Propriétaire"].str.lower().str.contains(term)
            | detailed_df["Vaisseau"].str.lower().str.contains(term)
            | detailed_df["Rôle"].str.lower().str.contains(term)
        ]

    # Regroupement pour une vue lisible
    view = detailed_df.groupby(["Vaisseau", "Propriétaire", "Rôle", "Source"]).agg(
        Assurance=("Assurance", lambda x: ", ".join(sorted(x))),
        Quantité=("Vaisseau", "count"),
        Image=("Image", "first"),
    ).reset_index()

    # Prix selon la source
    def compute_price(row):
        info = SHIPS_DB.get(row["Vaisseau"])
        if not info:
            return "N/A"
        if row["Source"] == "STORE":
            return f"${info.get('price', 0):,.0f}"
        else:
            p = info.get("auec_price", 0)
            return p if isinstance(p, str) else f"{p:,.0f} aUEC"

    view["Prix"] = view.apply(compute_price, axis=1)
    view["Visuel"] = view["Image"].apply(get_local_img_as_base64)

    st.dataframe(
        view,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Visuel": st.column_config.ImageColumn("Image", width="small"),
            "Vaisseau": st.column_config.TextColumn("Vaisseau"),
            "Propriétaire": st.column_config.TextColumn("Pilote"),
            "Rôle": st.column_config.TextColumn("Rôle"),
            "Source": st.column_config.TextColumn("Source"),
            "Assurance": st.column_config.TextColumn("Assurances"),
            "Quantité": st.column_config.TextColumn("x"),
            "Prix": st.column_config.TextColumn("Prix"),
        },
        height=450,
    )
# -------------------------------------------------------
# 12. ROUTER PRINCIPAL / MAIN APP
# -------------------------------------------------------

def render_sidebar():
    """Sidebar de navigation + infos pilote"""
    with st.sidebar:

        st.markdown(
            "<h2 style='color:white; text-transform:uppercase;'>💠 Pioneer Command</h2>",
            unsafe_allow_html=True
        )
        st.markdown("---")

        if st.session_state.current_pilot:

            st.markdown(
                f"<div style='color:#00d4ff; font-weight:bold;'>Pilote : {st.session_state.current_pilot}</div>",
                unsafe_allow_html=True
            )

            if st.button("⬅ Déconnexion"):
                st.session_state.current_pilot = None
                st.session_state.menu_nav = "CATALOGUE"
                st.rerun()

            st.markdown("---")

            st.session_state.menu_nav = st.radio(
                "Navigation",
                ["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"],
                index=["CATALOGUE", "MON HANGAR", "FLOTTE CORPO"].index(
                    st.session_state.get("menu_nav", "CATALOGUE")
                )
            )

        else:
            st.info("Veuillez vous connecter.")
            st.session_state.menu_nav = "HOME"


# -------------------------------------------------------
# MAIN DISPLAY
# -------------------------------------------------------
render_sidebar()

if st.session_state.menu_nav == "HOME":
    home_page()

else:
    st.markdown("<h1>🔷 Pioneer Command Console</h1>", unsafe_allow_html=True)

    if st.session_state.menu_nav == "CATALOGUE":
        catalogue_page()

    elif st.session_state.menu_nav == "MON HANGAR":
        hangar_page()

    elif st.session_state.menu_nav == "FLOTTE CORPO":
        corpo_fleet_page()
