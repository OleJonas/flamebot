import discord
import os
from riotwatcher import LolWatcher, ApiError
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime
import schedule
import time
import json
import atexit


load_dotenv()

disc_token = os.getenv('TOKEN')
riot_token = os.getenv("RIOT_TOKEN")
watcher = LolWatcher(riot_token)
region = "europe"

latest = watcher.data_dragon.versions_for_region("euw1")['n']['champion']
static_champ_list = watcher.data_dragon.champions(latest, False, 'en_US')
champ_dict = {}
for key in static_champ_list['data']:
    row = static_champ_list['data'][key]
    champ_dict[row['key']] = row['id']

requests = 0

account_dict = {"kenneth": ["buggiz", "johooplater"],
"daniel": ["Ghettο mamacita"],
    "busty": ["bustian"],
    "ole": ["gabeutsecs", "saladspinner01"],
    "willers": ["willers"],
    "gule": ["amarillo", "amarillov2"],
    "benjamin": ["wabe", "djwabe"],
    "christer": ["rekerogmayo", "gtgod"],
    "eric": ["lukterbæsj"],
    "henrik": ["gretalovesu"],
    "kirat": ["nebulask"],
    "borge": ["volt", "hansmajestet", "b0rge"],
    "lars": ["hannagule"],
    "simen": ["crowman"],
    "nyhuus": ["chadout"],
    "braathen": ["braathen"]
    }

"""
"kenneth": ["buggiz", "johooplater"],
"daniel": ["Ghettο mamacita"],
    "busty": ["bustian"],
    "ole": ["gabeutsecs", "saladspinner01"],
    "willers": ["willers"],
    "gule": ["amarillo", "amarillov2"],
    "benjamin": ["wabe", "djwabe"],
    "christer": ["rekerogmayo", "gtgod"],
    "eric": ["lukterbæsj"],
    "henrik": ["gretalovesu"],
    "kirat": ["nebulask"],
    "borge": ["volt", "hansmajestet", "b0rge"],
    "lars": ["hannagule"],
    "simen": ["crowman"],
    "nyhuus": ["chadout"]"""



client = discord.Client()
kda_limit = 0.8

# Some helper functions
"""def get_user_match_history(username):
    user = watcher.summoner.by_name("euw1", username)
    return watcher.match.matchlist_by_puuid(region, user["puuid"], 0, 10)
"""
def create_match_dict(match_details, date):
    match_dict = defaultdict()
    match_dict["date"] = date
    match_dict["summonerName"] = match_details["summonerName"]
    match_dict['champion'] = match_details['championId']
    match_dict['win'] = match_details['win']
    match_dict['kills'] = match_details['kills']
    match_dict['deaths'] = match_details['deaths']
    match_dict['assists'] = match_details['assists']
    match_dict['totalDamageDealtToChampions'] = match_details['totalDamageDealtToChampions']
    match_dict['goldEarned'] = match_details['goldEarned']
    match_dict['champLevel'] = match_details['champLevel']
    match_dict['totalMinionsKilled'] = match_details['totalMinionsKilled']
    return match_dict

def check_int(stats):
    k = int(stats["kills"])
    d = int(stats["deaths"])
    a = int(stats["assists"])
    kda = (k + a) if d == 0 else (k + a) / d

    inter = True
    if kda >= kda_limit:
         if d <= 15:
            role = str(stats["role"]).lower()
            if role == "duo_support" and a-d > 3:
                    inter = False
            elif k >= d-3 or ((k + a*0.6) - d) >= 2:
                    inter = False
    return inter


def make_match_history(matches):
    matches_string = ""
    for m in matches:
        matches_string += str(m["date"])
        matches_string += "\n" + m["summonerName"]
        matches_string += ("\n" + champ_dict[str(m['champion'])])
        matches_string += ("\n" + ("Victory" if m['win'] else "Defeat"))
        matches_string += ("\nKDA: " + str(m['kills']) + "/" + str(m['deaths']) + "/" + str(m['assists']))
        matches_string += ("\n" + "Damage: " + str(m['totalDamageDealtToChampions']))
        matches_string += ("\n" + "Gold: " + str(m['goldEarned']))
        matches_string += ("\n" + "Lvl: " + str(m['champLevel']))
        matches_string += ("\n" + "CS: " + str(m['totalMinionsKilled']))
        matches_string += "\n\n"

    return matches_string
    

# Storing new data on exit
def exit_handler():
    with open("account_dict.txt", "w+") as f:
        json.dump(account_dict, f)
atexit.register(exit_handler)

# Bot commands

