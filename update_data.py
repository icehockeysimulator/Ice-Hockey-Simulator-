import json
import requests
from datetime import datetime, timedelta
import os

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

def obter_data_ontem():
    ontem = datetime.now() - timedelta(days=1)
    return ontem.strftime("%Y-%m-%d")

def obter_resultados_nhl(data_str):
    url = f"https://api-web.nhle.com/v1/score/{data_str}"
    try:
        resposta = requests.get(url, timeout=15)
        resposta.raise_for_status()
        return resposta.json()
    except Exception as e:
        print(f"Erro ao obter dados da API da NHL para {data_str}: {e}")
        return None

def processar_jogos_nhl(dados):
    novos_jogos = []
    if not dados or "games" not in dados:
        return novos_jogos
    
    for jogo in dados["games"]:
        estado_jogo = jogo.get("gameState", "")
        if estado_jogo not in ["FINAL", "OFF"]:
            continue
        
        data_jogo = jogo.get("gameDate", "")
        if len(data_jogo) >= 10:
            data_jogo = data_jogo[:10]
            
        abrev_casa = jogo.get("homeTeam", {}).get("abbrev", "")
        abrev_fora = jogo.get("awayTeam", {}).get("abbrev", "")
        
        info_casa = TEAM_MAP.get(abrev_casa, {"id": 0, "name": abrev_casa})
        info_fora = TEAM_MAP.get(abrev_fora, {"id": 0, "name": abrev_fora})
        
        golos_casa = jogo.get("homeTeam", {}).get("score", 0)
        golos_fora = jogo.get("awayTeam", {}).get("score", 0)
        
        descr_periodo = jogo.get("periodDescriptor", {})
        tipo_periodo = descr_periodo.get("periodType", "REG")
        foi_prolongamento = tipo_periodo in ["OT", "SO"]
        
        jogo_obj = {
            "date": data_jogo,
            "league": "Estados Unidos e Canadá",
            "leagueId": 1,
            "homeTeamName": info_casa["name"],
            "homeTeamId": info_casa["id"],
            "homeTeamAbbr": "",
            "awayTeamName": info_fora["name"],
            "awayTeamId": info_fora["id"],
            "awayTeamAbbr": "",
            "homeGoals": golos_casa,
            "awayGoals": golos_fora,
            "isOT": foi_prolongamento
        }
        novos_jogos.append(jogo_obj)
    return novos_jogos

def main():
    caminho_json = "games_USA_&_Canada.json"
    data_ontem = obter_data_ontem()
    print(f"A obter resultados da NHL para a data: {data_ontem}")
    
    dados = obter_resultados_nhl(data_ontem)
    novos_jogos = processar_jogos_nhl(dados)
    
    if not novos_jogos:
        print("Nenhum jogo novo encontrado para adicionar.")
        return
        
    print(f"Encontrados {len(novos_jogos)} novos jogos para adicionar.")
    
    conteudo = {}
    jogos_existentes = []
    
    if os.path.exists(caminho_json):
        try:
            with open(caminho_json, "r", encoding="utf-8") as f:
                conteudo = json.load(f)
            if isinstance(conteudo, dict) and "games" in conteudo:
                jogos_existentes = conteudo["games"]
            elif isinstance(conteudo, list):
                jogos_existentes = conteudo
        except Exception as e:
            print(f"Aviso: Erro ao ler {caminho_json}, a iniciar lista vazia: {e}")
            
    chaves_existentes = {(g.get("date"), g.get("homeTeamName"), g.get("awayTeamName")) for g in jogos_existentes}
    
    jogos_a_adicionar = []
    for g in novos_jogos:
        chave = (g.get("date"), g.get("homeTeamName"), g.get("awayTeamName"))
        if chave not in chaves_existentes:
            jogos_a_adicionar.append(g)
            chaves_existentes.add(chave)
            
    if not jogos_a_adicionar:
        print("Todos os jogos obtidos já existem no ficheiro.")
        return
        
    jogos_atualizados = jogos_a_adicionar + jogos_existentes
    jogos_atualizados = jogos_atualizados[:1312]
    
    if isinstance(conteudo, dict):
        conteudo["games"] = jogos_atualizados
        dados_saida = conteudo
    else:
        dados_saida = {"games": jogos_atualizados}
        
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(dados_saida, f, ensure_ascii=False, indent=4)
        
    print(f"Sucesso! {len(jogos_a_adicionar)} novos jogos adicionados com os IDs corretos. Total: {len(jogos_atualizados)}")

if __name__ == "__main__":
    main()