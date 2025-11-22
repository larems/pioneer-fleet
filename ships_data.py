import os

# --- CONFIGURATION ---
ASSETS_DIR = "assets"
OUTPUT_FILE = "ships_data.py"

# --- ENCYCLOPÉDIE MASSIVE (Prix Mises à jour 2024/2025) ---
KNOWLEDGE_BASE = {
    # --- RSI ---
    "polaris": {"price": 750, "role": "Corvette", "brand": "RSI"},
    "perseus": {"price": 675, "role": "Gunship Lourd", "brand": "RSI"},
    "galaxy": {"price": 380, "role": "Modulaire", "brand": "RSI"},
    "orion": {"price": 650, "role": "Minage Capital", "brand": "RSI"},
    "arrastra": {"price": 575, "role": "Minage Capital", "brand": "RSI"},
    "phoenix": {"price": 350, "role": "Luxe", "brand": "RSI"},
    "aquila": {"price": 310, "role": "Exploration", "brand": "RSI"},
    "andromeda": {"price": 240, "role": "Gunship", "brand": "RSI"},
    "taurus": {"price": 190, "role": "Fret", "brand": "RSI"},
    "scorpius antares": {"price": 230, "role": "Guerre Elec.", "brand": "RSI"},
    "scorpius": {"price": 240, "role": "Chasseur Lourd", "brand": "RSI"},
    "mantis": {"price": 150, "role": "Interdiction", "brand": "RSI"},
    "apollo medivac": {"price": 275, "role": "Médical Blindé", "brand": "RSI"},
    "apollo": {"price": 250, "role": "Médical", "brand": "RSI"},
    "zeus mr": {"price": 190, "role": "Chasseur Primes", "brand": "RSI"},
    "zeus cl": {"price": 150, "role": "Fret Rapide", "brand": "RSI"},
    "zeus es": {"price": 150, "role": "Exploration", "brand": "RSI"},
    "zeus": {"price": 150, "role": "Polyvalent", "brand": "RSI"},
    "legionnaire": {"price": 120, "role": "Abordage", "brand": "Anvil"},
    "aurora ln": {"price": 40, "role": "Starter Combat", "brand": "RSI"},
    "aurora cl": {"price": 45, "role": "Starter Fret", "brand": "RSI"},
    "aurora lx": {"price": 35, "role": "Starter Luxe", "brand": "RSI"},
    "aurora es": {"price": 20, "role": "Starter", "brand": "RSI"},
    "aurora": {"price": 30, "role": "Starter", "brand": "RSI"},
    "ursa": {"price": 50, "role": "Rover", "brand": "RSI"},
    "lynx": {"price": 60, "role": "Rover Luxe", "brand": "RSI"},

    # --- ORIGIN ---
    "890": {"price": 950, "role": "Yacht Capital", "brand": "Origin"},
    "600i explorer": {"price": 475, "role": "Exploration Luxe", "brand": "Origin"},
    "600i touring": {"price": 435, "role": "Tourisme", "brand": "Origin"},
    "600i": {"price": 475, "role": "Exploration Luxe", "brand": "Origin"},
    "400i": {"price": 250, "role": "Exploration Luxe", "brand": "Origin"},
    "350r": {"price": 125, "role": "Course", "brand": "Origin"},
    "325a": {"price": 70, "role": "Combat", "brand": "Origin"},
    "315p": {"price": 65, "role": "Exploration", "brand": "Origin"},
    "300i": {"price": 60, "role": "Luxe", "brand": "Origin"},
    "135c": {"price": 65, "role": "Fret Léger", "brand": "Origin"},
    "125a": {"price": 60, "role": "Combat Léger", "brand": "Origin"},
    "100i": {"price": 50, "role": "Starter Luxe", "brand": "Origin"},
    "85x": {"price": 50, "role": "Snub Luxe", "brand": "Origin"},
    "m50": {"price": 100, "role": "Course", "brand": "Origin"},
    "x1": {"price": 45, "role": "Gravlev", "brand": "Origin"},
    "g12": {"price": 60, "role": "Rover", "brand": "Origin"},

    # --- AEGIS ---
    "javelin": {"price": 3000, "role": "Destroyer", "brand": "Aegis"},
    "idris": {"price": 1500, "role": "Frégate", "brand": "Aegis"},
    "hammerhead": {"price": 725, "role": "Corvette", "brand": "Aegis"},
    "nautilus": {"price": 725, "role": "Mineur", "brand": "Aegis"},
    "reclaimer": {"price": 400, "role": "Recyclage Lourd", "brand": "Aegis"},
    "redeemer": {"price": 330, "role": "Gunship", "brand": "Aegis"},
    "vanguard harbinger": {"price": 290, "role": "Bombardier", "brand": "Aegis"},
    "vanguard sentinel": {"price": 275, "role": "Guerre Elec.", "brand": "Aegis"},
    "vanguard hoplite": {"price": 235, "role": "Dropship", "brand": "Aegis"},
    "vanguard": {"price": 260, "role": "Chasseur Lourd", "brand": "Aegis"},
    "eclipse": {"price": 300, "role": "Bombardier Furtif", "brand": "Aegis"},
    "sabre raven": {"price": 200, "role": "Interdiction", "brand": "Aegis"},
    "sabre firebird": {"price": 185, "role": "Intercepteur", "brand": "Aegis"},
    "sabre": {"price": 170, "role": "Furtif", "brand": "Aegis"},
    "vulcan": {"price": 200, "role": "Réparation", "brand": "Aegis"},
    "gladius valiant": {"price": 110, "role": "Chasseur Léger", "brand": "Aegis"},
    "gladius": {"price": 90, "role": "Chasseur Léger", "brand": "Aegis"},
    "warlock": {"price": 85, "role": "EMP", "brand": "Aegis"},
    "stalker": {"price": 60, "role": "Chasseur Primes", "brand": "Aegis"},
    "titan renegade": {"price": 75, "role": "Combat", "brand": "Aegis"},
    "titan": {"price": 55, "role": "Fret Léger", "brand": "Aegis"},
    "avenger": {"price": 55, "role": "Fret Léger", "brand": "Aegis"},
    "retaliator": {"price": 175, "role": "Bombardier Lourd", "brand": "Aegis"},

    # --- CRUSADER ---
    "a2": {"price": 750, "role": "Bombardier", "brand": "Crusader"},
    "m2": {"price": 520, "role": "Transport Militaire", "brand": "Crusader"},
    "c2": {"price": 400, "role": "Fret Lourd", "brand": "Crusader"},
    "hercules": {"price": 400, "role": "Transport Lourd", "brand": "Crusader"},
    "mercury": {"price": 260, "role": "Données", "brand": "Crusader"},
    "msr": {"price": 260, "role": "Données", "brand": "Crusader"},
    "ion": {"price": 250, "role": "Anti-Capital", "brand": "Crusader"},
    "inferno": {"price": 250, "role": "Anti-Capital", "brand": "Crusader"},
    "ares": {"price": 250, "role": "Anti-Capital", "brand": "Crusader"},
    "spirit a1": {"price": 200, "role": "Bombardier", "brand": "Crusader"},
    "spirit e1": {"price": 150, "role": "VIP", "brand": "Crusader"},
    "spirit c1": {"price": 125, "role": "Fret Moyen", "brand": "Crusader"},
    "spirit": {"price": 125, "role": "Polyvalent", "brand": "Crusader"},
    "genesis": {"price": 400, "role": "Passagers", "brand": "Crusader"},

    # --- ANVIL ---
    "carrack": {"price": 600, "role": "Exploration", "brand": "Anvil"},
    "liberator": {"price": 575, "role": "Transport", "brand": "Anvil"},
    "valkyrie": {"price": 375, "role": "Dropship", "brand": "Anvil"},
    "crucible": {"price": 350, "role": "Réparation", "brand": "Anvil"},
    "f8c": {"price": 300, "role": "Chasseur Lourd", "brand": "Anvil"},
    "terrapin": {"price": 220, "role": "Exploration", "brand": "Anvil"},
    "hurricane": {"price": 195, "role": "Chasseur Lourd", "brand": "Anvil"},
    "super hornet": {"price": 180, "role": "Chasseur Moyen", "brand": "Anvil"},
    "heartseeker": {"price": 195, "role": "Chasseur Moyen", "brand": "Anvil"},
    "wildfire": {"price": 175, "role": "Chasseur Moyen", "brand": "Anvil"},
    "ghost": {"price": 125, "role": "Furtif", "brand": "Anvil"},
    "tracker": {"price": 140, "role": "Radar", "brand": "Anvil"},
    "hornet": {"price": 110, "role": "Chasseur Moyen", "brand": "Anvil"},
    "f7c": {"price": 110, "role": "Chasseur Moyen", "brand": "Anvil"},
    "f7a": {"price": 110, "role": "Chasseur Militaire", "brand": "Anvil"},
    "gladiator": {"price": 165, "role": "Bombardier", "brand": "Anvil"},
    "ballista": {"price": 140, "role": "DCA", "brand": "Anvil"},
    "centurion": {"price": 110, "role": "DCA", "brand": "Anvil"},
    "hawk": {"price": 100, "role": "Chasseur Primes", "brand": "Anvil"},
    "arrow": {"price": 75, "role": "Chasseur Léger", "brand": "Anvil"},
    "spartan": {"price": 80, "role": "Transport", "brand": "Anvil"},
    "pisces rescue": {"price": 65, "role": "Médical", "brand": "Anvil"},
    "c8r": {"price": 65, "role": "Médical", "brand": "Anvil"},
    "pisces": {"price": 45, "role": "Snub", "brand": "Anvil"},
    "c8": {"price": 45, "role": "Snub", "brand": "Anvil"},

    # --- DRAKE ---
    "kraken privateer": {"price": 2000, "role": "Marché Volant", "brand": "Drake"},
    "kraken": {"price": 1650, "role": "Porte-Vaisseaux", "brand": "Drake"},
    "ironclad assault": {"price": 535, "role": "Fret Blindé", "brand": "Drake"},
    "ironclad": {"price": 450, "role": "Fret Blindé", "brand": "Drake"},
    "caterpillar pirate": {"price": 330, "role": "Fret Lourd", "brand": "Drake"},
    "caterpillar": {"price": 330, "role": "Fret Lourd", "brand": "Drake"},
    "corsair": {"price": 250, "role": "Exploration", "brand": "Drake"},
    "vulture": {"price": 175, "role": "Recyclage", "brand": "Drake"},
    "cutlass steel": {"price": 235, "role": "Dropship", "brand": "Drake"},
    "cutlass blue": {"price": 175, "role": "Police", "brand": "Drake"},
    "cutlass red": {"price": 135, "role": "Médical", "brand": "Drake"},
    "cutlass black": {"price": 110, "role": "Polyvalent", "brand": "Drake"},
    "cutlass": {"price": 110, "role": "Polyvalent", "brand": "Drake"},
    "buccaneer": {"price": 110, "role": "Intercepteur", "brand": "Drake"},
    "herald": {"price": 85, "role": "Données", "brand": "Drake"},
    "cutter rambler": {"price": 50, "role": "Exploration", "brand": "Drake"},
    "cutter scout": {"price": 50, "role": "Eclaireur", "brand": "Drake"},
    "cutter": {"price": 45, "role": "Starter", "brand": "Drake"},
    "mule": {"price": 45, "role": "Fret Sol", "brand": "Drake"},
    "dragonfly": {"price": 40, "role": "Gravlev", "brand": "Drake"},

    # --- MISC ---
    "hull e": {"price": 750, "role": "Fret Capital", "brand": "MISC"},
    "hull d": {"price": 450, "role": "Fret Lourd", "brand": "MISC"},
    "hull c": {"price": 350, "role": "Fret Lourd", "brand": "MISC"},
    "hull b": {"price": 140, "role": "Fret Moyen", "brand": "MISC"},
    "hull a": {"price": 90, "role": "Fret Léger", "brand": "MISC"},
    "odyssey": {"price": 700, "role": "Exploration", "brand": "MISC"},
    "endeavor": {"price": 350, "role": "Science", "brand": "MISC"},
    "starfarer gemini": {"price": 340, "role": "Ravitaillement Militaire", "brand": "MISC"},
    "starfarer": {"price": 300, "role": "Ravitaillement", "brand": "MISC"},
    "freelancer mis": {"price": 175, "role": "Gunship", "brand": "MISC"},
    "freelancer max": {"price": 150, "role": "Fret Lourd", "brand": "MISC"},
    "freelancer dur": {"price": 135, "role": "Exploration", "brand": "MISC"},
    "freelancer": {"price": 110, "role": "Fret", "brand": "MISC"},
    "prospector": {"price": 155, "role": "Minage", "brand": "MISC"},
    "razor ex": {"price": 155, "role": "Furtif", "brand": "MISC"},
    "razor lx": {"price": 150, "role": "Course", "brand": "MISC"},
    "razor": {"price": 145, "role": "Course", "brand": "MISC"},
    "reliant tana": {"price": 75, "role": "Combat", "brand": "MISC"},
    "reliant mako": {"price": 95, "role": "News", "brand": "MISC"},
    "reliant sen": {"price": 85, "role": "Science", "brand": "MISC"},
    "reliant kore": {"price": 65, "role": "Starter", "brand": "MISC"},
    "reliant": {"price": 65, "role": "Starter", "brand": "MISC"},
    "expanse": {"price": 150, "role": "Raffinage", "brand": "MISC"},

    # --- ALIEN & EXOTIQUE (VANDUUL & CO) ---
    # Vanduul
    "stringer": {"price": 0, "role": "Chasseur Lourd", "brand": "Vanduul"}, # Ton fichier spécifique
    "stinger": {"price": 0, "role": "Chasseur Lourd", "brand": "Vanduul"},
    "scythe": {"price": 300, "role": "Chasseur Moyen", "brand": "Vanduul"},
    "glaive": {"price": 350, "role": "Chasseur Moyen", "brand": "Vanduul"},
    "blade": {"price": 275, "role": "Chasseur Léger", "brand": "Vanduul"},
    "void": {"price": 0, "role": "Bombardier", "brand": "Vanduul"},
    "kingship": {"price": 0, "role": "Capital", "brand": "Vanduul"},
    
    # Banu / Tevarin / Xi'an
    "merchantman": {"price": 650, "role": "Commerce Alien", "brand": "Banu"},
    "defender": {"price": 220, "role": "Chasseur Alien", "brand": "Banu"},
    "prowler": {"price": 440, "role": "Dropship", "brand": "Tevarin"},
    "talon shrike": {"price": 115, "role": "Chasseur Alien", "brand": "Tevarin"},
    "talon": {"price": 115, "role": "Chasseur Alien", "brand": "Tevarin"},
    "santok": {"price": 220, "role": "Chasseur Alien", "brand": "Aopoa"},
    "khartu": {"price": 170, "role": "Eclaireur", "brand": "Aopoa"},
    "nox": {"price": 45, "role": "Gravlev", "brand": "Aopoa"},
    "railen": {"price": 225, "role": "Fret Alien", "brand": "Gatac"},
    "syulen": {"price": 70, "role": "Starter Alien", "brand": "Gatac"},
    
    # --- CNOU / ARGO / GREYCAT / MIRAI ---
    "pioneer": {"price": 850, "role": "Construction", "brand": "CNOU"},
    "nomad": {"price": 80, "role": "Starter Avancé", "brand": "CNOU"},
    "mustang delta": {"price": 65, "role": "Combat", "brand": "CNOU"},
    "mustang gamma": {"price": 55, "role": "Course", "brand": "CNOU"},
    "mustang beta": {"price": 40, "role": "Exploration", "brand": "CNOU"},
    "mustang alpha": {"price": 30, "role": "Starter", "brand": "CNOU"},
    "mustang": {"price": 30, "role": "Starter", "brand": "CNOU"},
    "mole": {"price": 315, "role": "Minage", "brand": "ARGO"},
    "srv": {"price": 150, "role": "Remorquage", "brand": "ARGO"},
    "raft": {"price": 125, "role": "Fret", "brand": "ARGO"},
    "mpuv": {"price": 40, "role": "Utilitaire", "brand": "ARGO"},
    "argo": {"price": 40, "role": "Utilitaire", "brand": "ARGO"},
    "roc ds": {"price": 75, "role": "Minage Sol", "brand": "Greycat"},
    "roc": {"price": 55, "role": "Minage Sol", "brand": "Greycat"},
    "stv": {"price": 40, "role": "Véhicule", "brand": "Greycat"},
    "ptv": {"price": 15, "role": "Buggy", "brand": "Greycat"},
    "fury lx": {"price": 55, "role": "Course", "brand": "Mirai"},
    "fury mx": {"price": 55, "role": "Bombardier", "brand": "Mirai"},
    "fury": {"price": 55, "role": "Snub", "brand": "Mirai"},
    "pulse": {"price": 30, "role": "Gravlev", "brand": "Mirai"},
}

