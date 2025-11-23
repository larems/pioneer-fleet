# ships_data.py
import json
from typing import Dict, Any

# --- 1. BASE DE CONNAISSANCE UNIFIÉE (Prix, Rôle, Image locale) ---
# NOTE: Le statut 'ingame' est forcé à True ici pour assurer l'affichage dans l'onglet INGAME/aUEC.
# Les prix aUEC réels sont mis à jour pour le C1 Spirit (3.2M) et A1 Spirit (3.8M).
BASE_CATALOG_DATA = {
    "100i": {"price": 50, "role": "Starter Luxe", "brand": "Origin", "ingame": True, "auec_price": 700000, "img": "assets/100i.webp", "crew_max": 1},
    "125a": {"price": 60, "role": "Combat Léger", "brand": "Origin", "ingame": True, "auec_price": 800000, "img": "assets/125a.webp", "crew_max": 1},
    "135c": {"price": 65, "role": "Fret Léger", "brand": "Origin", "ingame": True, "auec_price": 900000, "img": "assets/135c.webp", "crew_max": 1},
    "300i": {"price": 60, "role": "Luxe", "brand": "Origin", "ingame": True, "auec_price": 850000, "img": "assets/300i.webp", "crew_max": 1},
    "315p": {"price": 65, "role": "Exploration", "brand": "Origin", "ingame": True, "auec_price": 950000, "img": "assets/315p.webp", "crew_max": 1},
    "325a": {"price": 70, "role": "Combat", "brand": "Origin", "ingame": True, "auec_price": 1100000, "img": "assets/325a.webp", "crew_max": 1},
    "350r": {"price": 125, "role": "Course", "brand": "Origin", "ingame": True, "auec_price": 1600000, "img": "assets/350r.webp", "crew_max": 1},
    "400i": {"price": 250, "role": "Exploration Luxe", "brand": "Origin", "ingame": True, "auec_price": 5000000, "img": "assets/400i.webp", "crew_max": 2},
    "600i Explorer": {"price": 475, "role": "Exploration Luxe", "brand": "Origin", "ingame": True, "auec_price": 12500000, "img": "assets/600i explorer.webp", "crew_max": 3},
    "600i Touring": {"price": 475, "role": "Exploration Luxe", "brand": "Origin", "ingame": True, "auec_price": 12500000, "img": "assets/600i touring.webp", "crew_max": 3},
    "85x": {"price": 50, "role": "Snub Luxe", "brand": "Origin", "ingame": True, "auec_price": 450000, "img": "assets/85X.webp", "crew_max": 2},
    "890 Jump": {"price": 950, "role": "Yacht Capital", "brand": "Origin", "ingame": True, "auec_price": 0, "img": "assets/890 jump.webp", "crew_max": 5},
    "C2 Hercules": {"price": 400, "role": "Fret Lourd", "brand": "Crusader", "ingame": True, "auec_price": 6250000, "img": "assets/C2 hercules.webp", "crew_max": 2},
    "Carrack W C8X": {"price": 600, "role": "Exploration", "brand": "Anvil", "ingame": True, "auec_price": 26000000, "img": "assets/Carrack w c8x.webp", "crew_max": 5},
    "Clipper": {"price": 150, "role": "Fret Léger", "brand": "MISC", "ingame": True, "auec_price": 600000, "img": "assets/Clipper.webp", "crew_max": 1},
    "Constellation Andromeda": {"price": 240, "role": "Polyvalent", "brand": "RSI", "ingame": True, "auec_price": 4000000, "img": "assets/Constellation Andromeda.webp", "crew_max": 4},
    "Golemx OX": {"price": 60, "role": "Minage", "brand": "Drake", "ingame": True, "auec_price": 0, "img": "assets/Golemx OX.webp", "crew_max": 2},
    "A1 Spirit": {"price": 125, "role": "Bombardier Léger", "brand": "Crusader", "ingame": True, "auec_price": 3800000, "img": "assets/a1 spirit.webp", "crew_max": 1},
    "A2 Hercules": {"price": 750, "role": "Bombardier", "brand": "Crusader", "ingame": True, "auec_price": 15000000, "img": "assets/a2 hercules.webp", "crew_max": 4},
    "Anvil Ballista Dunestalker": {"price": 140, "role": "DCA", "brand": "Anvil", "ingame": True, "auec_price": 1900000, "img": "assets/anvil ballista dunestalker.webp", "crew_max": 2},
    "Anvil Ballista Snowblind": {"price": 140, "role": "DCA", "brand": "Anvil", "ingame": True, "auec_price": 1900000, "img": "assets/anvil ballista snowblind.webp", "crew_max": 2},
    "Apollo Medivac": {"price": 250, "role": "Médical", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/apollo medivac.webp", "crew_max": 3},
    "Apollo Triage": {"price": 250, "role": "Médical", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/apollo triage.webp", "crew_max": 3},
    "Ares Inferno": {"price": 250, "role": "Anti-Capital", "brand": "Crusader", "ingame": True, "auec_price": 3800000, "img": "assets/ares inferno.webp", "crew_max": 1},
    "Ares Ion": {"price": 250, "role": "Anti-Capital", "brand": "Crusader", "ingame": True, "auec_price": 3800000, "img": "assets/ares ion.webp", "crew_max": 1},
    "Argo Mole Carbon Edition": {"price": 315, "role": "Minage", "brand": "ARGO", "ingame": True, "auec_price": 5000000, "img": "assets/argo mole carbon edition.webp", "crew_max": 4},
    "Argo Mole Talus Edition": {"price": 315, "role": "Minage", "brand": "ARGO", "ingame": True, "auec_price": 5000000, "img": "assets/argo mole talus edition.webp", "crew_max": 4},
    "Arrastra": {"price": 575, "role": "Minage Capital", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/arrastra.webp", "crew_max": 5},
    "Arrow": {"price": 75, "role": "Chasseur Léger", "brand": "Anvil", "ingame": True, "auec_price": 1050000, "img": "assets/arrow.webp", "crew_max": 1},
    "Asgard": {"price": 350, "role": "Dropship / Combat", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/asgard.webp", "crew_max": 4},
    "Atls Geo": {"price": 40, "role": "Exosquelette", "brand": "ARGO", "ingame": True, "auec_price": 0, "img": "assets/atls geo.webp", "crew_max": 1},
    "Atls": {"price": 40, "role": "Exosquelette", "brand": "ARGO", "ingame": True, "auec_price": 0, "img": "assets/atls.webp", "crew_max": 1},
    "Aurora CL": {"price": 45, "role": "Fret Léger", "brand": "RSI", "ingame": True, "auec_price": 350000, "img": "assets/aurora cl.webp", "crew_max": 1},
    "Aurora ES": {"price": 20, "role": "Starter", "brand": "RSI", "ingame": True, "auec_price": 300000, "img": "assets/aurora es.webp", "crew_max": 1},
    "Aurora LN": {"price": 35, "role": "Combat Léger", "brand": "RSI", "ingame": True, "auec_price": 350000, "img": "assets/aurora ln.webp", "crew_max": 1},
    "Aurora LX": {"price": 25, "role": "Luxe Léger", "brand": "RSI", "ingame": True, "auec_price": 320000, "img": "assets/aurora lx.webp", "crew_max": 1},
    "Aurora MR": {"price": 25, "role": "Starter", "brand": "RSI", "ingame": True, "auec_price": 300000, "img": "assets/aurora mr.webp", "crew_max": 1},
    "Avenger Stalker": {"price": 75, "role": "Chasseur Primes", "brand": "Aegis", "ingame": True, "auec_price": 900000, "img": "assets/avenger stalker.webp", "crew_max": 1},
    "Avenger Titan Renegade": {"price": 65, "role": "Polyvalent", "brand": "Aegis", "ingame": True, "auec_price": 800000, "img": "assets/avenger titan renegade.webp", "crew_max": 1},
    "Avenger Titan": {"price": 55, "role": "Fret Léger", "brand": "Aegis", "ingame": True, "auec_price": 800000, "img": "assets/avenger titan.webp", "crew_max": 1},
    "Avenger Warlock": {"price": 85, "role": "EMP", "brand": "Aegis", "ingame": True, "auec_price": 1800000, "img": "assets/avenger warlock.webp", "crew_max": 1},
    "Ballista": {"price": 140, "role": "DCA", "brand": "Anvil", "ingame": True, "auec_price": 1900000, "img": "assets/ballista.webp", "crew_max": 2},
    "Blade": {"price": 275, "role": "Chasseur Léger", "brand": "Vanduul", "ingame": True, "auec_price": 0, "img": "assets/blade.webp", "crew_max": 1},
    "Buccaneer": {"price": 110, "role": "Intercepteur", "brand": "Drake", "ingame": True, "auec_price": 1450000, "img": "assets/buccaneer.webp", "crew_max": 1},
    "C1 Spirit": {"price": 125, "role": "Fret Rapide", "brand": "Crusader", "ingame": True, "auec_price": 3200000, "img": "assets/c1 spirit.webp", "crew_max": 1}, 
    "C8 Pisces": {"price": 40, "role": "Snub", "brand": "Anvil", "ingame": True, "auec_price": 350000, "img": "assets/c8 pisces.webp", "crew_max": 1},
    "C8R Pisces": {"price": 60, "role": "Médical Snub", "brand": "Anvil", "ingame": True, "auec_price": 350000, "img": "assets/c8r pisces.webp", "crew_max": 1},
    "C8X Pisces Expedition": {"price": 45, "role": "Exploration Snub", "brand": "Anvil", "ingame": True, "auec_price": 350000, "img": "assets/c8x pisces expedition.webp", "crew_max": 1},
    "Carrack Expedition W C8X": {"price": 600, "role": "Exploration", "brand": "Anvil", "ingame": True, "auec_price": 26000000, "img": "assets/Carrack w c8x.webp", "crew_max": 5},
    "Carrack Expedition": {"price": 600, "role": "Exploration", "brand": "Anvil", "ingame": True, "auec_price": 26000000, "img": "assets/carrack expedition.webp", "crew_max": 5},
    "Carrack": {"price": 600, "role": "Exploration", "brand": "Anvil", "ingame": True, "auec_price": 26000000, "img": "assets/carrack.webp", "crew_max": 5},
    "Carterpillar Best In Show Edition 2949": {"price": 330, "role": "Fret Lourd", "brand": "Drake", "ingame": True, "auec_price": 4650000, "img": "assets/carterpillar best in show edition 2949.webp", "crew_max": 4},
    "Caterpillar Pirate Edition": {"price": 330, "role": "Fret Lourd", "brand": "Drake", "ingame": True, "auec_price": 4650000, "img": "assets/caterpillar pirate edition.webp", "crew_max": 4},
    "Caterpillar": {"price": 330, "role": "Fret Lourd", "brand": "Drake", "ingame": True, "auec_price": 4650000, "img": "assets/caterpillar.webp", "crew_max": 4},
    "Centurion": {"price": 110, "role": "DCA", "brand": "Anvil", "ingame": True, "auec_price": 1400000, "img": "assets/centurion.webp", "crew_max": 2},
    "Constellation Phoenix Emerald": {"price": 350, "role": "Luxe", "brand": "RSI", "ingame": True, "auec_price": 6500000, "img": "assets/constellation phoenix emerald.webp", "crew_max": 4},
    "Constellation Phoenix": {"price": 350, "role": "Luxe", "brand": "RSI", "ingame": True, "auec_price": 6500000, "img": "assets/constellation phoenix.webp", "crew_max": 4},
    "Corsair": {"price": 250, "role": "Exploration", "brand": "Drake", "ingame": True, "auec_price": 5000000, "img": "assets/corsair.webp", "crew_max": 3},
    "Cosntellation Taurus": {"price": 190, "role": "Fret", "brand": "RSI", "ingame": True, "auec_price": 3200000, "img": "assets/cosntellation taurus.webp", "crew_max": 2},
    "Crucible": {"price": 350, "role": "Réparation", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/crucible.webp", "crew_max": 4},
    "CSV SM": {"price": 45, "role": "Autre", "brand": "Argo", "ingame": True, "auec_price": 30000, "img": "assets/csv-sm.webp", "crew_max": 1},
    "Cutlass Black Best In Show Edition 2949": {"price": 110, "role": "Polyvalent", "brand": "Drake", "ingame": True, "auec_price": 1380000, "img": "assets/cutlass black best in show edition 2949.webp", "crew_max": 2},
    "Cutlass Black": {"price": 110, "role": "Polyvalent", "brand": "Drake", "ingame": True, "auec_price": 1380000, "img": "assets/cutlass black.webp", "crew_max": 2},
    "Cutlass Blue": {"price": 150, "role": "Patrouille", "brand": "Drake", "ingame": True, "auec_price": 2500000, "img": "assets/cutlass blue.webp", "crew_max": 2},
    "Cutlass Red": {"price": 135, "role": "Médical", "brand": "Drake", "ingame": True, "auec_price": 1700000, "img": "assets/cutlass red.webp", "crew_max": 2},
    "Cutlass Steel": {"price": 235, "role": "Dropship", "brand": "Drake", "ingame": True, "auec_price": 3700000, "img": "assets/cutlass steel.webp", "crew_max": 4},
    "Cutter Rambler": {"price": 50, "role": "Exploration Starter", "brand": "Drake", "ingame": True, "auec_price": 500000, "img": "assets/cutter rambler.webp", "crew_max": 1},
    "Cutter Scout": {"price": 50, "role": "Eclaireur Starter", "brand": "Drake", "ingame": True, "auec_price": 500000, "img": "assets/cutter scout.webp", "crew_max": 1},
    "Cutter": {"price": 45, "role": "Starter", "brand": "Drake", "ingame": True, "auec_price": 500000, "img": "assets/cutter.webp", "crew_max": 1},
    "Cyclone AA": {"price": 55, "role": "DCA Sol", "brand": "Tumbril", "ingame": True, "auec_price": 190000, "img": "assets/cyclone aa.webp", "crew_max": 2},
    "Cyclone MT": {"price": 50, "role": "Combat Léger Sol", "brand": "Tumbril", "ingame": True, "auec_price": 190000, "img": "assets/cyclone mt.webp", "crew_max": 2},
    "Cyclone RC": {"price": 40, "role": "Course Sol", "brand": "Tumbril", "ingame": True, "auec_price": 190000, "img": "assets/cyclone rc.webp", "crew_max": 1},
    "Cyclone RN": {"price": 45, "role": "Eclaireur Sol", "brand": "Tumbril", "ingame": True, "auec_price": 190000, "img": "assets/cyclone rn.webp", "crew_max": 2},
    "Cyclone TR": {"price": 40, "role": "Combat Sol", "brand": "Tumbril", "ingame": True, "auec_price": 190000, "img": "assets/cyclone tr.webp", "crew_max": 2},
    "Cyclone": {"price": 28, "role": "Véhicule", "brand": "Tumbril", "ingame": True, "auec_price": 190000, "img": "assets/cyclone.webp", "crew_max": 2},
    "Defender": {"price": 220, "role": "Chasseur Alien", "brand": "Banu", "ingame": True, "auec_price": 3600000, "img": "assets/defender.webp", "crew_max": 2},
    "Dragonfly Black": {"price": 40, "role": "Gravlev", "brand": "Drake", "ingame": True, "auec_price": 150000, "img": "assets/dragonfly black.webp", "crew_max": 2},
    "Dragonfly Yellowjacket": {"price": 40, "role": "Gravlev", "brand": "Drake", "ingame": True, "auec_price": 150000, "img": "assets/dragonfly yellowjacket.webp", "crew_max": 2},
    "E1 Spirit": {"price": 150, "role": "Luxe / Transport", "brand": "Crusader", "ingame": True, "auec_price": 0, "img": "assets/e1 spirit.webp", "crew_max": 1}, 
    "Eclipse": {"price": 300, "role": "Bombardier Furtif", "brand": "Aegis", "ingame": True, "auec_price": 6000000, "img": "assets/eclipse.webp", "crew_max": 1},
    "Endeavor": {"price": 350, "role": "Science", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/endeavor.webp", "crew_max": 4},
    "Expanse": {"price": 150, "role": "Raffinage", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/expanse.webp", "crew_max": 1},
    "F7A Hornet Mk I": {"price": 110, "role": "Militaire", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7a hornet mk i.webp", "crew_max": 1},
    "F7A Hornet Mk II": {"price": 110, "role": "Militaire", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7a hornet mk ii.webp", "crew_max": 1},
    "F7C Honrnet Mk II": {"price": 175, "role": "Chasseur Moyen", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7c honrnet mk II.webp", "crew_max": 1},
    "F7C Hornet Mk I": {"price": 110, "role": "Chasseur Moyen", "brand": "Anvil", "ingame": True, "auec_price": 1500000, "img": "assets/f7c hornet mk I.webp", "crew_max": 1},
    "F7C Hornet Wildfire Mk I": {"price": 120, "role": "Chasseur Spé.", "brand": "Anvil", "ingame": True, "auec_price": 1600000, "img": "assets/f7c hornet wildfire mk i.webp", "crew_max": 1},
    "F7C M Super Hornet Heartseeker Mk I": {"price": 180, "role": "Autre", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7c-m super hornet heartseeker mk i.webp", "crew_max": 1},
    "F7C M Super Hornet Mk I": {"price": 200, "role": "Autre", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7c-m super hornet mk i.webp", "crew_max": 1},
    "F7C M Super Hornet Mk II": {"price": 240, "role": "Autre", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7c-m super hornet mk ii.webp", "crew_max": 1},
    "F7C R Hornet Tracker Mk I": {"price": 150, "role": "Autre", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7c-r hornet tracker mk I.webp", "crew_max": 1},
    "F7C R Hornet Tracker Mk II": {"price": 185, "role": "Autre", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7c-r hornet tracker mk II.webp", "crew_max": 1},
    "F7C S Hornet Ghost Mk I": {"price": 140, "role": "Autre", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7c-s hornet ghost mk i.webp", "crew_max": 1},
    "F7C S Hornet Ghost Mk II": {"price": 185, "role": "Autre", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f7c-s hornet ghost mk ii.webp", "crew_max": 1},
    "F8C Lightning Executive Edition": {"price": 300, "role": "Chasseur Lourd", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f8c lightning executive edition.webp", "crew_max": 1},
    "F8C Lightning": {"price": 300, "role": "Chasseur Lourd", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/f8c lightning.webp", "crew_max": 1},
    "Fortune": {"price": 175, "role": "Recyclage / Indus", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/fortune.webp", "crew_max": 2},
    "Freelancer DUR": {"price": 135, "role": "Exploration", "brand": "MISC", "ingame": True, "auec_price": 1300000, "img": "assets/freelancer dur.webp", "crew_max": 2},
    "Freelancer MAX": {"price": 150, "role": "Fret Lourd", "brand": "MISC", "ingame": True, "auec_price": 1300000, "img": "assets/freelancer max.webp", "crew_max": 2},
    "Freelancer MIS": {"price": 175, "role": "Militaire", "brand": "MISC", "ingame": True, "auec_price": 1300000, "img": "assets/freelancer mis.webp", "crew_max": 2},
    "Freelancer": {"price": 110, "role": "Fret", "brand": "MISC", "ingame": True, "auec_price": 1300000, "img": "assets/freelancer.webp", "crew_max": 2},
    "Fury LX": {"price": 60, "role": "Course Snub", "brand": "Mirai", "ingame": True, "auec_price": 0, "img": "assets/fury lx.webp", "crew_max": 1},
    "Fury MX": {"price": 65, "role": "Combat Snub", "brand": "Mirai", "ingame": True, "auec_price": 0, "img": "assets/fury mx.webp", "crew_max": 1},
    "Fury": {"price": 55, "role": "Snub", "brand": "Mirai", "ingame": True, "auec_price": 0, "img": "assets/fury.webp", "crew_max": 1},
    "G12": {"price": 40, "role": "Véhicule", "brand": "Origin", "ingame": True, "auec_price": 0, "img": "assets/g12.webp", "crew_max": 2},
    "G12A": {"price": 45, "role": "Véhicule", "brand": "Origin", "ingame": True, "auec_price": 0, "img": "assets/g12a.webp", "crew_max": 2},
    "G12r": {"price": 45, "role": "Véhicule", "brand": "Origin", "ingame": True, "auec_price": 0, "img": "assets/g12r.webp", "crew_max": 2},
    "Galaxy": {"price": 380, "role": "Modulaire", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/galaxy.webp", "crew_max": 4},
    "Genesis": {"price": 400, "role": "Passagers", "brand": "Crusader", "ingame": True, "auec_price": 0, "img": "assets/genesis.webp", "crew_max": 4},
    "Gladiator": {"price": 165, "role": "Bombardier", "brand": "Anvil", "ingame": True, "auec_price": 2500000, "img": "assets/gladiator.webp", "crew_max": 2},
    "Gladius Pirate Edition": {"price": 100, "role": "Chasseur Léger", "brand": "Aegis", "ingame": True, "auec_price": 1250000, "img": "assets/gladius pirate edition.webp", "crew_max": 1},
    "Gladius Valiant": {"price": 95, "role": "Chasseur Léger", "brand": "Aegis", "ingame": True, "auec_price": 1250000, "img": "assets/gladius valiant.webp", "crew_max": 1},
    "Gladius": {"price": 90, "role": "Chasseur Léger", "brand": "Aegis", "ingame": True, "auec_price": 1250000, "img": "assets/gladius.webp", "crew_max": 1},
    "Glaive": {"price": 350, "role": "Chasseur Moyen", "brand": "Vanduul", "ingame": True, "auec_price": 0, "img": "assets/glaive.webp", "crew_max": 2},
    "Golem": {"price": 60, "role": "Minage", "brand": "Drake", "ingame": True, "auec_price": 0, "img": "assets/golem.webp", "crew_max": 2},
    "Guardian MX": {"price": 225, "role": "Chasseur Lourd", "brand": "Mirai", "ingame": True, "auec_price": 0, "img": "assets/guardian mx.webp", "crew_max": 1},
    "Guardian QI": {"price": 225, "role": "Chasseur Lourd", "brand": "Mirai", "ingame": True, "auec_price": 0, "img": "assets/guardian qi.webp", "crew_max": 1},
    "Guardian": {"price": 225, "role": "Chasseur Lourd", "brand": "Mirai", "ingame": True, "auec_price": 0, "img": "assets/guardian.webp", "crew_max": 1},
    "Hammerhead Best In Show Edition 2949": {"price": 725, "role": "Corvette", "brand": "Aegis", "ingame": True, "auec_price": 17500000, "img": "assets/hammerhead best in show edition 2949.webp", "crew_max": 6},
    "Hammerhead": {"price": 725, "role": "Corvette", "brand": "Aegis", "ingame": True, "auec_price": 17500000, "img": "assets/hammerhead.webp", "crew_max": 6},
    "Hawk": {"price": 100, "role": "Chasseur Primes", "brand": "Anvil", "ingame": True, "auec_price": 1300000, "img": "assets/hawk.webp", "crew_max": 1},
    "Herarld": {"price": 85, "role": "Données", "brand": "Drake", "ingame": True, "auec_price": 1130000, "img": "assets/herarld.webp", "crew_max": 1},
    "Hoverquad": {"price": 30, "role": "Gravlev", "brand": "CNOU", "ingame": True, "auec_price": 140000, "img": "assets/hoverquad.webp", "crew_max": 1},
    "Hull A": {"price": 90, "role": "Fret Léger", "brand": "MISC", "ingame": True, "auec_price": 1150000, "img": "assets/hull a.webp", "crew_max": 1},
    "Hull B": {"price": 140, "role": "Fret Moyen", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/hull b.webp", "crew_max": 2},
    "Hull D": {"price": 450, "role": "Fret Lourd", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/hull d.webp", "crew_max": 3},
    "Hull E": {"price": 750, "role": "Fret Capital", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/hull e.webp", "crew_max": 3},
    "Hullc": {"price": 350, "role": "Fret Lourd", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/hullc.webp", "crew_max": 3},
    "Hurricane": {"price": 195, "role": "Chasseur Lourd", "brand": "Anvil", "ingame": True, "auec_price": 3000000, "img": "assets/hurricane.webp", "crew_max": 2},
    "Idris M": {"price": 1500, "role": "Frégate Militaire", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/idris-m.webp", "crew_max": 8},
    "Idris P": {"price": 1500, "role": "Frégate", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/idris-p.webp", "crew_max": 8},
    "Intrepid": {"price": 65, "role": "Fret Léger", "brand": "Crusader", "ingame": True, "auec_price": 0, "img": "assets/intrepid.webp", "crew_max": 1},
    "Ironclad Assault": {"price": 450, "role": "Fret Blindé", "brand": "Drake", "ingame": True, "auec_price": 0, "img": "assets/ironclad assault.webp", "crew_max": 3},
    "Ironclad": {"price": 450, "role": "Fret Blindé", "brand": "Drake", "ingame": True, "auec_price": 0, "img": "assets/ironclad.webp", "crew_max": 3},
    "Javelin": {"price": 3000, "role": "Destroyer", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/javelin.webp", "crew_max": 15},
    "Khartu Ai": {"price": 175, "role": "Autre", "brand": "Alien", "ingame": True, "auec_price": 2800000, "img": "assets/khartu-AI.webp", "crew_max": 1},
    "Kraken Privateer": {"price": 1650, "role": "Porte-Vaisseaux", "brand": "Drake", "ingame": True, "auec_price": 0, "img": "assets/kraken privateer.webp", "crew_max": 7},
    "Kraken": {"price": 1650, "role": "Porte-Vaisseaux", "brand": "Drake", "ingame": True, "auec_price": 0, "img": "assets/kraken.webp", "crew_max": 7},
    "L 21 Wolf": {"price": 100, "role": "Autre", "brand": "Kruger", "ingame": True, "auec_price": 60000, "img": "assets/l-21 wolf.webp", "crew_max": 1},
    "Legionnaire": {"price": 120, "role": "Abordage", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/legionnaire.webp", "crew_max": 2},
    "Liberator": {"price": 575, "role": "Transport", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/liberator.webp", "crew_max": 4},
    "Lynx": {"price": 60, "role": "Rover Luxe", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/lynx.webp", "crew_max": 4},
    "M2 Hercules": {"price": 520, "role": "Transport Militaire", "brand": "Crusader", "ingame": True, "auec_price": 10500000, "img": "assets/m2 hercules.webp", "crew_max": 3},
    "M50": {"price": 100, "role": "Course", "brand": "Origin", "ingame": True, "auec_price": 1400000, "img": "assets/m50.webp", "crew_max": 1},
    "Mantis": {"price": 150, "role": "Interdiction", "brand": "RSI", "ingame": True, "auec_price": 2250000, "img": "assets/mantis.webp", "crew_max": 2},
    "Merchantman": {"price": 650, "role": "Commerce Alien", "brand": "Banu", "ingame": True, "auec_price": 0, "img": "assets/merchantman.webp", "crew_max": 4},
    "Mercury": {"price": 260, "role": "Données", "brand": "Crusader", "ingame": True, "auec_price": 4500000, "img": "assets/mercury.webp", "crew_max": 2},
    "Meteor": {"price": 260, "role": "Chasseur Moyen", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/meteor.webp", "crew_max": 1},
    "Mole": {"price": 315, "role": "Minage", "brand": "ARGO", "ingame": True, "auec_price": 5000000, "img": "assets/mole.webp", "crew_max": 3},
    "MPUV Cargo": {"price": 40, "role": "Utilitaire", "brand": "ARGO", "ingame": True, "auec_price": 30000, "img": "assets/mpuv cargo.webp", "crew_max": 1},
    "MPUV Personnel": {"price": 40, "role": "Transport", "brand": "ARGO", "ingame": True, "auec_price": 50000, "img": "assets/mpuv personnel.webp", "crew_max": 1},
    "MPUV Tractor": {"price": 40, "role": "Manutention", "brand": "ARGO", "ingame": True, "auec_price": 55000, "img": "assets/mpuv tractor.webp", "crew_max": 1},
    "Mtc": {"price": 50, "role": "Combat Sol", "brand": "Greycat", "ingame": True, "auec_price": 45000, "img": "assets/mtc.webp", "crew_max": 1},
    "Mule": {"price": 45, "role": "Fret Sol", "brand": "Drake", "ingame": True, "auec_price": 35000, "img": "assets/mule.webp", "crew_max": 1},
    "Mustang Alpha Vindicator": {"price": 30, "role": "Starter", "brand": "CNOU", "ingame": True, "auec_price": 350000, "img": "assets/mustang alpha vindicator.webp", "crew_max": 1},
    "Mustang Alpha": {"price": 30, "role": "Starter", "brand": "CNOU", "ingame": True, "auec_price": 350000, "img": "assets/mustang alpha.webp", "crew_max": 1},
    "Mustang Beta": {"price": 40, "role": "Exploration Starter", "brand": "CNOU", "ingame": True, "auec_price": 450000, "img": "assets/mustang beta.webp", "crew_max": 1},
    "Mustang Delta": {"price": 65, "role": "Combat Léger", "brand": "CNOU", "ingame": True, "auec_price": 950000, "img": "assets/mustang delta.webp", "crew_max": 1},
    "Mustang Gamma": {"price": 55, "role": "Course", "brand": "CNOU", "ingame": True, "auec_price": 650000, "img": "assets/mustang gamma.webp", "crew_max": 1},
    "Mustang Omega": {"price": 40, "role": "Course", "brand": "CNOU", "ingame": True, "auec_price": 0, "img": "assets/mustang omega.webp", "crew_max": 1},
    "Nautilius": {"price": 725, "role": "Mineur", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/nautilius.webp", "crew_max": 5},
    "Nautilus Solstice Edition": {"price": 725, "role": "Mineur", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/nautilus solstice edition.webp", "crew_max": 5},
    "Nomad": {"price": 80, "role": "Starter Avancé", "brand": "CNOU", "ingame": True, "auec_price": 1050000, "img": "assets/nomad.webp", "crew_max": 1},
    "Nova": {"price": 120, "role": "Char", "brand": "Tumbril", "ingame": True, "auec_price": 2200000, "img": "assets/nova.webp", "crew_max": 2},
    "Nox Kue": {"price": 40, "role": "Gravlev", "brand": "Mirai", "ingame": True, "auec_price": 150000, "img": "assets/nox kue.webp", "crew_max": 1},
    "Nox": {"price": 40, "role": "Gravlev", "brand": "Mirai", "ingame": True, "auec_price": 150000, "img": "assets/nox.webp", "crew_max": 1},
    "Odyssey": {"price": 700, "role": "Exploration", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/odyssey.webp", "crew_max": 3},
    "Orion": {"price": 650, "role": "Minage Capital", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/orion.webp", "crew_max": 5},
    "P 52 Merlin": {"price": 25, "role": "Autre", "brand": "Kruger", "ingame": True, "auec_price": 50000, "img": "assets/p-52 merlin.webp", "crew_max": 1},
    "P 72 Archimedes Emerlad": {"price": 40, "role": "Autre", "brand": "Kruger", "ingame": True, "auec_price": 75000, "img": "assets/p-72 archimedes emerlad.webp", "crew_max": 1},
    "P 72 Archimedes": {"price": 35, "role": "Autre", "brand": "Kruger", "ingame": True, "auec_price": 65000, "img": "assets/p-72 archimedes.webp", "crew_max": 1},
    "Paladin": {"price": 350, "role": "Gunship", "brand": "Anvil", "ingame": True, "auec_price": 0, "img": "assets/paladin.webp", "crew_max": 2},
    "Perseus": {"price": 675, "role": "Gunship Lourd", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/perseus.webp", "crew_max": 4},
    "Pioneer": {"price": 850, "role": "Construction", "brand": "CNOU", "ingame": True, "auec_price": 0, "img": "assets/pioneer.webp", "crew_max": 4},
    "Polaris": {"price": 750, "role": "Corvette", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/polaris.webp", "crew_max": 6},
    "Prospector": {"price": 155, "role": "Minage", "brand": "MISC", "ingame": True, "auec_price": 2000000, "img": "assets/prospector.webp", "crew_max": 1},
    "Prowler Utility": {"price": 440, "role": "Dropship", "brand": "Tevarin", "ingame": True, "auec_price": 9500000, "img": "assets/prowler utility.webp", "crew_max": 2},
    "Prowler": {"price": 440, "role": "Dropship", "brand": "Tevarin", "ingame": True, "auec_price": 9500000, "img": "assets/prowler.webp", "crew_max": 2},
    "PTV": {"price": 15, "role": "Buggy", "brand": "Greycat", "ingame": True, "auec_price": 15000, "img": "assets/ptv.webp", "crew_max": 1},
    "Pulse Kx": {"price": 30, "role": "Gravlev", "brand": "Mirai", "ingame": True, "auec_price": 0, "img": "assets/pulse kx.webp", "crew_max": 1},
    "Pulse": {"price": 30, "role": "Gravlev", "brand": "Mirai", "ingame": True, "auec_price": 0, "img": "assets/pulse.webp", "crew_max": 1},
    "Raft": {"price": 125, "role": "Fret", "brand": "ARGO", "ingame": True, "auec_price": 1700000, "img": "assets/raft.webp", "crew_max": 1},
    "Railen": {"price": 225, "role": "Fret Alien", "brand": "Gatac", "ingame": True, "auec_price": 0, "img": "assets/railen.webp", "crew_max": 3},
    "Ranger Cv": {"price": 40, "role": "Moto", "brand": "Tumbril", "ingame": True, "auec_price": 0, "img": "assets/ranger cv.webp", "crew_max": 1},
    "Ranger RC": {"price": 45, "role": "Moto Course", "brand": "Tumbril", "ingame": True, "auec_price": 0, "img": "assets/ranger rc.webp", "crew_max": 1},
    "Ranger TR": {"price": 45, "role": "Moto Combat", "brand": "Tumbril", "ingame": True, "auec_price": 0, "img": "assets/ranger tr.webp", "crew_max": 1},
    "Razor EX": {"price": 155, "role": "Course Furtif", "brand": "MISC", "ingame": True, "auec_price": 1900000, "img": "assets/razor ex.webp", "crew_max": 1},
    "Razor LX": {"price": 145, "role": "Course", "brand": "MISC", "ingame": True, "auec_price": 1900000, "img": "assets/razor lx.webp", "crew_max": 1},
    "Razor": {"price": 145, "role": "Course", "brand": "MISC", "ingame": True, "auec_price": 1900000, "img": "assets/razor.webp", "crew_max": 1},
    "Reclaimer Best In Show Edition 2949": {"price": 400, "role": "Recyclage Lourd", "brand": "Aegis", "ingame": True, "auec_price": 12500000, "img": "assets/reclaimer best in show edition 2949.webp", "crew_max": 3},
    "Reclaimer": {"price": 400, "role": "Recyclage Lourd", "brand": "Aegis", "ingame": True, "auec_price": 12500000, "img": "assets/reclaimer.webp", "crew_max": 3},
    "Reliant Kore": {"price": 0, "role": "Autre", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/reliant kore.webp", "crew_max": 1},
    "Reliant Mako": {"price": 100, "role": "Journalisme", "brand": "MISC", "ingame": True, "auec_price": 1600000, "img": "assets/reliant mako.webp", "crew_max": 2},
    "Reliant Sen": {"price": 85, "role": "Science", "brand": "MISC", "ingame": True, "auec_price": 1250000, "img": "assets/reliant sen.webp", "crew_max": 2},
    "Reliant Tana": {"price": 0, "role": "Autre", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/reliant tana.webp", "crew_max": 1},
    "Retaliator": {"price": 175, "role": "Bombardier Lourd", "brand": "Aegis", "ingame": True, "auec_price": 5000000, "img": "assets/retaliator.webp", "crew_max": 6},
    "ROC DS": {"price": 75, "role": "Autre", "brand": "Greycat", "ingame": True, "auec_price": 270000, "img": "assets/roc-ds.webp", "crew_max": 1},
    "ROC": {"price": 55, "role": "Minage Sol", "brand": "Greycat", "ingame": True, "auec_price": 270000, "img": "assets/roc.webp", "crew_max": 1},
    "Sabre Comet": {"price": 0, "role": "Autre", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/sabre comet.webp", "crew_max": 1},
    "Sabre Firebird": {"price": 0, "role": "Autre", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/sabre firebird.webp", "crew_max": 1},
    "Sabre Peregrine": {"price": 0, "role": "Autre", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/sabre peregrine.webp", "crew_max": 1},
    "Sabre Raven": {"price": 0, "role": "Autre", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/sabre raven.webp", "crew_max": 1},
    "Sabre": {"price": 170, "role": "Furtif", "brand": "Aegis", "ingame": True, "auec_price": 2700000, "img": "assets/sabre.webp", "crew_max": 1},
    "Salvation": {"price": 60, "role": "Sauvetage Léger", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/salvation.webp", "crew_max": 2},
    "San'tok.yai": {"price": 220, "role": "Chasseur Alien", "brand": "Aopoa", "ingame": True, "auec_price": 0, "img": "assets/san'tok.yai.webp", "crew_max": 1},
    "Scorpius Antares": {"price": 230, "role": "Guerre Elec.", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/scorpius antares.webp", "crew_max": 2},
    "Scorpius": {"price": 240, "role": "Chasseur Lourd", "brand": "RSI", "ingame": True, "auec_price": 3500000, "img": "assets/scorpius.webp", "crew_max": 2},
    "Scrythe": {"price": 300, "role": "Chasseur Moyen", "brand": "Vanduul", "ingame": True, "auec_price": 0, "img": "assets/scrythe.webp", "crew_max": 1},
    "Shiv": {"price": 150, "role": "Chasseur Lourd", "brand": "Vanduul", "ingame": True, "auec_price": 0, "img": "assets/shiv.webp", "crew_max": 1},
    "Spartan": {"price": 80, "role": "Transport", "brand": "Anvil", "ingame": True, "auec_price": 1000000, "img": "assets/spartan.webp", "crew_max": 2},
    "SRV": {"price": 150, "role": "Remorquage", "brand": "ARGO", "ingame": True, "auec_price": 0, "img": "assets/srv.webp", "crew_max": 2},
    "Starfarer Femini": {"price": 340, "role": "Ravitaillement Mil.", "brand": "MISC", "ingame": True, "auec_price": 8000000, "img": "assets/starfarer femini.webp", "crew_max": 3},
    "Starfarer": {"price": 300, "role": "Ravitaillement", "brand": "MISC", "ingame": True, "auec_price": 8000000, "img": "assets/starfarer.webp", "crew_max": 3},
    "Starlancer MAX": {"price": 240, "role": "Fret", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/starlancer max.webp", "crew_max": 2},
    "Starlancer Tac": {"price": 275, "role": "Combat", "brand": "MISC", "ingame": True, "auec_price": 0, "img": "assets/starlancer tac.webp", "crew_max": 2},
    "Storm AA": {"price": 100, "role": "Char Léger DCA", "brand": "Tumbril", "ingame": True, "auec_price": 0, "img": "assets/storm aa.webp", "crew_max": 2},
    "Storm": {"price": 100, "role": "Char Léger", "brand": "Tumbril", "ingame": True, "auec_price": 0, "img": "assets/storm.webp", "crew_max": 2},
    "Stringer": {"price": 315, "role": "Chasseur Lourd", "brand": "Vanduul", "ingame": True, "auec_price": 0, "img": "assets/stringer.webp", "crew_max": 1},
    "STV": {"price": 40, "role": "Véhicule", "brand": "Greycat", "ingame": True, "auec_price": 210000, "img": "assets/stv.webp", "crew_max": 2},
    "Syulen": {"price": 70, "role": "Starter Alien", "brand": "Gatac", "ingame": True, "auec_price": 0, "img": "assets/syulen.webp", "crew_max": 1},
    "Talon": {"price": 115, "role": "Chasseur Alien", "brand": "Tevarin", "ingame": True, "auec_price": 1750000, "img": "assets/talon .webp", "crew_max": 1},
    "Talon Shrike": {"price": 125, "role": "Chasseur Alien", "brand": "Tevarin", "ingame": True, "auec_price": 1900000, "img": "assets/talon shrike.webp", "crew_max": 1},
    "Terrapin Medic": {"price": 220, "role": "Exploration", "brand": "Anvil", "ingame": True, "auec_price": 4200000, "img": "assets/terrapin medic.webp", "crew_max": 2},
    "Terrapin": {"price": 220, "role": "Exploration", "brand": "Anvil", "ingame": True, "auec_price": 4200000, "img": "assets/terrapin.webp", "crew_max": 2},
    "Ursa Fortuna": {"price": 50, "role": "Rover", "brand": "RSI", "ingame": True, "auec_price": 280000, "img": "assets/ursa fortuna.webp", "crew_max": 4},
    "Ursa Medivac": {"price": 55, "role": "Rover Médical", "brand": "RSI", "ingame": True, "auec_price": 350000, "img": "assets/ursa medivac.webp", "crew_max": 4},
    "Ursa": {"price": 50, "role": "Rover", "brand": "RSI", "ingame": True, "auec_price": 280000, "img": "assets/ursa.webp", "crew_max": 4},
    "Valkyrie Liberator Edition": {"price": 375, "role": "Dropship", "brand": "Anvil", "ingame": True, "auec_price": 6000000, "img": "assets/valkyrie liberator edition.webp", "crew_max": 4},
    "Valkyrie": {"price": 375, "role": "Dropship", "brand": "Anvil", "ingame": True, "auec_price": 6000000, "img": "assets/valkyrie.webp", "crew_max": 4},
    "Vanguard Harbinger": {"price": 280, "role": "Bombardier", "brand": "Aegis", "ingame": True, "auec_price": 4800000, "img": "assets/vanguard harbinger.webp", "crew_max": 2},
    "Vanguard Hoplite": {"price": 235, "role": "Transport", "brand": "Aegis", "ingame": True, "auec_price": 4200000, "img": "assets/vanguard hoplite.webp", "crew_max": 2},
    "Vanguard Sentinel": {"price": 275, "role": "Guerre Elec.", "brand": "Aegis", "ingame": True, "auec_price": 4700000, "img": "assets/vanguard sentinel.webp", "crew_max": 2},
    "Vanguard Warden": {"price": 260, "role": "Chasseur Lourd", "brand": "Aegis", "ingame": True, "auec_price": 4500000, "img": "assets/vanguard warden.webp", "crew_max": 2},
    "Vulcan": {"price": 200, "role": "Réparation", "brand": "Aegis", "ingame": True, "auec_price": 0, "img": "assets/vulcan.webp", "crew_max": 2},
    "Vulture": {"price": 175, "role": "Recyclage", "brand": "Drake", "ingame": True, "auec_price": 2800000, "img": "assets/vulture.webp", "crew_max": 1},
    "X1 Force": {"price": 60, "role": "Gravlev", "brand": "Origin", "ingame": True, "auec_price": 0, "img": "assets/x1 force.webp", "crew_max": 1},
    "X1 Velocity": {"price": 55, "role": "Gravlev", "brand": "Origin", "ingame": True, "auec_price": 0, "img": "assets/x1 velocity.webp", "crew_max": 1},
    "X1": {"price": 50, "role": "Gravlev", "brand": "Origin", "ingame": True, "auec_price": 0, "img": "assets/x1.webp", "crew_max": 1},
    "Zeus Mk II CL": {"price": 180, "role": "Fret", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/zeus mk II cl.webp", "crew_max": 2},
    "Zeus Mk II ES": {"price": 150, "role": "Exploration", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/zeus mk II es.webp", "crew_max": 2},
    "Zeus Mk II MR": {"price": 160, "role": "Combat", "brand": "RSI", "ingame": True, "auec_price": 0, "img": "assets/zeus mk ii mr.webp", "crew_max": 2},
}


# --- 2. FONCTIONS DE FUSION ET DE NETTOYAGE DES DONNÉES ---

def clean_name(name: str) -> str:
    """Nettoie et normalise le nom du vaisseau pour la clé de fusion (match scrap.json)."""
    name = name.lower()
    replacements = {
        "best in show edition 2949": "", "expedition w/c8x": "w c8x", "expedition": "", 
        "pirate edition": "", "utility": "", "emerald": "", "solstice": "", 
        "vindicator": "", "firebird": "", "peregrine": "", "raven": "", 
        "comet": "", "talus": "", "carbon": "", "force": "", "velocity": "",
        "lx": "", "mx": "", "aa": "", "mt": "", "rc": "", "rn": "", "tr": "", 
        "ds": "", "cl": "", "es": "", "mr": "", "ln": "", "g12r": "g12", 
        "g12a": "g12", "kue": "", "l-21 wolf": "l 21 wolf", 
        "p-52 merlin": "p 52 merlin", "p-72 archimedes": "p 72 archimedes",
        "atls geo": "atls", "honrnet": "hornet", "femini": "gemini"
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
        
    name = name.replace("-", " ").replace(".", " ").strip()
    return " ".join(name.split())


def load_and_merge_ships_data(catalog_data: Dict[str, Any], json_path: str = "scrap.json") -> Dict[str, Any]:
    """
    Charge les données de scrap.json et les fusionne avec la base de données du catalogue.
    """
    
    # 1. Charger les données du fichier JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            scrap_data_list = json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Fichier {json_path} non trouvé. Utilisation de la BASE_CATALOG_DATA seule.")
        return catalog_data
    except json.JSONDecodeError:
        print(f"❌ Erreur de décodage JSON dans {json_path}. Vérifiez la syntaxe du fichier.")
        return catalog_data
    
    # 2. Convertir le JSON en dictionnaire de spécifications
    scrap_db = {}
    for entry in scrap_data_list:
        try:
            raw_title = entry["ship"]["title"]["title"]
            normalized_key = clean_name(raw_title)
            
            specs = entry["ship"]["specification"]
            
            # Nettoyage et capitalisation des clés de spécification
            specs_clean = {k.replace('_', ' ').title().replace('M/S/S', 'm/s²').replace('M/S', 'm/s').replace('Kg', 'kg').replace('M', 'm'): v for k, v in specs.items()}
            
            # Retirer les champs d'équipage et cargo qui ne correspondent pas au format de BASE_CATALOG_DATA
            specs_clean.pop("Min Crew", None)
            specs_clean.pop("Max Crew", None)
            
            specs_clean["Titre Original Scrap"] = raw_title
            
            # Ajuster le format de CargoCapacity (SCU) si possible
            if 'Cargocapacity' in specs_clean and specs_clean['Cargocapacity'] not in ('-', '0', None):
                try:
                    # Assurez-vous que c'est un nombre entier
                    specs_clean['Cargocapacity'] = str(int(float(specs_clean['Cargocapacity'])))
                except ValueError:
                    pass

            scrap_db[normalized_key] = specs_clean
            
        except KeyError:
            continue

    # 3. Fusionner les données et appliquer les règles d'affichage
    final_ships_db = {}
    match_count = 0
    
    for name, data in catalog_data.items():
        final_data = data.copy()
        
        # Tenter la fusion avec les données de scrap.json
        normalized_key = clean_name(name)
        specs = scrap_db.get(normalized_key)
        
        if specs:
            final_data.update(specs)
            match_count += 1
            
        # --- RÈGLE D'AFFICHAGE DU PRIX aUEC : 0 devient la chaîne ---
        # Si le prix est 0 (indiquant l'absence de prix connu), on remplace par la chaîne descriptive.
        if final_data.get("auec_price") == 0:
            final_data["auec_price"] = "Non achetable en jeu"

        final_ships_db[name] = final_data

    # Log pour info
    print(f"\n--- Fusion & Nettoyage de Données ---")
    print(f"Statut 'ingame' forcé à True pour l'affichage aUEC.")
    print(f"Spécifications fusionnées : {match_count} entrées")
    print(f"Prix aUEC à 0 remplacés par 'Non achetable en jeu'.")
    print("---")
    
    return final_ships_db

# --- 3. EXÉCUTION DE LA FUSION ET EXPORTATION DE LA CONSTANTE FINALE ---
SHIPS_DB = load_and_merge_ships_data(BASE_CATALOG_DATA, "scrap.json")