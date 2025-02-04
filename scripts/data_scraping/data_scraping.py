from dotenv import load_dotenv
import os
import pandas as pd
import requests
import time
import asyncio
import aiohttp

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
    
def fetch_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"{response.status_code}: {response.reason}")
    return response.json()

async def fetch_data_async(url, session):
    async with session.get(url) as response:
        if response.status != 200:
            raise Exception(f"{response.status}: {response.reason}")
        return await response.json()
    
async def scrape_data(regionTag, count, id):
    #Start chrono
    print("Starting Riot data scratching...")
    current_time= time.time()
    full_start_time = current_time

    #Get API key
    load_dotenv()
    riot_key = os.getenv("RIOT_API_KEY")

    #Get basic urls
    regions = {
        "na1":"americas",
        "kr":"asia",
        "euw1":"europe"
    }
    route_url = f"https://{regions[regionTag]}.api.riotgames.com"
    tag_url = f"https://{regionTag}.api.riotgames.com"
    
    i=0
    while i<count:
        #Get match id
        match_id = regionTag.upper()+"_"+str(id-i)
        print(f"{count-i} remaining matches: {match_id}")
        
        #Start chrono
        start_time = time.time()
        
        #Get match data
        try:
            matchUrl = f"{route_url}/lol/match/v5/matches/{match_id}?api_key={riot_key}"
            raw_match = fetch_data(matchUrl)
        except Exception as e:
            if '429' in str(e):
                print("Rate limit exceeded. Waiting 10 seconds...")
                print("---------------------")
                time.sleep(10)
                continue
            elif '404' in str(e):
                print("Match not found. Skipping...")
                print("---------------------")
                i+=1
                count+=1
                continue
            else:
                print("Error: ", e)
                print("---------------------")
                i+=1
                count+=1
                continue

        #Get mastery and ranked data asynchronously for each participant
        try:
            async with aiohttp.ClientSession() as session:
                match = []
                tasks = []
                for participant in raw_match["info"]["participants"]:
                    masteryUrl = f"{tag_url}/lol/champion-mastery/v4/champion-masteries/by-puuid/{participant['puuid']}/by-champion/{participant['championId']}?api_key={riot_key}"
                    rankedUrl = f"{tag_url}/lol/league/v4/entries/by-summoner/{participant['summonerId']}?api_key={riot_key}"
                    tasks.append(fetch_data_async(masteryUrl, session))
                    tasks.append(fetch_data_async(rankedUrl, session))
                
                responses = await asyncio.gather(*tasks)
        except Exception as e:
            if '429' in str(e):
                print("Rate limit exceeded. Waiting 10 seconds...")
                print("---------------------")
                time.sleep(10)
                continue
            else:
                print("Error: ", e)
                print("---------------------")
                i+=1
                count+=1
                continue
            
        for participant_idx, participant in enumerate(raw_match["info"]["participants"]):
            masteryData = responses[participant_idx * 2]
            ranks = responses[participant_idx * 2 + 1]
            
            if 'status' in masteryData:
                masteryData = {"championLevel": 0}
            else:
                masteryData = {"championLevel": masteryData["championLevel"]}
            
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
        save_match(match_id, match, win)
        end_time = time.time()
        print(f"Done in {end_time - start_time} seconds")
        print("---------------------")
        i+=1

    full_end_time = time.time()
    print(f"Done in {full_end_time - full_start_time} seconds")