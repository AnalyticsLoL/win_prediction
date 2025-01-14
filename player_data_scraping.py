from dotenv import load_dotenv
import os
import pandas as pd
import requests
import time

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

getPuuidUrl = f"{route_url}/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={riot_key}"
puuid = requests.get(getPuuidUrl).json()["puuid"]

getMatchIdsUrl = f"{route_url}/lol/match/v5/matches/by-puuid/{puuid}/ids?api_key={riot_key}"
matchIds = requests.get(getMatchIdsUrl).json()

matches = pd.DataFrame(columns=["MatchId", "Player1", "Player2", "Player3", "Player4", "Player5", "Player6", "Player7", "Player8", "Player9", "Player10", "Win"])
try:
    for id in matchIds:
        print(id)
        start_time = time.time()
        getMatchUrl = f"{route_url}/lol/match/v5/matches/{id}?api_key={riot_key}"
        raw_match = requests.get(getMatchUrl).json()
        
        match = []
        for participant in raw_match["info"]["participants"]:
            getMasteryUrl = f"{tag_url}/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/by-champion/{participant['championId']}?api_key={riot_key}"
            masteryData = requests.get(getMasteryUrl).json()
            if 'status' in masteryData:
                masteryData = {"championLevel": 0}
            else:
                masteryData = {"championLevel": masteryData["championLevel"]}
            getRankUrl = f"{tag_url}/lol/league/v4/entries/by-summoner/{participant['summonerId']}?api_key={riot_key}"
            ranks = requests.get(getRankUrl).json()
            found_ranked = False
            for rank in ranks:
                if rank == "":
                    break
                if rank.get("queueType") == "RANKED_SOLO_5x5":
                    match.append([participant["championId"], participant["teamPosition"], rank["tier"], rank["rank"], masteryData["championLevel"]])
                    found_ranked = True
                    break
            if not found_ranked:
                match.append([participant["championId"], participant["teamPosition"], "UNRANKED", "UNRANKED", masteryData["championLevel"]])
        win = int(not participant["win"])
        matches.loc[len(matches)] = [id] + match + [win]
        end_time = time.time()
        print(f"Done in {end_time - start_time} seconds")
        print("---------------------")
except:
    pass

full_end_time = time.time()
print(f"Done in {full_end_time - full_start_time} seconds")
print("---------------------")
print("Saving data in csv...")
matches.to_csv("matches.csv", index=False)