import requests
from lxml import etree
from io import StringIO
from datetime import datetime
from collections import defaultdict
import time
import csv

# Gender: Male, Female, All
gender = "All"
state = "CT"

def getPlayerHistory(pdganum, target_year, retries=3, delay=1):
    url = f"https://www.pdga.com/player/{pdganum}/history"
    for attempt in range(retries):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")
            parser = etree.HTMLParser()
            tree = etree.parse(StringIO(r.text), parser)
            root = tree.getroot()
            rows = root.xpath('//*[@id="player-results-history"]/tbody/tr')
            history = []

            for row in rows:
                date_text = row.xpath('./td[1]/text()')
                rating_text = row.xpath('./td[2]/text()')

                if not date_text or not rating_text:
                    continue

                date_text = date_text[0].strip()
                rating = int(rating_text[0].strip())
                dt = datetime.strptime(date_text, "%d-%b-%Y")
                year = dt.year

                if year < target_year:
                    break

                if year == target_year:
                    history.append((date_text, rating))

            return history
        except Exception as e:
            print(f"Attempt {attempt+1} failed for player {pdganum}: {e}")
            time.sleep(delay)
    return []

#TODO add ability for more players (more pages)
def getPlayerList(year, state, div):
    playerList = []
    
    r = requests.get("https://www.pdga.com/players/stats?Year=" + str(year) + "&player_Class=1&Gender=" + div + "&Bracket=All&continent=All&Country=All&StateProv=" + state + "&order=player_Rating&sort=desc")
    html = r.content.decode("utf-8")
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(html), parser)
    root = tree.getroot()
    rows = root.xpath('//*[@id="block-system-main"]//table/tbody/tr')

    for row in rows:
        name = row.xpath('./td[1]/a/text()')
        number = row.xpath('./td[2]/text()')

        if name and number:
            playerList.append((number[0].strip(), name[0].strip()))

    return list(dict.fromkeys(playerList))


def genDataset():
    start_year = 2001
    dataset = {} # {year: {month: {player: rating}}}
    while start_year <= 2025:
        playerList = getPlayerList(start_year, state, gender)
        for player in playerList:
            name = player[1]
            pdganum = player[0]
            history = getPlayerHistory(pdganum, start_year)
            time.sleep(1.5) 
            for item in history:
                date_text, rating = item
                dt = datetime.strptime(date_text, "%d-%b-%Y")
                year = dt.year
                month = dt.month
                if year not in dataset:
                    dataset[year] = {}

                if month not in dataset[year]:
                    dataset[year][month] = {}

                dataset[year][month][name] = rating
        print(f"Processed year {start_year} with {len(playerList)} players")     
        start_year += 1
    
    return dataset


def flatten_dataset(dataset):
    rows = []
    for year in sorted(dataset):
        for month in sorted(dataset[year]):
            for name, rating in dataset[year][month].items():
                date_string = f"{year}-{month:02d}-01"
                rows.append([date_string, name, rating])
    return rows



def forward_fill(rows):
    dates = sorted(set(row[0] for row in rows))
    players = sorted(set(row[1] for row in rows))
    date_lookup = defaultdict(dict)
    for date, name, rating in rows:
        date_lookup[date][name] = rating
    last_rating = {}
    filled_rows = []
    for date in dates:
        for player in players:
            if player in date_lookup[date]:
                last_rating[player] = date_lookup[date][player]
            if player in last_rating:
                filled_rows.append([date, player, last_rating[player]])
    return filled_rows


def save_to_csv(rows, filename="pdga_ratings.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "name", "value"])
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {filename}")

save_to_csv(forward_fill(flatten_dataset(genDataset())))