import eventlet

eventlet.monkey_patch(thread=True, socket=True)

import os
import re
import argparse
import threading
import dataclasses
import configparser
from queue import Queue
from datetime import date
from typing import Optional, Tuple

import requests
import pandas as pd
from bs4 import BeautifulSoup, ResultSet
from requests.adapters import HTTPAdapter, Retry

from utils import Logger, VERSIONS, BOOKS

config = configparser.ConfigParser()

with open("./settings/settings.ini", "r") as file:
    config.read_file(file)

VERSION = config.get("version to scrape", "version_id")

THREAD_NUM = 20

OUTPUT_PATH = "./data/"

PARSER = argparse.ArgumentParser(description="Html scraping decision")

COLUMN_MAPPINGS = {
    "version": "Version",
    "version_id": "ID",
    "book": "Book",
    "chapter": "Chapter",
    "chapter_title": "Chapter Title",
    "content": "Content"
}

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

URL = "https://www.biblegateway.com/passage"

@dataclasses.dataclass
class BibleVerse:
    version: str
    version_id: str
    book: str
    chapter: str
    chapter_title: Optional[str] = None
    content: Optional[str] = None

class BibleGatewayScraper:
    """Scrapes biblical scriptures from https://www.biblegateway.com/"""
    def __init__(self, include_html: Optional[bool]=True) -> None:
        self.logger = Logger(__class__.__name__)
        self.logger.info("{:*^50}".format(f"{__class__.__name__} Started"))

        self.queue = Queue()
        self.save_queue = Queue()
        self.session = requests.Session()
        
        self.verses = []
        self.verses_found = 0
        self.headers_added = False
        self.include_html = include_html
        self.__file_name = f"{date.today()}.csv"
    
    def __process_request(self, s: requests.Session, params: dict[str, str]) -> Optional[BeautifulSoup]:
        """Make a request to the website and return BeautifulSoup object of the response"""
        
        with eventlet.Timeout(5):
            response = s.get(URL, headers=HEADERS, params=params, timeout=3)

            if response.ok:
                return BeautifulSoup(response.text, "html.parser")
    
    @staticmethod
    def __get_book(book: str) -> Optional[Tuple[str, int]]:
        """Gets the search term corresponding to a given biblical book"""
        for book_dict in BOOKS["books"]["AMP"]:
            if re.search(book, book_dict["display"], re.I):
                return book_dict["display"], book_dict["num_chapters"]
    
    @staticmethod
    def __get_verse_text(span_tags: ResultSet[BeautifulSoup], verse: str) -> str:
        for span_tag in span_tags:
            cross_reference = span_tag.select_one("sup.crossreference")

            if cross_reference is not None:
                cross_reference.decompose()
            
            verse_num = ""

            verse_num_tag = span_tag.select_one("sup.versenum")

            if verse_num_tag is not None:
                verse_num = verse_num_tag.get_text(strip=True) + " "

                verse_num_tag.decompose()
            
            verse += verse_num + span_tag.get_text().strip().replace("\n", "") + " "

            while "  " in verse: verse = verse.replace("  ", " ")
        
        return verse

    def __extract_data(self, soup: BeautifulSoup, verse: BibleVerse, abbr: str) -> None:
        """Extracts the chapter title, content, and html"""
        passage_tag = soup.select_one("div.passage-text")

        if passage_tag is None: return

        header_tag = passage_tag.select_one("h3")

        chapter_title = header_tag.get_text(strip=True) if header_tag else None

        if chapter_title is not None:
            chapter_title = chapter_title.encode("ascii", errors="ignore").decode()

        verse.chapter_title = chapter_title

        if self.include_html:
            content = passage_tag.select_one("div.text-html")
        else:
            chapter_tag = passage_tag.select_one("span.chapternum")

            if chapter_tag: chapter_tag.decompose()

            content = ""

            for paragraph in passage_tag.select("p"):
                span_tags = paragraph.select("span.text")

                content = self.__get_verse_text(span_tags, content)
        
        verse.content = content.encode("ascii", errors="ignore").decode()

    def __create_work(self, chapters: int) -> None:
        """Creates work to be done by threads"""
        items = None

        for key, value in VERSIONS.items():
            if re.search(rf"{VERSION}", value, re.I):
                items = [(key, value)]

        if items is None:
            self.logger.error("Couldn't find the version specified in settings!", True)

        [self.queue.put((v, v_id, n + 1)) for n in range(chapters) for v, v_id in items]

        self.queue.join() 

    @staticmethod
    def __get_session() -> requests.Session:
        """Returns a session object"""  
        s = requests.Session()

        retries = Retry(total=1, backoff_factor=0.1)

        s.mount('http://', HTTPAdapter(max_retries=retries))

        s.mount('https://', HTTPAdapter(max_retries=retries))

        return s         
    
    def __work(self, book: str, bible_verses: list ) -> None:
        """Work to be done by the threads"""
        s = self.__get_session()

        while True:
            version, version_id, chapter = self.queue.get()

            params = {"search": f"{book} {chapter}", "version": version_id}

            if version_id in version:
                version = version.split(f"({version_id})")[0].strip()
            
            version = version.encode("ascii", errors="ignore").decode()

            version_id = version_id.encode("ascii", errors="ignore").decode()

            response = None

            while response is None:
                try:
                    response = self.__process_request(s, params)

                except eventlet.timeout.Timeout: pass

                except: s = self.__get_session()

            verse = BibleVerse(version=version, version_id=version_id, book=book, chapter=chapter)

            self.__extract_data(response, verse, version_id)

            if verse.content is not None: 
                self.verses.append(verse)

                self.verses_found += 1

                if len(self.verses) % 100 == 0: 
                    verses = self.verses[:]

                    self.save_queue.put(verses)

                    [self.verses.remove(i) for i in verses]

                    del verses

                    self.save_queue.join()
            
            bible_verses.append("")

            self.queue.task_done()

            queue, crawled = self.queue.unfinished_tasks, len(bible_verses)
            
            self.logger.info(f"Queue: {queue} || Crawled: {crawled} || Verses Found: {self.verses_found}")

    def __save(self, book: str) -> None:
        """Saves data retrieved to a csv file"""
        __file_name = f"{book}_{self.__file_name}"

        while True:
            bible_verses: list[BibleVerse] = self.save_queue.get()

            self.logger.info("Saving data retrieved...")

            results = [dataclasses.asdict(verse) for verse in bible_verses]

            df = pd.DataFrame(results)

            df.rename(columns=COLUMN_MAPPINGS, inplace=True)

            df.sort_values(by=["Chapter"], inplace=True)

            version_id = df.iloc[0]["ID"]

            file_name = "{}{}_{}".format(OUTPUT_PATH, version_id, __file_name)

            if not self.headers_added:
                df.to_csv(file_name, index=False, chunksize=20)

                self.headers_added = True

            else:
                df.to_csv(file_name, index=False, header=False, mode="a", chunksize=20)

            self.logger.info(f"{len(df)} records saved to {self.__file_name}")

            self.save_queue.task_done()

            del df

            del results

    def scrape(self, book: str) -> None:
        """Entry point to the scraper"""
        if not os.path.exists(OUTPUT_PATH): os.makedirs(OUTPUT_PATH)

        bible_verses = []

        search_args = self.__get_book(book)

        search_term, num_chapters = search_args if search_args is not None else (None, None)
        
        if search_term is None:
            self.logger.error(f"Failed to find chapter named <{book}>", True)

        search_term = book if search_term is None else search_term

        [threading.Thread(target=self.__work, 
                          args=(search_term, bible_verses,), 
                          daemon=True).start() for _ in range(THREAD_NUM)]
        
        threading.Thread(target=self.__save, args=(book,), daemon=True).start()

        self.__create_work(num_chapters)

        if len(self.verses):
            self.save_queue.put(self.verses)

            self.save_queue.join()

        self.logger.info(f"Scraper done scraping all the {book} chapters.")

PARSER.add_argument("chapter", type=str, nargs="+")

PARSER.add_argument("--html", dest="html", const="yes", default="no", action="store_const")

if __name__ == "__main__":
    args = PARSER.parse_args()
    html_decision = True if args.html == "yes" else False

    app = BibleGatewayScraper(html_decision)
    app.scrape(" ".join(args.chapter))