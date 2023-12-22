# bible-scraper
Scrapes biblical scriptures from https://www.biblegateway.com/

# Usage
Requires python 3.10+

Open the terminal

change terminal's directory into the project directory

If running for the first time, install dependencies using the command:

```pip install -r requirements.txt```

Run the script using the command:

For linux/mac:

    Without Html:

        python3 main.py <chapter> e.g python3 main.py genesis
    
    With Html:

        - include the argument "--html"

        eg python3 main.py genesis --html

For windows:

    Without Html:

        python main.py <chapter> e.g python main.py genesis
    
    With Html:

        - include the argument "--html"

        eg python main.py genesis --html