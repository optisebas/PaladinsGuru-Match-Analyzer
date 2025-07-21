#!/usr/bin/env python3
"""
PaladinsGuru Deep Match Analyzer - URL-Only Version
Analiza partidas usando únicamente URLs de PaladinsGuru

Uso: python paladins_analyzer_standalone.py --url "https://paladins.guru/profile/ID-NOMBRE"
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from colorama import Fore, Style, init as colorama_init
from collections import defaultdict
import os
import re
import time
from datetime import datetime, timedelta
import json
import sqlite3
import logging
import sys
import argparse

colorama_init(autoreset=True)

# --- CONFIGURACIÓN GLOBAL CARGADA DESDE JSON ---
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "configuracion_general": {
        "retraso_entre_peticiones_seg": 0.5,
        "max_paginas_historial_a_escanear": 300,
        "top_n_relaciones_a_mostrar": 24,
        "analizar_estadisticas_por_campeon": True,
        "analizar_estadisticas_por_mapa": True,
        "extraer_fecha_partida": True,
        "extraer_mapa_partida": True
    },
    "configuracion_cache": {
        "habilitar_cache_partidas": True,
        "directorio_cache": "cache_partidas",
        "forzar_reanalisis_partidas_cacheadas": False
    },
    "opciones_de_salida": {
        "generar_csv_estadisticas_detalladas": True,
        "generar_csv_relaciones": True,
        "generar_csv_estadisticas_campeon": True,
        "generar_csv_estadisticas_mapa": True,
        "mostrar_resumen_consola_relaciones": True,
        "mostrar_resumen_consola_stats_campeon": True,
        "mostrar_resumen_consola_stats_mapa": True,
        "mostrar_resumen_consola_stats_globales": True
    },
    "base_de_datos_sqlite": {
        "habilitar_sqlite": True,
        "nombre_archivo_db": "paladins_analisis.sqlite"
    },
    "depuracion_y_logging": {
        "nivel_de_log": "INFO",
        "mostrar_prints_depuracion_curacion": False
    },
    "_configuracion_info": {
        "_uso": "Este archivo contiene solo configuraciones técnicas del script",
        "_entrada_usuarios": "Usa --url para analizar cualquier perfil de PaladinsGuru",
        "_ejemplo": "python paladins_analyzer_standalone.py --url 'https://paladins.guru/profile/ID-NOMBRE'"
    }
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                user_config = json.load(f)
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                        config[key].update(value)
                    else:
                        config[key] = value
            except json.JSONDecodeError:
                print(f"{Fore.RED}[CONFIG] Error al leer {CONFIG_FILE}. Usando configuración por defecto.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}[CONFIG] Archivo {CONFIG_FILE} no encontrado. Creando uno de ejemplo.{Style.RESET_ALL}")
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
    return config

def extract_player_info_from_url(profile_url):
    """Extrae ID y nombre del jugador desde la URL del perfil"""
    match = re.search(r'/profile/(\d+)-([^/]+)', profile_url)
    if match:
        player_id, player_name = match.groups()
        # Limpiar caracteres especiales en el nombre
        clean_name = player_name.replace('%20', ' ').replace('%D0%94', 'D').replace('%D0%B6', 'zh')
        return player_id, clean_name
    else:
        raise ValueError(f"URL de perfil inválida: {profile_url}")

# Cargar configuración
config = load_config()

# --- CONFIGURACIÓN DE LOGGING ---
log_level_str = config.get("depuracion_y_logging", {}).get("nivel_de_log", "INFO").upper()
numeric_log_level = getattr(logging, log_level_str, logging.INFO)

log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=numeric_log_level, format=log_format, datefmt='%Y-%m-%d %H:%M:%S')

if numeric_log_level > logging.DEBUG:
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# --- ACCESO A VALORES DE CONFIGURACIÓN ---
GENERAL_CFG = config.get("configuracion_general", DEFAULT_CONFIG["configuracion_general"])
CACHE_CFG = config.get("configuracion_cache", DEFAULT_CONFIG["configuracion_cache"])
OUTPUT_CFG = config.get("opciones_de_salida", DEFAULT_CONFIG["opciones_de_salida"])
SQLITE_CFG = config.get("base_de_datos_sqlite", DEFAULT_CONFIG["base_de_datos_sqlite"])
DEBUG_CFG = config.get("depuracion_y_logging", DEFAULT_CONFIG["depuracion_y_logging"])

REQUEST_DELAY = GENERAL_CFG.get("retraso_entre_peticiones_seg", 0.5)
MAX_PAGES_TO_SCAN_HISTORY = GENERAL_CFG.get("max_paginas_historial_a_escanear", 300)
TOP_N_RELATIONS = GENERAL_CFG.get("top_n_relaciones_a_mostrar", 24)

# Crear directorio de caché si está habilitado
if CACHE_CFG.get("habilitar_cache_partidas") and not os.path.exists(CACHE_CFG.get("directorio_cache")):
    try:
        os.makedirs(CACHE_CFG.get("directorio_cache"))
        logging.info(f"Directorio de caché '{CACHE_CFG.get('directorio_cache')}' creado.")
    except OSError as e:
        logging.error(f"Error al crear directorio de caché: {e}")
        CACHE_CFG["habilitar_cache_partidas"] = False

# --- CONSTANTES GLOBALES ---
MATCH_BASE_URL = "https://paladins.guru"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
PROFILE_URL_TEMPLATE = "https://paladins.guru/profile/{id}-{name}/matches"

# Selectores CSS
PROFILE_MATCH_LINK_SELECTOR = "a[href^='/match/details/'], a[href^='/match/']"
PAGINATION_UL_SELECTOR = "ul.pagination[data-v-bb727534]"
FALLBACK_PAGINATION_UL_SELECTOR = "ul.pagination"
MATCH_STATS_LOSING_TEAM_TABLE_SELECTOR = "section#match-stats div.match-table.loss"
MATCH_STATS_WINNING_TEAM_TABLE_SELECTOR = "section#match-stats div.match-table.win"
MATCH_STATS_PLAYER_ROW_SELECTOR = "div.row.match-table__row"
MATCH_STATS_PLAYER_INFO_CONTAINER = "div.row__player"
MATCH_STATS_PLAYER_NAME_SELECTOR = "a.row__player__name"
MATCH_STATS_PLAYER_CHAMP_IMG_SELECTOR = "img.row__player__img"
MATCH_STATS_SECTION_SCROLLABLE_SELECTOR = "section#match-stats div.scrollable"
ALL_TABLES_IN_SCROLLABLE_SELECTOR = "div.match-table"
ADV_STATS_PLAYER_ROW_SELECTOR = "div.row.match-table__row"
ADV_STATS_PLAYER_NAME_SELECTOR = "a.row__player__name"
MATCH_MAP_NAME_SELECTOR = "div.match-header__map-name, span.match-title__map, div.map-name"
MATCH_DATETIME_AGO_SELECTOR = "div.match-header__time span, span.timeago, time.timeago"

# Variables globales para SQLite
DB_CONN = None
DB_CURSOR = None

# --- FUNCIONES DE BASE DE DATOS ---
def init_sqlite():
    global DB_CONN, DB_CURSOR
    if SQLITE_CFG.get("habilitar_sqlite"):
        db_name = SQLITE_CFG.get("nombre_archivo_db", "paladins_analisis.sqlite")
        try:
            DB_CONN = sqlite3.connect(db_name)
            DB_CURSOR = DB_CONN.cursor()
            logging.info(f"{Fore.GREEN}Conectado a la base de datos SQLite: {db_name}{Style.RESET_ALL}")
            
            # Crear tablas
            DB_CURSOR.execute('CREATE TABLE IF NOT EXISTS Partidas (MatchID TEXT PRIMARY KEY, MapName TEXT, MatchDateTime TEXT)')
            DB_CURSOR.execute('''
                CREATE TABLE IF NOT EXISTS EstadisticasJugadorPartida (
                    StatID INTEGER PRIMARY KEY AUTOINCREMENT,
                    MatchID TEXT,
                    PlayerID TEXT,
                    PlayerName TEXT,
                    Champion TEXT,
                    TeamIdx INTEGER,
                    WonMatch INTEGER,
                    Level INTEGER,
                    Kills INTEGER,
                    Deaths INTEGER,
                    Assists INTEGER,
                    KDA REAL,
                    Credits INTEGER,
                    CPM INTEGER,
                    DamageDealt INTEGER,
                    DamageTaken INTEGER,
                    Shielding INTEGER,
                    Healing INTEGER,
                    FOREIGN KEY (MatchID) REFERENCES Partidas (MatchID)
                )
            ''')
            DB_CONN.commit()
            logging.info(f"{Fore.GREEN}Tablas SQLite verificadas/creadas.{Style.RESET_ALL}")
        except sqlite3.Error as e:
            logging.error(f"{Fore.RED}Error al inicializar SQLite: {e}{Style.RESET_ALL}")
            SQLITE_CFG["habilitar_sqlite"] = False

def close_sqlite():
    if DB_CONN:
        try:
            DB_CONN.close()
            logging.info(f"{Fore.GREEN}Conexión SQLite cerrada.{Style.RESET_ALL}")
        except sqlite3.Error as e:
            logging.error(f"{Fore.RED}Error al cerrar conexión SQLite: {e}{Style.RESET_ALL}")

def save_match_data_to_sqlite(match_id, map_name, match_datetime, players_data):
    if not SQLITE_CFG.get("habilitar_sqlite") or not DB_CURSOR:
        return
    
    try:
        DB_CURSOR.execute("INSERT OR IGNORE INTO Partidas (MatchID, MapName, MatchDateTime) VALUES (?, ?, ?)",
                         (match_id, map_name, match_datetime.isoformat() if match_datetime else None))
        
        for p_data in players_data:
            if p_data.get('ParseError'):
                continue
                
            DB_CURSOR.execute('''
                INSERT INTO EstadisticasJugadorPartida 
                (MatchID, PlayerID, PlayerName, Champion, TeamIdx, WonMatch, Level, Kills, Deaths, Assists, KDA, Credits, CPM, DamageDealt, DamageTaken, Shielding, Healing)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (p_data.get('MatchID'), p_data.get('PlayerID','NO_ID'), p_data.get('PlayerName','Unknown'),
                 p_data.get('Champion','Unknown'), p_data.get('TeamIdx'), 1 if p_data.get('WonMatch') else 0,
                 p_data.get('Level',0), p_data.get('Kills',0), p_data.get('Deaths',0), p_data.get('Assists',0),
                 p_data.get('KDA',0.0), p_data.get('Credits',0), p_data.get('CPM',0), p_data.get('DamageDealt',0),
                 p_data.get('DamageTaken',0), p_data.get('Shielding',0), p_data.get('Healing',0)))
        
        DB_CONN.commit()
        logging.debug(f"Datos de la partida {match_id} guardados en SQLite.")
    except sqlite3.Error as e:
        logging.error(f"{Fore.RED}Error al guardar datos en SQLite para {match_id}: {e}{Style.RESET_ALL}")

def is_match_in_sqlite(match_id):
    if not SQLITE_CFG.get("habilitar_sqlite") or not DB_CURSOR:
        return False
    try:
        DB_CURSOR.execute("SELECT 1 FROM Partidas WHERE MatchID = ?", (match_id,))
        return DB_CURSOR.fetchone() is not None
    except sqlite3.Error as e:
        logging.error(f"{Fore.RED}Error al verificar partida en SQLite {match_id}: {e}{Style.RESET_ALL}")
        return False

# --- FUNCIONES AUXILIARES ---
def safe_get_request(url, retries=3, delay_on_retry=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logging.warning(f"{Fore.YELLOW}HTTP 429: {url}. Esperando {delay_on_retry*(attempt+2)}s...{Style.RESET_ALL}")
                time.sleep(delay_on_retry*(attempt+2))
            elif e.response.status_code in [404, 500]:
                logging.error(f"{Fore.RED}HTTP {e.response.status_code}: {url}. No reintentar.{Style.RESET_ALL}")
                return None
            else:
                logging.error(f"{Fore.RED}HTTP Error: {e} en {url}{Style.RESET_ALL}")
        except requests.exceptions.RequestException as e:
            logging.error(f"{Fore.RED}Error de Red/Conexión: {e} en {url}{Style.RESET_ALL}")
        
        if attempt < retries - 1:
            logging.warning(f"{Fore.YELLOW}Reintento {attempt+1}/{retries} para {url}...{Style.RESET_ALL}")
            time.sleep(delay_on_retry)
    
    logging.error(f"{Fore.RED}Fallaron todos los reintentos para {url}{Style.RESET_ALL}")
    return None

def extract_player_id_from_href(href):
    if not href:
        return ""
    match = re.search(r'/profile/(\d+)-', href)
    return match.group(1) if match else ""

def parse_stat_value(text_value):
    if not text_value:
        return 0
    cleaned_value = text_value.strip().replace(".", "").replace(",", "")
    return int(cleaned_value) if cleaned_value.isdigit() else 0

def parse_relative_time(time_str):
    if not time_str or "ago" not in time_str.lower():
        return None
        
    now = datetime.now()
    time_str = time_str.lower().replace(" ago", "").strip()
    
    try:
        val_match = re.search(r'(\d+)', time_str)
        if not val_match:
            if "moment" in time_str:
                return now
            if "an hour" in time_str:
                return now - timedelta(hours=1)
            if "a day" in time_str:
                return now - timedelta(days=1)
            return now
        
        val = int(val_match.group(1))
        if "second" in time_str:
            return now - timedelta(seconds=val)
        elif "minute" in time_str:
            return now - timedelta(minutes=val)
        elif "hour" in time_str:
            return now - timedelta(hours=val)
        elif "day" in time_str:
            return now - timedelta(days=val)
        elif "week" in time_str:
            return now - timedelta(weeks=val)
        elif "month" in time_str:
            return now - timedelta(days=val * 30)
        elif "year" in time_str:
            return now - timedelta(days=val * 365)
    except Exception as e:
        logging.error(f"{Fore.RED}Error parseando tiempo relativo '{time_str}': {e}{Style.RESET_ALL}")
        return None
    
    return None

# --- FUNCIONES DE PARSING ---
def parse_player_main_stats(player_row_el, match_id_str, map_name_str, match_datetime_obj, team_idx_int, team_won_bool):
    player_name_str, player_id_str, champion_str = "UnknownPlayer", "NO_ID", "UnknownChamp"
    stats = {'Level':0,'Kills':0,'Deaths':0,'Assists':0,'KDA':0.0,'Credits':0,'CPM':0,'DamageDealt':0,'DamageTaken':0,'Shielding':0,'Healing':0}
    
    try:
        player_info_el = player_row_el.select_one(MATCH_STATS_PLAYER_INFO_CONTAINER)
        if not player_info_el:
            logging.debug("Contenedor player_info_el no encontrado.")
            return None
        
        name_el = player_info_el.select_one(MATCH_STATS_PLAYER_NAME_SELECTOR)
        champ_img_el = player_info_el.select_one(MATCH_STATS_PLAYER_CHAMP_IMG_SELECTOR)
        
        if not (name_el and champ_img_el):
            logging.debug("Nombre o imagen de campeón no encontrado.")
            return None
        
        player_name_str = name_el.text.strip()
        player_id_str = extract_player_id_from_href(name_el.get('href')) or "NO_ID"
        champion_str = champ_img_el.get('alt', "UnknownChamp").strip()
        
        direct_stat_items = [item for item in player_row_el.find_all('div', class_='row__item', recursive=False)]
        if len(direct_stat_items) < 7:
            logging.debug(f"Stats incompletas para {player_name_str} ({len(direct_stat_items)} de 7+).")
            return None
        
        stats['Level'] = parse_stat_value(direct_stat_items[0].text)
        
        kda_text = direct_stat_items[1].text.strip()
        kda_parts = [p.strip() for p in kda_text.split("/")]
        if len(kda_parts) == 3 and all(p.isdigit() for p in kda_parts):
            stats['Kills'], stats['Deaths'], stats['Assists'] = int(kda_parts[0]), int(kda_parts[1]), int(kda_parts[2])
            stats['KDA'] = round((stats['Kills'] + stats['Assists']) / max(stats['Deaths'], 1), 2)
        else:
            logging.warning(f"{Fore.YELLOW}KDA malformado '{kda_text}' para {player_name_str} en {match_id_str}{Style.RESET_ALL}")
        
        stats['Credits'] = parse_stat_value(direct_stat_items[2].text)
        stats['CPM'] = parse_stat_value(direct_stat_items[3].text)
        stats['DamageDealt'] = parse_stat_value(direct_stat_items[4].text)
        stats['DamageTaken'] = parse_stat_value(direct_stat_items[5].text)
        stats['Shielding'] = parse_stat_value(direct_stat_items[6].text)
        
        return {
            'MatchID': match_id_str,
            'PlayerName': player_name_str,
            'PlayerID': player_id_str,
            'Champion': champion_str,
            'MapName': map_name_str if GENERAL_CFG.get("extraer_mapa_partida") else "N/A_config",
            'MatchDateTime': match_datetime_obj.isoformat() if match_datetime_obj and GENERAL_CFG.get("extraer_fecha_partida") else None,
            'TeamIdx': team_idx_int,
            'WonMatch': team_won_bool,
            **stats,
            'ParseError': False
        }
        
    except Exception as e:
        logging.error(f"{Fore.RED}EXCEPCIÓN en parse_player_main_stats para {player_name_str}: {e}{Style.RESET_ALL}")
        return {
            'MatchID': match_id_str,
            'PlayerName': player_name_str,
            'PlayerID': player_id_str,
            'Champion': champion_str,
            'MapName': map_name_str,
            'MatchDateTime': match_datetime_obj.isoformat() if match_datetime_obj else None,
            'TeamIdx': team_idx_int,
            'WonMatch': team_won_bool,
            **stats,
            'ParseError': True
        }

def add_healing_from_advanced_stats(soup, all_player_data_in_match):
    if DEBUG_CFG.get("mostrar_prints_depuracion_curacion"):
        logging.debug(f"{Fore.BLUE}Buscando tablas avanzadas para curación...{Style.RESET_ALL}")
    
    parent_scrollable = soup.select_one(MATCH_STATS_SECTION_SCROLLABLE_SELECTOR)
    if not parent_scrollable:
        logging.debug(f"{Fore.YELLOW}Contenedor padre para tablas avanzadas no encontrado.{Style.RESET_ALL}")
        return
    
    all_tables_in_parent = parent_scrollable.select(ALL_TABLES_IN_SCROLLABLE_SELECTOR)
    if DEBUG_CFG.get("mostrar_prints_depuracion_curacion"):
        logging.debug(f"Tablas encontradas en scrollable: {len(all_tables_in_parent)}")
    
    if len(all_tables_in_parent) < 4:
        logging.debug(f"{Fore.YELLOW}No hay suficientes tablas para stats avanzadas de curación.{Style.RESET_ALL}")
        return
    
    advanced_tables_to_process = all_tables_in_parent[2:4]
    healing_data = {}
    
    for table_el in advanced_tables_to_process:
        player_rows_adv = table_el.select(ADV_STATS_PLAYER_ROW_SELECTOR)
        for row_adv in player_rows_adv:
            name_el_adv = row_adv.select_one(ADV_STATS_PLAYER_NAME_SELECTOR)
            if not name_el_adv:
                continue
            
            player_id_adv = extract_player_id_from_href(name_el_adv.get('href')) or "NO_ID_ADV_HEAL"
            player_name_adv = name_el_adv.text.strip()
            
            if player_id_adv == "NO_ID_ADV_HEAL" and not player_name_adv:
                continue
            
            direct_stat_items_adv = [item for item in row_adv.find_all('div', class_='row__item', recursive=False)]
            if len(direct_stat_items_adv) >= 3:
                healing_value = parse_stat_value(direct_stat_items_adv[2].text)
                key_to_use = player_id_adv if player_id_adv != "NO_ID_ADV_HEAL" else player_name_adv.lower()
                healing_data[key_to_use] = healing_value
    
    for player_stats in all_player_data_in_match:
        heal_val = 0
        player_id_key = player_stats.get('PlayerID', "NO_ID")
        player_name_key = player_stats.get('PlayerName', "").lower()
        
        if player_id_key != "NO_ID" and player_id_key in healing_data:
            heal_val = healing_data[player_id_key]
        elif player_name_key and player_name_key in healing_data:
            heal_val = healing_data[player_name_key]
        
        player_stats['Healing'] = heal_val

# --- FUNCIONES PRINCIPALES DE SCRAPING ---
def download_match_links_for_player(player_name, player_id):
    base_url_for_profile_page = PROFILE_URL_TEMPLATE.format(id=player_id, name=player_name.lower().replace(" ", "%20"))
    all_match_urls_set = set()
    current_page = 1
    max_pages_to_check = MAX_PAGES_TO_SCAN_HISTORY
    
    logging.info(f"{Fore.CYAN}Descargando historial para {player_name} (ID: {player_id}). Máx. páginas: {max_pages_to_check}.{Style.RESET_ALL}")
    
    while current_page <= max_pages_to_check:
        page_url = f"{base_url_for_profile_page}?page={current_page}" if current_page > 1 else base_url_for_profile_page
        logging.info(f"{Fore.BLUE}Procesando página de historial: {current_page}{Style.RESET_ALL}")
        
        response = safe_get_request(page_url)
        if not response:
            logging.error(f"{Fore.RED}No se pudo obtener página {current_page}. Deteniendo paginación.{Style.RESET_ALL}")
            break
        
        soup = BeautifulSoup(response.text, 'html.parser')
        match_list_container = soup.select_one("div.match-history-list, div.infinite-scroll > div > div")
        link_elements = match_list_container.select("a[href^='/match/']") if match_list_container else soup.select(PROFILE_MATCH_LINK_SELECTOR)
        
        if not link_elements and current_page > 1:
            logging.warning(f"{Fore.YELLOW}No se encontraron más enlaces en la página {current_page}.{Style.RESET_ALL}")
            break
        
        new_links_count = 0
        for a in link_elements:
            href = a.get('href')
            if href and ('/match/details/' in href or ('/match/' in href and '/profile/' not in href)):
                path_parts = [p for p in href.split('/') if p]
                if path_parts and path_parts[0] == 'match' and (len(path_parts) == 2 or (len(path_parts) == 3 and path_parts[1] == 'details')):
                    full_url = MATCH_BASE_URL + href
                    if full_url not in all_match_urls_set:
                        all_match_urls_set.add(full_url)
                        new_links_count += 1
        
        if new_links_count == 0 and current_page > 1:
            logging.info(f"{Fore.YELLOW}No se encontraron NUEVOS enlaces válidos en página {current_page}.{Style.RESET_ALL}")
        
        pagination_ul = soup.select_one(PAGINATION_UL_SELECTOR) or soup.select_one(FALLBACK_PAGINATION_UL_SELECTOR)
        if not pagination_ul:
            logging.info(f"{Fore.YELLOW}No se encontró bloque de paginación en página {current_page}.{Style.RESET_ALL}")
            break
        
        next_li_element = pagination_ul.select_one("li:last-child")
        has_next_page = False
        if next_li_element and not next_li_element.get('class'):
            next_link = next_li_element.select_one("a")
            if next_link and next_link.get('href') and 'disabled' not in next_li_element.get('class', []):
                has_next_page = True
        
        if not has_next_page:
            logging.info(f"{Fore.GREEN}Última página de historial alcanzada: {current_page}{Style.RESET_ALL}")
            break
        
        current_page += 1
        if REQUEST_DELAY > 0:
            time.sleep(REQUEST_DELAY)
    
    logging.info(f"{Fore.GREEN}Total de enlaces de partida encontrados: {len(all_match_urls_set)}{Style.RESET_ALL}")
    return list(all_match_urls_set)

def download_and_parse_single_match(match_url):
    match_id = match_url.split('/')[-1] if match_url.split('/')[-1] else match_url.split('/')[-2]
    
    # Verificar si ya está en SQLite
    if SQLITE_CFG.get("habilitar_sqlite") and not CACHE_CFG.get("forzar_reanalisis_partidas_cacheadas"):
        if is_match_in_sqlite(match_id):
            logging.debug(f"Partida {match_id} ya existe en SQLite. Saltando.")
            return []
    
    # Verificar caché HTML
    cache_file_path = None
    if CACHE_CFG.get("habilitar_cache_partidas"):
        cache_file_path = os.path.join(CACHE_CFG.get("directorio_cache"), f"{match_id}.html")
        if os.path.exists(cache_file_path) and not CACHE_CFG.get("forzar_reanalisis_partidas_cacheadas"):
            logging.debug(f"Usando caché para partida {match_id}")
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
        else:
            response = safe_get_request(match_url)
            if not response:
                logging.warning(f"{Fore.YELLOW}No se pudo obtener datos para {match_url}{Style.RESET_ALL}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Guardar en caché
            if cache_file_path:
                with open(cache_file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logging.debug(f"Guardado en caché: {cache_file_path}")
    else:
        response = safe_get_request(match_url)
        if not response:
            logging.warning(f"{Fore.YELLOW}No se pudo obtener datos para {match_url}{Style.RESET_ALL}")
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extraer información del mapa y fecha
    map_name = "UnknownMap"
    if GENERAL_CFG.get("extraer_mapa_partida"):
        map_element = soup.select_one(MATCH_MAP_NAME_SELECTOR)
        if map_element:
            map_name = map_element.text.strip()
    
    match_datetime = None
    if GENERAL_CFG.get("extraer_fecha_partida"):
        time_element = soup.select_one(MATCH_DATETIME_AGO_SELECTOR)
        if time_element:
            match_datetime = parse_relative_time(time_element.text.strip())
    
    # Obtener tablas de equipos
    losing_team_table = soup.select_one(MATCH_STATS_LOSING_TEAM_TABLE_SELECTOR)
    winning_team_table = soup.select_one(MATCH_STATS_WINNING_TEAM_TABLE_SELECTOR)
    
    all_player_data = []
    
    # Procesar equipo perdedor (Team 0)
    if losing_team_table:
        losing_players = losing_team_table.select(MATCH_STATS_PLAYER_ROW_SELECTOR)
        for player_row in losing_players:
            player_data = parse_player_main_stats(player_row, match_id, map_name, match_datetime, 0, False)
            if player_data:
                all_player_data.append(player_data)
    
    # Procesar equipo ganador (Team 1)
    if winning_team_table:
        winning_players = winning_team_table.select(MATCH_STATS_PLAYER_ROW_SELECTOR)
        for player_row in winning_players:
            player_data = parse_player_main_stats(player_row, match_id, map_name, match_datetime, 1, True)
            if player_data:
                all_player_data.append(player_data)
    
    # Añadir datos de curación
    add_healing_from_advanced_stats(soup, all_player_data)
    
    # Guardar en SQLite
    if SQLITE_CFG.get("habilitar_sqlite"):
        save_match_data_to_sqlite(match_id, map_name, match_datetime, all_player_data)
    
    if REQUEST_DELAY > 0:
        time.sleep(REQUEST_DELAY)
    
    return all_player_data

def analyze_matches_for_player(player_name, player_id, match_urls):
    all_matches_data = []
    total_matches = len(match_urls)
    
    logging.info(f"{Fore.GREEN}=== ANALIZANDO {len(match_urls)} PARTIDAS PARA {player_name.upper()} ==={Style.RESET_ALL}")
    
    for i, match_url in enumerate(match_urls, 1):
        logging.info(f"{Fore.BLUE}[{i}/{len(match_urls)}] Procesando: {match_url}{Style.RESET_ALL}")
        match_data = download_and_parse_single_match(match_url)
        all_matches_data.extend(match_data)
    
    if not all_matches_data:
        logging.warning(f"{Fore.YELLOW}No se pudieron obtener datos de partidas para {player_name}.{Style.RESET_ALL}")
        return
    
    # Crear DataFrame
    df = pd.DataFrame(all_matches_data)
    
    # Filtrar datos del jugador analizado
    player_df = df[df['PlayerID'] == player_id].copy()
    if player_df.empty:
        player_df = df[df['PlayerName'].str.lower() == player_name.lower()].copy()
    
    if player_df.empty:
        logging.warning(f"{Fore.YELLOW}No se encontraron datos específicos para {player_name} en las partidas.{Style.RESET_ALL}")
        return
    
    # Generar análisis y archivos CSV
    generate_analysis_and_csvs(player_name, df, player_df)

def calculate_statistical_relevance(teammate_stats):
    """Calcula un score de relevancia estadística combinando winrate y número de partidas"""
    teammate_stats = teammate_stats.copy()
    
    # Score base del winrate
    teammate_stats['BaseScore'] = teammate_stats['WinRate']
    
    # Factor de confianza basado en número de partidas
    # Más partidas = más confiable el winrate
    teammate_stats['ConfidenceFactor'] = teammate_stats['TotalGames'].apply(
        lambda x: min(1.0, x / 10)  # Máximo factor de confianza a las 10 partidas
    )
    
    # Score final: winrate ajustado por confianza
    teammate_stats['RelevanceScore'] = (
        teammate_stats['BaseScore'] * teammate_stats['ConfidenceFactor'] * 0.7 + 
        teammate_stats['TotalGames'] * 2  # Bonificación por número de partidas
    ).round(1)
    
    return teammate_stats.sort_values('RelevanceScore', ascending=False)

def generate_analysis_and_csvs(player_name, all_df, player_df):
    """Genera todos los análisis y archivos CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV de estadísticas detalladas
    if OUTPUT_CFG.get("generar_csv_estadisticas_detalladas"):
        detailed_csv = f"estadisticas_detalladas_{player_name}_{timestamp}.csv"
        all_df.to_csv(detailed_csv, index=False, encoding='utf-8')
        logging.info(f"{Fore.GREEN}CSV detallado generado: {detailed_csv}{Style.RESET_ALL}")
    
    # Análisis de relaciones (con quién gana/pierde más)
    if OUTPUT_CFG.get("generar_csv_relaciones") or OUTPUT_CFG.get("mostrar_resumen_consola_relaciones"):
        player_matches = player_df['MatchID'].unique()
        relations_data = []
        
        for match_id in player_matches:
            match_players = all_df[all_df['MatchID'] == match_id]
            player_row = match_players[match_players['PlayerID'] == player_df.iloc[0]['PlayerID']]
            if player_row.empty:
                continue
            
            player_won = player_row.iloc[0]['WonMatch']
            player_team = player_row.iloc[0]['TeamIdx']
            
            teammates = match_players[
                (match_players['TeamIdx'] == player_team) & 
                (match_players['PlayerID'] != player_df.iloc[0]['PlayerID'])
            ]
            
            for _, teammate in teammates.iterrows():
                relations_data.append({
                    'MatchID': match_id,
                    'TeammateID': teammate['PlayerID'],
                    'TeammateName': teammate['PlayerName'],
                    'TeammateChampion': teammate['Champion'],
                    'Won': player_won,
                    'MapName': teammate['MapName']
                })
        
        if relations_data:
            relations_df = pd.DataFrame(relations_data)
            
            # Generar CSV de relaciones
            if OUTPUT_CFG.get("generar_csv_relaciones"):
                relations_csv = f"relaciones_{player_name}_{timestamp}.csv"
                relations_df.to_csv(relations_csv, index=False, encoding='utf-8')
                logging.info(f"{Fore.GREEN}CSV de relaciones generado: {relations_csv}{Style.RESET_ALL}")
            
            # Mostrar resumen de relaciones en consola CON CORRECCIÓN
            if OUTPUT_CFG.get("mostrar_resumen_consola_relaciones"):
                teammate_stats = relations_df.groupby(['TeammateID', 'TeammateName']).agg({
                    'Won': ['count', 'sum']
                }).round(2)
                teammate_stats.columns = ['TotalGames', 'Wins']
                teammate_stats['Losses'] = teammate_stats['TotalGames'] - teammate_stats['Wins']
                teammate_stats['WinRate'] = (teammate_stats['Wins'] / teammate_stats['TotalGames'] * 100).round(1)
                
                # CORRECCIÓN: Ordenamiento inteligente por relevancia estadística
                # Primero por número de partidas (descendente), luego por winrate (descendente)
                teammate_stats_sorted = teammate_stats.sort_values(['TotalGames', 'WinRate'], ascending=[False, False])
                
                # Separar en dos grupos para mejor análisis
                # Grupo 1: Compañeros con múltiples partidas (más significativo)
                multi_game_teammates = teammate_stats_sorted[teammate_stats_sorted['TotalGames'] > 1]
                # Grupo 2: Compañeros con 1 sola partida
                single_game_teammates = teammate_stats_sorted[teammate_stats_sorted['TotalGames'] == 1]
                
                print(f"\n{Fore.CYAN}=== COMPAÑEROS MÁS FRECUENTES (2+ partidas) PARA {player_name.upper()} ==={Style.RESET_ALL}")
                if not multi_game_teammates.empty:
                    print(multi_game_teammates.head(15).to_string())
                    print(f"\n{Fore.YELLOW}📊 Mostrando compañeros con múltiples partidas (más estadísticamente relevantes){Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}⚠️  No hay compañeros con múltiples partidas registradas{Style.RESET_ALL}")
                
                print(f"\n{Fore.GREEN}=== TOP 15 MEJORES WINRATES (1 partida) PARA {player_name.upper()} ==={Style.RESET_ALL}")
                if not single_game_teammates.empty:
                    best_single = single_game_teammates[single_game_teammates['WinRate'] == 100.0].head(15)
                    print(best_single.to_string())
                
                print(f"\n{Fore.RED}=== COMPAÑEROS CON PEORES RESULTADOS PARA {player_name.upper()} ==={Style.RESET_ALL}")
                # Mostrar los peores por winrate, priorizando los que tienen más partidas
                worst_teammates = teammate_stats_sorted.sort_values(['WinRate', 'TotalGames'], ascending=[True, False])
                print(worst_teammates.tail(15).to_string())
                
                # EXTRA: Análisis de compañeros "problema" (winrate < 50% con múltiples partidas)
                problem_teammates = teammate_stats_sorted[
                    (teammate_stats_sorted['WinRate'] < 50.0) & 
                    (teammate_stats_sorted['TotalGames'] > 1)
                ]
                
                if not problem_teammates.empty:
                    print(f"\n{Fore.MAGENTA}=== ⚠️  COMPAÑEROS PROBLEMÁTICOS (Winrate < 50% y 2+ partidas) ==={Style.RESET_ALL}")
                    print(problem_teammates.to_string())
                    print(f"{Fore.YELLOW}💡 Considera evitar hacer equipo con estos jugadores{Style.RESET_ALL}")
                
                # ANÁLISIS DE RELEVANCIA ESTADÍSTICA
                teammate_stats_relevant = calculate_statistical_relevance(teammate_stats)
                print(f"\n{Fore.CYAN}=== RANKING POR RELEVANCIA ESTADÍSTICA (TOP 20) ==={Style.RESET_ALL}")
                print(teammate_stats_relevant[['TotalGames', 'Wins', 'Losses', 'WinRate', 'RelevanceScore']].head(20).to_string())
    
    # Análisis por campeón
    if GENERAL_CFG.get("analizar_estadisticas_por_campeon"):
        if OUTPUT_CFG.get("generar_csv_estadisticas_campeon") or OUTPUT_CFG.get("mostrar_resumen_consola_stats_campeon"):
            champion_stats = player_df.groupby('Champion').agg({
                'WonMatch': ['count', 'sum'],
                'Kills': 'mean',
                'Deaths': 'mean',
                'Assists': 'mean',
                'KDA': 'mean',
                'DamageDealt': 'mean',
                'Healing': 'mean'
            }).round(2)
            
            champion_stats.columns = ['TotalGames', 'Wins', 'AvgKills', 'AvgDeaths', 'AvgAssists', 'AvgKDA', 'AvgDamage', 'AvgHealing']
            champion_stats['WinRate'] = (champion_stats['Wins'] / champion_stats['TotalGames'] * 100).round(1)
            champion_stats = champion_stats.sort_values(['TotalGames', 'WinRate'], ascending=[False, False])
            
            if OUTPUT_CFG.get("generar_csv_estadisticas_campeon"):
                champion_csv = f"estadisticas_campeon_{player_name}_{timestamp}.csv"
                champion_stats.to_csv(champion_csv, encoding='utf-8')
                logging.info(f"{Fore.GREEN}CSV de estadísticas por campeón generado: {champion_csv}{Style.RESET_ALL}")
            
            if OUTPUT_CFG.get("mostrar_resumen_consola_stats_campeon"):
                print(f"\n{Fore.MAGENTA}=== ESTADÍSTICAS POR CAMPEÓN PARA {player_name.upper()} ==={Style.RESET_ALL}")
                print(champion_stats.to_string())
    
    # Análisis por mapa
    if GENERAL_CFG.get("analizar_estadisticas_por_mapa"):
        if OUTPUT_CFG.get("generar_csv_estadisticas_mapa") or OUTPUT_CFG.get("mostrar_resumen_consola_stats_mapa"):
            map_stats = player_df.groupby('MapName').agg({
                'WonMatch': ['count', 'sum'],
                'Kills': 'mean',
                'Deaths': 'mean',
                'Assists': 'mean',
                'KDA': 'mean'
            }).round(2)
            
            map_stats.columns = ['TotalGames', 'Wins', 'AvgKills', 'AvgDeaths', 'AvgAssists', 'AvgKDA']
            map_stats['WinRate'] = (map_stats['Wins'] / map_stats['TotalGames'] * 100).round(1)
            map_stats = map_stats.sort_values(['TotalGames', 'WinRate'], ascending=[False, False])
            
            if OUTPUT_CFG.get("generar_csv_estadisticas_mapa"):
                map_csv = f"estadisticas_mapa_{player_name}_{timestamp}.csv"
                map_stats.to_csv(map_csv, encoding='utf-8')
                logging.info(f"{Fore.GREEN}CSV de estadísticas por mapa generado: {map_csv}{Style.RESET_ALL}")
            
            if OUTPUT_CFG.get("mostrar_resumen_consola_stats_mapa"):
                print(f"\n{Fore.YELLOW}=== ESTADÍSTICAS POR MAPA PARA {player_name.upper()} ==={Style.RESET_ALL}")
                print(map_stats.to_string())
    
    # Estadísticas globales
    if OUTPUT_CFG.get("mostrar_resumen_consola_stats_globales"):
        total_games = len(player_df)
        total_wins = player_df['WonMatch'].sum()
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        
        avg_kills = player_df['Kills'].mean()
        avg_deaths = player_df['Deaths'].mean()
        avg_assists = player_df['Assists'].mean()
        avg_kda = player_df['KDA'].mean()
        avg_damage = player_df['DamageDealt'].mean()
        avg_healing = player_df['Healing'].mean()
        
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"RESUMEN GLOBAL PARA {player_name.upper()}")
        print(f"{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total de partidas analizadas: {total_games}")
        print(f"Victorias: {total_wins} | Derrotas: {total_games - total_wins}")
        print(f"Winrate: {win_rate:.1f}%{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Promedios:")
        print(f"  K/D/A: {avg_kills:.1f}/{avg_deaths:.1f}/{avg_assists:.1f}")
        print(f"  KDA Ratio: {avg_kda:.2f}")
        print(f"  Daño: {avg_damage:,.0f}")
        print(f"  Curación: {avg_healing:,.0f}{Style.RESET_ALL}")