async def get_daily_inters(msg):
    batch_sz = 30
    inters = defaultdict()
    date_today = datetime.now()
    for person, accounts in account_dict.items():
        inted_matches = []
        for account in accounts:
            print(f"Checking ints for {person}, {account}...\n")
            try:
                user = watcher.summoner.by_name("euw1", account)

                fetched_matches = 0
                
                history = watcher.match.matchlist_by_puuid(region, user["puuid"], fetched_matches, fetched_matches+batch_sz)
                for match in history:
                    match_details = watcher.match.by_id(region, match)

                    ts = match_details["info"]["gameCreation"] / 1000 # in seconds
                    date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

                    print("date-diff (days): ", (date_today - datetime.fromtimestamp(ts)).days)
                    if (date_today - datetime.fromtimestamp(ts)).days > 1:
                        print(f"done for {account}...\n ")
                        break
                    else: 
                        participants = match_details["metadata"]["participants"]
                        for i, puuid in enumerate(participants):
                            if puuid == user["puuid"]:
                                if check_int(match_details["info"]["participants"][i]):
                                    int_match = create_match_dict(match_details["info"]["participants"][i], date)
                                    inted_matches.append(int_match)
                                    print("int")
            except:
                print(f"User {account} not found...\n")
        if len(inted_matches) > 0:
            inters[person] = inted_matches
            print(inters[person])
    

    matches_string = f"Dette var gårsdagens inters:\n\n"
    for inter, matches in inters.items():
        matches_string += "-----------------------------------------------------------\n"
        matches_string += f"{inter}: \n"
        matches_string += make_match_history(matches)

    with open("inters.txt", "w+") as f:
        f.write(matches_string)
    await msg.channel.send(file=discord.File(r"inters.txt", "intebois.txt"))

    #await msg.channel.send(matches_string)

async def get_matches(msg):
    line = msg.content.split(" ")
    n_matches = int(line[1])
    username = "".join(line[2:])
    user = watcher.summoner.by_name("euw1", username)
    print(f"Received request from {msg.author} to get inted matches for username {username} from last {n_matches} matches")
    history = watcher.match.matchlist_by_puuid(region, user["puuid"], 0, n_matches)

    inted_matches = []
    for i in range(n_matches):
        match_meta = history[i]
        match_details = watcher.match.by_id(region, match_meta)
        participants = match_details["metadata"]["participants"]
        for i, puuid in enumerate(participants):
            if puuid == user["puuid"]:
                ts = match_details["info"]["gameCreation"] / 1000 # in seconds
                date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                int_match = create_match_dict(match_details["info"]["participants"][i], date)
                inted_matches.append(int_match)

    matches_string = f"{username}'s {n_matches} siste games:\n"
    matches_string += make_match_history(inted_matches)

    await msg.channel.send(matches_string)

async def get_inted_matches(msg):
    line = msg.content.split(" ")
    parsed_matches = int(line[1])
    n_matches = parsed_matches if parsed_matches < 20 else 20
    username = "".join(line[2:])
    user = watcher.summoner.by_name("euw1", username)
    print(f"Received request from {msg.author} to get inted matches for username {username} from last {n_matches} matches")
    history = watcher.match.matchlist_by_puuid(region, user["puuid"], 0, n_matches)

    inted_matches = []
    for i in range(n_matches):
        match_meta = history[i]
        match_details = watcher.match.by_id(region, match_meta)
        gamemode = str(match_details["info"]["gameMode"]).lower()
        if gamemode != "aram":
            print(f"gamemode: {gamemode}")
            participants = match_details["metadata"]["participants"]
            for i, puuid in enumerate(participants):
                if puuid == user["puuid"]:
                    if check_int(match_details["info"]["participants"][i]):
                        ts = match_details["info"]["gameCreation"] / 1000 # in seconds
                        date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                        int_match = create_match_dict(match_details["info"]["participants"][i], date)
                        inted_matches.append(int_match)

    matches_string = f"Av sine {n_matches} siste games har {username} inta disse:\n"
    matches_string += make_match_history(inted_matches)

    await msg.channel.send(matches_string)


async def add_account(msg):
    line = msg.content.split(" ")
    person = line[1]
    account = line[2]
    try:
        user = watcher.summoner.by_name("euw1", account)
    except:
        await msg.channel.send(f"Summoner with name {account} not found")
        return
    account_dict[person].append(account)
    await msg.channel.send(f"Summoner with name {account} added to list of accounts for {person}")





async def get_inted_matches_by_person(msg):
    pass


@client.event
async def on_ready():
    print("Flamebot is good to go for user {0.user}".format(client))
    #with open("account_dict.txt", "r") as f:
        #account_dict = json.load(f)
    #print(account_dict.items())

# Request / message handling

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if msg.content.startswith("pisslow_Int"):
        await get_inted_matches(msg)
    
    if msg.content.startswith("pisslow_Daily"):
        await get_daily_inters(msg)

    if msg.content.startswith("pisslow_AddAcc"):
        await add_account(msg)

    if msg.content.startswith("pisslow_IntPerson"):
        await get_inted_matches_by_person(msg)

client.run(disc_token)