def format_ship_name(raw_name):
    UPPER_WORDS = ["ii", "iii", "iv", "vi", "cl", "es", "mr", "ln", "lx", "ex", "zx", "msr", "mis", "max", "dur", "f7c", "f7a", "f8c", "c8", "c8r", "c8x", "g12", "g12a", "mpuv", "srv", "ptv", "stv", "roc", "ds", "c2", "m2", "a2", "c1", "a1", "e1", "85x", "300i", "315p", "325a", "350r", "400i", "600i", "890", "100i", "125a", "135c", "a1", "e1"]
    clean = raw_name.replace("_", " ").replace("-", " ")
    words = clean.split()
    formatted_words = []
    for w in words:
        if w.lower() in UPPER_WORDS:
            formatted_words.append(w.upper())
        elif w.lower() == "mk":
            formatted_words.append("Mk")
        else:
            formatted_words.append(w.capitalize())
    return " ".join(formatted_words)

def generate_ships_data():
    if not os.path.exists(ASSETS_DIR):
        print(f"❌ Erreur : Dossier '{ASSETS_DIR}' introuvable.")
        return

    files = [f for f in os.listdir(ASSETS_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    files.sort()

    print(f"📂 Analyse de {len(files)} fichiers...")
    error_count = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# ships_data.py\n# AUTO-GENERATED\n\nSHIPS_DB = {\n")

        for filename in files:
            raw_name = os.path.splitext(filename)[0]
            display_name = format_ship_name(raw_name)
            search_key = raw_name.replace("_", " ").lower()
            
            price = 0
            role = "Autre"
            brand = "Inconnu"
            found = False

            # 1. Recherche Exacte
            if search_key in KNOWLEDGE_BASE:
                data = KNOWLEDGE_BASE[search_key]
                price, role, brand = data['price'], data['role'], data['brand']
                found = True
            
            # 2. Recherche Partielle
            if not found:
                for key, data in KNOWLEDGE_BASE.items():
                    if key in search_key.split():
                        price, role, brand = data['price'], data['role'], data['brand']
                        found = True
                        break
            
            if not found:
                # Dernier recours : recherche de sous-chaîne
                for key, data in KNOWLEDGE_BASE.items():
                    if key in search_key:
                        price, role, brand = data['price'], data['role'], data['brand']
                        found = True
                        break

            # 3. Fallback Marque si toujours Inconnu
            if brand == "Inconnu":
                error_count += 1
                print(f"⚠️ ATTENTION : Vaisseau non reconnu '{filename}'. Prix mis à 0.")
                if "rsi" in search_key: brand = "RSI"
                elif "drake" in search_key: brand = "Drake"
                elif "aegis" in search_key: brand = "Aegis"
                elif "anvil" in search_key: brand = "Anvil"
                elif "origin" in search_key: brand = "Origin"
                elif "crusader" in search_key: brand = "Crusader"
                elif "misc" in search_key: brand = "MISC"
                elif "argo" in search_key: brand = "ARGO"
                elif "banu" in search_key: brand = "Banu"
                elif "gatac" in search_key: brand = "Gatac"
                elif "mirai" in search_key: brand = "Mirai"
                elif "vanduul" in search_key or "scythe" in search_key or "stringer" in search_key: brand = "Vanduul"

            line = f'    "{display_name}": {{"price": {price}, "role": "{role}", "brand": "{brand}", "img": "{ASSETS_DIR}/{filename}"}},\n'
            f.write(line)

        f.write("}\n")
    
    print(f"✅ Terminé !")
    if error_count > 0:
        print(f"⚠️ Il y a {error_count} vaisseaux dont le prix est à 0. Vérifie les noms de fichiers.")

if __name__ == "__main__":
    generate_ships_data()
