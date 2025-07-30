import argparse
import csv
import json
import re
import sqlite3


def load_lines_from_file_as_set(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return set([line.strip() for line in f if line.strip()])


PREFIXES = load_lines_from_file_as_set("lists/prefixes.txt")
SUFFIXES = load_lines_from_file_as_set("lists/suffixes.txt")

IRREGULAR_PLURALS = load_lines_from_file_as_set("lists/irregular_plurals.txt")
IRREGULAR_VERBS = load_lines_from_file_as_set("lists/irregular_verbs.txt")
IRREGULAR_COMPARATIVES_AND_SUPERLATIVES = load_lines_from_file_as_set(
    "lists/irregular_comparatives_and_superlatives.txt"
)

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

UNLESS_IRREGULAR_INVALID_TAGS = set(
    [
        "form-of",
        "plural",
    ]
)

OTHER_INVALID_TAGS = set(
    [
        "slang",
        "dialectical",
        "vulgar",
        "obsolete",
        "alt-of",
        "abbreviation",
        "humorous",
        "nonstandard",
        "informal",
        "Internet",
        "archaic",
    ]
)

INVALID_CATEGORIES = set(["Furry fandom", "Paraphilias"])


def does_table_exist(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    return cursor.fetchone() is not None


def create_ngram_table(conn, frequency_file):
    if does_table_exist(conn, "frequency"):
        print("frequency table already exists")
        return

    print("creating frequency table")

    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE frequency (
            word TEXT PRIMARY KEY,
            frequency INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_frequency_word ON frequency(word);
        CREATE INDEX IF NOT EXISTS idx_frequency_frequency ON frequency(frequency);
    """)
    data = []
    count = 0
    with open(frequency_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) < 2:
                continue
            word, freq = row[0], row[1]
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
        if data:
            print("executing sql statements")
            cursor.executemany(
                "INSERT INTO frequency (word, frequency) VALUES (?, ?)",
                data,
            )
    conn.commit()


def create_wiktionary_table(conn, wiktionary_file):
    cursor = conn.cursor()

    if does_table_exist(conn, "wiktionary"):
        print("wiktionary table already exists")
        return

    print("creating wiktionary table")

    cursor.executescript("""
        CREATE TABLE wiktionary (
            word TEXT NOT NULL,
            definition TEXT NULL,
            audio_file_name TEXT NULL,
            is_real_word BOOLEAN NOT NULL DEFAULT 1,
            comments TEXT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_wiktionary_word_isreal ON wiktionary(word, is_real_word);
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

            is_real_word = True
            definition = None
            audio_file_name = None
            comments = ""

            # word is all lowercase ASCII letters
            if not (word and word.islower() and word.isalpha() and word.isascii()):
                comments += "not lowercase letters only;"

            # word is a valid part of speech
            if entry.get("pos") not in VALID_POS:
                comments += "invalid pos;"

            # word is a trivial prefix or suffix (based on etymology information)
            """
            - note to self: command to get common prefixes or suffixes
                - grep "prefixed with" kaikki.org-dictionary-English.jsonl | jq | grep "prefixed with" | sort | uniq -c | sort -nr | head -100
            """
            etymology_text = entry.get("etymology_text")

            if etymology_text:
                # remove non-ascii characters
                etymology_text = re.sub(r"[^\x00-\x7F]+", "", etymology_text)

                # determine if the etymology text is simply "From [prefix]- + [base]."
                prefix_match = re.match(
                    r"From ([a-z]+\-)\s\+\s([a-z]+)\.", etymology_text
                )
                if prefix_match:
                    prefix, base = prefix_match.groups()
                    if prefix in PREFIXES:
                        comments += f"trivial prefix {prefix};"

                # determine if the etymology text is simply "From [base] + -[suffix]."
                suffix_match = re.match(
                    r"From ([a-z]+)\s\+\s(\-[a-z]+)\.", etymology_text
                )
                if suffix_match:
                    base, suffix = suffix_match.groups()
                    if suffix in SUFFIXES:
                        comments += f"trivial suffix {suffix};"

            # if no comments so far, look for an acceptable sense
            valid_sense = None
            first_sense_comments = ""
            if not comments:
                senses = entry.get("senses", [])
                for i, sense in enumerate(senses):
                    # sense cannot be tagged "form-of" or have a "form-of" field
                    # UNLESS it is
                    # - an irregular plural
                    # - an irregular verb form
                    # - an irregular comparative/superlative
                    # TODO: if a sense is acceptable, get the definition of its root instead

                    tags = set(sense.get("tags", []))

                    form_of_word = None
                    form_of = sense.get("form_of")
                    if form_of:
                        if isinstance(form_of, list) and len(form_of) >= 1:
                            form_of_word = form_of[0].get("word")

                    if form_of_word or "form-of" in tags:
                        exception = False

                        # look for irregular plurals
                        if "plural" in tags:
                            if word in IRREGULAR_PLURALS:
                                exception = True
                            else:
                                if i == 0:
                                    first_sense_comments += "form-of (plural);"
                                continue

                        # look for irregular verbs
                        if "verb" in tags:
                            if form_of_word in IRREGULAR_VERBS:
                                exception = True
                            else:
                                if i == 0:
                                    first_sense_comments += "form-of (verb);"
                                continue

                        # look for irregular comparatives and superlatives
                        if "comparative" in tags or "superlative" in tags:
                            if form_of_word in IRREGULAR_COMPARATIVES_AND_SUPERLATIVES:
                                exception = True
                            else:
                                if i == 0:
                                    first_sense_comments += (
                                        "form-of (comparative/superlative);"
                                    )
                                continue

                        if not exception:
                            if i == 0:
                                first_sense_comments += "form-of (other);"
                            continue

                    """
                    other invalid tags - no exceptions
                    """

                    other_invalid_tags_in_sense = tags.intersection(OTHER_INVALID_TAGS)
                    if other_invalid_tags_in_sense:
                        if i == 0:
                            first_sense_comments += (
                                f"invalid tags {','.join(other_invalid_tags_in_sense)};"
                            )
                        continue

                    """
                    invalid categories - no exceptions
                    """

                    categories = set(
                        category.get("name")
                        for category in sense.get("categories", [])
                        if category.get("name") is not None
                    )

                    invalid_categories_in_sense = categories.intersection(
                        INVALID_CATEGORIES
                    )

                    if invalid_categories_in_sense:
                        if i == 0:
                            first_sense_comments += f"invalid categories {','.join(invalid_categories_in_sense)};"
                        continue

                    # sense is valid
                    valid_sense = sense
                    break

            if valid_sense:
                # gather other fields of the sense
                definition = " ".join(valid_sense.get("glosses", []))

                audio_file_name = None

                sounds = entry.get("sounds", [])
                if sounds:
                    # see if there is an audio file name
                    # it would be an object in the sounds list with an "audio" field with a value that ends in ".ogg"
                    for sound in sounds:
                        if isinstance(sound, dict) and "audio" in sound:
                            if sound["audio"].endswith(".ogg"):
                                audio_file_name = sound["audio"]
                                break

            else:
                # add comments from the first checked sense to the data
                is_real_word = False
                comments += first_sense_comments

            data.append(
                (
                    word,
                    definition,
                    audio_file_name,
                    is_real_word,
                    comments if comments else None,
                )
            )

            if count % 10000 == 0:
                print(f"processed {count} lines")
                if count % 100000 == 0:
                    print("executing sql statements")
                    cursor.executemany(
                        "INSERT INTO wiktionary (word, definition, audio_file_name, is_real_word, comments) VALUES (?, ?, ?, ?, ?)",
                        data,
                    )
                    data = []

            count += 1

        if data:
            print("executing sql statements")
            cursor.executemany(
                "INSERT INTO wiktionary (word, definition, audio_file_name, is_real_word, comments) VALUES (?, ?, ?, ?, ?)",
                data,
            )

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

    # # drop wiktionary table
    if does_table_exist(conn, "wiktionary"):
        print("dropping existing wiktionary table")
        conn.execute("DROP TABLE wiktionary")

    # create wiktionary table if it doesn't exist
    create_wiktionary_table(conn, args.wiktionary)


if __name__ == "__main__":
    main()
