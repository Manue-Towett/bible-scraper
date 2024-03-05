# bible-scraper
Scrapes biblical scriptures from https://www.biblegateway.com/

# Settings
Use settings.ini file in settings directory to configure the version to be scraped. Take a look at the mappings.json for the version and version id values.

# Usage
Requires python 3.10+  
Open the terminal  
change terminal's directory into the project directory  
If running for the first time, install dependencies using the command:  

```pip install -r requirements.txt```

Run the script using the command:

## For linux/mac:
- ### For the scraper:  
- Without Html:
    
    - single book:
        - python3 main.py -b <book> e.g `python3 main.py -b genesis`

- With Html:

    - include the argument "--html"

        - eg `python3 main.py -b genesis --html`

- ### For Merger bot:  
- python3 merger.py -csv <csv_path> -html <html_path> 
    - e.g. `python3 merger.py -csv ./data/csv/ -html ./data/html/`

- Default paths used if not provided are ./data/csv/ and ./data/html/. As such, if files to be merged are in these folders, you can just use the command:

    - `python3 merger.py`

## For windows:  
- ### For the scraper:  
- Without Html:  
    - python main.py -b <chapter> e.g `python main.py -b genesis`  

- With Html:  
    - include the argument "--html"  
        - eg `python main.py -b genesis --html`


- ### For Merger bot:  
- python merger.py -csv <csv_path> -html <html_path> 
    - e.g. `python merger.py -csv ./data/csv/ -html ./data/html/`

- Default paths used if not provided are ./data/csv/ and ./data/html/. As such, if files to be merged are in these folders, you can just use the command:

    - `python merger.py`