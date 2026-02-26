import csv
from datetime import datetime
from collections import defaultdict
from dateutil.relativedelta import relativedelta

def load_csv(filename):
    data = defaultdict(dict)
    players = set()
    dates = set()

    with open(filename, newline='', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            date_str, name, rating = row
            #rating = int(rating)

            data[date_str][name] = rating
            players.add(name)
            dates.add(date_str)

    return data, sorted(players), sorted(dates)

def generate_full_dates(dates):
    start = datetime.strptime(min(dates), "%Y-%m-%d")
    end = datetime.strptime(max(dates), "%Y-%m-%d")

    full_dates = []
    current = start
    while current <= end:
        full_dates.append(current.strftime("%Y-%m-%d"))
        current += relativedelta(months=1)

    return full_dates

def forward_fill(data, players, full_dates):
    last_rating = {}
    filled = defaultdict(dict)

    for date in full_dates:
        for player in players:
            if player in data[date]:
                last_rating[player] = data[date][player]

            if player in last_rating:
                filled[date][player] = last_rating[player]

    return filled

def apply_decay(filled, players, full_dates):
    final = defaultdict(dict)
    last_base_rating = {}  
    unchanged_count = defaultdict(int)

    for date in full_dates:
        for player in players:
            if player not in filled[date]:
                continue

            base_rating = int(filled[date][player])

            if player in last_base_rating:
                if base_rating == last_base_rating[player]:
                    unchanged_count[player] += 1
                else:
                    unchanged_count[player] = 0
            else:
                unchanged_count[player] = 0
            # decay ratings by 3 points every month after 3 months of no change
            decay_steps = max(0, unchanged_count[player] - 2)
            decayed_rating = base_rating - (3 * decay_steps)
            final[date][player] = decayed_rating
            last_base_rating[player] = base_rating

    return final


def save_clean_csv(final, filename="pdga_ratings_decay.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for date in sorted(final):
            for player, rating in final[date].items():
                writer.writerow([date, player, rating])

def pivot_for_flourish(final, players, full_dates, output_file):
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Name"] + full_dates)

        for player in sorted(players):
            row = [player]

            for date in full_dates:
                if date in final and player in final[date]:
                    row.append(final[date][player])
                else:
                    row.append("")  

            writer.writerow(row)


data, players, dates = load_csv("pdga_ratings.csv")
full_dates = generate_full_dates(dates)
filled = forward_fill(data, players, full_dates)
final = apply_decay(filled, players, full_dates)
#save_clean_csv(final)

pivot_for_flourish(final, players, full_dates, "pdga_flourish_ready.csv")