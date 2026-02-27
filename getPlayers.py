import requests
from lxml import etree
from io import StringIO
from datetime import datetime
from collections import defaultdict
import time
import csv
import re

# Gender: Male, Female, All
gender = "All"
state = "MA"
file_name = f"pdga_history_{state}.csv"

def get_join_year(pdganum, retries=3, delay=1):
    url = f"https://www.pdga.com/player/{pdganum}"

    for attempt in range(retries):
        try:
            r = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )

            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")

            parser = etree.HTMLParser()
            tree = etree.parse(StringIO(r.text), parser)
            root = tree.getroot()
            joined_nodes = root.xpath(
                '//li[contains(., "Member Since")]'
            )

            if joined_nodes:
                text = joined_nodes[0].xpath("string(.)").strip()
                match = re.search(r"\b(19|20)\d{2}\b", text)
                if match:
                    return int(match.group())

            return None

        except Exception as e:
            print(f"Join year attempt {attempt+1} failed for {pdganum}: {e}")
            time.sleep(delay)

    return None

def categorize_year(year):
    if year is None:
        return "Unknown"
    if year < 1990:
        return "Pre 1990s"
    if 1990 <= year < 2000:
        return "1990-2000"
    if 2000 <= year < 2005:
        return "2000-2005"
    if 2005 <= year < 2010:
        return "2005-2010"
    if 2010 <= year < 2015:
        return "2010-2015"
    if 2015 <= year < 2020:
        return "2015-2020"
    if 2020 <= year <= 2025:
        return "2020-2025"
    return "Other"

def getPlayerHistory(pdganum, target_year, retries=3, delay=1.1):
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
def getPlayerList(year, state, div, pages=2):
    playerList = []

    base_url = (
        "https://www.pdga.com/players/stats?"
        f"Year={year}"
        f"&player_Class=1"
        f"&Gender={div}"
        f"&Bracket=All"
        f"&continent=All"
        f"&Country=All"
        f"&StateProv={state}"
        f"&order=player_Rating"
        f"&sort=desc"
    )

    for page in range(pages):
        if page == 0:
            url = base_url
        else:
            url = f"{base_url}&page={page}"

        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        html = r.content.decode("utf-8")

        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(html), parser)
        root = tree.getroot()

        rows = root.xpath('//*[@id="block-system-main"]//table/tbody/tr')

        if not rows:
            break

        for row in rows:
            name = row.xpath('./td[1]/a/text()')
            number = row.xpath('./td[2]/text()')

            if name and number:
                playerList.append((number[0].strip(), name[0].strip()))

        time.sleep(1.1)

    return list(dict.fromkeys(playerList))


def genDataset():
    start_year = 1998
    dataset = {} # {year: {month: {player: rating}}}
    while start_year <= 2025:
        playerList = getPlayerList(start_year, state, gender)
        for player in playerList:
            name = player[1]
            pdganum = player[0]
            time.sleep(1.1) 
            join_year = get_join_year(pdganum)
            join_category = categorize_year(join_year)
            time.sleep(1.1) 
            history = getPlayerHistory(pdganum, start_year)
            time.sleep(1.1) 
            for item in history:
                date_text, rating = item
                dt = datetime.strptime(date_text, "%d-%b-%Y")
                year = dt.year
                month = dt.month
                if year not in dataset:
                    dataset[year] = {}

                if month not in dataset[year]:
                    dataset[year][month] = {}

                dataset[year][month][name] = {
                    "rating": rating,
                    "category": join_category
                }
        print(f"Processed year {start_year} with {len(playerList)} players")     
        start_year += 1
    
    return dataset


def flatten_dataset(dataset):
    rows = []
    player_categories = {}

    for year in sorted(dataset):
        for month in sorted(dataset[year]):
            for name, data in dataset[year][month].items():
                date_string = f"{year}-{month:02d}-01"
                rows.append([date_string, name, data["rating"]])
                player_categories[name] = data["category"]

    return rows, player_categories



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


def pivot_with_category(rows, player_categories, output_file):
    from collections import defaultdict

    dates = sorted(set(r[0] for r in rows))
    players = sorted(set(r[1] for r in rows))

    lookup = defaultdict(dict)
    for date, name, rating in rows:
        lookup[name][date] = rating

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["Year Joined", "Name"] + dates)

        for player in players:
            category = player_categories.get(player, "Unknown")
            row = [category, player]

            for date in dates:
                row.append(lookup[player].get(date, ""))

            writer.writerow(row)
    print("saved dataset")

dataset = genDataset()
rows, player_categories = flatten_dataset(dataset)
filled = forward_fill(rows)

pivot_with_category(filled, player_categories, file_name)