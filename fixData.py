import csv
from datetime import datetime
from collections import defaultdict
from dateutil.relativedelta import relativedelta

def apply_decay_to_pivot(input_file, output_file):
    with open(input_file, newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    header = reader[0] 
    date_columns = header[2:]

    output_rows = [header]

    for row in reader[1:]:
        category = row[0]
        name = row[1]
        ratings = row[2:]

        last_base = None
        unchanged_count = 0
        new_ratings = []

        for value in ratings:
            if value == "":
                new_ratings.append("")
                continue

            base_rating = int(value)

            if last_base is None:
                unchanged_count = 0
            else:
                if base_rating == last_base:
                    unchanged_count += 1
                else:
                    unchanged_count = 0

            decay_steps = max(0, unchanged_count - 2)
            decayed_rating = base_rating - (3 * decay_steps)

            new_ratings.append(decayed_rating)
            last_base = base_rating

        output_rows.append([category, name] + new_ratings)

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(output_rows)

    print("Saved decayed dataset.")


apply_decay_to_pivot(
    "pdga_history_MA.csv",
    "pdga_history_MA_decayed.csv"
)