# Standard library
from collections import deque
import configparser
import ctypes
import ctypes.wintypes as wt
from datetime import datetime, timedelta
import difflib
import glob
import json
import keyring
import os
import platform
import re
import shutil
import sqlite3
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.request
import winsound
import pygame
import zipfile

# Third-party
import cv2
from mss import mss
import numpy as np
from PIL import Image
import pytesseract
import win32gui

try:
    ULONG_PTR = wt.ULONG_PTR
except AttributeError:
    ULONG_PTR = ctypes.c_size_t

APP_BASE = "Astralis"
APP_VERSION = "3.1"
APP_PREFIX = f"{APP_BASE} v"
MARKER_FILE = ".astralis_marker"

APP_NAME = f"{APP_PREFIX}{APP_VERSION}"
APP_INSTANCE = None

APP_DATA_BASEDIR = os.path.join(os.environ.get("APPDATA",""), APP_BASE)
DATA_ROOT = APP_DATA_BASEDIR
ASSETS_DIR = os.path.join(DATA_ROOT, "assets")
BALLS_UI_DIR = os.path.join(ASSETS_DIR, "pokeballs")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
OTHER_DIR = os.path.join(ASSETS_DIR, "other")
ITEMS_DIR = os.path.join(ASSETS_DIR, "items")
CFG_PATH = os.path.join(DATA_ROOT, "settings.ini")

icon_path  = os.path.join(OTHER_DIR, "Astralis.png" or "Astralis.ico")

CFG = {
    "poll_ms": 50,
    
    # ----- Thresholds -----
    "ball_threshold": 0.35,
    "bag_threshold":  0.45,
    "run_threshold":  0.45,

    # ----- Images -----    
    "bag_image":  "bag.png",
    "run_image":  "run.png",
    "use_choice": "Poke Ball.png",

    # ----- Regions -----
    "target_region":  "0,0.75,0.6,1",
    "pokemon_name_region": "0.05,0.15,0.35,0.25",
    "hud_region":     "0.6,0.88,0.99,1",
    "bag_hud_region": "0,0,0.50,1",
    "run_hud_region": "0.50,0,1,1",
    "ball_region":    "0.27,0.16,0.53,0.785",
    "use_region":     "0.35,0.785,0.44,0.825",
    
    # ----- Saffron Bot Click Points -----
    "farm_move_choice":         "move1",
    "npc_click_point":          "0.65,0.55",
    "yes_click_point":          "0.755,0.695",
    "next_click_point":         "0.755,0.695",
    "fight_click_point":        "0.70,0.82",
    "move1_click_point":        "0.15,0.82",
    "move2_click_point":        "0.45,0.82",
    "move3_click_point":        "0.15,0.95",
    "move4_click_point":        "0.45,0.95",
    "no_click_point":           "0.85,0.95",
    "learntext_ocr_region":     "0.00,0.755,0.60,1.00",

    "enabled_targets": "",
    "enabled_pokemon_targets": "",
    "targets_order": "Dark Aura Potion|Skinifier|Super Skinifier|Dark Skinifier|Tintifier|Super Tintifier|Shinifier|Leftovers|Light Ball|Lucky Egg|Black Augurite|Peat Block|Auspicious Armor|Malicious Armor|Wellspring Mask|Hearthflame Mask|Cornerstone Mask|Abomasite|Absolite|Aerodactylite|Aggronite|Alakazite|Altarianite|Ampharosite|Audinite|Banettite|Beedrillite|Blastoisinite|Blazikenite|Cameruptite|Charizardite X|Charizardite Y|Diancite|Galladite|Garchompite|Gardevoirite|Gengarite|Glalitite|Gyaradosite|Heracronite|Houndoominite|Kangaskhanite|Latiasite|Latiosite|Lopunnite|Lucarionite|Manectite|Mawilite|Medichamite|Metagrossite|Pidgeotite|Pinsirite|Sablenite|Salamencite|Sceptilite|Scizorite|Sharpedonite|Slowbronite|Steelixite|Swampertite|Tyranitarite|Venusaurite",
    
    # ----- Presets -----
    "preset_1": "Dark Aura Potion|Super Skinifier|Dark Skinifier|Tintifier|Super Tintifier",
    "preset_1_name": "Popular",
    "preset_2": "Dark Aura Potion|Skinifier|Super Skinifier|Dark Skinifier|Tintifier|Super Tintifier|Shinifier",
    "preset_2_name": "Popular 2",
    "preset_3": "Abomasite|Absolite|Aerodactylite|Aggronite|Alakazite|Altarianite|Ampharosite|Audinite|Banettite|Beedrillite|Blastoisinite|Blazikenite|Cameruptite|Charizardite X|Charizardite Y|Diancite|Galladite|Garchompite|Gardevoirite|Gengarite|Glalitite|Gyaradosite|Heracronite|Houndoominite|Kangaskhanite|Latiasite|Latiosite|Lopunnite|Lucarionite|Manectite|Mawilite|Medichamite|Metagrossite|Pidgeotite|Pinsirite|Sablenite|Salamencite|Sceptilite|Scizorite|Sharpedonite|Slowbronite|Steelixite|Swampertite|Tyranitarite|Venusaurite",
    "preset_3_name": "Mega Stones",
    "preset_4": "",
    "preset_4_name": "Custom 1",
    "preset_5": "",
    "preset_5_name": "Custom 2",
    
    # ----- Sounds -----
    "sound_enabled": True,
    "vol_master": 100,
    "vol_item_found": 100,
    "vol_hover": 100,
    "vol_click": 100,
    "vol_out_of_balls": 100,

    # ----- Misc -----
    "mouse_clicks": "1",
    "vk_pause":   "F6",
    "vk_exit":    "F7",
    "vk_hide_overlay": "F8",
    "vk_regions": "F10",
    "fuzzy_ratio": 0.90,
    "developer_mode": False,
    "encounter_logging": False,
    "enable_session_data": False,
    "encounter_log_retention_days": 30,
    "tesseract_path": "",
    "debug_copy_lines": 50,
    "show_welcome_on_start": False,
    "tutorial_seen": False,
    "enable_fallback_capture": False,
    "notify_token": "",
    "sd_prune_mode": "off",
    "sd_prune_days": 30,
    "sd_prune_keep": 50,
    "sd_min_enc_on": False,
    "sd_min_enc": 0,
    "sd_min_cap_on": False,
    "sd_min_cap": 0, 
    
    # ----- Theme Designer -----
    "fg_bg": "#111315",
    "fg_bg_hover": "#1A1D20",
    "fg_card": "#0F1720",
    "fg_card_alt": "#081018",
    "text_primary": "#E5E7EB",
    "text_secondary": "#9AA0A6",
    "text_muted": "#7F8790",
    "text_warning": "#D73A49",
    "accent": "#1561C0",
    "accent_hover": "#1C75E5",
    "border": "#263241",
    "border_muted": "#3A3F44",
    "link": "#4EA3F1",
    "debug_colorize_enabled": "True",
    "debug_color_startup":    "#6AA3FF",
    "debug_color_encounter":  "#9CDCFE",
    "debug_color_run":        "#F78C6C",
    "debug_color_caught":     "#C3E88D",
    "debug_color_error":      "#FF5370",
    "debug_color_other":      "#E0E0E0",
}

ITEM_NOTES = {
    "Dark Aura Potion":   "Any grass patch *(1/40,000 | 1/20,000 with gamepass)*",
    "Skinifier":          "Any grass patch *(1/1,500)*",
    "Super Skinifier":    "Any grass patch *(1/10,000)*",
    "Dark Skinifier":     "Any grass patch *(1/40,000 | 1/20,000 with gamepass)*",
    "Tintifier":          "Any grass patch *(1/3,000)*",
    "Super Tintifier":    "Any grass patch *(1/100,000)*",
    "Shinifier":          "Any grass patch *(1/1,000)*",
    "Leftovers":          "Found on **Munchlax** in _[Viridian Forest](https://project-polaro-alpha.fandom.com/wiki/Viridian%20Forest)_ and _[Deep Forest Zone 2](https://project-polaro-alpha.fandom.com/wiki/Almia%20Town#Deep%20Forest%20Zone%202)_ *(1/3)*",
    "Light Ball":         "Found on **Pikachu** at _[Route 1](https://project-polaro-alpha.fandom.com/wiki/Route%201)_ *(1/5)*",
    "Lucky Egg":          "Found on **Chansey** in _[Fuchsia City](https://project-polaro-alpha.fandom.com/wiki/Fuchsia%20City)_ *(1/3)* and _[Isle of Armor](https://project-polaro-alpha.fandom.com/wiki/Isle%20of%20Armor)_ *(1/1,000)*",
    "Black Augurite":     "Found on any **Mythical Pokémon** in _[Area Zero Green Grass Patches](https://project-polaro-alpha.fandom.com/wiki/Area_Zero#Area%20Zero%20Green%20Grass%20Patches)_ *(1/10)*",
    "Peat Block":         "Found on any **Mythical Pokémon** in _[Area Zero Green Grass Patches](https://project-polaro-alpha.fandom.com/wiki/Area_Zero#Area%20Zero%20Green%20Grass%20Patches)_ *(1/10)*",
    "Auspicious Armor":   "Found on any **Mythical Pokémon** in _[Area Zero Red Grass Patches](https://project-polaro-alpha.fandom.com/wiki/Area_Zero#Area%20Zero%20Red%20Grass%20Patches)_ *(1/10)*",
    "Malicious Armor":    "Found on any **Mythical Pokémon** in _[Area Zero Red Grass Patches](https://project-polaro-alpha.fandom.com/wiki/Area_Zero#Area%20Zero%20Red%20Grass%20Patches)_ *(1/10)*",
    "Wellspring Mask":    "Found on **Ogerpon** in _[Area Zero Green Grass Patches](https://project-polaro-alpha.fandom.com/wiki/Area_Zero#Area%20Zero%20Green%20Grass%20Patches)_ *(1/2)*",
    "Hearthflame Mask":   "Found on **Ogerpon** in _[Area Zero Green Grass Patches](https://project-polaro-alpha.fandom.com/wiki/Area_Zero#Area%20Zero%20Green%20Grass%20Patches)_ *(1/2)*",
    "Cornerstone Mask":   "Found on **Ogerpon** in _[Area Zero Green Grass Patches](https://project-polaro-alpha.fandom.com/wiki/Area_Zero#Area%20Zero%20Green%20Grass%20Patches)_ *(1/2)*",
    "Abomasite":          "Found on any Pokémon *(1/250)*",
    "Absolite":           "Found on any Pokémon *(1/250)*",
    "Aerodactylite":      "Found on any Pokémon *(1/250)*",
    "Aggronite":          "Found on any Pokémon *(1/250)*",
    "Alakazite":          "Found on any Pokémon *(1/250)*",
    "Altarianite":        "Found on any Pokémon *(1/250)*",
    "Ampharosite":        "Found on any Pokémon *(1/250)*",
    "Audinite":           "Found on any Pokémon *(1/250)*",
    "Banettite":          "Found on any Pokémon *(1/250)*",
    "Beedrillite":        "Found on any Pokémon *(1/250)*",
    "Blastoisinite":      "Found on any Pokémon *(1/250)*",
    "Blazikenite":        "Found on any Pokémon *(1/250)*",
    "Cameruptite":        "Found on any Pokémon *(1/250)*",
    "Charizardite X":     "Found on any Pokémon *(1/250)*",
    "Charizardite Y":     "Found on any Pokémon *(1/250)*",
    "Diancite":           "Found on any Pokémon *(1/250)*",
    "Galladite":          "Found on any Pokémon *(1/250)*",
    "Garchompite":        "Found on any Pokémon *(1/250)*",
    "Gardevoirite":       "Found on any Pokémon *(1/250)*",
    "Gengarite":          "Found on any Pokémon *(1/250)*",
    "Glalitite":          "Found on any Pokémon *(1/250)*",
    "Gyaradosite":        "Found on any Pokémon *(1/250)*",
    "Heracronite":        "Found on any Pokémon *(1/250)*",
    "Houndoominite":      "Found on any Pokémon *(1/250)*",
    "Kangaskhanite":      "Found on any Pokémon *(1/250)*",
    "Latiasite":          "Found on any Pokémon *(1/250)*",
    "Latiosite":          "Found on any Pokémon *(1/250)*",
    "Lopunnite":          "Found on any Pokémon *(1/250)*",
    "Lucarionite":        "Found on any Pokémon *(1/250)*",
    "Manectite":          "Found on any Pokémon *(1/250)*",
    "Mawilite":           "Found on any Pokémon *(1/250)*",
    "Medichamite":        "Found on any Pokémon *(1/250)*",
    "Metagrossite":       "Found on any Pokémon *(1/250)*",
    "Pidgeotite":         "Found on any Pokémon *(1/250)*",
    "Pinsirite":          "Found on any Pokémon *(1/250)*",
    "Sablenite":          "Found on any Pokémon *(1/250)*",
    "Salamencite":        "Found on any Pokémon *(1/250)*",
    "Sceptilite":         "Found on any Pokémon *(1/250)*",
    "Scizorite":          "Found on any Pokémon *(1/250)*",
    "Sharpedonite":       "Found on any Pokémon *(1/250)*",
    "Slowbronite":        "Found on any Pokémon *(1/250)*",
    "Steelixite":         "Found on any Pokémon *(1/250)*",
    "Swampertite":        "Found on any Pokémon *(1/250)*",
    "Tyranitarite":       "Found on any Pokémon *(1/250)*",
    "Venusaurite":        "Found on any Pokémon *(1/250)*",
}

