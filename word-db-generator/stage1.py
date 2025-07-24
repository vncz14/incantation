import sqlite3
import argparse
import csv
import json

# parts of speech that are valid for our purposes
VALID_POS = set(
    [
        "adj",
        "adv",
        "conj",
        "noun",
        "det",
        "pron",
        "num",
        "verb",
        "particle",
        "prep",
        "conj",
    ]
)


def does_table_exist(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    return cursor.fetchone() is not None


def create_ngram_table(conn, frequency_file):
    cursor = conn.cursor()

    if does_table_exist(conn, "frequency"):
        print("frequency table already")
        return

    print("creating frequency table")

    cursor.execute("""
        CREATE TABLE frequency (
            word TEXT PRIMARY KEY,
            frequency INTEGER NOT NULL
        )
    """)
    data = []
    count = 0
    with open(frequency_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) < 2:
                continue
            word, freq = row[0], row[1]
            try:
                freq = int(freq)
                data.append((word, freq))
                count += 1
                if count % 100000 == 0:
                    print(f"processed {count} lines of csv")
                    if count % 1000000 == 0:
                        print("executing sql statements")
                        cursor.executemany(
                            "INSERT INTO frequency (word, frequency) VALUES (?, ?)",
                            data,
                        )
                    data = []
            except ValueError:
                continue
    conn.commit()


def create_wiktionary_table(conn, wiktionary_file):
    cursor = conn.cursor()

    if does_table_exist(conn, "wiktionary"):
        print("wiktionary table already exists")
        return

    print("creating wiktionary table")

    cursor.execute("""
        CREATE TABLE wiktionary (
            word TEXT PRIMARY KEY,
            definition TEXT NOT NULL,
            is_real_word BOOLEAN NOT NULL DEFAULT 1,
            comments TEXT NULL
        )
    """)

    with open(wiktionary_file, "r", encoding="utf-8") as f:
        data = []
        count = 0
        for line in f:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            word = entry.get("word")

            # completely skip over entries with spaces in it because it will not align with the ngram data
            if " " in word:
                continue

            comments = ""

            if not word or not word.islower() or not word.isalpha():
                comments += "not lowercase letters only;"

            # check that the word is a valid part of speech
            if entry.get("pos") not in VALID_POS:
                comments += "invalid pos;"

    conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frequency", type=str, required=True)
    parser.add_argument("--wiktionary", type=str, required=True)
    args = parser.parse_args()

    # make sure frequency and wiktionary are csv and jsonl files respectively
    if not args.frequency.endswith(".csv"):
        raise ValueError("frequency file must be a csv file")
    if not args.wiktionary.endswith(".jsonl"):
        raise ValueError("wiktionary file must be a jsonl file")

    # create database file
    conn = sqlite3.connect("stage1.sqlite3")

    # create ngram table if it doesn't exist
    create_ngram_table(conn, args.frequency)

    # create wiktionary table if it doesn't exist
    create_wiktionary_table(conn, args.wiktionary)


if __name__ == "__main__":
    main()
