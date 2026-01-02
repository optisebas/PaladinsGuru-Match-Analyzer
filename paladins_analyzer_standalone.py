#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
   🚀 OPTISEBAS PALADINS ANALYZER - ULTIMATE SPEED EDITION (2026)
   -------------------------------------------------------------------------
   Autor:       OptiSebas
   Descripción: Analizador profundo de partidas de PaladinsGuru.
   Tecnología:  Python + Pandas + SQLite + Curl_CFFI (Anti-Bloqueo TLS)
   Estado:      OPTIMIZADO: Timeout reducido y User-Agent más ligero.
=============================================================================
"""

# --- 1. IMPORTACIÓN DE LIBRERÍAS ---
import os
import re
import sys
import time
import json
import random
import logging
import sqlite3
import argparse
from datetime import datetime

# Librerías externas
import pandas as pd
from bs4 import BeautifulSoup
from colorama import Fore, Style, init as colorama_init

# Verificación de librerías críticas
try:
    from curl_cffi import requests
except ImportError:
    print(f"{Fore.RED}❌ ERROR CRÍTICO: Falta instalar 'curl_cffi'.{Style.RESET_ALL}")
    print(f"👉 Ejecuta: {Fore.YELLOW}pip install curl-cffi{Style.RESET_ALL}")
    sys.exit(1)

colorama_init(autoreset=True)

# --- 2. CONFIGURACIÓN ---
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "_nota_sistema": "Configuración de respaldo OptiSebas",
    "perfil_vip_por_defecto": {"usar_automaticamente": False, "url_o_id": ""}
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

raw_config = load_config()

# Mapeo de variables
VIP_CFG       = raw_config.get("perfil_vip_por_defecto", {})
ANTI_BOT_CFG  = raw_config.get("configuracion_anti_bloqueo", {})
LIMITS_CFG    = raw_config.get("limites_de_analisis", {})
ANALYSIS_OPTS = raw_config.get("que_quieres_analizar", {})
DB_CFG        = raw_config.get("base_de_datos", {})
OUTPUT_OPTS   = raw_config.get("reportes_y_salida", {})
CACHE_OPTS    = raw_config.get("cache_y_archivos", {})

# AJUSTES DE VELOCIDAD
REQUEST_DELAY = 1.0 # Más rápido entre peticiones
MAX_RETRIES   = 3
MAX_PAGES     = LIMITS_CFG.get("max_paginas_historial", 300)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

MATCH_BASE_URL = "https://paladins.guru"
# Headers simplificados para evitar conflictos
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# --- 3. BASE DE DATOS SQLITE ---
DB_CONN = None
DB_CURSOR = None

def init_sqlite():
    global DB_CONN, DB_CURSOR
    if not DB_CFG.get("usar_sqlite", True): return
    db_name = DB_CFG.get("nombre_archivo", "paladins_analisis.sqlite")
    try:
        DB_CONN = sqlite3.connect(db_name)
        DB_CURSOR = DB_CONN.cursor()
        logging.info(f"{Fore.GREEN}💾 Memoria conectada: {db_name}{Style.RESET_ALL}")
        DB_CURSOR.execute('CREATE TABLE IF NOT EXISTS Partidas (MatchID TEXT PRIMARY KEY, MapName TEXT, MatchDateTime TEXT)')
        DB_CURSOR.execute('''
            CREATE TABLE IF NOT EXISTS EstadisticasJugadorPartida (
                StatID INTEGER PRIMARY KEY AUTOINCREMENT, MatchID TEXT, PlayerID TEXT, PlayerName TEXT, Champion TEXT,
                TeamIdx INTEGER, WonMatch INTEGER, Level INTEGER, Kills INTEGER, Deaths INTEGER, Assists INTEGER,
                KDA REAL, Credits INTEGER, CPM INTEGER, DamageDealt INTEGER, DamageTaken INTEGER, Shielding INTEGER,
                Healing INTEGER, FOREIGN KEY (MatchID) REFERENCES Partidas (MatchID)
            )
        ''')
        DB_CONN.commit()
    except Exception as e:
        logging.error(f"❌ Error DB: {e}")

def close_sqlite():
    if DB_CONN: DB_CONN.close()

def save_to_db(match_id, map_name, match_date, players):
    if not DB_CURSOR: return
    try:
        DB_CURSOR.execute("INSERT OR IGNORE INTO Partidas VALUES (?, ?, ?)", (match_id, map_name, str(match_date)))
        for p in players:
            if p.get('ParseError'): continue
            DB_CURSOR.execute('''INSERT INTO EstadisticasJugadorPartida 
                (MatchID, PlayerID, PlayerName, Champion, TeamIdx, WonMatch, Level, Kills, Deaths, Assists, KDA, Credits, CPM, DamageDealt, DamageTaken, Shielding, Healing)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (p['MatchID'], p['PlayerID'], p['PlayerName'], p['Champion'], p['TeamIdx'], 
                 1 if p['WonMatch'] else 0, p['Level'], p['Kills'], p['Deaths'], p['Assists'], 
                 p['KDA'], p['Credits'], p['CPM'], p['DamageDealt'], p['DamageTaken'], p['Shielding'], p['Healing']))
        DB_CONN.commit()
    except Exception: pass

def is_match_saved(match_id):
    if not DB_CURSOR: return False
    res = DB_CURSOR.execute("SELECT 1 FROM Partidas WHERE MatchID = ?", (match_id,)).fetchone()
    return res is not None

# --- 4. CONEXIÓN SEGURA Y RÁPIDA (CURL_CFFI OPTIMIZADO) ---
def safe_get_request(url):
    delay = REQUEST_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            # Usamos Chrome 110 (más ligero/estable) y timeout de 10s
            response = requests.get(
                url, 
                headers=HEADERS, 
                impersonate="chrome110", 
                timeout=10
            )
            
            if response.status_code == 200: 
                return response
            elif response.status_code == 404: 
                return None
            elif response.status_code in [403, 429, 503]:
                wait = delay * (attempt + 1)
                logging.warning(f"⏳ Esperando {wait}s (Servidor ocupado)...")
                time.sleep(wait)
            else:
                logging.error(f"Error HTTP: {response.status_code}")
                
        except Exception as e:
            # Si falla por timeout, reintentamos rápido
            pass
            
    return None

# --- 5. PARSING ---
def parse_stat_val(text):
    if not text: return 0
    clean = text.strip().replace(",", "").replace(".", "")
    return int(clean) if clean.isdigit() else 0

def extract_id_from_url(href):
    if not href: return "Unknown"
    match = re.search(r'/profile/(\d+)-', href)
    return match.group(1) if match else "Unknown"

def process_single_match(match_url):
    match_id = match_url.split('/')[-1] or match_url.split('/')[-2]
    
    if not CACHE_OPTS.get("reanalizar_todo_forzado") and is_match_saved(match_id):
        return []

    logging.info(f"🔎 Analizando: {Fore.CYAN}{match_id}{Style.RESET_ALL}")
    response = safe_get_request(match_url)
    if not response: return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    map_name = "Desconocido"
    try:
        map_el = soup.select_one("div.match-header__map-name, span.match-title__map")
        if map_el and ANALYSIS_OPTS.get("extraer_mapa"): 
            map_name = map_el.text.strip()
    except Exception: pass

    match_date = datetime.now().isoformat()
    
    players_data = []
    tables = soup.select("div.match-table")
    
    for table in tables:
        if not table.select("div.row.match-table__row"): continue
        is_winner = "win" in table.get("class", [])
        team_idx = 1 if is_winner else 0
        
        for row in table.select("div.row.match-table__row"):
            try:
                name_el = row.select_one("a.row__player__name")
                img_el = row.select_one("img.row__player__img")
                if not name_el: continue
                
                p_name = name_el.text.strip()
                p_id = extract_id_from_url(name_el.get('href'))
                p_champ = img_el.get('alt', 'Unknown') if img_el else 'Unknown'
                
                stats_items = row.find_all('div', class_='row__item', recursive=False)
                if len(stats_items) < 5: continue
                
                lvl = parse_stat_val(stats_items[0].text)
                kda_raw = stats_items[1].text.strip().split('/')
                k, d, a = (int(x) for x in kda_raw) if len(kda_raw) == 3 else (0,0,0)
                dmg = parse_stat_val(stats_items[4].text)
                
                player_dict = {
                    'MatchID': match_id, 'PlayerID': p_id, 'PlayerName': p_name,
                    'Champion': p_champ, 'TeamIdx': team_idx, 'WonMatch': is_winner,
                    'Level': lvl, 'Kills': k, 'Deaths': d, 'Assists': a,
                    'KDA': round((k+a)/max(d,1), 2), 'DamageDealt': dmg,
                    'Credits': 0, 'CPM': 0, 'DamageTaken': 0, 'Shielding': 0, 'Healing': 0,
                    'MapName': map_name,
                    'ParseError': False
                }
                players_data.append(player_dict)
            except Exception: pass
            
    save_to_db(match_id, map_name, match_date, players_data)
    time.sleep(random.uniform(0.1, 0.5)) # Pausa más corta
    return players_data

def get_full_history(player_id, player_name):
    base_url = f"{MATCH_BASE_URL}/profile/{player_id}-{player_name}/matches"
    found_urls = set()
    page = 1
    logging.info(f"{Fore.MAGENTA}🕵️‍♂️ Rastreando historial para: {player_name}{Style.RESET_ALL}")
    
    while page <= MAX_PAGES:
        url = f"{base_url}?page={page}"
        print(f"   📄 Conectando página {page}...", end='\r') # Feedback visual instantáneo
        
        resp = safe_get_request(url)
        if not resp: 
            print("❌ Error de conexión en historial.")
            break
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        links = soup.select("a[href^='/match/']")
        new_in_page = 0
        for link in links:
            href = link.get('href')
            if href and "/match/" in href and "/profile/" not in href:
                full_link = MATCH_BASE_URL + href
                if full_link not in found_urls:
                    found_urls.add(full_link)
                    new_in_page += 1
        
        print(f"   ✅ Página {page}: {new_in_page} partidas encontradas.")
        
        if new_in_page == 0 and LIMITS_CFG.get("detenerse_si_no_hay_nuevas_partidas", True): break
        pagination = soup.select_one("ul.pagination")
        if not pagination or "disabled" in str(pagination.select("li")[-1]):
            logging.info("🏁 Fin del historial.")
            break
        page += 1
        
    return list(found_urls)

# --- 6. LÓGICA DE REPORTE AVANZADA ---
def calculate_statistical_relevance(teammate_stats):
    stats = teammate_stats.copy()
    stats['BaseScore'] = stats['WinRate']
    stats['Confidence'] = stats['TotalGames'].apply(lambda x: min(1.0, x / 10))
    stats['RelevanceScore'] = (
        stats['BaseScore'] * stats['Confidence'] * 0.7 + 
        stats['TotalGames'] * 2
    ).round(1)
    return stats.sort_values('RelevanceScore', ascending=False)

def generate_full_detailed_report(player_name, all_df):
    if all_df.empty: return
    player_df = all_df[all_df['PlayerName'].str.lower() == player_name.lower()]
    if player_df.empty:
        print(f"{Fore.RED}⚠️ No encontré datos exactos de '{player_name}'.{Style.RESET_ALL}")
        return

    # 1. ANÁLISIS DE RELACIONES
    relations_data = []
    analyzed_matches = player_df['MatchID'].unique()
    
    for mid in analyzed_matches:
        match_data = all_df[all_df['MatchID'] == mid]
        my_row = match_data[match_data['PlayerID'] == player_df[player_df['MatchID']==mid].iloc[0]['PlayerID']]
        if my_row.empty: continue
        
        my_team = my_row.iloc[0]['TeamIdx']
        won = my_row.iloc[0]['WonMatch']
        teammates = match_data[(match_data['TeamIdx'] == my_team) & (match_data['PlayerID'] != my_row.iloc[0]['PlayerID'])]
        
        for _, tm in teammates.iterrows():
            relations_data.append({'TeammateID': tm['PlayerID'], 'TeammateName': tm['PlayerName'], 'Won': won})

    if relations_data:
        rel_df = pd.DataFrame(relations_data)
        tm_stats = rel_df.groupby(['TeammateID', 'TeammateName']).agg({'Won': ['count', 'sum']})
        tm_stats.columns = ['TotalGames', 'Wins']
        tm_stats['Losses'] = tm_stats['TotalGames'] - tm_stats['Wins']
        tm_stats['WinRate'] = (tm_stats['Wins'] / tm_stats['TotalGames'] * 100).round(1)
        ranked_stats = calculate_statistical_relevance(tm_stats)

        print(f"\n{Fore.CYAN}=== RANKING POR RELEVANCIA ESTADÍSTICA (TOP 20) ==={Style.RESET_ALL}")
        print(ranked_stats[['TotalGames', 'Wins', 'Losses', 'WinRate', 'RelevanceScore']].head(20).to_string())
        
        multi_game = ranked_stats[ranked_stats['TotalGames'] > 1].sort_values(['TotalGames', 'WinRate'], ascending=[False, False])
        print(f"\n{Fore.CYAN}=== COMPAÑEROS MÁS FRECUENTES (2+ partidas) PARA {player_name.upper()} ==={Style.RESET_ALL}")
        if not multi_game.empty:
            print(multi_game[['TotalGames', 'Wins', 'Losses', 'WinRate']].head(15).to_string())

    # 2. ESTADÍSTICAS POR CAMPEÓN
    if ANALYSIS_OPTS.get("analizar_por_campeon"):
        champ_stats = player_df.groupby('Champion').agg({
            'WonMatch': ['count', 'sum'], 'Kills': 'mean', 'Deaths': 'mean', 'Assists': 'mean', 'KDA': 'mean', 'DamageDealt': 'mean'
        }).round(2)
        champ_stats.columns = ['TotalGames', 'Wins', 'AvgKills', 'AvgDeaths', 'AvgAssists', 'AvgKDA', 'AvgDamage']
        champ_stats['WinRate'] = (champ_stats['Wins'] / champ_stats['TotalGames'] * 100).round(1)
        champ_stats = champ_stats.sort_values(['TotalGames', 'WinRate'], ascending=[False, False])
        print(f"\n{Fore.MAGENTA}=== ESTADÍSTICAS POR CAMPEÓN PARA {player_name.upper()} ==={Style.RESET_ALL}")
        print(champ_stats.head(15).to_string())

    # 3. ESTADÍSTICAS POR MAPA
    if ANALYSIS_OPTS.get("analizar_por_mapa") and 'MapName' in player_df.columns:
        map_stats = player_df.groupby('MapName').agg({
                'WonMatch': ['count', 'sum'], 'Kills': 'mean', 'Deaths': 'mean', 'KDA': 'mean'
        }).round(2)
        map_stats.columns = ['TotalGames', 'Wins', 'AvgKills', 'AvgDeaths', 'AvgKDA']
        map_stats['WinRate'] = (map_stats['Wins'] / map_stats['TotalGames'] * 100).round(1)
        map_stats = map_stats.sort_values(['TotalGames', 'WinRate'], ascending=[False, False])
        print(f"\n{Fore.YELLOW}=== ESTADÍSTICAS POR MAPA PARA {player_name.upper()} ==={Style.RESET_ALL}")
        print(map_stats.head(15).to_string())

    # 4. RESUMEN GLOBAL FINAL
    total_games = len(player_df)
    total_wins = player_df['WonMatch'].sum()
    wr = (total_wins / total_games * 100) if total_games > 0 else 0
    print(f"\n{Fore.GREEN}{'='*40}\nRESUMEN GLOBAL PARA {player_name.upper()}\n{'='*40}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total de partidas analizadas: {total_games}")
    print(f"Victorias: {total_wins} | Derrotas: {total_games - total_wins}")
    print(f"Winrate: {wr:.1f}%{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Promedios: K/D/A: {player_df['Kills'].mean():.1f}/{player_df['Deaths'].mean():.1f}/{player_df['Assists'].mean():.1f} | KDA: {player_df['KDA'].mean():.2f} | Daño: {player_df['DamageDealt'].mean():,.0f}{Style.RESET_ALL}\n")

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    csv_name = f"reporte_{player_name}_{ts}.csv"
    if OUTPUT_OPTS.get("crear_csv_detallado"):
        all_df.to_csv(csv_name, index=False)
        print(f"📊 Reporte CSV guardado: {csv_name}")

# --- 7. MAIN ---
def main():
    print(f"{Fore.CYAN}🚀 Iniciando OptiSebas Analyzer...{Style.RESET_ALL}")
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, required=False)
    args = parser.parse_args()
    
    target_url = args.url
    if not target_url:
        if VIP_CFG.get("usar_automaticamente") and VIP_CFG.get("url_o_id"):
            target_url = VIP_CFG.get("url_o_id")
            logging.info(f"{Fore.MAGENTA}✨ Modo Automático VIP activado para: {target_url}{Style.RESET_ALL}")
        else:
            logging.error(f"{Fore.RED}❌ Falta URL o Config VIP.{Style.RESET_ALL}")
            return

    try:
        match = re.search(r'/profile/(\d+)-([^/]+)', target_url)
        p_id, p_name = match.groups()
        p_name = p_name.replace('%20', ' ')
    except: return

    init_sqlite()
    match_links = get_full_history(p_id, p_name)
    
    if match_links:
        all_players_data = []
        logging.info(f"{Fore.GREEN}⚡ Comenzando análisis de {len(match_links)} partidas...{Style.RESET_ALL}")
        for i, link in enumerate(match_links):
            match_data = process_single_match(link)
            all_players_data.extend(match_data)
            
        if all_players_data:
            df = pd.DataFrame(all_players_data)
            generate_full_detailed_report(p_name, df)
            
    close_sqlite()
    print(f"{Fore.GREEN}✅ ¡Trabajo terminado!{Style.RESET_ALL}")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: sys.exit(0)