pokemon_names = [ "Bulbasaur", "Ivysaur", "Venusaur", "Charmander", "Charmeleon", "Charizard", "Squirtle", "Wartortle", "Blastoise", "Caterpie", "Metapod", "Butterfree", "Weedle", "Kakuna", "Beedrill", "Pidgey", "Pidgeotto", "Pidgeot", "Rattata", "Raticate", "Spearow", "Fearow", "Ekans", "Arbok", "Pikachu", "Raichu", "Sandshrew", "Sandslash", "NidoranF", "Nidorina", "Nidoqueen", "NidoranM", "Nidorino", "Nidoking", "Clefairy", "Clefable", "Vulpix", "Ninetales", "Jigglypuff", "Wigglytuff", "Zubat", "Golbat", "Oddish", "Gloom", "Vileplume", "Paras", "Parasect", "Venonat", "Venomoth", "Diglett", "Dugtrio", "Meowth", "Persian", "Psyduck", "Golduck", "Mankey", "Primeape", "Growlithe", "Arcanine", "Poliwag", "Poliwhirl", "Poliwrath", "Abra", "Kadabra", "Alakazam", "Machop", "Machoke", "Machamp", "Bellsprout", "Weepinbell", "Victreebel", "Tentacool", "Tentacruel", "Geodude", "Graveler", "Golem", "Ponyta", "Rapidash", "Slowpoke", "Slowbro", "Magnemite", "Magneton", "Farfetch'd", "Doduo", "Dodrio", "Seel", "Dewgong", "Grimer", "Muk", "Shellder", "Cloyster", "Gastly", "Haunter", "Gengar", "Onix", "Drowzee", "Hypno", "Krabby", "Kingler", "Voltorb", "Electrode", "Exeggcute", "Exeggutor", "Cubone", "Marowak", "Hitmonlee", "Hitmonchan", "Lickitung", "Koffing", "Weezing", "Rhyhorn", "Rhydon", "Chansey", "Tangela", "Kangaskhan", "Horsea", "Seadra", "Goldeen", "Seaking", "Staryu", "Starmie", "Mr. Mime", "Scyther", "Jynx", "Electabuzz", "Magmar", "Pinsir", "Tauros", "Magikarp", "Gyarados", "Lapras", "Ditto", "Eevee", "Vaporeon", "Jolteon", "Flareon", "Porygon", "Omanyte", "Omastar", "Kabuto", "Kabutops", "Aerodactyl", "Snorlax", "Articuno", "Zapdos", "Moltres", "Dratini", "Dragonair", "Dragonite", "Mewtwo", "Mew", "Chikorita", "Bayleef", "Meganium", "Cyndaquil", "Quilava", "Typhlosion", "Totodile", "Croconaw", "Feraligatr", "Sentret", "Furret", "Hoothoot", "Noctowl", "Ledyba", "Ledian", "Spinarak", "Ariados", "Crobat", "Chinchou", "Lanturn", "Pichu", "Cleffa", "Igglybuff", "Togepi", "Togetic", "Natu", "Xatu", "Mareep", "Flaaffy", "Ampharos", "Bellossom", "Marill", "Azumarill", "Sudowoodo", "Politoed", "Hoppip", "Skiploom", "Jumpluff", "Aipom", "Sunkern", "Sunflora", "Yanma", "Wooper", "Quagsire", "Espeon", "Umbreon", "Murkrow", "Slowking", "Misdreavus", "Unown", "Wobbuffet", "Girafarig", "Pineco", "Forretress", "Dunsparce", "Gligar", "Steelix", "Snubbull", "Granbull", "Qwilfish", "Scizor", "Shuckle", "Heracross", "Sneasel", "Teddiursa", "Ursaring", "Slugma", "Magcargo", "Swinub", "Piloswine", "Corsola", "Remoraid", "Octillery", "Delibird", "Mantine", "Skarmory", "Houndour", "Houndoom", "Kingdra", "Phanpy", "Donphan", "Porygon2", "Stantler", "Smeargle", "Tyrogue", "Hitmontop", "Smoochum", "Elekid", "Magby", "Miltank", "Blissey", "Raikou", "Entei", "Suicune", "Larvitar", "Pupitar", "Tyranitar", "Lugia", "Ho-Oh", "Celebi", "Treecko", "Grovyle", "Sceptile", "Torchic", "Combusken", "Blaziken", "Mudkip", "Marshtomp", "Swampert", "Poochyena", "Mightyena", "Zigzagoon", "Linoone", "Wurmple", "Silcoon", "Beautifly", "Cascoon", "Dustox", "Lotad", "Lombre", "Ludicolo", "Seedot", "Nuzleaf", "Shiftry", "Taillow", "Swellow", "Wingull", "Pelipper", "Ralts", "Kirlia", "Gardevoir", "Surskit", "Masquerain", "Shroomish", "Breloom", "Slakoth", "Vigoroth", "Slaking", "Nincada", "Ninjask", "Shedinja", "Whismur", "Loudred", "Exploud", "Makuhita", "Hariyama", "Azurill", "Nosepass", "Skitty", "Delcatty", "Sableye", "Mawile", "Aron", "Lairon", "Aggron", "Meditite", "Medicham", "Electrike", "Manectric", "Plusle", "Minun", "Volbeat", "Illumise", "Roselia", "Gulpin", "Swalot", "Carvanha", "Sharpedo", "Wailmer", "Wailord", "Numel", "Camerupt", "Torkoal", "Spoink", "Grumpig", "Spinda", "Trapinch", "Vibrava", "Flygon", "Cacnea", "Cacturne", "Swablu", "Altaria", "Zangoose", "Seviper", "Lunatone", "Solrock", "Barboach", "Whiscash", "Corphish", "Crawdaunt", "Baltoy", "Claydol", "Lileep", "Cradily", "Anorith", "Armaldo", "Feebas", "Milotic", "Castform", "Kecleon", "Shuppet", "Banette", "Duskull", "Dusclops", "Tropius", "Chimecho", "Absol", "Wynaut", "Snorunt", "Glalie", "Spheal", "Sealeo", "Walrein", "Clamperl", "Huntail", "Gorebyss", "Relicanth", "Luvdisc", "Bagon", "Shelgon", "Salamence", "Beldum", "Metang", "Metagross", "Regirock", "Regice", "Registeel", "Latias", "Latios", "Kyogre", "Groudon", "Rayquaza", "Jirachi", "Deoxys", "Turtwig", "Grotle", "Torterra", "Chimchar", "Monferno", "Infernape", "Piplup", "Prinplup", "Empoleon", "Starly", "Staravia", "Staraptor", "Bidoof", "Bibarel", "Kricketot", "Kricketune", "Shinx", "Luxio", "Luxray", "Budew", "Roserade", "Cranidos", "Rampardos", "Shieldon", "Bastiodon", "Burmy", "Wormadam", "Mothim", "Combee", "Vespiquen", "Pachirisu", "Buizel", "Floatzel", "Cherubi", "Cherrim", "Shellos", "Gastrodon", "Ambipom", "Drifloon", "Drifblim", "Buneary", "Lopunny", "Mismagius", "Honchkrow", "Glameow", "Purugly", "Chingling", "Stunky", "Skuntank", "Bronzor", "Bronzong", "Bonsly", "Mime Jr.", "Happiny", "Chatot", "Spiritomb", "Gible", "Gabite", "Garchomp", "Munchlax", "Riolu", "Lucario", "Hippopotas", "Hippowdon", "Skorupi", "Drapion", "Croagunk", "Toxicroak", "Carnivine", "Finneon", "Lumineon", "Mantyke", "Snover", "Abomasnow", "Weavile", "Magnezone", "Lickilicky", "Rhyperior", "Tangrowth", "Electivire", "Magmortar", "Togekiss", "Yanmega", "Leafeon", "Glaceon", "Gliscor", "Mamoswine", "Porygon-Z", "Gallade", "Probopass", "Dusknoir", "Froslass", "Rotom", "Uxie", "Mesprit", "Azelf", "Dialga", "Palkia", "Heatran", "Regigigas", "Giratina", "Cresselia", "Phione", "Manaphy", "Darkrai", "Shaymin", "Arceus", "Victini", "Snivy", "Servine", "Serperior", "Tepig", "Pignite", "Emboar", "Oshawott", "Dewott", "Samurott", "Patrat", "Watchog", "Lillipup", "Herdier", "Stoutland", "Purrloin", "Liepard", "Pansage", "Simisage", "Pansear", "Simisear", "Panpour", "Simipour", "Munna", "Musharna", "Pidove", "Tranquill", "Unfezant", "Blitzle", "Zebstrika", "Roggenrola", "Boldore", "Gigalith", "Woobat", "Swoobat", "Drilbur", "Excadrill", "Audino", "Timburr", "Gurdurr", "Conkeldurr", "Tympole", "Palpitoad", "Seismitoad", "Throh", "Sawk", "Sewaddle", "Swadloon", "Leavanny", "Venipede", "Whirlipede", "Scolipede", "Cottonee", "Whimsicott", "Petilil", "Lilligant", "Basculin", "Sandile", "Krokorok", "Krookodile", "Darumaka", "Darmanitan", "Maractus", "Dwebble", "Crustle", "Scraggy", "Scrafty", "Sigilyph", "Yamask", "Cofagrigus", "Tirtouga", "Carracosta", "Archen", "Archeops", "Trubbish", "Garbodor", "Zorua", "Zoroark", "Minccino", "Cinccino", "Gothita", "Gothorita", "Gothitelle", "Solosis", "Duosion", "Reuniclus", "Ducklett", "Swanna", "Vanillite", "Vanillish", "Vanilluxe", "Deerling", "Sawsbuck", "Emolga", "Karrablast", "Escavalier", "Foongus", "Amoonguss", "Frillish", "Jellicent", "Alomomola", "Joltik", "Galvantula", "Ferroseed", "Ferrothorn", "Klink", "Klang", "Klinklang", "Tynamo", "Eelektrik", "Eelektross", "Elgyem", "Beheeyem", "Litwick", "Lampent", "Chandelure", "Axew", "Fraxure", "Haxorus", "Cubchoo", "Beartic", "Cryogonal", "Shelmet", "Accelgor", "Stunfisk", "Mienfoo", "Mienshao", "Druddigon", "Golett", "Golurk", "Pawniard", "Bisharp", "Bouffalant", "Rufflet", "Braviary", "Vullaby", "Mandibuzz", "Heatmor", "Durant", "Deino", "Zweilous", "Hydreigon", "Larvesta", "Volcarona", "Cobalion", "Terrakion", "Virizion", "Tornadus", "Thundurus", "Reshiram", "Zekrom", "Landorus", "Kyurem", "Keldeo", "Meloetta", "Genesect", "Chespin", "Quilladin", "Chesnaught", "Fennekin", "Braixen", "Delphox", "Froakie", "Frogadier", "Greninja", "Bunnelby", "Diggersby", "Fletchling", "Fletchinder", "Talonflame", "Scatterbug", "Spewpa", "Vivillon", "Litleo", "Pyroar", "Flabebe", "Floette", "Florges", "Skiddo", "Gogoat", "Pancham", "Pangoro", "Furfrou", "Espurr", "Meowstic", "Honedge", "Doublade", "Aegislash", "Spritzee", "Aromatisse", "Swirlix", "Slurpuff", "Inkay", "Malamar", "Binacle", "Barbaracle", "Skrelp", "Dragalge", "Clauncher", "Clawitzer", "Helioptile", "Heliolisk", "Tyrunt", "Tyrantrum", "Amaura", "Aurorus", "Sylveon", "Hawlucha", "Dedenne", "Carbink", "Goomy", "Sliggoo", "Goodra", "Klefki", "Phantump", "Trevenant", "Pumpkaboo", "Gourgeist", "Bergmite", "Avalugg", "Noibat", "Noivern", "Xerneas", "Yveltal", "Zygarde", "Diancie", "Hoopa", "Volcanion", "Rowlet", "Dartrix", "Decidueye", "Litten", "Torracat", "Incineroar", "Popplio", "Brionne", "Primarina", "Pikipek", "Trumbeak", "Toucannon", "Yungoos", "Gumshoos", "Grubbin", "Charjabug", "Vikavolt", "Crabrawler", "Crabominable", "Oricorio", "Cutiefly", "Ribombee", "Rockruff", "Lycanroc", "Wishiwashi", "Mareanie", "Toxapex", "Mudbray", "Mudsdale", "Dewpider", "Araquanid", "Fomantis", "Lurantis", "Morelull", "Shiinotic", "Salandit", "Salazzle", "Stufful", "Bewear", "Bounsweet", "Steenee", "Tsareena", "Comfey", "Oranguru", "Passimian", "Wimpod", "Golisopod", "Sandygast", "Palossand", "Pyukumuku", "Type: Null", "Silvally", "Minior", "Komala", "Turtonator", "Togedemaru", "Mimikyu", "Bruxish", "Drampa", "Dhelmise", "Jangmo-o", "Hakamo-o", "Kommo-o", "Tapu Koko", "Tapu Lele", "Tapu Bulu", "Tapu Fini", "Cosmog", "Cosmoem", "Solgaleo", "Lunala", "Nihilego", "Buzzwole", "Pheromosa", "Xurkitree", "Celesteela", "Kartana", "Guzzlord", "Necrozma", "Magearna", "Marshadow", "Poipole", "Naganadel", "Stakataka", "Blacephalon", "Zeraora", "Meltan", "Melmetal", "Grookey", "Thwackey", "Rillaboom", "Scorbunny", "Raboot", "Cinderace", "Sobble", "Drizzile", "Inteleon", "Skwovet", "Greedent", "Rookidee", "Corvisquire", "Corviknight", "Blipbug", "Dottler", "Orbeetle", "Nickit", "Thievul", "Gossifleur", "Eldegoss", "Wooloo", "Dubwool", "Chewtle", "Drednaw", "Yamper", "Boltund", "Rolycoly", "Carkol", "Coalossal", "Applin", "Flapple", "Appletun", "Silicobra", "Sandaconda", "Cramorant", "Arrokuda", "Barraskewda", "Toxel", "Toxtricity", "Sizzlipede", "Centiskorch", "Clobbopus", "Grapploct", "Sinistea", "Polteageist", "Hatenna", "Hattrem", "Hatterene", "Impidimp", "Morgrem", "Grimmsnarl", "Obstagoon", "Perrserker", "Cursola", "Sirfetch'd", "Mr. Rime", "Runerigus", "Milcery", "Alcremie", "Falinks", "Pincurchin", "Snom", "Frosmoth", "Stonjourner", "Eiscue", "Indeedee", "Morpeko", "Cufant", "Copperajah", "Dracozolt", "Arctozolt", "Dracovish", "Arctovish", "Duraludon", "Dreepy", "Drakloak", "Dragapult", "Zacian", "Zamazenta", "Eternatus", "Kubfu", "Urshifu", "Zarude", "Regieleki", "Regidrago", "Glastrier", "Spectrier", "Calyrex", "Wyrdeer", "Kleavor", "Ursaluna", "Basculegion", "Sneasler", "Overqwil", "Enamorus", "Sprigatito", "Floragato", "Meowscarada", "Fuecoco", "Crocalor", "Skeledirge", "Quaxly", "Quaxwell", "Quaquaval", "Lechonk", "Oinkologne", "Tarountula", "Spidops", "Nymble", "Lokix", "Pawmi", "Pawmo", "Pawmot", "Tandemaus", "Maushold", "Fidough", "Dachsbun", "Smoliv", "Dolliv", "Arboliva", "Squawkabilly", "Nacli", "Naclstack", "Garganacl", "Charcadet", "Armarouge", "Ceruledge", "Tadbulb", "Bellibolt", "Wattrel", "Kilowattrel", "Maschiff", "Mabosstiff", "Shroodle", "Grafaiai", "Bramblin", "Brambleghast", "Toedscool", "Toedscruel", "Klawf", "Capsakid", "Scovillain", "Rellor", "Rabsca", "Flittle", "Espathra", "Tinkatink", "Tinkatuff", "Tinkaton", "Wiglett", "Wugtrio", "Bombirdier", "Finizen", "Palafin", "Varoom", "Revavroom", "Cyclizar", "Orthworm", "Glimmet", "Glimmora", "Greavard", "Houndstone", "Flamigo", "Cetoddle", "Cetitan", "Veluza", "Dondozo", "Tatsugiri", "Annihilape", "Clodsire", "Farigiraf", "Dudunsparce", "Kingambit", "Great Tusk", "Scream Tail", "Brute Bonnet", "Flutter Mane", "Slither Wing", "Sandy Shocks", "Iron Treads", "Iron Bundle", "Iron Hands", "Iron Jugulis", "Iron Moth", "Iron Thorns", "Frigibax", "Arctibax", "Baxcalibur", "Gimmighoul", "Gholdengo", "Wo-Chien", "Chien-Pao", "Ting-Lu", "Chi-Yu", "Roaring Moon", "Iron Valiant", "Koraidon", "Miraidon", "Walking Wake", "Iron Leaves", "Dipplin", "Poltchageist", "Sinistcha", "Okidogi", "Munkidori", "Fezandipiti", "Ogerpon", "Archaludon", "Hydrapple", "Gouging Fire", "Raging Bolt", "Iron Boulder", "Iron Crown", "Terapagos", "Pecharunt", "Alolan Rattata", "Alolan Raticate", "Alolan Raichu", "Alolan Sandshrew", "Alolan Sandslash", "Alolan Vulpix", "Alolan Ninetales", "Alolan Diglett", "Alolan Dugtrio", "Alolan Meowth", "Alolan Persian", "Alolan Geodude", "Alolan Graveler", "Alolan Golem", "Alolan Grimer", "Alolan Muk", "Alolan Exeggutor", "Alolan Marowak", "Galarian Meowth", "Galarian Ponyta", "Galarian Rapidash", "Galarian Farfetch'd", "Galarian Weezing", "Galarian Mr. Mime", "Galarian Corsola", "Galarian Zigzagoon", "Galarian Linoone", "Galarian Darumaka", "Galarian Darmanitan", "Galarian Darmanitan Zen", "Galarian Yamask", "Galarian Stunfisk", "Galarian Slowbro", "Galarian Slowking", "Galarian Slowpoke", "Galarian Articuno", "Galarian Zapdos", "Galarian Moltres", "Hisuian Growlithe", "Hisuian Arcanine", "Hisuian Voltorb", "Hisuian Electrode", "Hisuian Typhlosion", "Hisuian Qwilfish", "Hisuian Sneasel", "Hisuian Samurott", "Hisuian Lilligant", "Hisuian Zorua", "Hisuian Zoroark", "Hisuian Braviary", "Hisuian Sliggoo", "Hisuian Goodra", "Hisuian Avalugg", "Hisuian Decidueye", "Paldean Wooper", "Paldean Tauros Combat Breed", "Paldean Tauros Aqua Breed", "Paldean Tauros Blaze Breed", "Mega Venusaur", "Mega Charizard X", "Mega Charizard Y", "Mega Blastoise", "Mega Beedrill", "Mega Pidgeot", "Mega Alakazam", "Mega Slowbro", "Mega Gengar", "Mega Kangaskhan", "Mega Pinsir", "Mega Gyarados", "Mega Aerodactyl", "Mega Mewtwo X", "Mega Mewtwo Y", "Mega Ampharos", "Mega Steelix", "Mega Scizor", "Mega Heracross", "Mega Houndoom", "Mega Tyranitar", "Mega Sceptile", "Mega Blaziken", "Mega Swampert", "Mega Gardevoir", "Mega Sableye", "Mega Mawile", "Mega Aggron", "Mega Medicham", "Mega Manectric", "Mega Sharpedo", "Mega Camerupt", "Mega Altaria", "Mega Banette", "Mega Absol", "Mega Glalie", "Mega Salamence", "Mega Metagross", "Mega Latias", "Mega Latios", "Mega Rayquaza", "Mega Lopunny", "Mega Garchomp", "Mega Lucario", "Mega Abomasnow", "Mega Gallade", "Mega Audino", "Mega Diancie", "Castform Sunny Form", "Castform Rainy Form", "Castform Snowy Form", "Deoxys Attack Forme", "Deoxys Defense Forme", "Deoxys Speed Forme", "Burmy Plant Cloak", "Burmy No Cloak", "Burmy Sandy Cloak", "Burmy Trash Cloak", "Cherrim Overcast", "Cherrim Sunny", "Gastrodon West Sea", "Gastrodon East Sea", "Giratina Altered Forme", "Giratina Origin Forme", "Shaymin Land Forme", "Shaymin Sky Forme", "Shellos West Sea", "Shellos East Sea", "Wormadam Plant Cloak", "Wormadam Sandy Cloak", "Wormadam Trash Cloak", "Basculin Red-Striped", "Basculin Blue-Striped", "Basculin White-Striped", "Darmanitan Standard", "Darmanitan Zen", "Deerling Spring", "Deerling Autumn", "Deerling Summer", "Deerling Winter", "Keldeo Resolute", "Landorus Incarnate", "Landorus Therian", "Meloetta Aria", "Meloetta Pirouette", "Sawsbuck Spring", "Sawsbuck Autumn", "Sawsbuck Summer", "Sawsbuck Winter", "Thundurus Incarnate", "Thundurus Therian", "Tornadus Incarnate", "Tornadus Therian", "Aegislash Shield", "Aegislash Blade", "Flabebe Red Flower", "Floette Red Flower", "Floette Eternal Flower", "Florges Red Flower", "Furfrou Natural Trim", "Furfrou Diamond Trim", "Furfrou Heart Trim", "Furfrou Star Trim", "Gourgeist Average Size", "Hoopa Confined", "Hoopa Unbound", "Meowstic-Male", "Meowstic-Female", "Pumpkaboo Average Size", "Pyroar-Male", "Pyroar-Female", "Scatterbug Icy Snow", "Vivillon Archipelago Pattern", "Vivillon Continental Pattern", "Vivillon Elegant Pattern", "Vivillon Fancy Pattern", "Vivillon Garden Pattern", "Vivillon High Plains Pattern", "Vivillon Icy Snow Pattern", "Vivillon Jungle Pattern", "Vivillon Marine Pattern", "Vivillon Meadow Pattern", "Vivillon Modern Pattern", "Vivillon Monsoon Pattern", "Vivillon Ocean Pattern", "Vivillon Poké Ball Pattern", "Vivillon Polar Pattern", "Vivillon River Pattern", "Vivillon Sandstorm Pattern", "Vivillon Savanna Pattern", "Vivillon Sun Pattern", "Vivillon Tundra Pattern", "Xerneas Active", "Xerneas Neutral", "Zygarde Complete", "Zygarde 10 Percent", "Zygarde 50 Percent", "Zygarde Cell", "Zygarde Core", "Lycanroc Midday", "Lycanroc Dusk", "Lycanroc Midnight", "Mimikyu Disguised Form", "Mimikyu Busted Form", "Minior Meteor", "Minior Core", "Oricorio Baile Style", "Oricorio Pom-Pom Style", "Oricorio Pa'u Style", "Oricorio Sensu Style", "Wishiwashi Solo", "Wishiwashi School", "Alcremie Vanilla Cream", "Basculegion-Male", "Basculegion-Female", "Eiscue Ice Face", "Eiscue Noice Face", "Enamorus Incarnate", "Enamorus Therian", "Indeedee-Male", "Indeedee-Female", "Morpeko Full Belly", "Morpeko Hangry", "Polteageist Phony", "Sinistea Phony", "Toxtricity-Amped", "Toxtricity-Low-Key", "Ursaluna Full Moon", "Urshifu-Single-Strike", "Urshifu-Rapid-Strike", "Zacian-Crowned", "Zamazenta-Crowned", "Dudunsparce Two-Segment", "Dudunsparce Three-Segment", "Gimmighoul Chest", "Gimmighoul Roaming", "Maushold Family of Four", "Maushold Family of Three", "Oinkologne-Male", "Oinkologne-Female", "Ogerpon Teal Mask", "Ogerpon Wellspring Mask", "Ogerpon Hearthflame Mask", "Ogerpon Cornerstone Mask", "Palafin Zero", "Palafin Hero", "Poltchageist Counterfeit", "Sinistcha Counterfeit", "Squawkabilly Green-Plumage", "Squawkabilly Blue-Plumage", "Squawkabilly Yellow-Plumage", "Squawkabilly White-Plumage", "Tatsugiri Curly", "Tatsugiri Droopy", "Tatsugiri Stretchy", "Terapagos-Stellar", "Terapagos-Terastal", "Calyrex Ice Rider", "Calyrex Shadow Rider", "Cramorant Gulping", "Cramorant Gorging", "Dialga Origin Forme", "Primal Dialga", "Ash-Greninja", "Primal Groudon", "Primal Kyogre", "Kyurem-Black", "Kyurem-White", "Lunala Full Moon Phase", "Marshadow Alt", "Necrozma Dawn Wings", "Necrozma Dusk Mane", "Ultra Necrozma", "Palkia Origin Forme", "Reshiram Activated", "Rotom Heat", "Rotom Wash", "Rotom Frost", "Rotom Fan", "Rotom Mow", "Solgaleo Radiant Sun Phase", "Zekrom Activated" ]

CFG_DEFAULTS = dict(CFG)
STATS_DB_PATH = os.path.join(DATA_ROOT, "stats.db")
user32 = ctypes.WinDLL('user32', use_last_error=True)
GA_ROOT = 2
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN, SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 76, 77, 78, 79
STATS_UPDATED = threading.Event()
CURRENT_SESSION_ID = None
SESSION_T0 = 0.0
SESSION_PAUSED_TOTAL = 0.0
SESSION_PAUSE_T0 = 0.0
SEEN_LOG_LOCK = threading.Lock()
_last_seen_logged = None
LOG_LOCK = threading.Lock()
LOG_ENTRIES = []
COUNTS_LOCK = threading.Lock()
ENCOUNTER_COUNT = 0
ITEM_COUNT = 0
FLED_COUNT = 0
LAST_DM_KEY = ""
LAST_DM_T = 0.0
ENCOUNTER_FILE_LOCK = threading.Lock()
_last_encounter_prune_ts = 0.0
STATUS_CB = None
_status = "idle"
_last_status = None
stop_flag = threading.Event()
pause_flag = threading.Event()
BOT_THREAD = None
FARM_THREAD = None
SELECTED_ROBLOX_HWNDS = []
OVERLAY_THREAD = None
OVERLAY_STOP = threading.Event()
OVERLAY_HIDDEN = False
HOTKEY_THREAD = None
HOTKEY_STOP = threading.Event()
CLICK_LOCK = threading.Lock()
START_MONO = time.monotonic()

SERVICE_NAME = "Astralis"

CONTENTS_API = "https://api.github.com/repos/Bloxables/astralis/contents?ref=main"
MAIN_ARCHIVE_URL = "https://github.com/Bloxables/astralis/archive/refs/heads/main.zip"
UPDATE_CHECK_TIMEOUT = 6

def _http_get_json(url, timeout=UPDATE_CHECK_TIMEOUT):
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME} Updater"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        _log(f"[update] check failed: {e}")
        return None

def get_notify_token():
    t = os.environ.get("ASTRALIS_NOTIFY_TOKEN")
    if t:
        return t.strip()
    if keyring:
        v = keyring.get_password(SERVICE_NAME, "notify_token") or ""
        return v.strip()
    p = os.path.join(os.environ.get("APPDATA",""), "Astralis", "secrets.json")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return (json.load(f).get("notify_token","") or "").strip()
    except Exception:
        return ""