def main():
    """Función principal del analizador - SOLO acepta URL"""
    parser = argparse.ArgumentParser(description='PaladinsGuru Deep Match Analyzer')
    parser.add_argument('--url', type=str, required=True, 
                       help='URL del perfil de PaladinsGuru (REQUERIDO)')
    parser.add_argument('--pages', type=int, 
                       help='Páginas a escanear (sobreescribe config.json)')
    
    args = parser.parse_args()
    
    # Extraer información del jugador desde URL
    try:
        player_id, player_name = extract_player_info_from_url(args.url)
        logging.info(f"{Fore.GREEN}🎯 Analizando: {player_name} (ID: {player_id}){Style.RESET_ALL}")
        logging.info(f"{Fore.BLUE}📄 URL: {args.url}{Style.RESET_ALL}")
    except ValueError as e:
        logging.error(f"{Fore.RED}❌ {e}{Style.RESET_ALL}")
        logging.info(f"{Fore.YELLOW}💡 Formato: https://paladins.guru/profile/ID-NOMBRE{Style.RESET_ALL}")
        logging.info(f"{Fore.YELLOW}💡 Ejemplo: https://paladins.guru/profile/725628302-katrella{Style.RESET_ALL}")
        sys.exit(1)
    
    # Configurar páginas máximas
    global MAX_PAGES_TO_SCAN_HISTORY
    if args.pages:
        MAX_PAGES_TO_SCAN_HISTORY = args.pages
        logging.info(f"{Fore.CYAN}⚙️ Páginas personalizadas: {args.pages}{Style.RESET_ALL}")
    else:
        logging.info(f"{Fore.CYAN}⚙️ Páginas desde config: {MAX_PAGES_TO_SCAN_HISTORY}{Style.RESET_ALL}")
    
    # Resto del análisis
    init_sqlite()
    
    match_urls = download_match_links_for_player(player_name, player_id)
    if match_urls:
        analyze_matches_for_player(player_name, player_id, match_urls)
        logging.info(f"{Fore.GREEN}🎉 Análisis completado para {player_name}!{Style.RESET_ALL}")
    else:
        logging.warning(f"{Fore.YELLOW}⚠️ No se encontraron partidas para analizar{Style.RESET_ALL}")
    
    close_sqlite()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}🛑 Análisis interrumpido por el usuario{Style.RESET_ALL}")
        close_sqlite()
        sys.exit(1)
    except Exception as e:
        logging.error(f"{Fore.RED}❌ Error crítico durante el análisis: {e}{Style.RESET_ALL}")
        close_sqlite()
        sys.exit(1)
