import os
import argparse
import threading
import dataclasses
from queue import Queue
from typing import Optional, Tuple

import pandas as pd
from bs4 import BeautifulSoup

QUEUE = Queue()

MERGED_OUTPUT_PATH = "./data/merged/"

BASE_TEMPLATE = '[parsehtml]\n<div id="{}_{}">{}</div>\n[/parsehtml]'

SELECT_TEMPLATE = '''
<select class="div-toggle" data-target=".versionselect">{}\n</select>'''

VERSE_CONTAINER_TEMPLATE = '\n<div class="versionselect"> {}</div>\n'

OPTION_BASE = '\n\t<option value="{}" data-show=".{}">{}</option>'

VERSION_CONTENT_BASE = '\n<div class="{} hide">\n{}\n</div>'

COLUMN_MAPPINGS = {
    "Version": "version",
    "ID": "version_id",
    "Book": "book",
    "Chapter": "chapter",
    "Chapter Title": "chapter_title",
    "Content": "content"
}

PARSER = argparse.ArgumentParser(description="Directories for csv and html")

PARSER.add_argument("-csv", "--csv_path", nargs="+", type=str, default="./data/csv/")

PARSER.add_argument("-html", "--html_path", nargs="+", type=str, default="./data/html/")

@dataclasses.dataclass
class BibleVerse:
    version: str
    version_id: str
    book: str
    chapter: str
    chapter_title: Optional[str] = None
    content: Optional[str] = None

def read_csv(file_path: str) -> list[BibleVerse]:
    """Reads a csv and returns a list of BibleVerse objects"""
    df = pd.read_csv(file_path)

    df.rename(columns=COLUMN_MAPPINGS, inplace=True)

    data_list = df.to_dict("records")

    return [BibleVerse(**item) for item in data_list]

def read_html(file_path: str) -> str:
    """Reads html file and returns the html string"""
    with open(file_path, encoding="utf-8") as file:
        return file.read()
    
def create_option(verse: BibleVerse) -> str:
    """Creates an html option from the verse provided"""
    version = verse.version_id.lower().strip()
    
    return OPTION_BASE.format(version, version, verse.version)

def create_version_content(verse: BibleVerse, html: str) -> str:
    """Creates version content from the verse and html from file"""
    return VERSION_CONTENT_BASE.format(verse.version_id.lower(), html)

def create_content(verse: BibleVerse, options: str, versions_content: str) -> str:
    """Creates content from the bible verse given"""
    select_content = SELECT_TEMPLATE.format(options)
    main_content = VERSE_CONTAINER_TEMPLATE.format(versions_content)

    return create_base_template(verse, select_content + main_content)

def create_base_template(verse: BibleVerse, content: str) -> str:
    """Creates the base template from the given verse"""
    return BASE_TEMPLATE.format(verse.book.lower(), verse.chapter, content)

def groupby_chapter(verses: list[BibleVerse]) -> dict[int, list[BibleVerse]]:
    """Groups bible verses by chapter"""
    grouped_verses: dict[int, list] = {}

    for verse in verses:
        if not grouped_verses.get(verse.chapter): grouped_verses[verse.chapter] = []
        
        grouped_verses[verse.chapter].append(verse)
    
    return grouped_verses

def groupby_book(verses: list[list[BibleVerse]]) -> dict[str, list[BibleVerse]]:
    grouped_verses: dict[str, list] = {}

    added = set()

    for bible_verses in verses:
        for verse in bible_verses:
            verse_id = f"{verse.version_id} {verse.book} {verse.chapter}"

            if verse_id in added: continue

            if not grouped_verses.get(verse.book): grouped_verses[verse.book] = []

            grouped_verses[verse.book].append(verse)

            added.add(verse_id)
    
    return grouped_verses

def process_grouped_verses(chapter_verses: list[BibleVerse], html_path: str) -> Tuple[str, str]:
    options, content = '', ''

    for verse in chapter_verses:
        options += f"{create_option(verse=verse)}"

        html = read_html(f"{html_path}{verse.content}")

        version_content = create_version_content(verse=verse, html=html)

        content += f"{version_content}"

    return options, content

def work(html_path: str) -> None:
    while True:
        chapter_verses: list[BibleVerse] = QUEUE.get()

        options, content = process_grouped_verses(chapter_verses, html_path)

        merged_content = create_content(chapter_verses[0], options, content)

        save_merged(merged_content, chapter_verses[0].book, chapter_verses[0].chapter)

        del merged_content, options, content

        QUEUE.task_done()

def save_merged(html: str, book: str, chapter: int) -> None:
    """Saves merged content to an html file"""
    filename = f"{'{:05d}'.format(chapter)}{book.lower()}{chapter}.html"

    pretty_html = BeautifulSoup(html, "html.parser").prettify()

    with open(f'{MERGED_OUTPUT_PATH}{filename}', "w", encoding="utf-8") as f:
        f.write(pretty_html)
    
    print(f"Merged content saved to: {filename}")
    
def run(csv_path: str, html_path: str) -> None:
    """Entry point to the script"""
    if not os.path.exists(MERGED_OUTPUT_PATH): os.makedirs(MERGED_OUTPUT_PATH)

    verses: list[list[BibleVerse]] = [
        read_csv(f"{csv_path}{f}") for f in os.listdir(csv_path)]
    
    grouped_verses: dict[str, dict] = groupby_book(verses=verses)

    for book, g_verses in grouped_verses.items():
        grouped_verses[book] = groupby_chapter(verses=g_verses)
    
    [threading.Thread(target=work, args=(html_path,), daemon=True).start() for _ in range(5)]
    
    [QUEUE.put(cvs) for _, bvs in grouped_verses.items() for _, cvs in bvs.items()]

    QUEUE.join()

if __name__ == "__main__":
    args = PARSER.parse_args()

    run(' '.join(args.csv_path), ' '.join(args.html_path))