def set_notify_token(token: str):
    token = (token or "").strip()
    if keyring:
        if token:
            keyring.set_password(SERVICE_NAME, "notify_token", token)
        else:
            try:
                keyring.delete_password(SERVICE_NAME, "notify_token")
            except Exception:
                pass
    p = os.path.join(os.environ.get("APPDATA",""), "Astralis", "secrets.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    existing = {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            existing = json.load(f) or {}
    except Exception:
        existing = {}
    prev_token = (existing.get("notify_token") or "").strip()
    if token and token != prev_token:
        existing["link_dm_sent"] = False
    existing["notify_token"] = token
    with open(p, "w", encoding="utf-8") as f:
        json.dump(existing, f)
    if token:
        try:
            with open(p, "r", encoding="utf-8") as f:
                now_data = json.load(f) or {}
        except Exception:
            now_data = {}
        if not now_data.get("link_dm_sent", False):
            notify_link_success()
            now_data["link_dm_sent"] = True
            with open(p, "w", encoding="utf-8") as f:
                json.dump(now_data, f)

def sound_allowed(kind="generic"):
    try:
        def _bool(v):
            return str(v).strip().lower() in ("1", "true", "yes", "on")
        if not _bool(CFG.get("sound_enabled", True)):
            return False
        vm = int(CFG.get("vol_master", 100) or 0)
        if vm <= 0:
            return False
        if kind == "hover":
            return int(CFG.get("vol_hover", 100) or 0) > 0
        if kind == "click":
            return int(CFG.get("vol_click", 100) or 0) > 0
        if kind == "item_found":
            return int(CFG.get("vol_item_found", 100) or 0) > 0
        if kind == "out_of_balls":
            return int(CFG.get("vol_out_of_balls", 100) or 0) > 0
        return True
    except Exception:
        return False

_HOVER_SOUND = None
_CLICK_SOUND = None
_OOB_SOUND = None

def _sound_volume(kind="generic"):
    try:
        master = max(0, min(100, int(CFG.get("vol_master", 100) or 0)))
        if kind == "hover":
            specific = max(0, min(100, int(CFG.get("vol_hover", 100) or 0)))
        elif kind == "click":
            specific = max(0, min(100, int(CFG.get("vol_click", 100) or 0)))
        elif kind == "item_found":
            specific = max(0, min(100, int(CFG.get("vol_item_found", 100) or 0)))
        elif kind == "out_of_balls":
            specific = max(0, min(100, int(CFG.get("vol_out_of_balls", 100) or 0)))
        else:
            specific = 100
        return (master / 100.0) * (specific / 100.0)
    except Exception:
        return 0.0

def _init_hover_sound_engine():
    global _HOVER_SOUND
    path = os.path.join(SOUNDS_DIR, "ButtonHover.wav")
    _HOVER_SOUND = None
    if not os.path.isfile(path):
        return
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        _HOVER_SOUND = pygame.mixer.Sound(path)
    except Exception as e:
        _HOVER_SOUND = None
        _log(f"Hover sound engine init failed: {e}")

def _init_click_sound_engine():
    global _CLICK_SOUND
    path = os.path.join(SOUNDS_DIR, "ButtonClick.wav")
    _CLICK_SOUND = None
    if not os.path.isfile(path):
        return
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        _CLICK_SOUND = pygame.mixer.Sound(path)
    except Exception as e:
        _CLICK_SOUND = None
        _log(f"Click sound engine init failed: {e}")

def _init_out_of_balls_sound_engine():
    global _OOB_SOUND
    path = os.path.join(SOUNDS_DIR, "OutOfBalls.wav")
    _OOB_SOUND = None
    if not os.path.isfile(path):
        return
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.set_num_channels(32)
        _OOB_SOUND = pygame.mixer.Sound(path)
    except Exception as e:
        _OOB_SOUND = None
        _log(f"Out-of-balls sound engine init failed: {e}")

def _play_hover_sound():
    global _HOVER_SOUND
    try:
        if not sound_allowed("hover"):
            return
        vol = _sound_volume("hover")
        if vol <= 0:
            return
        if _HOVER_SOUND is None:
            _init_hover_sound_engine()
        if _HOVER_SOUND is None or not pygame.mixer.get_init():
            return
        ch = pygame.mixer.find_channel(True)
        if ch is None:
            return
        ch.set_volume(vol)
        ch.play(_HOVER_SOUND)
    except Exception as e:
        _log(f"[sound] hover failed: {e}")

def _play_click_sound():
    global _CLICK_SOUND
    try:
        if not sound_allowed("click"):
            return
        vol = _sound_volume("click")
        if vol <= 0:
            return
        if _CLICK_SOUND is None:
            _init_click_sound_engine()
        if _CLICK_SOUND is None or not pygame.mixer.get_init():
            return
        ch = pygame.mixer.find_channel(True)
        if ch is None:
            return
        ch.set_volume(vol)
        ch.play(_CLICK_SOUND)
    except Exception as e:
        _log(f"[sound] click failed: {e}")

def _play_out_of_balls_sound():
    global _OOB_SOUND
    try:
        if not sound_allowed("out_of_balls"):
            return
        vol = _sound_volume("out_of_balls")
        if vol <= 0:
            return
        if _OOB_SOUND is None:
            _init_out_of_balls_sound_engine()
        if _OOB_SOUND is None or not pygame.mixer.get_init():
            return
        ch = pygame.mixer.find_channel(True)
        if ch is None:
            return
        ch.set_volume(vol)
        ch.play(_OOB_SOUND)
    except Exception as e:
        _log(f"[sound] out_of_balls failed: {e}")

def session_data_autodelete_apply():
    mode = str(CFG.get("sd_prune_mode", "off") or "off").strip().lower()
    min_enc_enabled = bool(CFG.get("sd_min_enc_on", False))
    min_cap_enabled = bool(CFG.get("sd_min_cap_on", False))
    if mode not in ("days", "entries") and not min_enc_enabled and not min_cap_enabled: return
    _ensure_session_db()
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        with conn:
            current_sid = int(CURRENT_SESSION_ID) if CURRENT_SESSION_ID is not None else -1
            ids = set()

            if mode == "days":
                keep_days = max(0, int(CFG.get("sd_prune_days", 30) or 0))
                if keep_days <= 0:
                    ids.update(r[0] for r in conn.execute("SELECT id FROM sessions WHERE id != ?", (current_sid,)).fetchall())
                else:
                    cutoff = int(time.time()) - keep_days * 86400
                    ids.update(r[0] for r in conn.execute("SELECT id FROM sessions WHERE COALESCE(end_ts, start_ts, 0) < ? AND id != ?", (cutoff, current_sid)).fetchall())

            elif mode == "entries":
                keep_n = max(0, int(CFG.get("sd_prune_keep", 100) or 0))
                if keep_n <= 0:
                    ids.update(r[0] for r in conn.execute("SELECT id FROM sessions WHERE id != ?", (current_sid,)).fetchall())
                else:
                    ids.update(r[0] for r in conn.execute("""
                        SELECT id FROM sessions
                        WHERE id NOT IN (
                            SELECT id FROM sessions
                            WHERE id != ?
                            ORDER BY id DESC
                            LIMIT ?
                        ) AND id != ?
                    """, (current_sid, keep_n, current_sid)).fetchall())

            if min_enc_enabled:
                min_enc = max(0, int(CFG.get("sd_min_enc", 0) or 0))
                ids.update(r[0] for r in conn.execute("SELECT id FROM sessions WHERE id != ? AND COALESCE(encounters, 0) <= ?", (current_sid, min_enc)).fetchall())
            
            if min_cap_enabled:
                min_cap = max(0, int(CFG.get("sd_min_cap", 0) or 0))
                ids.update(r[0] for r in conn.execute("SELECT id FROM sessions WHERE id != ? AND COALESCE(captured, 0) <= ?", (current_sid, min_cap)).fetchall())
                
            if ids:
                conn.executemany("DELETE FROM session_items WHERE session_id=?", [(sid,) for sid in ids])
                conn.executemany("DELETE FROM sessions WHERE id=?", [(sid,) for sid in ids])
    finally:
        conn.close()

def _ensure_session_db():
    os.makedirs(DATA_ROOT, exist_ok=True)
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_ts INTEGER NOT NULL,
                    end_ts   INTEGER,
                    run_secs INTEGER NOT NULL DEFAULT 0,
                    encounters INTEGER NOT NULL DEFAULT 0,
                    captured   INTEGER NOT NULL DEFAULT 0,
                    fled       INTEGER NOT NULL DEFAULT 0,
                    fallbacks  INTEGER NOT NULL DEFAULT 0,
                    balls_used INTEGER NOT NULL DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_items (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    ts         TEXT    NOT NULL,
                    name       TEXT    NOT NULL,
                    captured   INTEGER NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
            """)
    finally:
        conn.close()

def _ensure_stats_db():
    os.makedirs(DATA_ROOT, exist_ok=True)
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS item_stats (
                    name     TEXT PRIMARY KEY,
                    total    INTEGER NOT NULL DEFAULT 0,
                    captured INTEGER NOT NULL DEFAULT 0,
                    fled     INTEGER NOT NULL DEFAULT 0
                )
            """)
            cols = {r[1] for r in conn.execute("PRAGMA table_info(item_stats)").fetchall()}
            if "seen" in cols and "total" not in cols:
                conn.execute("ALTER TABLE item_stats ADD COLUMN total INTEGER NOT NULL DEFAULT 0")
                conn.execute("UPDATE item_stats SET total=seen")
    finally:
        conn.close()

def session_start():
    global CURRENT_SESSION_ID, SESSION_T0, SESSION_PAUSED_TOTAL, SESSION_PAUSE_T0
    SESSION_T0 = time.monotonic()
    SESSION_PAUSED_TOTAL = 0.0
    SESSION_PAUSE_T0 = 0.0
    if not bool(CFG.get("enable_session_data", False)):
        CURRENT_SESSION_ID = None
        return
    _ensure_session_db()
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        with conn:
            cur = conn.execute("INSERT INTO sessions(start_ts) VALUES (?)", (int(time.time()),))
            CURRENT_SESSION_ID = cur.lastrowid
    finally:
        conn.close()
    session_data_autodelete_apply()

def session_end():
    global CURRENT_SESSION_ID
    if CURRENT_SESSION_ID is None:
        return
    _ensure_session_db()
    run_secs = int(_uptime_sec())
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        with conn:
            conn.execute("UPDATE sessions SET end_ts=?, run_secs=? WHERE id=?", (int(time.time()), run_secs, CURRENT_SESSION_ID))
    finally:
        conn.close()
    session_data_autodelete_apply()
    CURRENT_SESSION_ID = None

def session_inc(field, n=1):
    if CURRENT_SESSION_ID is None or not bool(CFG.get("enable_session_data", False)):
        return
    if field not in ("encounters", "captured", "fled", "fallbacks", "balls_used"):
        return
    _ensure_session_db()
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        with conn:
            conn.execute(f"UPDATE sessions SET {field}={field}+? WHERE id=?", (int(n), CURRENT_SESSION_ID))
    finally:
        conn.close()

def sessions_all():
    _ensure_session_db()
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        rows = conn.execute("""
            SELECT id, start_ts, end_ts, run_secs, encounters, captured, fled, fallbacks, balls_used
            FROM sessions
            ORDER BY id DESC
        """).fetchall()
        return rows
    finally:
        conn.close()

def session_get(session_id):
    _ensure_session_db()
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        row = conn.execute("""
            SELECT id, start_ts, end_ts, run_secs, encounters, captured, fled, fallbacks, balls_used
            FROM sessions WHERE id=?
        """, (int(session_id),)).fetchone()
        return row
    finally:
        conn.close()

def session_items(session_id: int):
    _ensure_session_db()
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        return conn.execute("""
            SELECT ts, name, captured
            FROM session_items
            WHERE session_id=?
            ORDER BY id DESC
        """, (int(session_id),)).fetchall()
    finally:
        conn.close()

def session_delete(session_id: int):
    _ensure_session_db()
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        with conn:
            conn.execute("DELETE FROM session_items WHERE session_id=?", (int(session_id),))
            conn.execute("DELETE FROM sessions WHERE id=?", (int(session_id),))
    finally:
        conn.close()

def stats_inc(name: str, captured: bool):
    name = (name or "(unknown)").strip()
    _ensure_stats_db()
    cap = 1 if captured else 0
    fld = 0 if captured else 1
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        with conn:
            conn.execute("""
                INSERT INTO item_stats(name, total, captured, fled)
                VALUES(?, 1, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    total    = item_stats.total    + 1,
                    captured = item_stats.captured + excluded.captured,
                    fled     = item_stats.fled     + excluded.fled
            """, (name, cap, fld))
    finally:
        conn.close()

def stats_all():
    _ensure_stats_db()
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        return conn.execute("SELECT name, total, captured, fled FROM item_stats ORDER BY total DESC, name ASC").fetchall()
    finally:
        conn.close()

def _encounter_log(name: str, captured: bool, kind: str = "items"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    kind = "pokemon" if str(kind).lower() in ("pokemon", "pokémon") else "items"
    label = "Pokémon" if kind == "pokemon" else "Item"
    if bool(CFG.get("encounter_logging", False)):
        line = f"[{ts}] Encountered {label} {name or '(unknown)'} — {'CAPTURED' if captured else 'RAN AWAY'}\n"
        try:
            os.makedirs(DATA_ROOT, exist_ok=True)
            with ENCOUNTER_FILE_LOCK:
                with open(os.path.join(DATA_ROOT, "encounter_logs.txt"), "a", encoding="utf-8") as f:
                    f.write(line)
        except Exception as e:
            _log(f"encounter log write failed: {e}")
        _prune_encounter_logs(force=False)
    if kind != "items" or CURRENT_SESSION_ID is None or not bool(CFG.get("enable_session_data", False)):
        return
    _ensure_session_db()
    conn = sqlite3.connect(STATS_DB_PATH)
    try:
        with conn:
            conn.execute("""
                INSERT INTO session_items(session_id, ts, name, captured)
                VALUES (?, ?, ?, ?)
            """, (CURRENT_SESSION_ID, ts, name, 1 if captured else 0))
    finally:
        conn.close()

def add_log(name: str, captured: bool, kind: str = "items"):
    global ITEM_COUNT, FLED_COUNT
    kind = "pokemon" if str(kind).lower() in ("pokemon", "pokémon") else "items"
    ts = datetime.now().strftime("%H:%M:%S")
    status_txt = "Captured" if captured else "Fled"
    line = f"{ts} - {name} - {status_txt}"

    with LOG_LOCK:
        LOG_ENTRIES.append(line)

    if kind == "items":
        stats_inc(name, captured)
    _encounter_log(name, captured, kind)

    if captured:
        with COUNTS_LOCK:
            ITEM_COUNT += 1
        session_inc("captured", 1)
        if kind == "items":
            notify_discord(name)
    else:
        with COUNTS_LOCK:
            FLED_COUNT += 1
        session_inc("fled", 1)

    row = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "kind": kind, "name": name or "(unknown)", "captured": bool(captured)}
    row["pokemon" if kind == "pokemon" else "item"] = name or "(unknown)"
    encounters, items, fled = get_counts()
    send("counts", {"encounters": encounters, "items": items, "fled": fled})
    send("encounter_result", {"item": name, "captured": captured, "line": line, "row": row})
    STATS_UPDATED.set()

def log_seen_once(text: str):
    global _last_seen_logged
    text = (text or "").strip()
    if not text:
        return
    with SEEN_LOG_LOCK:
        if text == _last_seen_logged:
            return
        _last_seen_logged = text
    _log(f"Seen OCR: {text}")

def _prune_encounter_logs(*, force: bool = False):
    global _last_encounter_prune_ts
    if not bool(CFG.get("encounter_logging", False)):
        return
    now = time.time()
    if not force and now - _last_encounter_prune_ts < 300:
        return
    _last_encounter_prune_ts = now

    try:
        days = int(CFG.get("encounter_log_retention_days", 30) or 30)
    except Exception:
        days = 30

    if days < 0:
        return

    cutoff = datetime.now() - timedelta(days=days)
    root = os.path.join(DATA_ROOT, "encounter_logs")
    if not os.path.isdir(root):
        return

    for path in glob.glob(os.path.join(root, "*.txt")):
        try:
            base = os.path.basename(path)
            m = re.match(r"encounters_(\d{4}-\d{2}-\d{2})\.txt$", base)
            if not m:
                continue
            d = datetime.strptime(m.group(1), "%Y-%m-%d")
            if d < cutoff:
                try:
                    os.remove(path)
                except Exception:
                    pass
        except Exception:
            pass

def get_counts():
    with COUNTS_LOCK:
        return ENCOUNTER_COUNT, ITEM_COUNT, FLED_COUNT

def get_logs():
    rows = []
    path = os.path.join(DATA_ROOT, "encounter_logs.txt")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                m = re.match(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] Encountered (?:(Item|Pokémon|Pokemon) )?(.*?) — (CAPTURED|RAN AWAY|FALLBACK)", line.strip(), re.I)
                if m:
                    label = (m.group(2) or "Item").strip().lower()
                    kind = "pokemon" if label in ("pokemon", "pokémon") else "items"
                    name = m.group(3).strip()
                    status = m.group(4).strip().upper()
                    row = {"ts": m.group(1), "kind": kind, "name": name, "captured": "fallback" if status == "FALLBACK" else status == "CAPTURED"}
                    row["pokemon" if kind == "pokemon" else "item"] = name
                    rows.append(row)
    except Exception:
        pass
    return rows

def get_log_days():
    days = set()
    path = os.path.join(DATA_ROOT, "encounter_logs.txt")
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("[") and len(line) > 12 and line[11] == " ":
                    d = line[1:11]
                    if len(d) == 10 and d[4] == "-" and d[7] == "-":
                        y, m, dd = d.split("-")
                        days.add((d, f"{m}-{dd}-{y}"))
    except Exception:
        pass
    return [{"iso": iso, "label": label} for iso, label in sorted(days, key=lambda t: t[0], reverse=True)]

def inc_encounter():
    global ENCOUNTER_COUNT
    with COUNTS_LOCK:
        ENCOUNTER_COUNT += 1
    session_inc("encounters", 1)
    encounters, items, fled = get_counts()
    send("counts", {"encounters": encounters, "items": items, "fled": fled})
    STATS_UPDATED.set()

def inc_item():
    global ITEM_COUNT
    with COUNTS_LOCK:
        ITEM_COUNT += 1
    session_inc("captured", 1)
    STATS_UPDATED.set()

def inc_fled():
    global FLED_COUNT
    with COUNTS_LOCK:
        FLED_COUNT += 1
    session_inc("fled", 1)
    STATS_UPDATED.set()

def _fmt_hms(secs: float) -> str:
    secs = max(0, int(secs))
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def _uptime_sec():
    if not SESSION_T0:
        return 0
    paused_extra = time.monotonic() - SESSION_PAUSE_T0 if SESSION_PAUSE_T0 else 0
    return max(0, time.monotonic() - SESSION_T0 - SESSION_PAUSED_TOTAL - paused_extra)

def _build_status_text():
    if not BOT_THREAD or not BOT_THREAD.is_alive():
        return "Ready. Click Start to begin."
    return _status

def _http_post_form(url, fields: dict, timeout=5):
    boundary = "----astralisFormBoundary"
    parts = []
    for name, value in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n")
    body = ("".join(parts) + f"--{boundary}--\r\n").encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    return urllib.request.urlopen(req, timeout=timeout)

def _status_poll_loop():
    while True:
        try:
            status(_build_status_text())
        except Exception:
            pass
        time.sleep(1.0)

def _log(msg: str):
    try:
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"{ts} - {msg}"
        with LOG_LOCK:
            LOG_ENTRIES.append(line)
        try:
            os.makedirs(DATA_ROOT, exist_ok=True)
            lines = read_debug_logs(499)
            lines.append(line)
            with open(DEBUG_LOG_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception:
            pass
        send("log", {"line": line})
    except Exception:
        pass

def notify_discord(item_name: str):
    try:
        if sound_allowed("item_found") and int(CFG.get("vol_master", 100) or 0) > 0:
            winsound.PlaySound(os.path.join(SOUNDS_DIR, "ItemFound.wav"),
                               winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        _log(f"[sound] failed: {e}")
    try:
        url = "http://157.230.180.25:8787/notify"
        boundary = "----astralisFormBoundary"
        parts = []

        def add_field(name, value):
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n")

        token = get_notify_token()
        if not token:
            return
        add_field("token", token)
        add_field("item", item_name)

        body = ("".join(parts) + f"--{boundary}--\r\n").encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        _log(f"[notify] failed: {e}")

def notify_out_of_balls(ball_name: str):
    try:
        url = "http://157.230.180.25:8787/out_of_balls"
        boundary = "----astralisFormBoundary"
        parts = []

        def add_field(name, value):
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n"
            )

        token = get_notify_token()
        if not token:
            return
        add_field("token", token)
        add_field("ball", ball_name)

        body = ("".join(parts) + f"--{boundary}--\r\n").encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        _log(f"[notify-out-of-balls] failed: {e}")

def notify_link_success():
    try:
        url = "http://157.230.180.25:8787/link_success"
        boundary = "----astralisFormBoundary"
        parts = []
        def add_field(name, value):
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n")
        token = get_notify_token()
        if not token:
            return
        add_field("token", token)
        body = ("".join(parts) + f"--{boundary}--\r\n").encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        _log(f"[notify-link] failed: {e}")

def _parse_version(s: str):
    parts = re.findall(r"\d+", s)
    return tuple(int(p) for p in parts) if parts else (0,)

def _is_older(v_other: str, v_current: str) -> bool:
    a = _parse_version(v_other)
    b = _parse_version(v_current)
    L = max(len(a), len(b))
    a += (0,) * (L - len(a))
    b += (0,) * (L - len(b))
    return a < b

def check_for_update():
    data = _http_get_json(CONTENTS_API)
    latest_ver = None
    latest_name = None
    exe_url = None
    if isinstance(data, list):
        pat = re.compile(rf"{re.escape(APP_BASE)}\s+v(.+)\.exe$", re.IGNORECASE)
        for it in data:
            name = (it.get("name") or "").strip()
            m = pat.match(name)
            if not m:
                continue
            ver = m.group(1).strip()
            if latest_ver is None or _is_older(latest_ver, ver):
                latest_ver = ver
                latest_name = name
                exe_url = it.get("download_url")
    if latest_ver:
        current = _version_from_exe_or(APP_VERSION)
        if _is_older(current, latest_ver):
            return {
                "latest": latest_ver,
                "url": exe_url,
                "asset": latest_name,
                "assets_zip_url": MAIN_ARCHIVE_URL
            }
    return None

def _copy_tree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        out_dir = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(out_dir, exist_ok=True)
        for f in files:
            s = os.path.join(root, f)
            d = os.path.join(out_dir, f)
            shutil.copy2(s, d)

def _update_assets_from_zip(zip_path):
    tmp = _extract_zip_to_temp(zip_path)
    tmp = _unwrap_single_subdir(tmp)

    assets_src = os.path.join(tmp, "assets")
    internals_src = os.path.join(tmp, "_internal")

    if os.path.isdir(assets_src):
        _copy_tree(assets_src, ASSETS_DIR)

    if os.path.isdir(internals_src):
        internals_dst = os.path.join(_current_app_dir(), "_internal")
        _copy_tree(internals_src, internals_dst)

    try:
        shutil.rmtree(tmp, ignore_errors=True)
    except Exception:
        pass

def _download_to_temp(url, filename, progress_cb=None):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME} Updater"})
    with urllib.request.urlopen(req, context=ctx) as r:
        total = int(r.headers.get("Content-Length", "0")) or None
        fd, tmp_path = tempfile.mkstemp(prefix="astralis_pkg_", suffix=os.path.splitext(filename)[1])
        os.close(fd)
        written = 0
        with open(tmp_path, "wb") as out:
            while True:
                chunk = r.read(1024 * 256)
                if not chunk:
                    break
                out.write(chunk); written += len(chunk)
                if progress_cb and total:
                    progress_cb(min(1.0, written / total))
        return tmp_path

def _current_executable_path():
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(sys.argv[0])

def _current_app_dir():
    return os.path.dirname(_current_executable_path())

def _version_from_exe_or(default_ver: str) -> str:
    try:
        base = os.path.basename(_current_executable_path())
        m = re.match(rf"{re.escape(APP_BASE)}\s+v(.+)\.exe$", base, re.IGNORECASE)
        return (m.group(1).strip() if m else default_ver)
    except Exception:
        return default_ver

def _extract_zip_to_temp(zip_path):
    out_dir = tempfile.mkdtemp(prefix="astralis_new_")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)
    return out_dir

def _unwrap_single_subdir(path):
    try:
        entries = [os.path.join(path, p) for p in os.listdir(path)]
        dirs = [p for p in entries if os.path.isdir(p)]
        if len(dirs) == 1 and not any(os.path.isfile(e) for e in entries):
            return dirs[0]
    except Exception:
        pass
    return path

def _self_replace_exe(new_exe_path):
    cur = _current_executable_path()
    bat = os.path.join(tempfile.gettempdir(), "astralis_update.bat")
    with open(bat, "w", encoding="utf-8") as f:
        f.write(f'''@echo off
        setlocal
        set SRC="{new_exe_path}"
        set DST="{cur}"
        :waitloop
        ping 127.0.0.1 -n 2 >nul
        move /Y %SRC% %DST% >nul 2>&1
        if errorlevel 1 goto waitloop
        start "" %DST%
        endlocal
        ''')
    flags = 0x00000008 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    try:
        subprocess.Popen(["cmd", "/c", bat], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)|getattr(subprocess, "DETACHED_PROCESS", 0))
    except Exception:
        subprocess.Popen(["cmd", "/c", bat])
    try:
        APP_INSTANCE.root.destroy()
    except Exception:
        pass
    try:
        sys.exit(0)
    except SystemExit:
        pass

def migrate_user_data():
    try:
        appdata = os.environ.get("APPDATA","")
        stable = os.path.join(appdata, APP_BASE)
        os.makedirs(stable, exist_ok=True)
        pat = re.compile(rf"^{re.escape(APP_BASE)} v[0-9]")
        for name in os.listdir(appdata):
            src = os.path.join(appdata, name)
            if not os.path.isdir(src): 
                continue
            if not pat.match(name): 
                continue
            if os.path.abspath(src) == os.path.abspath(stable): 
                continue
            for root, dirs, files in os.walk(src):
                rel = os.path.relpath(root, src)
                dst = os.path.join(stable, rel) if rel != "." else stable
                os.makedirs(dst, exist_ok=True)
                for fn in files:
                    s = os.path.join(root, fn)
                    d = os.path.join(dst, fn)
                    if not os.path.exists(d):
                        try: shutil.move(s, d)
                        except: pass
            try: shutil.rmtree(src, ignore_errors=True)
            except: pass
    except: 
        pass

def enable_dpi_awareness():
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

def ensure_dirs():
    os.makedirs(DATA_ROOT, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(BALLS_UI_DIR, exist_ok=True)
    os.makedirs(OTHER_DIR, exist_ok=True)
    os.makedirs(ITEMS_DIR, exist_ok=True)
    if not os.path.exists(CFG_PATH):
        save_ini()

def seed_from_exe_folder():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))

    src = os.path.join(exe_dir, "assets")
    if os.path.isdir(src):
        for root, _, files in os.walk(src):
            rel = os.path.relpath(root, src)
            out_dir = os.path.join(ASSETS_DIR, rel) if rel != "." else ASSETS_DIR
            os.makedirs(out_dir, exist_ok=True)
            for f in files:
                if f.lower().endswith(".png"):
                    shutil.copy2(os.path.join(root, f), os.path.join(out_dir, f))

def read_text_forgiving(path):
    raw = open(path, "rb").read()
    try:
        if raw.startswith(b"\xef\xbb\xbf"): return raw.decode("utf-8-sig")
        if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"): return raw.decode("utf-16")
        return raw.decode("utf-8")
    except Exception:
        for enc in ("utf-16","cp1252"):
            try: return raw.decode(enc)
            except: pass
        raise

