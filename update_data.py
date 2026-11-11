import json
import requests
from datetime import datetime, timedelta
import os

# Mapeamento oficial com os IDs corretos extraídos da base de dados
TEAM_MAP = {
    "ANA": {"id": 12, "name": "Anaheim"},
    "BOS": {"id": 30, "name": "Boston"},
    "BUF": {"id": 21, "name": "Buffalo"},
    "CGY": {"id": 9, "name": "Calgary"},
    "CAR": {"id": 29, "name": "Carolina"},
    "CHI": {"id": 20, "name": "Chicago"},
    "COL": {"id": 7, "name": "Colorado"},
    "CBJ": {"id": 26, "name": "Columbus"},
    "DAL": {"id": 22, "name": "Dallas"},
    "DET": {"id": 19, "name": "Detroit"},
    "EDM": {"id": 5, "name": "Edmonton"},
    "FLA": {"id": 18, "name": "Florida"},
    "LAK": {"id": 10, "name": "Los Angeles"},
    "MIN": {"id": 32, "name": "Minnesota"},
    "MTL": {"id": 25, "name": "Montreal"},
    "NSH": {"id": 11, "name": "Nashville"},
    "NJD": {"id": 31, "name": "New Jersey"},
    "NYI": {"id": 28, "name": "Long Island"},
    "NYR": {"id": 16, "name": "New York"},
    "OTT": {"id": 13, "name": "Ottawa"},
    "PHI": {"id": 24, "name": "Philadelphia"},
    "PIT": {"id": 23, "name": "Pittsburgh"},
    "SJS": {"id": 4, "name": "San Jose"},
    "SEA": {"id": 8, "name": "Seattle"},
    "STL": {"id": 2, "name": "St. Louis"},
    "TBL": {"id": 15, "name": "Tampa"},
    "TOR": {"id": 14, "name": "Toronto"},
    "UTA": {"id": 1, "name": "Utah"},
    "VAN": {"id": 6, "name": "Vancouver"},
    "VGK": {"id": 17, "name": "Las Vegas"},
    "WSH": {"id": 27, "name": "Washington"},
    "WPG": {"id": 3, "name": "Winnipeg"}
}

def get_yesterday_date():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def fetch_nhl_scores(date_str):
    url = f"https://api-web.nhle.com/v1/score/{date_str}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao obter dados da API da NHL para {date_str}: {e}")
        return None

def parse_games_from_nhl(data):
    new_games = []
    if not data or "games" not in data:
        return new_games
    
    for game in data["games"]:
        gameState = game.get("gameState", "")
        if gameState not in ["FINAL", "OFF"]:
            continue
        
        game_date = game.get("gameDate", "")
        if len(game_date) >= 10:
            game_date = game_date[:10]
            
        home_team_abbr = game.get("homeTeam", {}).get("abbrev", "")
        away_team_abbr = game.get("awayTeam", {}).get("abbrev", "")
        
        # Obter dados seguros do dicionário central com os IDs reais
        home_info = TEAM_MAP.get(home_team_abbr, {"id": 0, "name": home_team_abbr})
        away_info = TEAM_MAP.get(away_team_abbr, {"id": 0, "name": away_team_abbr})
        
        home_goals = game.get("homeTeam", {}).get("score", 0)
        away_goals = game.get("awayTeam", {}).get("score", 0)
        
        period_descriptor = game.get("periodDescriptor", {})
        period_type = period_descriptor.get("periodType", "REG")
        is_ot = period_type in ["OT", "SO"]
        
        game_obj = {
            "date": game_date,
            "league": "Estados Unidos e Canadá",
            "leagueId": 1,
            "homeTeamName": home_info["name"],
            "homeTeamId": home_info["id"],
            "homeTeamAbbr": "",
            "awayTeamName": away_info["name"],
            "awayTeamId": away_info["id"],
            "awayTeamAbbr": "",
            "homeGoals": home_goals,
            "awayGoals": away_goals,
            "isOT": is_ot
        }
        new_games.append(game_obj)
    return new_games

def main():
    json_path = "games_USA_&_Canada.json"
    yesterday_str = get_yesterday_date()
    print(f"A obter resultados da NHL para a data: {yesterday_str}")
    
    data = fetch_nhl_scores(yesterday_str)
    new_games = parse_games_from_nhl(data)
    
    if not new_games:
        print("Nenhum jogo novo encontrado para adicionar.")
        return
        
    print(f"Encontrados {len(new_games)} novos jogos para adicionar.")
    
    content = {}
    existing_games = []
    
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            if isinstance(content, dict) and "games" in content:
                existing_games = content["games"]
            elif isinstance(content, list):
                existing_games = content
        except Exception as e:
            print(f"Aviso: Erro ao ler {json_path}, a iniciar lista vazia: {e}")
            
    existing_keys = {(g.get("date"), g.get("homeTeamName"), g.get("awayTeamName")) for g in existing_games}
    
    games_to_add = []
    for g in new_games:
        key = (g.get("date"), g.get("homeTeamName"), g.get("awayTeamName"))
        if key not in existing_keys:
            games_to_add.append(g)
            existing_keys.add(key)
            
    if not games_to_add:
        print("Todos os jogos obtidos já existem no ficheiro.")
        return
        
    updated_games = games_to_add + existing_games
    updated_games = updated_games[:1312]
    
    if isinstance(content, dict):
        content["games"] = updated_games
        output_data = content
    else:
        output_data = {"games": updated_games}
        
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
        
    print(f"Sucesso! {len(games_to_add)} novos jogos adicionados com os IDs corretos. Total: {len(updated_games)}")

if __name__ == "__main__":
    main()