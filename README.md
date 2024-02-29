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

For linux/mac:

    Without Html:
        
        single book:
            python3 main.py -b <book> e.g python3 main.py -b genesis
    
    With Html:

        - include the argument "--html"

        eg python3 main.py -b genesis --html

For windows:

    Without Html:

        python main.py -b <chapter> e.g python main.py -b genesis
    
    With Html:

        - include the argument "--html"

        eg python main.py -b genesis --html