def load_ini():
    if not os.path.exists(CFG_PATH): return
    cp = configparser.ConfigParser()
    try:
        cp.read_string(read_text_forgiving(CFG_PATH))
    except Exception:
        save_ini(); return
    g = cp["general"] if "general" in cp else {}
    for k in CFG:
        if k in g: CFG[k] = g[k]
    for k in list(CFG):
        if k.endswith("_threshold"):
            try: CFG[k] = float(CFG[k])
            except: pass
        if k in ("poll_ms", "encounter_log_retention_days", "sd_prune_days", "sd_prune_keep", "sd_min_enc", "sd_min_cap"):
            try: CFG[k] = int(CFG[k])
            except: pass
        if k in ("sd_min_enc_on", "sd_min_cap_on", "developer_mode", "encounter_logging", "enable_session_data", "enable_fallback_capture", "sound_enabled", "show_welcome_on_start", "tutorial_seen"):
            CFG[k] = str(CFG[k]).strip().lower() in ("1", "true", "yes", "on")
    try: CFG["fuzzy_ratio"] = float(CFG.get("fuzzy_ratio", 0.90))
    except: pass

    try:
        CFG["encounter_log_retention_days"] = int(str(CFG.get("encounter_log_retention_days", 30)))
    except Exception:
        CFG["encounter_log_retention_days"] = 30    

def save_ini():
    cp = configparser.ConfigParser()
    cp["general"] = {k: str(v) for k,v in CFG.items()}
    os.makedirs(DATA_ROOT, exist_ok=True)
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        cp.write(f)

def ensure_tesseract_cmd():
    exe = None

    cand = shutil.which("tesseract")
    if cand and os.path.exists(cand):
        exe = cand
    else:
        cands = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(OTHER_DIR, "tesseract", "tesseract.exe"),
            os.path.join(
                os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
                else os.path.dirname(os.path.abspath(__file__)),
                "tesseract.exe"
            ),
        ]
        for p in cands:
            if p and os.path.exists(p):
                exe = p
                break

    if not exe:
        return

    pytesseract.pytesseract.tesseract_cmd = exe
    exe_base = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__)
    local_td = os.path.join(exe_base, "tessdata")
    if os.path.isdir(local_td):
        os.environ["TESSDATA_PREFIX"] = local_td
    else:
        exe_dir = os.path.dirname(exe)
        td = os.path.join(exe_dir, "tessdata")
        if os.path.isdir(td):
            os.environ["TESSDATA_PREFIX"] = td

def _find_local_tess_installer():
    base_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "tesseract-setup.exe"),
        os.path.join(base_dir, "tesseract", "tesseract-setup.exe"),
        os.path.join(OTHER_DIR, "tesseract-setup.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def run_tesseract_bootstrap(root):
    p = _find_local_tess_installer()
    if not p:
        return False
    try:
        try:
            root.withdraw()
        except Exception:
            pass
        proc = subprocess.Popen([p], shell=False)
        proc.wait()
        try:
            root.deiconify()
        except Exception:
            pass
        return True
    except Exception as e:
        _log(f"tesseract bootstrap failed: {e}")
        return False

def clean_old_appdata_versions():
    appdata = os.environ.get("APPDATA", "")
    if not appdata or not os.path.isdir(appdata):
        return
    current_dirname = os.path.basename(DATA_ROOT)
    base = APP_BASE
    current_version = APP_VERSION
    prefix = APP_PREFIX
    for name in os.listdir(appdata):
        if not name.startswith(prefix):
            continue
        if name == current_dirname:
            continue
        candidate = os.path.join(appdata, name)
        if not os.path.isdir(candidate):
            continue
        safe = _has_marker(candidate)
        if not safe:
            looks_like_us = (os.path.exists(os.path.join(candidate, "assets")) or
                             os.path.exists(os.path.join(candidate, "settings.ini")))
            if not looks_like_us:
                continue
        other_version = name[len(prefix):].strip()
        if current_version and _is_older(other_version, current_version):
            try:
                shutil.rmtree(candidate, ignore_errors=True)
                _log(f"Removed old data dir: {candidate}")
            except Exception as e:
                _log(f"Failed to remove {candidate}: {e}")

if shutil.which("tesseract") is None and platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def _has_marker(path: str) -> bool:
    return os.path.exists(os.path.join(path, MARKER_FILE))

def _write_marker(path: str):
    try:
        with open(os.path.join(path, MARKER_FILE), "w", encoding="utf-8") as f:
            f.write("astralis\n")
    except Exception:
        pass

def get_window_rect(hwnd):
    rect = wt.RECT()
    if not user32.GetWindowRect(wt.HWND(hwnd), ctypes.byref(rect)):
        return None
    return (rect.left, rect.top, rect.right, rect.bottom)

def get_client_rect(hwnd):
    rect = wt.RECT()
    if not user32.GetClientRect(wt.HWND(hwnd), ctypes.byref(rect)): return None
    p1 = wt.POINT(rect.left, rect.top); p2 = wt.POINT(rect.right, rect.bottom)
    user32.ClientToScreen(wt.HWND(hwnd), ctypes.byref(p1))
    user32.ClientToScreen(wt.HWND(hwnd), ctypes.byref(p2))
    return (p1.x, p1.y, p2.x, p2.y)

def _get_virtual_screen_rect():
    x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    w = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    h = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    return (x, y, x + w, y + h)

def _intersects(a, b):
    L1,T1,R1,B1 = a; L2,T2,R2,B2 = b
    return not (R1 <= L2 or R2 <= L1 or B1 <= T2 or B2 <= T1)

def find_roblox_hwnd():
    EnumWindows = user32.EnumWindows
    GetWindowTextW = user32.GetWindowTextW
    GetWindowTextLengthW = user32.GetWindowTextLengthW
    IsWindowVisible = user32.IsWindowVisible
    found = wt.HWND(0)
    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, lparam):
        if not IsWindowVisible(hwnd): return True
        n = GetWindowTextLengthW(hwnd)
        if n == 0: return True
        buf = ctypes.create_unicode_buffer(n+1)
        GetWindowTextW(hwnd, buf, n+1)
        if "Roblox" in buf.value:
            nonlocal found; found = hwnd; return False
        return True
    EnumWindows(cb, 0)
    return found or None

def get_window_title(hwnd):
    try:
        n = user32.GetWindowTextLengthW(wt.HWND(hwnd))
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(wt.HWND(hwnd), buf, n + 1)
        return buf.value or f"Roblox ({int(hwnd)})"
    except Exception:
        return f"Roblox ({int(hwnd)})"

def is_roblox_window_alive(hwnd):
    try:
        if not hwnd:
            return False
        if not user32.IsWindow(wt.HWND(hwnd)):
            return False
        if user32.GetWindowTextLengthW(wt.HWND(hwnd)) <= 0:
            return False
        return True
    except Exception:
        return False

def find_roblox_hwnds():
    EnumWindows = user32.EnumWindows; GetWindowTextW = user32.GetWindowTextW
    GetWindowTextLengthW = user32.GetWindowTextLengthW; IsWindowVisible = user32.IsWindowVisible
    results = []
    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, lparam):
        if not IsWindowVisible(hwnd): return True
        n = GetWindowTextLengthW(hwnd)
        if n == 0: return True
        buf = ctypes.create_unicode_buffer(n + 1)
        GetWindowTextW(hwnd, buf, n + 1)
        if "Roblox" in buf.value:
            results.append(hwnd)
        return True
    EnumWindows(cb, 0)
    return results

def force_foreground(hwnd):
    if not hwnd:
        return
    try:
        pid = wt.DWORD()
        tid_target = user32.GetWindowThreadProcessId(wt.HWND(hwnd), ctypes.byref(pid))
        tid_self = ctypes.windll.kernel32.GetCurrentThreadId()
        user32.AttachThreadInput(tid_self, tid_target, True)
        try:
            user32.BringWindowToTop(wt.HWND(hwnd))
            user32.SetForegroundWindow(wt.HWND(hwnd))
            user32.SetFocus(wt.HWND(hwnd))
        finally:
            user32.AttachThreadInput(tid_self, tid_target, False)
    except Exception as e:
        pass

def clear_taskbar_flash(hwnd, *also_hwnds):
    try:
        if not hwnd:
            return

        class FLASHWINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wt.UINT),
                ("hwnd", wt.HWND),
                ("dwFlags", wt.DWORD),
                ("uCount", wt.UINT),
                ("dwTimeout", wt.DWORD),
            ]

        user32.FlashWindowEx.argtypes = [ctypes.POINTER(FLASHWINFO)]
        user32.FlashWindowEx.restype = wt.BOOL

        GA_ROOT = 2
        FLASHW_STOP = 0

        targets = [wt.HWND(hwnd)]
        root = user32.GetAncestor(wt.HWND(hwnd), GA_ROOT)
        if root:
            targets.append(root)
        for h in also_hwnds:
            if h:
                targets.append(wt.HWND(h))

        for h in targets:
            fwi = FLASHWINFO(ctypes.sizeof(FLASHWINFO), h, FLASHW_STOP, 0, 0)
            user32.FlashWindowEx(ctypes.byref(fwi))
    except Exception as e:
        _log(f"clear_taskbar_flash failed: {e}")

def _send_input_checked(inp, op_name="SendInput"):
    n = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))
    if n != 1:
        err = ctypes.get_last_error()
        _log(f"{op_name} failed, GetLastError={err}")
        return False
    return True

def _root_hwnd_from_point(x, y):
    pt = wt.POINT(x, y)
    h = user32.WindowFromPoint(pt)
    if not h:
        return None
    return user32.GetAncestor(h, GA_ROOT)

def is_window_partially_visible(hwnd, ignore_rects=()):
    if not hwnd:
        return False
    if not user32.IsWindowVisible(wt.HWND(hwnd)):
        return False
    if user32.IsIconic(wt.HWND(hwnd)):
        return False
    cx = get_client_rect(hwnd)
    if not cx:
        return False
    L,T,R,B = cx
    if not _intersects((L,T,R,B), _get_virtual_screen_rect()):
        return False
    inset = 24
    L2, T2, R2, B2 = L+inset, T+inset, R-inset, B-inset
    if R2 <= L2 or B2 <= T2:
        L2, T2, R2, B2 = L, T, R, B
    probes = [
        ( (L2+R2)//2, (T2+B2)//2 ),
        ( L2, T2 ),
        ( R2-1, T2 ),
        ( L2, B2-1 ),
        ( R2-1, B2-1 ),
    ]
    filt_probes = []
    for x,y in probes:
        skip = False
        for ir in ignore_rects:
            if x >= ir[0] and x < ir[2] and y >= ir[1] and y < ir[3]:
                skip = True; break
        if not skip:
            filt_probes.append((x,y))
    if not filt_probes:
        filt_probes = probes
    target_root = user32.GetAncestor(wt.HWND(hwnd), GA_ROOT) or hwnd
    for x,y in filt_probes:
        root_at_pt = _root_hwnd_from_point(x, y)
        if root_at_pt == target_root:
            return True
    return False

def click(x, y, focus_hwnd=None, ensure_move=True, settle_ms=30, clicks=None):
    x = int(x); y = int(y)
    if clicks is None:
        try:
            clicks = int(str(CFG.get("mouse_clicks","1")).strip() or "1")
        except Exception:
            clicks = 1
    try:
        _ULONG_PTR = wt.ULONG_PTR
    except AttributeError:
        _ULONG_PTR = ctypes.c_size_t
    M_MOVE=0x0001; M_DOWN=0x0002; M_UP=0x0004; M_ABS=0x8000; M_VIRTUALDESK=0x4000; M_NOCOAL=0x2000
    class MOUSEINPUT(ctypes.Structure):
        _fields_=[("dx",wt.LONG),("dy",wt.LONG),("mouseData",wt.DWORD),("dwFlags",wt.DWORD),("time",wt.DWORD),("dwExtraInfo",_ULONG_PTR)]
    class INPUT(ctypes.Structure):
        _fields_=[("type",wt.DWORD),("mi",MOUSEINPUT)]
    def _virt_to_abs(xp,yp):
        vx=user32.GetSystemMetrics(76); vy=user32.GetSystemMetrics(77); vw=user32.GetSystemMetrics(78); vh=user32.GetSystemMetrics(79)
        ax=int((xp-vx)*65535/max(1,vw-1)); ay=int((yp-vy)*65535/max(1,vh-1))
        return ax,ay
    def send_move_abs(xp,yp):
        ax,ay=_virt_to_abs(xp,yp)
        inp=INPUT(0,MOUSEINPUT(ax,ay,0,M_MOVE|M_ABS|M_VIRTUALDESK|M_NOCOAL,0,0))
        return _send_input_checked(inp,"SendInput(MOVE_ABS)")
    def send_move(dx,dy):
        inp=INPUT(0,MOUSEINPUT(dx,dy,0,M_MOVE|M_NOCOAL,0,0))
        return _send_input_checked(inp,"SendInput(MOVE)")
    def send_down():
        inp=INPUT(0,MOUSEINPUT(0,0,0,M_DOWN,0,0))
        return _send_input_checked(inp,"SendInput(DOWN)")
    def send_up():
        inp=INPUT(0,MOUSEINPUT(0,0,0,M_UP,0,0))
        return _send_input_checked(inp,"SendInput(UP)")
    def legacy_move_abs(xp,yp):
        ax,ay=_virt_to_abs(xp,yp)
        ctypes.windll.user32.mouse_event(M_MOVE|M_ABS|M_VIRTUALDESK,ax,ay,0,0)
    if focus_hwnd:
        force_foreground(focus_hwnd)
        time.sleep(0.05)
    user32.SetCursorPos(x,y)
    if ensure_move:
        ok=send_move_abs(x,y)
        if not ok:
            legacy_move_abs(x,y)
        send_move(+1,0); send_move(-1,0)
        ctypes.windll.user32.mouse_event(M_MOVE, 1, 0, 0, 0)
        ctypes.windll.user32.mouse_event(M_MOVE,-1, 0, 0, 0)
        time.sleep(max(8,settle_ms)/1000.0)
    for _ in range(max(1,int(clicks))):
        ctypes.windll.user32.mouse_event(0x0002,0,0,0,0)
        time.sleep(0.02)
        ctypes.windll.user32.mouse_event(0x0004,0,0,0,0)

def set_status(s):
    global _status; _status = s

def status(msg: str):
    global _last_status, _status
    m = str(msg or "")
    if m == _last_status:
        return
    _last_status = m
    _status = m
    send("status", {"status": m})
    cb = STATUS_CB
    if cb:
        try:
            cb(m)
            return
        except Exception:
            pass

def load_png(path):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None: raise FileNotFoundError(path)
    return im

def list_pngs(root):
    return [(os.path.relpath(p, root), p)
            for p in glob.glob(os.path.join(root,"**","*.png"), recursive=True)]

def list_items_pngs(root):
    nb = os.path.join(root, "items")
    pairs = []
    for p in glob.glob(os.path.join(nb, "*.png")):
        pairs.append((os.path.relpath(p, root), p))
    return pairs

def grab(_unused_sct, L, T, R, B):
    w, h = R - L, B - T
    if w <= 0 or h <= 0:
        return None
    with mss() as sct:
        img = sct.grab({"left": L, "top": T, "width": w, "height": h})
    arr = np.frombuffer(img.rgb, dtype=np.uint8).reshape((h, w, 3))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)

def _auto_scales(screen_shape, tmpl_shape, min_scale=0.20, max_scale=1.60, min_px=10):
    if screen_shape is None or tmpl_shape is None:
        return [1.0]
    H, W = (int(screen_shape[0]), int(screen_shape[1]))
    th, tw = (int(tmpl_shape[0]), int(tmpl_shape[1]))
    if th <= 0 or tw <= 0 or H <= 0 or W <= 0:
        return [1.0]

    max_fit_scale = min((W - 1) / tw, (H - 1) / th)
    max_fit_scale = max(0.05, min(max_scale, max_fit_scale))
    min_fit_scale = max(min_px / max(1, tw), min_px / max(1, th), min_scale)
    if max_fit_scale < min_fit_scale:
        return [max(0.05, max_fit_scale)]

    base = [0.20, 0.25, 0.33, 0.40, 0.50, 0.60, 0.67, 0.75, 0.80, 0.90,
            1.00, 1.10, 1.20, 1.33, 1.40, 1.50, 1.60]
    scales = [s for s in base if min_fit_scale <= s <= max_fit_scale]

    if len(scales) < 6:
        lo, hi = (min_fit_scale, max_fit_scale)
        if hi <= lo:
            scales = [lo]
        else:
            steps = max(6, int(round( (hi/lo) ** 0.0 )))
            ratios = np.linspace(0.0, 1.0, steps)
            scales = [lo * (hi/lo) ** r for r in ratios]

    out = []
    for s in scales:
        if not out or abs(out[-1] - s) > 1e-6:
            out.append(s)
    return out

def _interp_for_template(tmpl, scale):
    g = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(g, 80, 160)
    edge_density = edges.mean() / 255.0
    is_pixel_art = edge_density < 0.055
    if is_pixel_art:
        return cv2.INTER_NEAREST, True
    return (cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR), False

def _edge_match_score(screen, rt):
    sg = cv2.Canny(cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY), 80, 160)
    tg = cv2.Canny(cv2.cvtColor(rt,     cv2.COLOR_BGR2GRAY), 80, 160)
    res = cv2.matchTemplate(sg, tg, cv2.TM_CCOEFF_NORMED)
    _, v, _, _ = cv2.minMaxLoc(res)
    return float(v)

