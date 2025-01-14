from dotenv import load_dotenv
import os
import pandas as pd
import requests
import time

def get_puuid(base_url, gameName, tagLine, riot_key):
    """
    Retrieves the PUUID for a given player using their game name and tag line.

    Args:
        base_url (str): The base URL for the Riot Games API.
        gameName (str): The game name of the player.
        tagLine (str): The tag line of the player.
        riot_key (str): The API key for accessing the Riot Games API.

    Returns:
        str: The PUUID of the player.
    """
    getPuuidUrl = f"{base_url}/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={riot_key}"
    puuid = requests.get(getPuuidUrl).json()["puuid"]
    return puuid

def get_matchIds(base_url, puuid, count, riot_key):
    """
    Fetches the match IDs for a given player using their PUUID.

    Args:
        base_url (str): The base URL for the Riot Games API.
        puuid (str): The PUUID of the player.
        count (int): The number of match IDs to retrieve, limited to 100 by Riot.
        riot_key (str): The API key for authenticating with the Riot Games API.

    Returns:
        list: A list of match IDs for the specified player.
    """
    getMatchIdsUrl = f"{base_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?count={count}&api_key={riot_key}"
    matchIds = requests.get(getMatchIdsUrl).json()
    return matchIds

def get_matchData(base_url, matchId, riot_key):
    """
    Fetches match data from the Riot Games API.

    Args:
        base_url (str): The base URL for the Riot Games API.
        matchId (str): The ID of the match to retrieve data for.
        riot_key (str): The API key for authenticating with the Riot Games API.

    Returns:
        dict: A dictionary containing the raw match data retrieved from the API.
    """
    getMatchUrl = f"{base_url}/lol/match/v5/matches/{matchId}?api_key={riot_key}"
    raw_match = requests.get(getMatchUrl).json()
    return raw_match

def get_masteryData(base_url, puuid, championId, riot_key):
    """
    Retrieves the mastery data for a given player using their PUUID and champion ID.

    Args:
        base_url (str): The base URL for the Riot Games API.
        puuid (str): The PUUID of the player.
        championId (int): The ID of the champion.
        riot_key (str): The API key for accessing the Riot Games API.

    Returns:
        dict: The mastery data for the specified player and champion.
    """
    getMasteryUrl = f"{base_url}/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/by-champion/{championId}?api_key={riot_key}"
    masteryData = requests.get(getMasteryUrl).json()
    return masteryData

def get_rankData(base_url, summonerId, riot_key):
    """
    Retrieves the rank data for a given player using their PUUID.

    Args:
        base_url (str): The base URL for the Riot Games API.
        summonerId (str): The summonerId of the player.
        riot_key (str): The API key for accessing the Riot Games API.

    Returns:
        list: The list of ranked data for the specified player.
    """
    getRankUrl = f"{base_url}/lol/league/v4/entries/by-summoner/{summonerId}?api_key={riot_key}"
    rankData = requests.get(getRankUrl).json()
    return rankData

def save_match(matchId, match, win):
    """
    Saves match data to a CSV file named 'matches.csv'. If the file does not exist, it creates one with the appropriate columns.

    Args:
        matchId (int): The unique identifier for the match.
        match (list): A list of player identifiers for the match.
        win (bool): A boolean indicating whether the match was won.

    Returns:
        None
    """
    if os.path.exists("matches.csv"):
        matches = pd.read_csv("matches.csv")
    else:
        matches = pd.DataFrame(columns=["MatchId", "Player1", "Player2", "Player3", "Player4", "Player5", "Player6", "Player7", "Player8", "Player9", "Player10", "Win"])
    if matchId in matches["MatchId"].values:
        return
    matches.loc[len(matches)] = [matchId] + match + [win]
    matches.to_csv("matches.csv", index=False)
    
    
if '__main__' == __name__:
    load_dotenv()

    print("Starting Riot data scratching...")
    current_time= time.time()
    full_start_time = current_time

    riot_key = os.getenv("RIOT_API_KEY")

    regionRoutes = ["americas", "asia", "europe", "esports"]

    gameName = "popcornsucré"
    tagLine = "pavif"
    regionTag = "euw1"
    regionRoute = regionRoutes[2]

    route_url = f"https://{regionRoute}.api.riotgames.com"
    tag_url = f"https://{regionTag}.api.riotgames.com"

    puuid = get_puuid(route_url, gameName, tagLine, riot_key)

    matchIds = get_matchIds(route_url, puuid, 100, riot_key)

    try:
        for id in matchIds:
            print(id)
            start_time = time.time()
            raw_match = get_matchData(route_url, id, riot_key)
            
            match = []
            for participant in raw_match["info"]["participants"]:
                masteryData = get_masteryData(tag_url, puuid, participant["championId"], riot_key)
                if 'status' in masteryData:
                    masteryData = {"championLevel": 0}
                else:
                    masteryData = {"championLevel": masteryData["championLevel"]}
                ranks = get_rankData(tag_url, participant["summonerId"], riot_key)
                found_ranked = False
                for rank in ranks:
                    if type(rank) == str:
                        break
                    if rank.get("queueType") == "RANKED_SOLO_5x5":
                        match.append(["champion_"+str(participant["championId"]), participant["teamPosition"], "tier_"+str(rank["tier"]), "rank_"+str(rank["rank"]), "mastery_"+str(masteryData["championLevel"])])
                        found_ranked = True
                        break
                if not found_ranked:
                    match.append(["champion_"+str(participant["championId"]), participant["teamPosition"], "UNRANKED", "UNRANKED", "mastery_"+str(masteryData["championLevel"])])
            win = int(not participant["win"])
            save_match(id, match, win)
            end_time = time.time()
            print(f"Done in {end_time - start_time} seconds")
            print("---------------------")
    except Exception as e:
        print(f"An error occurred: {e}")
        pass

    full_end_time = time.time()
    print(f"Done in {full_end_time - full_start_time} seconds")