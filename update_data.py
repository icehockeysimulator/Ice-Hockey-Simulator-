import json
import requests
from datetime import datetime, timedelta
import os

# Mapeamento ajustado exatamente aos nomes das equipas utilizados no JSON da aplicação do utilizador
TEAM_NAME_MAP = {
    "ANA": "Anaheim",
    "BOS": "Boston",
    "BUF": "Buffalo",
    "CGY": "Calgary",
    "CAR": "Carolina",
    "CHI": "Chicago",
    "COL": "Colorado",
    "CBJ": "Columbus",
    "DAL": "Dallas",
    "DET": "Detroit",
    "EDM": "Edmonton",
    "FLA": "Florida",
    "LAK": "Los Angeles",
    "MIN": "Minnesota",
    "MTL": "Montreal",
    "NSH": "Nashville",
    "NJD": "New Jersey",
    "NYI": "Long Island",
    "NYR": "New York",
    "OTT": "Ottawa",
    "PHI": "Philadelphia",
    "PIT": "Pittsburgh",
    "SJS": "San Jose",
    "SEA": "Seattle",
    "STL": "St. Louis",
    "TBL": "Tampa",
    "TOR": "Toronto",
    "UTA": "Utah",
    "VAN": "Vancouver",
    "VGK": "Las Vegas",
    "WSH": "Washington",
    "WPG": "Winnipeg"
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

        home_team_name = TEAM_NAME_MAP.get(home_team_abbr, home_team_abbr)
        away_team_name = TEAM_NAME_MAP.get(away_team_abbr, away_team_abbr)

        home_goals = game.get("homeTeam", {}).get("score", 0)
        away_goals = game.get("awayTeam", {}).get("score", 0)

        period_type = game.get("periodType", "REG")
        is_ot = period_type in ["OT", "SO"]

        game_obj = {
            "date": game_date,
            "league": "Estados Unidos e Canadá",
            "leagueId": 1,
            "homeTeamName": home_team_name,
            "homeTeamId": 0,
            "homeTeamAbbr": home_team_abbr,
            "awayTeamName": away_team_name,
            "awayTeamId": 0,
            "awayTeamAbbr": away_team_abbr,
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
        print("Todos os jogos obtidos já existem no games_USA_&_Canada.json.")
        return

    updated_games = games_to_add + existing_games
    updated_games = updated_games[:1312]

    output_data = {"games": updated_games}

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(f"Sucesso! {len(games_to_add)} novos jogos adicionados. Total de jogos em {json_path}: {len(updated_games)}")

if __name__ == "__main__":
    main()