def match_any(screen, tmpl, thr, *, mask=None, return_box=False, scales=None):
    if screen is None or tmpl is None:
        return False, None
    H, W = screen.shape[:2]
    th, tw = tmpl.shape[:2]
    scr_g = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    tmp_g = cv2.cvtColor(tmpl,  cv2.COLOR_BGR2GRAY)
    if scales is None:
        scales = _auto_scales((H, W), (th, tw))
    best = (0.0, None, None)
    for s in scales:
        w = max(8, int(tw * s)); h = max(8, int(th * s))
        if w > W or h > H:
            continue
        interp, is_pixel = _interp_for_template(tmpl, s)
        rt = cv2.resize(tmpl, (w, h), interpolation=interp)
        rg = cv2.resize(tmp_g, (w, h), interpolation=interp)
        if mask is not None:
            rm = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)
            rc = cv2.matchTemplate(screen, rt, cv2.TM_CCORR_NORMED, mask=rm)
        else:
            rc = cv2.matchTemplate(screen, rt, cv2.TM_CCOEFF_NORMED)
        rgm = cv2.matchTemplate(scr_g, rg, cv2.TM_CCOEFF_NORMED)
        vc, lc = cv2.minMaxLoc(rc)[1], cv2.minMaxLoc(rc)[3]
        vg, lg = cv2.minMaxLoc(rgm)[1], cv2.minMaxLoc(rgm)[3]
        v0, loc0 = (vc, lc) if vc >= vg else (vg, lg)
        if is_pixel:
            v = v0
            loc = loc0
        else:
            ve = _edge_match_score(screen, rt)
            if v0 >= vc:
                loc = loc0
            else:
                loc = lc
            v = 0.6 * v0 + 0.4 * ve
        if v > best[0]:
            best = (v, loc, (w, h))
    sc, loc, wh = best
    if sc >= thr and loc is not None:
        x, y = loc; w, h = wh
        return (True, (x, y, w, h)) if return_box else (True, (x + w//2, y + h//2))
    return False, None

def match_box_masked(screen, tmpl, thr, obj_mask=None, scales=None):
    return match_any(screen, tmpl, thr, mask=obj_mask, return_box=True, scales=scales)

def match_box(screen, tmpl, thr, scales=None):
    return match_any(screen, tmpl, thr, return_box=True,  scales=scales)

def match(screen, tmpl, thr, scales=None):
    return match_any(screen, tmpl, thr, return_box=False, scales=scales)

def best_match_score(screen, tmpl, scales=None):
    if screen is None or tmpl is None:
        return -1.0, None, None
    H, W = screen.shape[:2]
    th, tw = tmpl.shape[:2]
    scr_g = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    tmp_g_base = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)

    if scales is None:
        scales = _auto_scales((H, W), (th, tw))

    best = (-1.0, None, None)
    for s in scales:
        w = max(8, int(tw * s)); h = max(8, int(th * s))
        if w > W or h > H:
            continue
        rt = cv2.resize(tmpl, (w, h), interpolation=cv2.INTER_AREA)
        rg = cv2.resize(tmp_g_base, (w, h), interpolation=cv2.INTER_AREA)
        res_c = cv2.matchTemplate(screen, rt, cv2.TM_CCOEFF_NORMED)
        res_g = cv2.matchTemplate(scr_g, rg, cv2.TM_CCOEFF_NORMED)
        _, vc, _, lc = cv2.minMaxLoc(res_c)
        _, vg, _, lg = cv2.minMaxLoc(res_g)
        v, loc = (vc, lc) if vc >= vg else (vg, lg)
        if v > best[0]:
            best = (v, loc, (w, h))
    return best

def preprocess_for_white_text(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    S, V = hsv[:, :, 1], hsv[:, :, 2]
    mask = (S < 90) & (V > 150)
    img = np.zeros(S.shape, np.uint8)
    img[mask] = 255
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=2)
    if max(img.shape) < 1200:
        img = cv2.resize(img, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    return img

def preprocess_for_blue_text(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    mask = (H >= 100) & (H <= 140) & (S >= 80) & (V >= 80)
    img = np.zeros_like(H, dtype=np.uint8)
    img[mask] = 255
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=2)
    if max(img.shape) < 900:
        img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    return img

def ocr_text(bin_img):
    cfg_primary = (
        "--oem 1 --psm 6 -l eng "
        "-c preserve_interword_spaces=1 "
        "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz0123456789?'!.:,-()[] "
    )
    data = pytesseract.image_to_data(bin_img, config=cfg_primary, output_type=pytesseract.Output.DICT)
    n_boxes = len(data.get("text", []))
    lines = {}
    for i in range(n_boxes):
        word = (data["text"][i] or "").strip()
        if not word:
            continue
        key = (
            data.get("block_num", [0])[i],
            data.get("par_num", [0])[i],
            data.get("line_num", [0])[i],
        )
        if key not in lines:
            lines[key] = []
        lines[key].append((data.get("left", [0])[i], word, data.get("top", [0])[i]))

    ordered_lines = []
    for _, words in lines.items():
        words.sort(key=lambda x: x[0])
        line_text = " ".join([w[1] for w in words]).strip()
        if line_text:
            ordered_lines.append((words[0][2], line_text))

    ordered_lines.sort(key=lambda x: x[0])
    reconstructed = "\n".join([line[1] for line in ordered_lines]).strip()
    if reconstructed:
        return reconstructed

    cfg_single = (
        "--oem 1 --psm 7 -l eng "
        "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz0123456789?'!.:,-()[] "
    )
    text = pytesseract.image_to_string(bin_img, config=cfg_single).strip()
    if text:
        return text

    return pytesseract.image_to_string(bin_img, config="--oem 1 --psm 6 -l eng").strip()

def _ocr_lines_with_boxes(bin_img):
    cfg = ("--oem 1 --psm 6 -l eng "
           "-c preserve_interword_spaces=1 "
           "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ"
           "abcdefghijklmnopqrstuvwxyz0123456789'!-:.,()[] ")
    data = pytesseract.image_to_data(bin_img, config=cfg, output_type=pytesseract.Output.DICT)
    n = len(data.get("text", []))
    by_line = {}
    for i in range(n):
        t = (data["text"][i] or "").strip()
        if not t:
            continue
        key = (data.get("block_num", [0])[i], data.get("par_num", [0])[i], data.get("line_num", [0])[i])
        left = int(data.get("left", [0])[i]); top = int(data.get("top", [0])[i])
        width = int(data.get("width", [0])[i]); height = int(data.get("height", [0])[i])
        by_line.setdefault(key, []).append((left, top, t, width, height))

    lines = []
    for _, words in by_line.items():
        words.sort(key=lambda w: w[0])
        line_text = " ".join(w[2] for w in words).strip()
        if not line_text:
            continue
        x0 = min(w[0] for w in words); y0 = min(w[1] for w in words)
        x1 = max(w[0] + w[3] for w in words); y1 = max(w[1] + w[4] for w in words)
        lines.append((line_text, (x0, y0, x1 - x0, y1 - y0)))
    lines.sort(key=lambda it: it[1][1])
    return lines

def parse_region(s): return [float(x.strip()) for x in s.split(",")]

def perc_rect(cx, perc):
    L,T,R,B = cx; W=R-L; H=B-T
    pl,pt,pr,pb = perc
    return int(L+pl*W), int(T+pt*H), int(L+pr*W), int(T+pb*H)

def subrect(parent_rect, perc):
    L, T, R, B = parent_rect
    W, H = R - L, B - T
    pl, pt, pr, pb = perc
    return (
        int(L + pl * W),
        int(T + pt * H),
        int(L + pr * W),
        int(T + pb * H),
    )

def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

def _norm_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())

def fuzzy_contains(hay: str, needle: str, min_ratio: float = None) -> bool:
    if min_ratio is None:
        try:
            min_ratio = float(CFG.get("fuzzy_ratio", 0.90))
        except Exception:
            min_ratio = 0.90

    if not hay or not needle:
        return False

    H, N = hay, needle
    n = len(N)

    if N in H:
        return True

    for wlen in range(max(1, n - 2), n + 3):
        for i in range(0, max(0, len(H) - wlen) + 1):
            w = H[i:i + wlen]
            if difflib.SequenceMatcher(None, w, N).ratio() >= min_ratio:
                return True
    return False

def _fuzzy_ratio_contains(hay_norm: str, needle_norm: str) -> float:
    if not hay_norm or not needle_norm:
        return 0.0
    if needle_norm in hay_norm:
        return 1.0
    n = len(needle_norm)
    best = 0.0
    for wlen in range(max(1, n-2), n+3):
        for i in range(0, max(0, len(hay_norm)-wlen)+1):
            w = hay_norm[i:i+wlen]
            r = difflib.SequenceMatcher(None, w, needle_norm).ratio()
            if r > best:
                best = r
    return best

def _find_click_for_ball_text(bgr, desired_name: str, *, min_ratio: float = 0.85):
    if not desired_name:
        return None

    want_vars = _ball_variants(desired_name)
    if not want_vars:
        return None

    bin_img = preprocess_for_blue_text(bgr)

    try:
        sx = float(bin_img.shape[1]) / float(bgr.shape[1])
        sy = float(bin_img.shape[0]) / float(bgr.shape[0])
    except Exception:
        sx = sy = 1.0
    if sx <= 0: sx = 1.0
    if sy <= 0: sy = 1.0

    def roi_center(x, y, w, h):
        cx = int(round((x + w / 2.0) / sx))
        cy = int(round((y + h / 2.0) / sy))
        return (cx, cy)

    lines = _ocr_lines_with_boxes(bin_img)

    best_r = 0.0
    best_box = None

    for text, (x, y, w, h) in lines:
        tnorm = _norm(text)
        if not tnorm:
            continue

        cand = [tnorm, re.sub(r"x?\d+", "", tnorm)]
        if "ball" in tnorm:
            pre, _ = tnorm.split("ball", 1)
            cand.extend([pre + "ball", pre])

        seen = set()
        cand = [c for c in cand if c and not (c in seen or seen.add(c))]

        for c in cand:
            for wn in want_vars:
                if wn in c or c in wn:
                    return roi_center(x, y, w, h)

        r = max(difflib.SequenceMatcher(None, c, wn).ratio() for wn in want_vars for c in cand)
        if r > best_r:
            best_r = r
            best_box = (x, y, w, h)

    if best_box and best_r >= min_ratio:
        x, y, w, h = best_box
        return roi_center(x, y, w, h)

    return None

def _best_from_targets_order(hay_norm: str, *, min_ratio: float = None):
    hay_norm = _norm_name(hay_norm)
    if min_ratio is None:
        try:
            min_ratio = float(CFG.get("fuzzy_ratio", 0.90))
        except Exception:
            min_ratio = 0.90

    order_names, order_norms = _split_targets_order()
    if not hay_norm or not order_names:
        return None, False, 0.0

    for i, nn in enumerate(order_norms):
        if nn and nn == hay_norm:
            return order_names[i], True, 1.0

    contain = [(i, nn) for i, nn in enumerate(order_norms) if nn and (nn in hay_norm)]
    if contain:
        best_i, _ = max(contain, key=lambda t: len(t[1]))
        return order_names[best_i], False, 1.0

    scored = []
    for i, nn in enumerate(order_norms):
        if not nn:
            continue
        r = _fuzzy_ratio_contains(hay_norm, nn)
        scored.append((r, len(nn), i))

    if not scored:
        return None, False, 0.0

    scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
    best_r, _, best_i = scored[0]
    if best_r < min_ratio:
        return None, False, best_r
    return order_names[best_i], False, best_r

def _split_targets_order():
    raw = (CFG.get("targets_order") or "").strip()
    if not raw:
        return [], []
    names = [p.strip() for p in raw.replace(",", "|").split("|") if p.strip()]
    norms = [_norm_name(n) for n in names]
    return names, norms

def _ball_variants(name: str):
    base = (name or "").strip()
    if not base:
        return []
    tokens = [t for t in re.split(r"\s+", base) if t]
    full_norm = _norm(base)
    no_ball_norm = _norm(re.sub(r"\bball\b", "", base, flags=re.I))
    first_tok_norm = _norm(tokens[0]) if tokens else ""
    clipped_norm = full_norm[:-1] if len(full_norm) > 5 else full_norm
    variants = []
    for v in (full_norm, no_ball_norm, first_tok_norm, clipped_norm):
        if v and v not in variants:
            variants.append(v)
    return variants

def bot_loop(hwnd=None):
    try:
        load_ini()
        ensure_tesseract_cmd()
        try:
            session_start()
        except Exception as e:
            _log(f"[ERROR] Couldn't start session: {e}")

        hwnd = hwnd or find_roblox_hwnd()
        if not hwnd:
            status("error: Roblox not found")
            return

        FLEE_NORM      = _norm_name("You have successfully fled!")
        ENCOUNTER_NORM = _norm_name("You have encountered a wild")
        SHINY_NORM     = _norm_name("It's a shiny")
        GOTCHA_NORM    = _norm_name("Gotcha")
        WAS_CAUGHT_NORM = _norm_name("was caught")
        ADDED_BOX_NORM = _norm_name("added to box")
        HOLDING_RAW    = "Itseemstobeholdinga"
        HOLDING_NORM   = _norm_name("It seems to be holding a")
        HOLDING_NORM_TRIG = re.sub(r"\s+", "", "It seems to be holding a").lower()
        ROLL_MS = 2400
        ENC_LATCH_RESET = 0.50
        RUN_STABLE_HITS = 2
        BAG_STABLE_HITS = 1
        HOLDING_PRIOR_MS = 3.5
        SELF_FLEE_IGNORE = 0.75
        SELECT_TO_USE_DELAY = 0.75
        BAG_STABLE_HITS = 2
        bag_open_since = 0.0
        bag_use_attempt_ts = 0.0

        out_of_balls = False
        out_of_balls_since = 0.0
        out_of_balls_dm_sent = False
        last_keepalive_click = 0.0
        no_selected_ball_missing_since = 0.0

        def _ocr_norm(s: str) -> str:
            if not s:
                return ""
            s = re.sub(r"\s+", "", s)
            trans = str.maketrans({'|': 'l','1': 'l','¡': 'i','İ': 'i'})
            s = s.translate(trans).lower()
            s = re.sub(r'(^|[^a-z])ltseems', r'\1itseems', s)
            return s

        try:
            _log(f"Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")
            _log(f"Tesseract version: {pytesseract.get_tesseract_version()}")
        except Exception as e:
            _log(f"Tesseract version check failed: {e}")

        bag_png = load_png(os.path.join(OTHER_DIR, CFG["bag_image"]))
        run_png = load_png(os.path.join(OTHER_DIR, CFG["run_image"]))
        def _parse_use_choice(value):
            raw = str(value or "").strip()
            if raw.startswith("auto:"):
                return [x.replace(".png", "").replace(".PNG", "").strip() for x in raw[5:].split("|") if x.strip()][:3]
            v = raw.replace(".png", "").replace(".PNG", "").strip()
            return [v] if v else []
        desired_ball_names = _parse_use_choice(CFG.get("use_choice"))
        desired_ball_name = desired_ball_names[0] if desired_ball_names else ""

        perc_target   = parse_region(CFG["target_region"])
        perc_pokemon_name = parse_region(CFG.get("pokemon_name_region", "0.05,0.15,0.35,0.25"))
        perc_hud      = parse_region(CFG["hud_region"])
        perc_use      = parse_region(CFG.get("use_region", CFG["hud_region"]))
        perc_ball     = parse_region(CFG.get("ball_region", CFG["target_region"]))
        perc_bag_hud  = parse_region(CFG.get("bag_hud_region", "0.00,0.00,0.50,1.00"))
        perc_run_hud  = parse_region(CFG.get("run_hud_region", "0.50,0.00,1.00,1.00"))

        recent_norm = deque()
        roi_logged = False
        last_ocr_text = ""

        encounter_active = False
        encounter_counted = False
        last_enc_seen_ts = 0.0

        flee_latched = False
        last_flee_seen_ts = 0.0
        FLEE_RESET_GAP = 0.50
        ignore_flee_until = 0.0

        best_name = ""
        best_norm = ""
        best_is_exact = False
        best_score = 0.0
        want_capture = False
        last_best_announced = ""

        bag_hits = 0
        run_hits = 0

        last_holding_norm = ""
        last_holding_seen = 0.0
        
        agg_last_log = 0.0
        RAW_HOLD_GRACE_MS = 450
        battle_poke_norm = ""
        battle_shiny = False

        last_status_msg = None
        def set_status(msg: str):
            nonlocal last_status_msg
            if msg != last_status_msg:
                status(msg)
                last_status_msg = msg

        def _cfg_enabled_maps():
            raw = (CFG.get("enabled_targets", "") or "").strip()
            names = [x.strip() for x in raw.split("|") if x.strip()]
            norm_to_pretty = {_norm_name(x): x for x in names}
            enabled_norms = set(norm_to_pretty.keys())
            return enabled_norms, norm_to_pretty

        def _parse_enabled_pokemon_cfg_str(raw: str):
            raw = (raw or "").strip()
            cfg = {}
            for part in [p.strip() for p in raw.split("|") if p.strip()]:
                if "[" in part and part.endswith("]"):
                    name, rest = part.split("[", 1)
                    name = name.strip()
                    rest = rest[:-1]
                    shiny = False
                    amount = "inf"
                    for kv in rest.split(","):
                        if "=" not in kv:
                            continue
                        k, v = kv.split("=", 1)
                        k = k.strip().lower(); v = v.strip().lower()
                        if k in ("s","shiny"):
                            shiny = v in ("1","true","yes","on")
                        elif k in ("a","amount"):
                            if v in ("inf","∞"):
                                amount = "inf"
                            else:
                                try: amount = str(max(1, int(v)))
                                except: amount = "inf"
                    cfg[name] = {"shiny": shiny, "amount": amount}
                else:
                    name = part
                    cfg[name] = {"shiny": False, "amount": "inf"}
            return cfg
        
        def _format_enabled_pokemon_cfg_str(cfg: dict):
            items = []
            for name in sorted(cfg.keys(), key=lambda s: s.lower()):
                d = cfg[name]
                s = "1" if d.get("shiny") else "0"
                a = str(d.get("amount", "inf")).lower()
                if a != "inf":
                    try: a = str(max(1, int(a)))
                    except: a = "inf"
                items.append(f"{name}[s={s},a={a}]")
            return "|".join(items)
        
        def _load_poke_cfg_map():
            raw = CFG.get("enabled_pokemon_targets", "") or ""
            m = _parse_enabled_pokemon_cfg_str(raw)
            norm_to_key = {_norm_name(k): k for k in m.keys()}
            return m, norm_to_key
        
        def _save_poke_cfg_map(m: dict):
            CFG["enabled_pokemon_targets"] = _format_enabled_pokemon_cfg_str(m)
            save_ini()
        
        def _find_key_ci(m: dict, name_token_norm: str):
            _, norm_to_key = _load_poke_cfg_map()
            if name_token_norm in norm_to_key:
                return norm_to_key[name_token_norm]
            for k in m.keys():
                if _norm_name(k) == name_token_norm:
                    return k
            return None
    
        def _notify_poke_cfg_changed():
            try:
                send("settings", dict(CFG))
            except:
                pass
            try:
                cb = globals().get("UI_POKE_CFG_CHANGED")
                if callable(cb):
                    cb()
            except:
                pass
        
        def _pretty_pokemon_from_norm(enc_name_norm: str):
            enc_name_norm = _norm_name(enc_name_norm or "")
            if not enc_name_norm:
                return ""
            for n in pokemon_names:
                if _norm_name(n) == enc_name_norm:
                    return n
            return enc_name_norm

        def _dec_amount_if_finite(enc_name_norm: str):
            m, _ = _load_poke_cfg_map()
            key = _find_key_ci(m, enc_name_norm)
            if not key:
                return
            d = m.get(key, {})
            a = str(d.get("amount", "inf")).lower()
            if a == "inf":
                return
            try:
                n = max(0, int(a) - 1)
            except:
                n = 0
            if n <= 0:
                m.pop(key, None)
                _log(f"[POKEMON] Target amount complete: {key}")
            else:
                d["amount"] = str(n)
                m[key] = d
                _log(f"[POKEMON] Target amount reduced: {key} -> {n}")
            _save_poke_cfg_map(m)
            _notify_poke_cfg_changed()

        def _agg_norm():
            return "|".join(t for _, t in recent_norm)
        
        def _clear_buffers():
            recent_norm.clear()
        
        def _reset_target_state():
            nonlocal best_name, best_norm, best_is_exact, best_score, want_capture, last_best_announced, last_holding_norm, last_holding_seen, battle_poke_norm, battle_shiny
            _clear_buffers()
            best_name = ""
            best_norm = ""
            best_is_exact = False
            best_score = 0.0
            want_capture = False
            last_best_announced = ""
            last_holding_norm = ""
            last_holding_seen = 0.0
            battle_poke_norm = ""
            battle_shiny = False
        
        def _ocr_from_target(sct, rect):
            nonlocal roi_logged, last_ocr_text
            roi = grab(sct, *rect)
            if (not roi_logged) and (roi is not None):
                h, w = roi.shape[:2]
                _log(f"ROI size: {w}x{h}")
                roi_logged = True
            if roi is None or roi.size == 0:
                return ""
            try:
                bin_img = preprocess_for_white_text(roi)
                txt = ocr_text(bin_img).strip()
                if txt:
                    last_ocr_text = txt
                    return txt
                return ""
            except Exception:
                return ""

        def _encounter_name_rescue_burst(sct, rect, first_txt, duration=0.70):
            best_txt = first_txt or ""
            best_name = _extract_pokemon_from_norm_text(_ocr_norm(best_txt))
            t0 = time.time()
            while not best_name and time.time() - t0 < duration and not stop_flag.is_set():
                time.sleep(0.04)
                txt = _ocr_from_target(sct, rect)
                if txt:
                    _append_norm(txt)
                    name = _extract_pokemon_from_norm_text(_ocr_norm(txt)) or _extract_pokemon_from_recent()
                    if name:
                        best_txt = txt
                        best_name = name
                        break
            return best_txt, best_name

        def _pokemon_name_from_region_text(raw_txt: str) -> str:
            n = _ocr_norm(raw_txt)
            if not n or len(n) < 4:
                return ""
            hits = []
            for name in pokemon_names:
                base = _norm_name(name)
                variants = [base]
                parts = [p for p in re.split(r"[-\s]+", name) if p]
                if len(parts) > 1:
                    variants.append(_norm_name(" ".join(reversed(parts))))
                for variant in variants:
                    if len(variant) >= 4 and (variant in n or n in variant):
                        hits.append((len(variant), base))
            if hits:
                return sorted(hits, reverse=True)[0][1]
            norms = [_norm_name(name) for name in pokemon_names]
            close = difflib.get_close_matches(n, norms, n=1, cutoff=0.82)
            return close[0] if close else ""

        def _ocr_from_pokemon_name_region(sct, rect):
            roi = grab(sct, *rect)
            if roi is None or roi.size == 0:
                return ""
            try:
                txt = ocr_text(preprocess_for_white_text(roi)).strip()
                if txt:
                    name = _pokemon_name_from_region_text(txt)
                    if name:
                        return name
                return ""
            except Exception:
                return ""

        def _append_norm(raw_txt):
            if not raw_txt:
                return
            log_seen_once(raw_txt)
            n = _norm_name(raw_txt)
            if not n:
                return
            now = int(time.time() * 1000)
            recent_norm.append((now, n))
            while recent_norm and (now - recent_norm[0][0] > ROLL_MS):
                recent_norm.popleft()

        def _scan_holding_from_raw(raw_txt: str):
            nonlocal last_holding_norm, last_holding_seen
            if not raw_txt:
                return
            s_norm = _ocr_norm(raw_txt)
            trig = HOLDING_NORM_TRIG
            if trig in s_norm or fuzzy_contains(s_norm, trig):
                j = s_norm.find(trig)
                if j < 0:
                    j = s_norm.find(trig[:6])
                tail = s_norm[(j + (len(trig) if j >= 0 else 0)):] if j >= 0 else s_norm
                tail = tail.split("!", 1)[0]
                tail = re.sub(r"[^a-z0-9]", "", tail)
                if tail:
                    last_holding_norm = _norm_name(tail)
                    last_holding_seen = time.time()
                    _log(f"HOLD raw -> token '{tail}'")

        def _scan_holding_from_agg():
            nonlocal last_holding_norm, last_holding_seen, agg_last_log
            if not recent_norm:
                return
            if (time.time() - last_holding_seen) * 1000.0 <= RAW_HOLD_GRACE_MS:
                return
            now = time.time()
            if now - agg_last_log < 2.0:
                return
        
            trig = HOLDING_NORM_TRIG
            i = len(recent_norm) - 1
            hit_idx = -1
            while i >= 0:
                _, tok = recent_norm[i]
                s = _ocr_norm(tok)
                if trig in s:
                    hit_idx = i
                    break
                i -= 1
            if hit_idx < 0:
                return
        
            _, tok0 = recent_norm[hit_idx]
            s0 = _ocr_norm(tok0)
            j = s0.find(trig)
            tail = s0[j + len(trig):] if j >= 0 else ""
            if not tail and hit_idx + 1 < len(recent_norm):
                _, tok1 = recent_norm[hit_idx + 1]
                tail = _ocr_norm(tok1)
            tail = tail.split("!", 1)[0]
            tail = re.sub(r"[^a-z0-9]", "", tail)
            if not tail:
                return
        
            last_holding_norm = _norm_name(tail)
            last_holding_seen = now
            agg_last_log = now
            _log(f"HOLD agg -> token '{tail}'")

        def _resolve_from_holding():
            nonlocal best_name, best_norm, best_is_exact, best_score, want_capture, last_best_announced
            if not last_holding_norm:
                return False
            bn, ex, sc = _best_from_targets_order(last_holding_norm)
            if not bn:
                return False
            best_name = bn
            best_norm = _norm_name(bn)
            best_is_exact = bool(ex)
            best_score = float(sc or 0.0)
            enabled_norms, norm_to_pretty = _cfg_enabled_maps()
            want_capture = bool(best_norm and (best_norm in enabled_norms))
            pretty = norm_to_pretty.get(best_norm, best_name)
            if pretty and pretty != last_best_announced:
                set_status(f"target read: {pretty}")
                _log(f"OCR best -> {pretty} (exact={best_is_exact} score={best_score:.3f})")
                last_best_announced = pretty
            return True

        def _extract_pokemon_from_norm_text(s_norm: str) -> str:
            if not s_norm:
                return ""
            def _clean_pokemon_token(token: str) -> str:
                token = re.sub(r"[^a-z0-9]", "", token or "")
                for prefix in ("itsashiny", "itshiny", "shiny"):
                    if token.startswith(prefix):
                        token = token[len(prefix):]
                return token
            def _tail_after(trig: str) -> str:
                j = s_norm.find(trig)
                if j < 0:
                    if not fuzzy_contains(s_norm, trig):
                        return ""
                    j = s_norm.find(trig[:6])
                tail = s_norm[(j + (len(trig) if j >= 0 else 0)):] if j >= 0 else s_norm
                tail = tail.split("!", 1)[0]
                return _clean_pokemon_token(tail)

            for TRIG in (SHINY_NORM, ENCOUNTER_NORM):
                if TRIG in s_norm or fuzzy_contains(s_norm, TRIG):
                    name_token = _tail_after(TRIG)
                    if name_token:
                        return name_token
            return ""

        def _extract_pokemon_from_recent() -> str:
            if not recent_norm:
                return ""
            TRIGS = (ENCOUNTER_NORM, SHINY_NORM)
            i = len(recent_norm) - 1
            while i >= 0:
                _, tok = recent_norm[i]
                s = _ocr_norm(tok)
                if any(t in s or fuzzy_contains(s, t) for t in TRIGS):
                    for TRIG in TRIGS:
                        if TRIG in s or fuzzy_contains(s, TRIG):
                            j = s.find(TRIG)
                            if j < 0:
                                j = s.find(TRIG[:6])
                            tail = s[(j + (len(TRIG) if j >= 0 else 0)):] if j >= 0 else ""
                            tail = tail.split("!", 1)[0]
                            tail = re.sub(r"[^a-z0-9]", "", tail)
                            for prefix in ("itsashiny", "itshiny", "shiny"):
                                if tail.startswith(prefix):
                                    tail = tail[len(prefix):]
                            if tail:
                                return tail
                            if i + 1 < len(recent_norm):
                                _, tok2 = recent_norm[i + 1]
                                s2 = _ocr_norm(tok2)
                                s2 = s2.split("!", 1)[0]
                                s2 = re.sub(r"[^a-z0-9]", "", s2)
                                if s2:
                                    return s2
                    break
                i -= 1
            return ""

        def _try_log_pokemon_name(raw_txt: str):
            nonlocal battle_poke_norm
            s_norm = _ocr_norm(raw_txt)
            name_norm = _extract_pokemon_from_norm_text(s_norm)
            if not name_norm:
                name_norm = _extract_pokemon_from_recent()
            if name_norm:
                battle_poke_norm = _norm_name(name_norm)
                globals()['last_pokemon_seen'] = battle_poke_norm
                shiny_label = "shiny " if battle_shiny or (SHINY_NORM in s_norm) or fuzzy_contains(s_norm, SHINY_NORM) else ""
                _log(f"[POKEMON] Encountered: {shiny_label}{battle_poke_norm}")

        def _bag_seems_open(sct, rect_ball) -> bool:
            roi = grab(sct, *rect_ball)
            if roi is None:
                return False
            try:
                for ball_name in desired_ball_names:
                    pt = _find_click_for_ball_text(roi, ball_name, min_ratio=float(CFG.get("fuzzy_ratio", 0.90)))
                    if pt:
                        return True
                txt = ocr_text(preprocess_for_white_text(roi)).strip()
                n = _ocr_norm(txt)
                return ("ball" in n) or ("use" in n)
            except Exception:
                return False

        def _wait_bag_close(sct, rect_ball, timeout=4.0):
            t0 = time.time()
            while time.time() - t0 < timeout and not stop_flag.is_set():
                if not _bag_seems_open(sct, rect_ball):
                    return True
                time.sleep(0.08)
            return not _bag_seems_open(sct, rect_ball)

        def _find_ball_pt_fallback(roi, desired_name):
            base = (desired_name or "").strip()
            if not base:
                return None
            keys = []
            keys.append(base)
            no_ball = re.sub(r"\bball\b", "", base, flags=re.IGNORECASE).strip()
            if no_ball and no_ball not in keys:
                keys.append(no_ball)
            parts = base.split()
            if parts and parts[0] not in keys:
                keys.append(parts[0])
            ratios = [float(CFG.get("fuzzy_ratio", 0.90)), 0.86, 0.82]
            for k in keys:
                for r in ratios:
                    try:
                        pt = _find_click_for_ball_text(roi, k, min_ratio=r)
                    except Exception:
                        pt = None
                    if pt:
                        return pt
            return None

        def _format_desired_ball_names():
            return " > ".join(desired_ball_names) if desired_ball_names else "auto"

        def _find_priority_ball_pt(roi):
            for ball_name in desired_ball_names:
                pt = _find_ball_pt_fallback(roi, ball_name)
                if pt:
                    return ball_name, pt
            return "", None

        def _select_priority_ball(sct, rect_ball, log_prefix="Selecting ball"):
            if not desired_ball_names:
                return False
            ball_roi = grab(sct, *rect_ball)
            if ball_roi is None:
                return False
            ball_name, pt = _find_priority_ball_pt(ball_roi)
            if not pt:
                return False
            _log(f"{log_prefix}: {ball_name}")
            with CLICK_LOCK:
                click(rect_ball[0] + pt[0], rect_ball[1] + pt[1], focus_hwnd=hwnd)
            return True

        def _use_click_then_retry(sct, rect_use, rect_ball, desired_name):
            nonlocal bag_use_attempt_ts
            ux1, uy1, ux2, uy2 = rect_use
            cx_use = ux1 + (ux2 - ux1)//2
            cy_use = uy1 + (uy2 - uy1)//2

            def ball_visible():
                roi = grab(sct, *rect_ball)
                if roi is None:
                    return False
                try:
                    txt = ocr_text(preprocess_for_white_text(roi)).strip()
                    return "ball" in _ocr_norm(txt)
                except Exception:
                    return False

            def click_selected_ball():
                nonlocal out_of_balls, out_of_balls_since, out_of_balls_dm_sent, no_selected_ball_missing_since
                if not desired_ball_names:
                    return False

                if not _bag_seems_open(sct, rect_ball):
                    no_selected_ball_missing_since = 0.0
                    return False

                roi = grab(sct, *rect_ball)
                if roi is None:
                    return False

                selected_ball_name, pt = _find_priority_ball_pt(roi)
                if not pt:
                    if no_selected_ball_missing_since == 0.0:
                        # start timer only while bag + ball list are visible
                        try:
                            txt_probe = ocr_text(preprocess_for_white_text(roi)).strip().lower()
                            if ("ball" in txt_probe) or ("use" in txt_probe):
                                no_selected_ball_missing_since = time.time()
                        except Exception:
                            pass
                    else:
                        # after 15s, do one verification sweep before DM
                        if (time.time() - no_selected_ball_missing_since) >= 15.0 and not out_of_balls:
                            try:
                                _, pt2 = _find_priority_ball_pt(roi)
                            except Exception:
                                pt2 = None
                            if pt2:
                                no_selected_ball_missing_since = 0.0
                                return False
                            out_of_balls = True
                            out_of_balls_since = time.time()
                            set_status("selected balls depleted; keepalive enabled")
                            if not out_of_balls_dm_sent:
                                _play_out_of_balls_sound()
                                notify_out_of_balls(_format_desired_ball_names())
                                out_of_balls_dm_sent = True
                    return False

                no_selected_ball_missing_since = 0.0
                if out_of_balls:
                    out_of_balls = False
                    set_status("selected ball found; resuming")
                with CLICK_LOCK:
                    click(rect_ball[0] + pt[0], rect_ball[1] + pt[1], focus_hwnd=hwnd)
                return True

            if desired_ball_names:
                click_selected_ball()
                time.sleep(SELECT_TO_USE_DELAY)

            with CLICK_LOCK:
                click(cx_use, cy_use, focus_hwnd=hwnd)
            if bag_use_attempt_ts == 0.0:
                bag_use_attempt_ts = time.time()
            time.sleep(0.1)

            while not stop_flag.is_set() and ball_visible():
                if desired_ball_names:
                    clicked = click_selected_ball()
                    if not clicked:
                        time.sleep(0.1)
                        continue
                with CLICK_LOCK:
                    click(cx_use, cy_use, focus_hwnd=hwnd)
                time.sleep(0.1)

        def _followup_multiball(sct, target_rect, hud_rect, bag_hud_rect, run_hud_rect, use_rect, ball_rect):
            if _wait_bag_close(sct, ball_rect, timeout=4.0):
                session_inc("balls_used")
            else:
                deadline = time.time() + 3.0
                while time.time() < deadline and _bag_seems_open(sct, ball_rect) and not stop_flag.is_set():
                    _use_click_then_retry(sct, use_rect, ball_rect, desired_ball_name)
                    if _wait_bag_close(sct, ball_rect, timeout=0.6):
                        session_inc("balls_used")
                        break
                    time.sleep(0.1)
            while not stop_flag.is_set():
                if user32.IsIconic(wt.HWND(hwnd)) or not is_window_partially_visible(hwnd):
                    time.sleep(0.15)
                    continue
                txt_now = _ocr_from_target(sct, target_rect)
                n_now = _ocr_norm(txt_now)
                capture_done = (
                    GOTCHA_NORM in n_now
                    or WAS_CAUGHT_NORM in n_now
                    or ADDED_BOX_NORM in n_now
                    or fuzzy_contains(n_now, GOTCHA_NORM)
                    or fuzzy_contains(n_now, WAS_CAUGHT_NORM)
                    or fuzzy_contains(n_now, ADDED_BOX_NORM)
                )
                if capture_done:
                    _log("[RESULT] Capture confirmed")
                    return
                if ENCOUNTER_NORM in n_now or fuzzy_contains(n_now, ENCOUNTER_NORM):
                    _log("[RESULT] Capture resolved by next encounter fallback")
                    return
                if (time.time() >= ignore_flee_until) and (FLEE_NORM in n_now or fuzzy_contains(n_now, FLEE_NORM)):
                    _log("Flee text detected; stopping multi-ball throws")
                    return
                hud_full = grab(sct, *hud_rect)
                if hud_full is None:
                    time.sleep(0.08)
                    continue
                Lh, Th, Rh, Bh = hud_rect
                Lb, Tb, Rb, Bb = bag_hud_rect
                hud_bag = hud_full[(Tb - Th):(Bb - Th), (Lb - Lh):(Rb - Lh)]
                ok_bag, bag_pt_local = match(hud_bag, bag_png, CFG["bag_threshold"]) if hud_bag is not None else (False, None)
                if ok_bag and bag_pt_local is not None:
                    bag_pt = (bag_hud_rect[0] + bag_pt_local[0], bag_hud_rect[1] + bag_pt_local[1])
                    set_status("reopening bag…")
                    _log("[BALL] Capture failed — trying another ball")
                    with CLICK_LOCK:
                        click(bag_pt[0], bag_pt[1], focus_hwnd=hwnd)
                    time.sleep(0.18)
                    if desired_ball_names:
                        selected = False
                        t0 = time.time()
                        while time.time() - t0 < 1.10 and not selected:
                            selected = _select_priority_ball(sct, ball_rect)
                            if selected:
                                break
                            time.sleep(0.10)
                    time.sleep(SELECT_TO_USE_DELAY)
                    _use_click_then_retry(sct, use_rect, ball_rect, desired_ball_name)
                    if _wait_bag_close(sct, ball_rect, timeout=4.0):
                        session_inc("balls_used")
                    continue
                time.sleep(0.08)

        def _confirm_flee_or_retry(sct, target_rect, run_rect_click, timeout=1.5):
            t0 = time.time()
            while time.time() - t0 < timeout and not stop_flag.is_set():
                txt_now = _ocr_from_target(sct, target_rect)
                n_now = _ocr_norm(txt_now)
                if (time.time() >= ignore_flee_until) and (FLEE_NORM in n_now or fuzzy_contains(n_now, FLEE_NORM)):
                    _log("[RUN] Flee confirmed")
                    return True
                time.sleep(0.10)
            with CLICK_LOCK:
                click(run_rect_click[0], run_rect_click[1], focus_hwnd=hwnd)
            _log("[RUN] Retry click")
            time.sleep(0.35)
            txt_now = _ocr_from_target(sct, target_rect)
            n_now = _ocr_norm(txt_now)
            return (time.time() >= ignore_flee_until) and (FLEE_NORM in n_now or fuzzy_contains(n_now, FLEE_NORM))

        def _keepalive_worker():
            nonlocal last_keepalive_click
            j = 12
            while not stop_flag.is_set():
                if out_of_balls and (time.time() - last_keepalive_click) >= 300.0:
                    cx = get_client_rect(hwnd)
                    if cx:
                        x1, y1, x2, y2 = cx
                        mx = x1 + (x2 - x1)//2
                        my = y1 + (y2 - y1)//2
                        for _ in range(3):
                            dx = np.random.randint(-j, j+1)
                            dy = np.random.randint(-j, j+1)
                            with CLICK_LOCK:
                                click(mx + dx, my + dy, focus_hwnd=hwnd)
                            time.sleep(0.12)
                    set_status("ran out of selected ball; clicking every 5 minutes")
                    last_keepalive_click = time.time()
                time.sleep(0.5)

        threading.Thread(target=_keepalive_worker, daemon=True).start()
        set_status("attached")

        with mss() as sct:
            set_status("scanning for encounters…")
            was_hidden = False
            while not stop_flag.is_set():
                if pause_flag.is_set():
                    time.sleep(0.08)
                    continue
                try:
                    poll = max(1, int(CFG.get("poll_ms", 100)))
                except Exception:
                    poll = 100
                if not is_roblox_window_alive(hwnd):
                    status("Roblox closed — aborting bot")
                    _log("[ERROR] Roblox window closed/crashed; aborting bot")
                    stop_flag.set()
                    send("bot_status", {"running": False, "message": "Roblox closed — bot aborted"})
                    break
                cx = get_client_rect(hwnd)
                if not cx:
                    status("Roblox closed — aborting bot")
                    _log("[ERROR] Roblox client area unavailable; aborting bot")
                    stop_flag.set()
                    send("bot_status", {"running": False, "message": "Roblox closed — bot aborted"})
                    break
                if user32.IsIconic(wt.HWND(hwnd)) or not is_window_partially_visible(hwnd):
                    if not was_hidden:
                        set_status("Roblox not visible — pausing…")
                        _log("Window minimized/off-screen; pausing scans")
                        was_hidden = True
                    time.sleep(0.25)
                    continue
                elif was_hidden:
                    set_status("scanning for encounters…")
                    was_hidden = False

                target_rect  = perc_rect(cx, perc_target)
                pokemon_name_rect = perc_rect(cx, perc_pokemon_name)
                hud_rect     = perc_rect(cx, perc_hud)
                use_rect     = perc_rect(cx, perc_use)
                ball_rect    = perc_rect(cx, perc_ball)
                bag_hud_rect = subrect(hud_rect, perc_bag_hud)
                run_hud_rect = subrect(hud_rect, perc_run_hud)
                if out_of_balls:
                    is_bag_open = _bag_seems_open(sct, ball_rect)
                    if is_bag_open and desired_ball_names:
                        if _select_priority_ball(sct, ball_rect):
                            _use_click_then_retry(sct, use_rect, ball_rect, desired_ball_name)
                            time.sleep(0.2)
                    time.sleep(poll/1000.0)
                    continue
                is_bag_open = _bag_seems_open(sct, ball_rect)
                if is_bag_open:
                    if bag_open_since == 0.0:
                        bag_open_since = time.time()
                    if (bag_use_attempt_ts > 0.0) and (time.time() - bag_use_attempt_ts > 5.0):
                        _use_click_then_retry(sct, use_rect, ball_rect, desired_ball_name)
                        bag_use_attempt_ts = time.time()
                else:
                    bag_open_since = 0.0
                    bag_use_attempt_ts = 0.0
                    no_selected_ball_missing_since = 0.0

                txt = _ocr_from_target(sct, target_rect)
                now = time.time()

                n_now = _ocr_norm(txt)
                if ENCOUNTER_NORM in n_now or fuzzy_contains(n_now, ENCOUNTER_NORM) or SHINY_NORM in n_now or fuzzy_contains(n_now, SHINY_NORM):
                    last_enc_seen_ts = now
                    if not encounter_active:
                        encounter_active = True
                        encounter_counted = False
                    if not encounter_counted:
                        inc_encounter()
                        session_inc("encounters")
                        encounter_counted = True
                        set_status("encounter detected")
                        _log("[ENCOUNTER] Wild Pokémon found")
                        s_now = _ocr_norm(txt)
                        if ENCOUNTER_NORM in s_now or fuzzy_contains(s_now, ENCOUNTER_NORM):
                            log_seen_once(txt)
                        else:
                            for _, t in reversed(recent_norm):
                                if ENCOUNTER_NORM in t or fuzzy_contains(t, ENCOUNTER_NORM):
                                    log_seen_once(t)
                                    break
                        rescue_txt, rescue_name = _encounter_name_rescue_burst(sct, target_rect, txt)
                        if rescue_name:
                            battle_poke_norm = _norm_name(rescue_name)
                            globals()['last_pokemon_seen'] = battle_poke_norm
                            _log(f"[POKEMON] Encountered: {battle_poke_norm}")
                        else:
                            _try_log_pokemon_name(rescue_txt or txt)
                            if not battle_poke_norm:
                                fallback_name = _ocr_from_pokemon_name_region(sct, pokemon_name_rect)
                                if fallback_name:
                                    battle_poke_norm = _norm_name(fallback_name)
                                    globals()['last_pokemon_seen'] = battle_poke_norm
                                    _log(f"[POKEMON] Encountered: {battle_poke_norm}")
                        enc_tok = rescue_name or _extract_pokemon_from_norm_text(_ocr_norm(rescue_txt or txt)) or _extract_pokemon_from_recent()
                        battle_poke_norm = _norm_name(enc_tok) if enc_tok else battle_poke_norm
                        if (SHINY_NORM in s_now) or fuzzy_contains(s_now, SHINY_NORM):
                            battle_shiny = True
                elif encounter_active and (now - last_enc_seen_ts) > ENC_LATCH_RESET:
                    encounter_active = False
                    encounter_counted = False
                
                _append_norm(txt)
                if (SHINY_NORM in n_now) or fuzzy_contains(n_now, SHINY_NORM):
                    battle_shiny = True
                _scan_holding_from_raw(txt)
                _scan_holding_from_agg()
                agg = _agg_norm()

                if (time.time() >= ignore_flee_until) and (FLEE_NORM in agg or fuzzy_contains(agg, FLEE_NORM)):
                    if not flee_latched:
                        flee_latched = True
                        last_flee_seen_ts = now
                        set_status("flee detected — resetting…")
                        _log("[FLEE] Battle ended")
                        _reset_target_state()
                        time.sleep(0.25)
                        set_status("scanning…")
                elif flee_latched and (now - last_flee_seen_ts) > FLEE_RESET_GAP:
                    flee_latched = False

                use_holding = bool(last_holding_norm and (time.time() - last_holding_seen) <= HOLDING_PRIOR_MS)
                if use_holding:
                    _resolve_from_holding()
                else:
                    best_name = ""
                    best_norm = ""
                    best_is_exact = False
                    best_score = 0.0
                    want_capture = False
                    last_best_announced = ""

                enabled_norms, norm_to_pretty = _cfg_enabled_maps()
                pretty_name = norm_to_pretty.get(best_norm, best_name) if best_name else ""

                hud_full = grab(sct, *hud_rect)
                if hud_full is None:
                    time.sleep(poll/1000.0)
                    continue

                Lh, Th, Rh, Bh = hud_rect
                Lb, Tb, Rb, Bb = bag_hud_rect
                Lr, Tr, Rr, Br = run_hud_rect

                hud_bag = hud_full[(Tb - Th):(Bb - Th), (Lb - Lh):(Rb - Lh)]
                hud_run = hud_full[(Tr - Th):(Br - Th), (Lr - Lh):(Rr - Lh)]

                ok_bag, bag_pt_local = match(hud_bag, bag_png, CFG["bag_threshold"]) if hud_bag is not None else (False, None)
                ok_run, run_box = match_box(hud_run, run_png, CFG["run_threshold"]) if hud_run is not None else (False, None)
                
                bag_hits = BAG_STABLE_HITS if ok_bag else 0
                run_hits = RUN_STABLE_HITS if ok_run else 0
                
                battle_shiny = battle_shiny or (SHINY_NORM in n_now) or fuzzy_contains(n_now, SHINY_NORM)
                is_shiny_now = battle_shiny
                if not battle_poke_norm:
                    fallback_name = _ocr_from_pokemon_name_region(sct, pokemon_name_rect)
                    if fallback_name:
                        battle_poke_norm = _norm_name(fallback_name)
                        globals()['last_pokemon_seen'] = battle_poke_norm
                        _log(f"[POKEMON] Encountered: {battle_poke_norm}")
                enc_name_norm = battle_poke_norm or _norm_name(_extract_pokemon_from_norm_text(n_now) or _extract_pokemon_from_recent())
                if enc_name_norm and not battle_poke_norm:
                    battle_poke_norm = enc_name_norm or _norm_name(_extract_pokemon_from_norm_text(n_now) or _extract_pokemon_from_recent())
                if enc_name_norm and not battle_poke_norm:
                    battle_poke_norm = enc_name_norm
                
                poke_cfg_map, poke_norm_to_key = _load_poke_cfg_map()
                want_pokemon_capture = False
                pokemon_log_name = _pretty_pokemon_from_norm(enc_name_norm)
                if enc_name_norm:
                    key = _find_key_ci(poke_cfg_map, enc_name_norm)
                    if key:
                        pokemon_log_name = key
                        opts = poke_cfg_map.get(key, {"shiny": False, "amount": "inf"})
                        if opts.get("shiny", False):
                            want_pokemon_capture = bool(is_shiny_now)
                        else:
                            want_pokemon_capture = True
                        a = str(opts.get("amount", "inf")).lower()
                        if a != "inf":
                            try:
                                want_pokemon_capture = want_pokemon_capture and (int(a) > 0)
                            except:
                                want_pokemon_capture = want_pokemon_capture and True
                
                want_capture_effective = (use_holding and want_capture) or want_pokemon_capture

                if want_capture_effective and bag_hits >= BAG_STABLE_HITS and bag_pt_local is not None:
                    capture_name = (pokemon_log_name or _pretty_pokemon_from_norm(enc_name_norm or battle_poke_norm) or "Unknown") if want_pokemon_capture else (pretty_name or best_name or "target")
                    set_status(f"opening bag for {capture_name}…")
                    _log(f"Bag detected; capturing {capture_name}")
                    bag_pt = (bag_hud_rect[0] + bag_pt_local[0], bag_hud_rect[1] + bag_pt_local[1])
                    globals()['last_item_name_found'] = (pokemon_log_name if want_pokemon_capture else (pretty_name or best_name or "Target Item"))
                    add_log(pokemon_log_name or "Unknown", True, "pokemon") if want_pokemon_capture else add_log(pretty_name or (best_name or "Unknown"), True, "items")
                    session_inc("captured")
                    with CLICK_LOCK:
                        click(bag_pt[0], bag_pt[1], focus_hwnd=hwnd)
                    time.sleep(0.20)

                    if desired_ball_names:
                        selected = _select_priority_ball(sct, ball_rect, "[BALL] Selected")
                        if not selected:
                            set_status(f"using selected ball for {capture_name}…")

                    _use_click_then_retry(sct, use_rect, ball_rect, desired_ball_name)
                    _followup_multiball(sct, target_rect, hud_rect, bag_hud_rect, run_hud_rect, use_rect, ball_rect)
                    
                    if want_pokemon_capture and enc_name_norm:
                        _dec_amount_if_finite(enc_name_norm)

                    _reset_target_state()
                    encounter_active = False
                    encounter_counted = False
                    set_status("scanning for encounters…")
                    bag_hits = 0
                    run_hits = 0
                    time.sleep(poll/1000.0)
                    continue

                if (not want_capture_effective) and run_hits >= RUN_STABLE_HITS and ok_bag and bag_hits >= BAG_STABLE_HITS:
                    x, y, w, h = run_box if run_box else (0, 0, 0, 0)
                    cx_click = run_hud_rect[0] + x + (w//2 if w else int((Rr - Lr) * 0.75))
                    cy_click = run_hud_rect[1] + y + (int(h * 0.62) if h else int((Br - Tr) * 0.62))
                
                    if enc_name_norm:
                        add_log(pokemon_log_name or _pretty_pokemon_from_norm(enc_name_norm), False, "pokemon")
                        session_inc("fled")
                        _log(f"[RUN] Ran from {pokemon_log_name or _pretty_pokemon_from_norm(enc_name_norm)}")
                    elif use_holding and (best_name or last_holding_norm):
                        nm = pretty_name or best_name
                        add_log(nm or "Unknown", False, "items")
                        session_inc("fled")
                        _log(f"[RUN] Ran from {nm}")
                    else:
                        _log("[RUN] Ran from battle")
                
                    set_status("running…")
                    with CLICK_LOCK:
                        click(cx_click, cy_click, focus_hwnd=hwnd)
                    _confirm_flee_or_retry(sct, target_rect, (cx_click, cy_click))
                    ignore_flee_until = time.time() + SELF_FLEE_IGNORE
                    flee_latched = True
                    last_flee_seen_ts = time.time()
                    _clear_buffers()
                    best_name = best_norm = last_best_announced = last_holding_norm = ""
                    last_holding_seen = 0.0
                    battle_poke_norm = ""
                    battle_shiny = False
                    bag_hits = run_hits = 0
                    time.sleep(0.35)
                    set_status("scanning for encounters…")
                    time.sleep(poll/1000.0)
                    continue

                time.sleep(poll/1000.0)

    except Exception as e:
        status(f"error: {e}")
        _log(f"[ERROR] {e}")
    finally:
        try:
            session_end()
        except Exception as e:
            _log(f"[ERROR] Couldn't end session: {e}")
        try:
            overlay_stop()
        except Exception:
            pass
        try:
            stop_global_hotkeys()
        except Exception:
            pass
        send("bot_status", {"running": False, "message": "Bot stopped"})

def farm_bot_loop(stop_flag, move_choice=None):
    hwnd = find_roblox_hwnd()
    if not hwnd:
        status("Farm: Roblox not found")
        return

    move_choice = move_choice or CFG.get("farm_move_choice", "move1")

    def abort_if_roblox_closed():
        if is_roblox_window_alive(hwnd):
            return False
        status("Farm: Roblox closed — aborting bot")
        _log("[ERROR] Roblox window closed/crashed; aborting farm bot")
        stop_flag.set()
        send("farm_bot_status", {"running": False, "message": "Roblox closed — farm bot aborted"})
        return True

    npc_pt_perc      = CFG.get("npc_click_point",      "0.65,0.55")
    yes_pt_perc      = CFG.get("yes_click_point",      "0.755,0.695")
    next_pt_perc     = CFG.get("next_click_point",     "0.755,0.695")
    fight_pt_perc    = CFG.get("fight_click_point",    "0.70,0.82")
    move1_pt_perc    = CFG.get("move1_click_point",    "0.15,0.82")
    move2_pt_perc    = CFG.get("move2_click_point",    "0.45,0.82")
    move3_pt_perc    = CFG.get("move3_click_point",    "0.15,0.95")
    move4_pt_perc    = CFG.get("move4_click_point",    "0.45,0.95")
    learn_no_pt_perc = CFG.get("no_click_point", "0.85,0.95")
    learn_ocr_region = CFG.get("learntext_ocr_region", "0.00,0.755,0.60,1.00")

    def _pt_from_percent(cr, perc_str):
        parts = [p.strip() for p in str(perc_str).split(",") if p.strip() != ""]
        x = float(parts[0]); y = float(parts[1])
        L, T, R, B = cr
        return int(L + x * (R - L)), int(T + y * (B - T))

    def _rect_from_percent_str(cr, perc_str):
        parts = [p.strip() for p in str(perc_str).split(",") if p.strip() != ""]
        x0 = float(parts[0]); y0 = float(parts[1]); x1 = float(parts[2]); y1 = float(parts[3])
        L, T, R, B = cr
        return int(L + x0 * (R - L)), int(T + y0 * (B - T)), int(L + x1 * (R - L)), int(T + y1 * (B - T))

    def _interruptible_sleep(seconds):
        end = time.time() + max(0.0, float(seconds))
        while not stop_flag.is_set() and time.time() < end:
            time.sleep(0.02)

    def _human_click_screen(sx, sy, taps=1, delay=0.15):
        for _ in range(max(1, int(taps))):
            if stop_flag.is_set(): return
            try:
                click(int(sx), int(sy), focus_hwnd=hwnd)
            except Exception:
                pass
            _interruptible_sleep(delay)

    def click_pt_percent(perc_str, taps=1, delay=0.15):
        if stop_flag.is_set(): return
        cr = get_client_rect(hwnd)
        if not cr: return
        px, py = _pt_from_percent(cr, perc_str)
        _human_click_screen(px, py, taps=taps, delay=delay)

    def _slot_point_for_choice(choice):
        if choice == "move1": return move1_pt_perc
        if choice == "move2": return move2_pt_perc
        if choice == "move3": return move3_pt_perc
        if choice == "move4": return move4_pt_perc
        return move1_pt_perc

    def _is_learn_move_prompt():
        try:
            cr = get_client_rect(hwnd)
            if not cr: return False
            x0, y0, x1, y1 = _rect_from_percent_str(cr, learn_ocr_region)
            with mss() as sct:
                img = grab(sct, x0, y0, x1, y1)
            if img is None: return False
            txt = _norm(ocr_text(preprocess_for_white_text(img)))
            if not txt: return False
            keys = ("deleteamovetomakeroomfor", "shouldforgetsomemove", "deletemove", "forgetamove")
            return any(k in txt for k in keys)
        except Exception:
            return False

    while not stop_flag.is_set():
        click_pt_percent(npc_pt_perc, taps=3, delay=0.5)
        if stop_flag.is_set(): break
        click_pt_percent(yes_pt_perc, taps=2, delay=0.5)
        if stop_flag.is_set(): break
        click_pt_percent(next_pt_perc, taps=2, delay=3.75)
        if stop_flag.is_set(): break
        click_pt_percent(fight_pt_perc, taps=2, delay=0.3)
        if stop_flag.is_set(): break
        click_pt_percent(_slot_point_for_choice(move_choice), taps=2, delay=0.6)
        if stop_flag.is_set(): break

        t0 = time.time()
        while not stop_flag.is_set() and (time.time() - t0) < 2.5:
            if _is_learn_move_prompt():
                click_pt_percent(learn_no_pt_perc, taps=2, delay=0.5)
                break
            _interruptible_sleep(0.15)

        if stop_flag.is_set(): break
        click_pt_percent(next_pt_perc, taps=5, delay=0.15)
        _interruptible_sleep(0.25)

def get_items_payload():
    items = []
    order_names, _ = _split_targets_order()
    seen = set()
    for name in order_names:
        if name in seen:
            continue
        seen.add(name)
        img_path = os.path.join(ITEMS_DIR, f"{name}.png")
        items.append({
            "name": name,
            "note": ITEM_NOTES.get(name, ""),
            "image": img_path if os.path.exists(img_path) else ""
        })
    return items

def get_pokemon_payload():
    return list(pokemon_names)

def get_assets_payload():
    return {
        "data_root": DATA_ROOT,
        "assets_dir": ASSETS_DIR,
        "items_dir": ITEMS_DIR,
        "pokeballs_dir": BALLS_UI_DIR,
        "sounds_dir": SOUNDS_DIR,
        "other_dir": OTHER_DIR,
        "items": list_items_pngs(ASSETS_DIR),
        "pokeballs": list_pngs(BALLS_UI_DIR)
    }

def update_settings(values):
    bool_keys = ("sd_min_enc_on", "sd_min_cap_on", "developer_mode", "encounter_logging", "enable_session_data", "enable_fallback_capture", "sound_enabled", "show_welcome_on_start", "tutorial_seen", "debug_colorize_enabled")
    int_keys = ("poll_ms", "encounter_log_retention_days", "sd_prune_days", "sd_prune_keep", "sd_min_enc", "sd_min_cap", "debug_copy_lines")
    float_keys = ("ball_threshold", "bag_threshold", "run_threshold", "fuzzy_ratio")
    color_keys = ("fg_bg", "fg_bg_hover", "fg_card", "fg_card_alt", "text_primary", "text_secondary", "text_muted", "text_warning", "accent", "accent_hover", "border", "border_muted", "link", "debug_color_startup", "debug_color_encounter", "debug_color_run", "debug_color_caught", "debug_color_error", "debug_color_other")
    for key, value in values.items():
        if key not in CFG:
            continue
        if key in bool_keys:
            CFG[key] = str(value).strip().lower() in ("1", "true", "yes", "on")
        elif key in int_keys:
            try: CFG[key] = int(value)
            except Exception: pass
        elif key in float_keys:
            try: CFG[key] = float(value)
            except Exception: pass
        elif key in color_keys:
            s = str(value).strip()
            if re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", s) or re.fullmatch(r"rgb\(\s*(?:25[0-5]|2[0-4]\d|1?\d?\d)\s*,\s*(?:25[0-5]|2[0-4]\d|1?\d?\d)\s*,\s*(?:25[0-5]|2[0-4]\d|1?\d?\d)\s*\)", s) or re.fullmatch(r"rgba\(\s*(?:25[0-5]|2[0-4]\d|1?\d?\d)\s*,\s*(?:25[0-5]|2[0-4]\d|1?\d?\d)\s*,\s*(?:25[0-5]|2[0-4]\d|1?\d?\d)\s*,\s*(?:0|1|0?\.\d+)\s*\)", s):
                CFG[key] = s
        else:
            CFG[key] = value
    save_ini()
    load_ini()
    return dict(CFG)

SEND_LOCK = threading.Lock()

def send(event, payload=None):
    with SEND_LOCK:
        sys.stdout.write(json.dumps({"type": event, "payload": payload or {}}) + "\n")
        sys.stdout.flush()

def get_backend_health():
    hwnd = find_roblox_hwnd()
    tess_cmd = getattr(pytesseract.pytesseract, "tesseract_cmd", "")
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "data_root": DATA_ROOT,
        "cfg_path": CFG_PATH,
        "assets_dir": ASSETS_DIR,
        "roblox_found": bool(hwnd),
        "roblox_hwnd": int(hwnd or 0),
        "tesseract_cmd": tess_cmd,
        "tesseract_available": bool(shutil.which("tesseract") or os.path.exists(tess_cmd)),
        "settings_loaded": bool(CFG),
        "runtime": get_runtime_state()
    }

def get_runtime_state():
    return {
        "bot_running": bool(BOT_THREAD and BOT_THREAD.is_alive()),
        "farm_bot_running": bool(FARM_THREAD and FARM_THREAD.is_alive()),
        "paused": pause_flag.is_set(),
        "stopping": stop_flag.is_set(),
        "status": _status
    }

def download_update_payload(info):
    if not info:
        return {"ok": False, "message": "No update info provided"}
    exe_url = info.get("url")
    asset_name = info.get("asset") or "Astralis update.exe"
    zip_url = info.get("assets_zip_url")
    result = {"ok": True, "exe_path": "", "zip_path": "", "asset": asset_name}
    if exe_url:
        result["exe_path"] = _download_to_temp(exe_url, asset_name)
    if zip_url:
        result["zip_path"] = _download_to_temp(zip_url, "astralis-main.zip")
        try: _update_assets_from_zip(result["zip_path"])
        except Exception as e: result["assets_error"] = str(e)
    return result

def _stats_payload_rows():
    return [{"name": r[0], "total": r[1], "captured": r[2], "fled": r[3]} for r in stats_all()]

def _sessions_payload_rows():
    return [{
        "id": r[0],
        "startTs": r[1],
        "endTs": r[2] or None,
        "runSecs": r[3],
        "encounters": r[4],
        "captured": r[5],
        "fled": r[6],
        "fallbacks": r[7],
        "ballsUsed": r[8],
        "running": CURRENT_SESSION_ID is not None and int(CURRENT_SESSION_ID) == int(r[0])
    } for r in sessions_all()]

def _session_item_ts(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%H:%M:%S"):
        try:
            dt = datetime.strptime(text, fmt)
            if fmt == "%H:%M:%S":
                now = datetime.now()
                dt = dt.replace(year=now.year, month=now.month, day=now.day)
            return int(dt.timestamp())
        except Exception:
            pass
    return 0

def overlay_start(hwnd=None):
    global OVERLAY_THREAD, OVERLAY_HIDDEN
    OVERLAY_HIDDEN = False
    if OVERLAY_THREAD and OVERLAY_THREAD.is_alive():
        send("overlay_state", {"visible": True, "hidden": False})
        return
    OVERLAY_STOP.clear()
    OVERLAY_THREAD = threading.Thread(target=_overlay_loop, args=(hwnd,), daemon=True)
    OVERLAY_THREAD.start()

def overlay_stop():
    global OVERLAY_HIDDEN
    OVERLAY_HIDDEN = False
    OVERLAY_STOP.set()
    send("overlay_state", {"visible": False, "hidden": False})

def overlay_hide():
    global OVERLAY_HIDDEN
    OVERLAY_HIDDEN = True
    send("overlay_state", {"visible": False, "hidden": True})

def overlay_rebuild():
    global OVERLAY_THREAD, OVERLAY_HIDDEN
    OVERLAY_HIDDEN = False
    if not OVERLAY_THREAD or not OVERLAY_THREAD.is_alive():
        hwnd = SELECTED_ROBLOX_HWNDS[0] if SELECTED_ROBLOX_HWNDS else None
        OVERLAY_STOP.clear()
        OVERLAY_THREAD = threading.Thread(target=_overlay_loop, args=(hwnd,), daemon=True)
        OVERLAY_THREAD.start()
    send("overlay_state", {"visible": True, "hidden": False})

def toggle_pause_bot():
    global SESSION_PAUSED_TOTAL, SESSION_PAUSE_T0
    if pause_flag.is_set():
        pause_flag.clear()
        if SESSION_PAUSE_T0:
            SESSION_PAUSED_TOTAL += time.monotonic() - SESSION_PAUSE_T0
            SESSION_PAUSE_T0 = 0.0
        send("bot_status", {"running": bool(BOT_THREAD and BOT_THREAD.is_alive()), "paused": False, "message": "Bot resumed"})
    else:
        pause_flag.set()
        SESSION_PAUSE_T0 = time.monotonic()
        send("bot_status", {"running": bool(BOT_THREAD and BOT_THREAD.is_alive()), "paused": True, "message": "Bot paused"})

def _overlay_target_hwnd(hwnd=None):
    if hwnd:
        return hwnd
    if SELECTED_ROBLOX_HWNDS:
        return SELECTED_ROBLOX_HWNDS[0]
    return find_roblox_hwnd()

def _overlay_enabled_names():
    enabled = [s for s in str(CFG.get("enabled_targets", "") or "").split("|") if s]
    if not enabled:
        return "(none)"
    all_names = [s for s in str(CFG.get("targets_order", "") or "").split("|") if s]
    if all_names and {x.lower() for x in enabled}.issuperset({x.lower() for x in all_names}):
        return "All items are selected"
    return (", ".join(enabled[:3]) + " . . .") if len(enabled) > 3 else ", ".join(enabled)

def _overlay_loop(hwnd=None):
    global OVERLAY_HIDDEN
    was_shown = False
    def _overlay_ball_text():
        choice = str(CFG.get("use_choice", "") or "")
        if choice.startswith("auto:"):
            balls = [os.path.splitext(os.path.basename(p.strip()))[0] for p in choice[5:].split("|") if p.strip()]
            return " | ".join(f"{i + 1}. {b}" for i, b in enumerate(balls)) or "(auto)"
        return os.path.splitext(os.path.basename(choice))[0] or "(auto)"
    while not OVERLAY_STOP.is_set():
        if OVERLAY_HIDDEN:
            if was_shown:
                send("overlay_status", {"visible": False})
                was_shown = False
            time.sleep(0.3)
            continue
        target = _overlay_target_hwnd(hwnd)
        show = bool(target and is_window_partially_visible(target) and BOT_THREAD and BOT_THREAD.is_alive())
        if show:
            e, c, f = get_counts()
            x = 0
            y = 0
            try:
                l, t, r, b = get_window_rect(target)
                x = int(l)
                y = int(t + max(0, ((b - t) - 292) // 2))
            except Exception:
                pass
            send("overlay_status", {
                "visible": True,
                "x": x,
                "y": y,
                "status": _status,
                "poll": str(CFG.get("poll_ms", 50)),
                "ball": _overlay_ball_text(),
                "fallback": "ON" if bool(CFG.get("enable_fallback_capture", False)) else "OFF",
                "targets": _overlay_enabled_names(),
                "encounters": str(e),
                "caught": str(c),
                "fled": str(f),
                "runtime": _fmt_hms(_uptime_sec()),
                "paused": pause_flag.is_set(),
                "pauseKey": str(CFG.get("vk_pause", "F6")),
                "hideKey": str(CFG.get("vk_hide_overlay", "F8")),
                "exitKey": str(CFG.get("vk_exit", "F7")),
            })
            if not was_shown:
                send("overlay_state", {"visible": True, "hidden": False})
                was_shown = True
        else:
            if was_shown:
                send("overlay_status", {"visible": False})
                send("overlay_state", {"visible": False, "hidden": False})
                was_shown = False
        time.sleep(0.3)
    send("overlay_status", {"visible": False})

def _vk_from_setting(value, default):
    text = str(value or "").strip().upper()
    if re.fullmatch(r"F([1-9]|1[0-2])", text):
        return 0x70 + int(text[1:]) - 1
    if len(text) == 1 and "A" <= text <= "Z":
        return ord(text)
    if len(text) == 1 and "0" <= text <= "9":
        return ord(text)
    return default

def start_global_hotkeys():
    global HOTKEY_THREAD
    if HOTKEY_THREAD and HOTKEY_THREAD.is_alive():
        return
    HOTKEY_STOP.clear()
    HOTKEY_THREAD = threading.Thread(target=_hotkey_loop, daemon=True)
    HOTKEY_THREAD.start()

def stop_global_hotkeys():
    HOTKEY_STOP.set()

def _hotkey_loop():
    MOD_NOREPEAT = 0x4000
    WM_HOTKEY = 0x0312
    ids = [1, 2, 3, 4]
    def unregister_all():
        for i in ids:
            try: user32.UnregisterHotKey(None, i)
            except Exception: pass
    def register_all():
        unregister_all()
        user32.RegisterHotKey(None, 1, MOD_NOREPEAT, _vk_from_setting(CFG.get("vk_pause", "F6"), 0x75))
        user32.RegisterHotKey(None, 2, MOD_NOREPEAT, _vk_from_setting(CFG.get("vk_exit", "F7"), 0x76))
        user32.RegisterHotKey(None, 3, MOD_NOREPEAT, _vk_from_setting(CFG.get("vk_regions", "F10"), 0x79))
        user32.RegisterHotKey(None, 4, MOD_NOREPEAT, _vk_from_setting(CFG.get("vk_hide_overlay", "F8"), 0x77))
    try:
        register_all()
        msg = wt.MSG()
        while not HOTKEY_STOP.is_set():
            ok = user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1)
            if ok and msg.message == WM_HOTKEY:
                if msg.wParam == 1:
                    toggle_pause_bot()
                elif msg.wParam == 2:
                    stop_flag.set()
                    pause_flag.clear()
                    overlay_stop()
                    send("bot_status", {"running": False, "message": "Stop requested"})
                elif msg.wParam == 3:
                    preview_settings_regions()
                elif msg.wParam == 4:
                    overlay_hide()
            time.sleep(0.03)
    finally:
        unregister_all()

DEBUG_LOG_PATH = os.path.join(DATA_ROOT, "debug_logs.txt")

def read_debug_logs(max_lines=5000):
    try:
        with open(DEBUG_LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()[-int(max_lines):]
        try:
            os.makedirs(DATA_ROOT, exist_ok=True)
            with open(DEBUG_LOG_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + ("\n" if lines else ""))
        except Exception:
            pass
        return lines
    except Exception:
        return []

def clear_debug_logs():
    try:
        os.makedirs(DATA_ROOT, exist_ok=True)
        with open(DEBUG_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass

FARM_PREVIEW_OVERLAY = None
FARM_PREVIEW_KIND = None
FARM_PREVIEW_LOCK = threading.Lock()

def _farm_preview_float_list(value, expected, fallback):
    try:
        vals = [float(v.strip()) for v in str(value or "").split(",")]
        if len(vals) == expected:
            return vals
    except Exception:
        pass
    return [float(v.strip()) for v in fallback.split(",")]

def _farm_preview_point(value, fallback, L, T, R, B):
    x, y = _farm_preview_float_list(value, 2, fallback)
    return int(L + x * (R - L)), int(T + y * (B - T))

def _farm_preview_rect(value, fallback, L, T, R, B):
    x0, y0, x1, y1 = _farm_preview_float_list(value, 4, fallback)
    return int(L + x0 * (R - L)), int(T + y0 * (B - T)), int(L + x1 * (R - L)), int(T + y1 * (B - T))

def destroy_farm_preview_regions():
    global FARM_PREVIEW_OVERLAY, FARM_PREVIEW_KIND
    with FARM_PREVIEW_LOCK:
        overlay = FARM_PREVIEW_OVERLAY
        kind = FARM_PREVIEW_KIND or "farm"
        FARM_PREVIEW_OVERLAY = None
        FARM_PREVIEW_KIND = None
    try:
        if overlay:
            overlay.after(0, overlay.destroy)
    except Exception:
        pass
    if kind == "settings":
        send("settings_preview_state", {"visible": False, "message": "Advanced regions hidden."})
    else:
        send("farm_preview_state", {"visible": False, "message": "Farm regions hidden."})

def _farm_preview_regions_thread(points):
    global FARM_PREVIEW_OVERLAY, FARM_PREVIEW_KIND
    import tkinter as tk
    try:
        hwnd = find_roblox_hwnd()
        if not hwnd:
            send("farm_preview_state", {"visible": False, "message": "Roblox not found."})
            return
        cr = get_client_rect(hwnd)
        if not cr:
            send("farm_preview_state", {"visible": False, "message": "Roblox window not visible."})
            return
        L, T, R, B = cr
        W, H = max(1, R - L), max(1, B - T)
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        trans = "#010101"
        try:
            root.attributes("-transparentcolor", trans)
        except Exception:
            pass
        root.geometry(f"{W}x{H}+{L}+{T}")
        root.configure(bg=trans)
        canvas = tk.Canvas(root, highlightthickness=0, bg=trans, bd=0)
        canvas.pack(fill="both", expand=True)
        rows = [
            ("NPC", "npc_click_point", "0.50,0.45"),
            ("Yes", "yes_click_point", "0.50,0.70"),
            ("Next", "next_click_point", "0.80,0.90"),
            ("Fight", "fight_click_point", "0.25,0.85"),
            ("Slot1", "move1_click_point", "0.15,0.82"),
            ("Slot2", "move2_click_point", "0.45,0.82"),
            ("Slot3", "move3_click_point", "0.15,0.95"),
            ("Slot4", "move4_click_point", "0.45,0.95"),
            ("Learn-No", "no_click_point", "0.85,0.95"),
        ]
        for label, key, fallback in rows:
            x, y = _farm_preview_point(points.get(key) or CFG.get(key), fallback, L, T, R, B)
            x -= L
            y -= T
            canvas.create_oval(x - 7, y - 7, x + 7, y + 7, outline="#44DDF2", width=3)
            canvas.create_text(x + 10, y - 12, anchor="nw", text=label, fill="#E0E0E0")
        ocr_rect = _farm_preview_rect(points.get("learntext_ocr_region") or CFG.get("learntext_ocr_region"), "0.00,0.755,0.60,1.00", L, T, R, B)
        ocr_rect = (ocr_rect[0] - L, ocr_rect[1] - T, ocr_rect[2] - L, ocr_rect[3] - T)
        canvas.create_rectangle(*ocr_rect, outline="#7AD35A", width=3)
        canvas.create_text(ocr_rect[0] + 6, ocr_rect[1] + 6, anchor="nw", text="Learn-OCR", fill="#7AD35A")
        with FARM_PREVIEW_LOCK:
            FARM_PREVIEW_OVERLAY = root
            FARM_PREVIEW_KIND = "farm"
        send("farm_preview_state", {"visible": True, "message": "Showing farm regions."})
        root.mainloop()
    except Exception as e:
        with FARM_PREVIEW_LOCK:
            FARM_PREVIEW_OVERLAY = None
            FARM_PREVIEW_KIND = None
        send("farm_preview_state", {"visible": False, "message": f"Preview failed: {e}"})

def preview_farm_regions(points=None):
    global FARM_PREVIEW_OVERLAY, FARM_PREVIEW_KIND
    with FARM_PREVIEW_LOCK:
        visible = FARM_PREVIEW_OVERLAY is not None
    if visible:
        destroy_farm_preview_regions()
        return
    with FARM_PREVIEW_LOCK:
        FARM_PREVIEW_KIND = "farm"
    threading.Thread(target=_farm_preview_regions_thread, args=(dict(points or {}),), daemon=True).start()


def _settings_preview_regions_thread(regions):
    global FARM_PREVIEW_OVERLAY, FARM_PREVIEW_KIND
    import tkinter as tk
    try:
        hwnd = find_roblox_hwnd()
        if not hwnd:
            send("settings_preview_state", {"visible": False, "message": "Roblox not found."})
            return
        cr = get_client_rect(hwnd)
        if not cr:
            send("settings_preview_state", {"visible": False, "message": "Roblox window not visible."})
            return
        L, T, R, B = cr
        W, H = max(1, R - L), max(1, B - T)
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        trans = "#010101"
        try:
            root.attributes("-transparentcolor", trans)
        except Exception:
            pass
        root.geometry(f"{W}x{H}+{L}+{T}")
        root.configure(bg=trans)
        canvas = tk.Canvas(root, highlightthickness=0, bg=trans, bd=0)
        canvas.pack(fill="both", expand=True)
        rows = [
            ("Target Text", "target_region", "0,0.75,0.6,1"),
            ("Pokémon Name", "pokemon_name_region", "0.05,0.15,0.35,0.25"),
            ("HUD Text", "hud_region", "0.6,0.88,0.99,1"),
            ("Bag HUD", "bag_hud_region", "0,0,0.50,1"),
            ("Run HUD", "run_hud_region", "0.50,0,1,1"),
            ("Ball Button", "ball_region", "0.27,0.16,0.53,0.785"),
            ("Use Button", "use_region", "0.35,0.785,0.44,0.825"),
        ]
        rects = {}
        hud_abs = _farm_preview_rect(regions.get("hud_region") or CFG.get("hud_region"), "0.6,0.88,0.99,1", L, T, R, B)
        for label, key, fallback in rows:
            if key in ("bag_hud_region", "run_hud_region"):
                rect = _farm_preview_rect(regions.get(key) or CFG.get(key), fallback, *hud_abs)
            else:
                rect = _farm_preview_rect(regions.get(key) or CFG.get(key), fallback, L, T, R, B)
            rects[key] = [rect[0] - L, rect[1] - T, rect[2] - L, rect[3] - T]

        def fmt(v):
            return f"{v:.3f}".rstrip("0").rstrip(".")

        def rect_value(rect, key=None):
            x0, y0, x1, y1 = rect
            if key in ("bag_hud_region", "run_hud_region"):
                hx0, hy0, hx1, hy1 = rects.get("hud_region", [0, 0, W, H])
                hW, hH = max(1, hx1 - hx0), max(1, hy1 - hy0)
                return ",".join([fmt((x0 - hx0) / hW), fmt((y0 - hy0) / hH), fmt((x1 - hx0) / hW), fmt((y1 - hy0) / hH)])
            return ",".join([fmt(x0 / W), fmt(y0 / H), fmt(x1 / W), fmt(y1 / H)])

        def clamp_rect(rect):
            x0, y0, x1, y1 = rect
            x0 = max(0, min(W, x0))
            x1 = max(0, min(W, x1))
            y0 = max(0, min(H, y0))
            y1 = max(0, min(H, y1))
            if x1 - x0 < 10:
                x1 = min(W, x0 + 10)
            if y1 - y0 < 10:
                y1 = min(H, y0 + 10)
            return [x0, y0, x1, y1]

        def draw():
            canvas.delete("all")
            for label, key, fallback in rows:
                rect = rects[key]
                canvas.create_rectangle(*rect, outline="#7AD35A", width=3)
                canvas.create_text(rect[0] + 6, rect[1] + 6, anchor="nw", text=label, fill="#7AD35A")

        drag = {"key": None, "edges": None, "last": None}

        def hit_test(x, y):
            margin = 8
            for label, key, fallback in reversed(rows):
                x0, y0, x1, y1 = rects[key]
                if x < x0 - margin or x > x1 + margin or y < y0 - margin or y > y1 + margin:
                    continue
                edges = []
                if abs(x - x0) <= margin:
                    edges.append("left")
                if abs(x - x1) <= margin:
                    edges.append("right")
                if abs(y - y0) <= margin:
                    edges.append("top")
                if abs(y - y1) <= margin:
                    edges.append("bottom")
                if edges:
                    return key, edges
            return None, None

        def update_cursor(event):
            key, edges = hit_test(event.x, event.y)
            if not edges:
                canvas.config(cursor="")
            elif len(edges) == 2:
                canvas.config(cursor="sizing")
            elif "left" in edges or "right" in edges:
                canvas.config(cursor="sb_h_double_arrow")
            else:
                canvas.config(cursor="sb_v_double_arrow")

        def on_press(event):
            key, edges = hit_test(event.x, event.y)
            if not key:
                return
            drag["key"] = key
            drag["edges"] = edges
            drag["last"] = (event.x, event.y)

        def on_drag(event):
            if not drag["key"]:
                return
            key = drag["key"]
            last_x, last_y = drag["last"]
            dx, dy = event.x - last_x, event.y - last_y
            x0, y0, x1, y1 = rects[key]
            if "left" in drag["edges"]:
                x0 += dx
            if "right" in drag["edges"]:
                x1 += dx
            if "top" in drag["edges"]:
                y0 += dy
            if "bottom" in drag["edges"]:
                y1 += dy
            rects[key] = clamp_rect([x0, y0, x1, y1])
            drag["last"] = (event.x, event.y)
            draw()

        def on_release(event):
            if not drag["key"]:
                return
            key = drag["key"]
            value = rect_value(rects[key], key)
            regions[key] = value
            send("setting_region_changed", {"key": key, "value": value})
            drag["key"] = None
            drag["edges"] = None
            drag["last"] = None

        canvas.bind("<Motion>", update_cursor)
        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)
        draw()
        with FARM_PREVIEW_LOCK:
            FARM_PREVIEW_OVERLAY = root
            FARM_PREVIEW_KIND = "settings"
        send("settings_preview_state", {"visible": True, "message": "Showing advanced regions."})
        root.mainloop()
    except Exception as e:
        with FARM_PREVIEW_LOCK:
            FARM_PREVIEW_OVERLAY = None
            FARM_PREVIEW_KIND = None
        send("settings_preview_state", {"visible": False, "message": f"Preview failed: {e}"})

def preview_settings_regions(regions=None):
    global FARM_PREVIEW_OVERLAY, FARM_PREVIEW_KIND
    with FARM_PREVIEW_LOCK:
        visible = FARM_PREVIEW_OVERLAY is not None
    if visible:
        destroy_farm_preview_regions()
        return
    with FARM_PREVIEW_LOCK:
        FARM_PREVIEW_KIND = "settings"
    threading.Thread(target=_settings_preview_regions_thread, args=(dict(regions or {}),), daemon=True).start()

def find_astralis_hwnd():
    found = wt.HWND(0)
    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, lparam):
        nonlocal found
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n <= 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        title = buf.value or ""
        if title == "Astralis" or title.startswith("Astralis "):
            found = hwnd
            return False
        return True
    user32.EnumWindows(cb, 0)
    return found or None

def save_theme_screenshot(payload=None):
    payload = payload or {}
    request_id = payload.get("request_id", "")
    name = re.sub(r"[^a-z0-9_-]+", "", str(payload.get("name", "")).lower()) or "theme"
    themes_dir = os.path.join(ASSETS_DIR, "themes")
    os.makedirs(themes_dir, exist_ok=True)
    path = os.path.join(themes_dir, f"{name}.png")
    send("theme_screenshot_started", {"name": name, "path": path, "request_id": request_id})
    try:
        hwnd = find_astralis_hwnd()
        with mss() as sct:
            if hwnd:
                l, t, r, b = win32gui.GetClientRect(hwnd)
                left_top = win32gui.ClientToScreen(hwnd, (l, t))
                right_bottom = win32gui.ClientToScreen(hwnd, (r, b))
                monitor = {"left": left_top[0], "top": left_top[1], "width": right_bottom[0] - left_top[0], "height": right_bottom[1] - left_top[1]}
            else:
                monitor = sct.monitors[1]
            img = sct.grab(monitor)
            Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX").save(path)
        if not os.path.exists(path):
            raise RuntimeError(f"Screenshot file was not created: {path}")
        send("theme_screenshot_saved", {"name": name, "path": path, "request_id": request_id})
    except Exception as e:
        send("theme_screenshot_error", {"name": name, "path": path, "message": str(e), "traceback": traceback.format_exc(), "request_id": request_id})

def delete_theme_screenshot(payload=None):
    payload = payload or {}
    request_id = payload.get("request_id", "")
    name = re.sub(r"[^a-z0-9_-]+", "", str(payload.get("name", "")).lower()) or "theme"
    path = os.path.join(ASSETS_DIR, "themes", f"{name}.png")
    try:
        if os.path.exists(path):
            os.remove(path)
        send("theme_screenshot_deleted", {"name": name, "path": path, "request_id": request_id})
    except Exception as e:
        send("theme_screenshot_error", {"name": name, "path": path, "message": str(e), "traceback": traceback.format_exc(), "request_id": request_id})

def handle_message(msg):
    msg_type = msg.get("type")
    send("python_message_received", {"type": msg_type, "payload": msg.get("payload", {}), "request_id": msg.get("payload", {}).get("request_id", "")})
    if msg_type == "ping":
        send("pong", {"message": "pong from python"})
    elif msg_type == "get_backend_info":
        send("backend_info", {"app_name": APP_NAME, "version": APP_VERSION, "data_root": DATA_ROOT, "cfg_path": CFG_PATH})
    elif msg_type == "get_settings":
        send("settings", dict(CFG))
    elif msg_type == "save_settings":
        send("settings", update_settings(msg.get("payload", {})))
    elif msg_type == "reset_settings":
        CFG.clear()
        CFG.update(CFG_DEFAULTS)
        save_ini()
        send("settings", dict(CFG))
    elif msg_type == "play_hover_sound":
        _play_hover_sound()
        send("sound_played", {"kind": "hover"})
    elif msg_type == "play_click_sound":
        _play_click_sound()
        send("sound_played", {"kind": "click"})
    elif msg_type == "play_out_of_balls_sound":
        _play_out_of_balls_sound()
        send("sound_played", {"kind": "out_of_balls"})
    elif msg_type == "get_logs":
        send("logs", {"rows": get_logs()})
    elif msg_type == "get_log_days":
        send("log_days", {"days": get_log_days()})
    elif msg_type == "get_counts":
        encounters, items, fled = get_counts()
        send("counts", {"encounters": encounters, "items": items, "fled": fled})
    elif msg_type == "get_item_stats":
        send("item_stats", {"rows": _stats_payload_rows()})
    elif msg_type == "get_sessions":
        send("sessions", {"rows": _sessions_payload_rows()})
    elif msg_type == "get_session":
        session_id = msg.get("payload", {}).get("session_id")
        r = session_get(session_id)
        items = session_items(session_id)
        send("session", {
            "row": None if not r else {
                "id": r[0],
                "startTs": r[1],
                "endTs": r[2] or None,
                "runSecs": r[3],
                "encounters": r[4],
                "captured": r[5],
                "fled": r[6],
                "fallbacks": r[7],
                "ballsUsed": r[8],
                "running": CURRENT_SESSION_ID is not None and int(CURRENT_SESSION_ID) == int(r[0])
            },
            "items": [{"seenAt": _session_item_ts(ts), "item": str(name), "result": "Captured" if int(captured_flag) else "Fled"} for ts, name, captured_flag in items]
        })
    elif msg_type == "delete_session":
        session_delete(msg.get("payload", {}).get("session_id"))
        send("sessions", {"rows": _sessions_payload_rows()})
    elif msg_type == "prune_sessions":
        session_data_autodelete_apply()
        send("sessions", {"rows": _sessions_payload_rows()})
    elif msg_type == "get_logs":
        send("logs", {"rows": get_logs()})
    elif msg_type == "get_log_days":
        send("log_days", {"days": get_log_days()})
    elif msg_type == "clear_logs":
        with LOG_LOCK:
            LOG_ENTRIES.clear()
        try:
            with open(os.path.join(DATA_ROOT, "encounter_logs.txt"), "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass
        send("logs", {"rows": []})
    elif msg_type == "get_debug_logs":
        send("debug_logs", {"lines": read_debug_logs()})
    elif msg_type == "clear_debug_logs":
        clear_debug_logs()
        send("debug_logs_cleared", {})
    elif msg_type == "get_notify_token":
        send("notify_token", {"token": get_notify_token()})
    elif msg_type == "set_notify_token":
        set_notify_token(msg.get("payload", {}).get("token", ""))
        send("notify_token", {"token": get_notify_token()})
    elif msg_type == "test_notify_link":
        notify_link_success()
        send("notify_tested", {"kind": "link_success"})
    elif msg_type == "test_notify_item":
        notify_discord(msg.get("payload", {}).get("item", "Test Item"))
        send("notify_tested", {"kind": "item"})
    elif msg_type == "test_notify_out_of_balls":
        notify_out_of_balls(msg.get("payload", {}).get("ball", "Poke Ball"))
        send("notify_tested", {"kind": "out_of_balls"})
    elif msg_type == "check_for_update":
        send("update_info", {"update": check_for_update(), "current": _version_from_exe_or(APP_VERSION)})
    elif msg_type == "download_update":
        try:
            send("update_downloaded", download_update_payload(msg.get("payload", {}).get("update")))
        except Exception as e:
            send("update_error", {"message": str(e)})
    elif msg_type == "apply_update":
        payload = msg.get("payload", {})
        exe_path = payload.get("exe_path", "")
        if exe_path and os.path.exists(exe_path):
            send("shutdown", {"message": "Applying update"})
            _self_replace_exe(exe_path)
            return False
        send("update_error", {"message": "Missing downloaded exe_path"})
    elif msg_type == "get_items":
        send("items", {"items": get_items_payload()})
    elif msg_type == "get_pokemon":
        send("pokemon", {"pokemon": get_pokemon_payload()})
    elif msg_type == "get_assets":
        send("assets", get_assets_payload())
    elif msg_type == "get_tesseract_status":
        ensure_tesseract_cmd()
        send("tesseract_status", {"cmd": getattr(pytesseract.pytesseract, "tesseract_cmd", ""), "installer": _find_local_tess_installer(), "available": bool(shutil.which("tesseract") or os.path.exists(getattr(pytesseract.pytesseract, "tesseract_cmd", "")))})
    elif msg_type == "install_tesseract":
        ok = run_tesseract_bootstrap(None)
        ensure_tesseract_cmd()
        send("tesseract_status", {"installed": ok, "cmd": getattr(pytesseract.pytesseract, "tesseract_cmd", ""), "installer": _find_local_tess_installer(), "available": bool(shutil.which("tesseract") or os.path.exists(getattr(pytesseract.pytesseract, "tesseract_cmd", "")))})
    elif msg_type == "browse_tesseract":
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            guesses = [r"C:\Program Files\Tesseract-OCR", r"C:\Program Files (x86)\Tesseract-OCR", os.path.join(OTHER_DIR, "tesseract")]
            initialdir = next((p for p in guesses if os.path.isdir(p)), os.getcwd())
            d = filedialog.askdirectory(parent=root, title="Select Tesseract-OCR folder", mustexist=True, initialdir=initialdir)
            root.destroy()
            if not d:
                send("tesseract_status", {"cancelled": True, "cmd": getattr(pytesseract.pytesseract, "tesseract_cmd", ""), "installer": _find_local_tess_installer(), "available": bool(shutil.which("tesseract") or os.path.exists(getattr(pytesseract.pytesseract, "tesseract_cmd", "")))})
            else:
                cand = os.path.join(d, "tesseract.exe")
                if os.path.exists(cand):
                    CFG["tesseract_path"] = d
                    save_ini()
                    pytesseract.pytesseract.tesseract_cmd = cand
                    send("tesseract_status", {"selected": True, "cmd": cand, "installer": _find_local_tess_installer(), "available": True})
                else:
                    send("tesseract_status", {"error": "That folder does not contain tesseract.exe.", "cmd": getattr(pytesseract.pytesseract, "tesseract_cmd", ""), "installer": _find_local_tess_installer(), "available": False})
        except Exception as e:
            send("tesseract_status", {"error": str(e), "cmd": getattr(pytesseract.pytesseract, "tesseract_cmd", ""), "installer": _find_local_tess_installer(), "available": bool(shutil.which("tesseract") or os.path.exists(getattr(pytesseract.pytesseract, "tesseract_cmd", "")))})
    elif msg_type == "clean_old_appdata_versions":
        clean_old_appdata_versions()
        send("cleanup_done", {"data_root": DATA_ROOT})
    elif msg_type == "save_theme_screenshot":
        save_theme_screenshot(msg.get("payload", {}))
    elif msg_type == "delete_theme_screenshot":
        delete_theme_screenshot(msg.get("payload", {}))
    elif msg_type == "find_roblox":
        hwnd = find_roblox_hwnd()
        send("roblox_window", {"hwnd": int(hwnd or 0), "client_rect": get_client_rect(hwnd) if hwnd else None, "visible": is_window_partially_visible(hwnd) if hwnd else False})
    elif msg_type == "find_roblox_windows":
        hwnds = find_roblox_hwnds()
        send("roblox_windows", {"windows": [{"hwnd": int(hwnd or 0), "title": get_window_title(hwnd), "client_rect": get_client_rect(hwnd), "visible": is_window_partially_visible(hwnd)} for hwnd in hwnds]})
    elif msg_type == "attach_roblox_windows":
        global SELECTED_ROBLOX_HWNDS
        hwnds = msg.get("payload", {}).get("hwnds", [])
        SELECTED_ROBLOX_HWNDS = [int(h) for h in hwnds if int(h or 0)]
        send("roblox_attached", {"count": len(SELECTED_ROBLOX_HWNDS)})
    elif msg_type == "click":
        payload = msg.get("payload", {})
        click(payload.get("x", 0), payload.get("y", 0), focus_hwnd=payload.get("hwnd") or None)
        send("clicked", {"x": payload.get("x", 0), "y": payload.get("y", 0)})
    elif msg_type == "get_status":
        send("status", {"status": _status})
    elif msg_type == "get_backend_health":
        send("backend_health", get_backend_health())
    elif msg_type == "get_runtime_state":
        send("runtime_state", get_runtime_state())
    elif msg_type == "start_bot":
        global BOT_THREAD
        if BOT_THREAD and BOT_THREAD.is_alive():
            send("bot_status", {"running": True, "message": "Bot already running"})
        else:
            stop_flag.clear()
            pause_flag.clear()
            hwnd = SELECTED_ROBLOX_HWNDS[0] if SELECTED_ROBLOX_HWNDS else None
            BOT_THREAD = threading.Thread(target=bot_loop, args=(hwnd,), daemon=True)
            BOT_THREAD.start()
            overlay_start(hwnd)
            start_global_hotkeys()
            send("bot_status", {"running": True, "message": "Bot started"})
    elif msg_type == "pause_bot":
        if not pause_flag.is_set():
            toggle_pause_bot()
    elif msg_type == "resume_bot":
        if pause_flag.is_set():
            toggle_pause_bot()
    elif msg_type == "toggle_pause_bot":
        toggle_pause_bot()
    elif msg_type == "hide_overlay":
        overlay_hide()
    elif msg_type == "rebuild_overlay":
        overlay_rebuild()
    elif msg_type == "preview_farm_regions":
        preview_farm_regions(msg.get("payload", {}).get("points", {}))
    elif msg_type == "preview_settings_regions":
        preview_settings_regions(msg.get("payload", {}).get("regions", {}))
    elif msg_type == "start_farm_bot":
        global FARM_THREAD
        if FARM_THREAD and FARM_THREAD.is_alive():
            send("farm_bot_status", {"running": True, "message": "Farm bot already running"})
        else:
            stop_flag.clear()
            move_choice = msg.get("payload", {}).get("move_choice") or CFG.get("farm_move_choice", "move1")
            FARM_THREAD = threading.Thread(target=farm_bot_loop, args=(stop_flag, move_choice), daemon=True)
            FARM_THREAD.start()
            send("farm_bot_status", {"running": True, "message": "Farm bot started"})
    elif msg_type == "stop_bot":
        stop_flag.set()
        pause_flag.clear()
        overlay_stop()
        stop_global_hotkeys()
        try: session_end()
        except Exception: pass
        send("bot_status", {"running": False, "message": "Stop requested"})
        send("runtime_state", get_runtime_state())
    elif msg_type == "quit":
        stop_flag.set()
        pause_flag.clear()
        try: session_end()
        except Exception: pass
        send("shutdown", {"message": "Python backend shutting down"})
        return False
    else:
        send("unknown", {"message": f"Unknown message type: {msg_type}"})
    return True

def main():
    enable_dpi_awareness()
    migrate_user_data()
    ensure_dirs()
    _write_marker(DATA_ROOT)
    seed_from_exe_folder()
    load_ini()
    try: session_data_autodelete_apply()
    except Exception: pass
    ensure_tesseract_cmd()
    try: _init_hover_sound_engine()
    except Exception as e: _log(f"Hover sound engine init failed: {e}")
    try: _init_click_sound_engine()
    except Exception as e: _log(f"Click sound engine init failed: {e}")
    try: _init_out_of_balls_sound_engine()
    except Exception as e: _log(f"Out-of-balls sound engine init failed: {e}")
    try: _prune_encounter_logs(force=True)
    except Exception: pass
    try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_NAME)
    except Exception: pass
    threading.Thread(target=_status_poll_loop, daemon=True).start()
    send("backend_ready", {"message": "Python backend is online"})
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        try:
            msg = json.loads(line.strip())
        except Exception:
            send("error", {"message": "Invalid JSON received"})
            continue
        try:
            if not handle_message(msg):
                break
        except Exception as e:
            send("error", {"message": str(e), "traceback": traceback.format_exc()})

if __name__ == "__main__":
    main()