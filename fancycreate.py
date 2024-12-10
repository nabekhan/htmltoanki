# Import Packages
from bs4 import BeautifulSoup
import requests
import logging
import genanki
import html2text
import os
import markdown2

logging.basicConfig(level=logging.DEBUG)

# Convert HTML to plain text
text_maker = html2text.HTML2Text()

# Customize settings
text_maker.ignore_links = False  # Include links in Markdown format
text_maker.ignore_images = True  # Exclude images
text_maker.ignore_emphasis = False  # Keep bold/italic formatting
text_maker.bypass_tables = False  # Preserve table formatting

# Alphabet
alphaUpper = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


def processtxt(souphtml):
    # Use html2text or text_maker to convert HTML to Markdown-like text
    souptext = text_maker.handle(str(souphtml))

    # Remove all zero-width spaces
    souptext = souptext.replace('\u200b', '')  # Removes all instances of \u200b

    # Convert the processed Markdown text to HTML
    souptext = markdown2.markdown(souptext)

    # Replace all remaining newline characters with <br>
    souptext = souptext.replace('\n\n', '<br>')

    # Replace all remaining newline characters with <br>
    souptext = souptext.replace('\n', "")

    return souptext

def find_sublist_with_string(list_of_lists, target_string):
    for sublist in list_of_lists:
        if target_string in sublist:
            return sublist
    return ""  # Return None if the string is not found in any sublist

# Import files
with open("src/mcfrontside.html", "r", encoding="utf-8") as f:
    qfmt_content = f.read()

with open("src/mcbackside.html", "r", encoding="utf-8") as f:
    afmt_content = f.read()

with open("src/mccss.html", "r", encoding="utf-8") as f:
    css_content = f.read()


def deckcreate(username, password, deck):
    if "details" in deck:
        deck = deck.replace("details", "printdeck")

    # Define URLs
    login_url = "https://cards.ucalgary.ca/login"
    collection_url = "https://cards.ucalgary.ca/collection"

    # Start a session to handle cookies and persistence
    session = requests.Session()

    # Set headers to mimic browser behavior
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Origin": "https://cards.ucalgary.ca",
        "Referer": "https://cards.ucalgary.ca/login",
        "Upgrade-Insecure-Requests": "1",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Form data for login
    payload = {
        "username": username,
        "password": password,
        "login": "Login",
    }

    # Perform login
    response = session.post(login_url, data=payload, headers=headers, allow_redirects=False)

    # Log response details
    logging.debug(f"Login POST Response Headers:\n{response.headers}")
    logging.debug(f"Login POST Response Status Code: {response.status_code}")
    logging.debug(f"Cookies after login: {session.cookies.get_dict()}")

    # Check for redirection (302 Found)
    if response.status_code == 302:
        # Follow the redirect to the collection page
        collection_response = session.get(collection_url, headers=headers)
        logging.debug(f"Collection Page Response Headers:\n{collection_response.headers}")
        logging.debug(f"Collection Page Response Status Code: {collection_response.status_code}")

        if "Welcome" in collection_response.text or "<title>Cards - Collection</title>" in collection_response.text:
            logging.info("Login successful! Collection page loaded.")
            # Navigate to the target URL
            target_response = session.get(deck, headers=headers, timeout=10)

            # Verify that the target page has loaded successfully
            if target_response.status_code == 200 and "Cards" in target_response.text:
                logging.info("Target deck page loaded successfully.")
                # Process the HTML content with BeautifulSoup
                S = BeautifulSoup(target_response.text, 'html.parser')
            else:
                logging.error("Failed to load the target deck page. Check the URL or network connectivity.")
                raise Exception("Deck page did not load successfully.")
        else:
            logging.error("Login might have failed. Collection page does not have expected content.")
    else:
        logging.error("Login failed or unexpected response.")

    """

    # Open the HTML file
    with open("gitignore/Cards.html", "r", encoding="utf-8") as html_file:
        S = BeautifulSoup(html_file, 'html.parser')
"""

    # Print Name
    details_div = S.find("div", class_="details")
    filename = details_div.find("p").text.strip() + "::" + details_div.find("h1").text.strip()
    print(filename)

    # Select records
    records_div = S.find("div", class_="records")

    # Find all <div> elements with the class "page"
    page_divs = records_div.find_all("div", class_="page", recursive=False)

    # Check if any <div class="page"> elements are found
    if page_divs:
        notes = {}
        print(f"Found {len(page_divs)} 'page' divs.")
        # Iterate and print the content of each
        for i, div in enumerate(page_divs, start=1):
            if i % 2 != 0:
                # Define Question
                print(f"Question {int(i / 2 + 0.5)} Content:")
                front = {}

                # print stats
                stats = div.find_all("div", class_="stats")
                listofstats = []
                for stat in stats:
                    stat = processtxt(stat)
                    print(stat)
                    listofstats.append(stat)
                front["Stats"] = listofstats

                # print pt description
                descriptions = div.find_all("div", class_="block group")
                listofdesc = []
                for description in descriptions:
                    description = processtxt(description)
                    print(description)
                    # description = description.text.strip()
                    listofdesc.append(description)
                front["Desc"] = listofdesc

                # print question
                headers = div.find_all("h3")
                listofheaders = []
                for header in headers:
                    header = processtxt(header)
                    print(header)
                    listofheaders.append(header)
                front["Question"] = listofheaders

                # print options
                options = div.select('div[class*="option"]')
                option_list = [div.text.strip() for div in options][1:]
                listofoptions = []
                for index, option in enumerate(option_list):
                    option = processtxt(option)
                    print(option)
                    listofoptions.append([alphaUpper[index], option])
                front["Options"] = listofoptions

                # find images
                images = div.find_all("img")
                listofimages = []
                for image in images:
                    urlstub = image.get("src")
                    url = "https://cards.ucalgary.ca/" + urlstub[1:]
                    print(url)
                    listofimages.append(url)
                front["Images"] = listofimages
            else:
                back = {}

                # print answers
                print(f"Question {int(i / 2)} Answer:")
                answers = div.find_all("div", class_="correct")
                listofanswers = []
                for answer in answers:
                    answer = processtxt(answer)
                    print(answer)
                    answerletter = find_sublist_with_string(listofoptions, answer)[0]
                    listofanswers.append([answerletter, answer])
                back["Answers"] = listofanswers

                # print feedback
                feedbacks = div.find_all("div", class_="results container")
                listoffeed = []
                for feedback in feedbacks:
                    feedback = processtxt(feedback)
                    print(feedback)
                    listoffeed.append(feedback)
                back["Feedback"] = listoffeed

                # find images
                backimages = div.find_all("img")
                listofbackimages = []
                for image in backimages:
                    bkurlstub = image.get("src")
                    bkurl = "https://cards.ucalgary.ca/" + bkurlstub[1:]
                    print(bkurl)
                    if bkurl in listofimages:
                        continue
                    else:
                        listofbackimages.append(bkurl)
                back["BackImages"] = listofbackimages

                notes[int(i / 2)] = [front, back]
                print("-" * 50)
        print(notes)
    else:
        print("No <div> elements with class 'page' found.")
    cards_dict = notes

    # Define a model for the Anki cards
    anki_model = genanki.Model(
        1607342344,  # Unique model ID
        "MC Model",
        fields=[
            {"name": "id"},
            {"name": "frontimage"},
            {"name": "stats"},
            {"name": "desc"},
            {"name": "question"},
            {"name": "answer"},
            {"name": "feedback"},
            {"name": "backimage"},
            {"name": "note"},
            {"name": "url"},
            {"name": "Tags"},
            {"name": "optionA"},
            {"name": "optionB"},
            {"name": "optionC"},
            {"name": "optionD"},
            {"name": "optionE"},
            {"name": "optionF"},
            {"name": "optionG"},
            {"name": "optionH"},
            {"name": "optionI"},
            {"name": "optionJ"},
            {"name": "optionK"},
            {"name": "optionL"},
            {"name": "optionM"},
            {"name": "optionN"},
            {"name": "optionO"},
            {"name": "optionP"},
            {"name": "optionQ"},
            {"name": "optionR"},
            {"name": "optionS"},
            {"name": "optionT"},
            {"name": "optionU"},
            {"name": "optionV"},
            {"name": "optionW"},
            {"name": "optionX"},
            {"name": "optionY"},
            {"name": "optionZ"},
        ],
        templates=[
            {
                "name": "MC Card",
                "qfmt": qfmt_content,
                "afmt": afmt_content,
            },
        ],
        css=css_content,
    )

    # Create the deck
    anki_deck = genanki.Deck(
        205940548,
        filename
    )

    def process_images(images):
        if not isinstance(images, list):
            return ""
        return "<br>".join([f"<img src='{img}'>" for img in images if img])

    # Add cards from the dictionary
    for card_id, card_data in cards_dict.items():
        front_data = card_data[0]
        back_data = card_data[1]

        stats = front_data.get("Stats")
        if stats:
            statslist = stats[0].split("<br>")
            typesofstats = ["hr", "sp", "rr", "temp", "nbp"]
            stats = ""
            for index, stat in enumerate(statslist):
                stats += f'<div class=stat {typesofstats[index]}>{stat}</div>'
            stats = [stats]
        print(stats)
        desc = front_data.get("Desc")
        question = front_data.get("Question")
        images = process_images(front_data.get("Images", []))
        feedback = back_data.get("Feedback")
        backimages = process_images(back_data.get("BackImages", []))
        url = [f'<a href="{deck}">Link to Deck</a>']

        options = front_data.get("Options")
        optiontext = []
        if options:
            for option in options:
                optiontext.append(option[1])

        while len(optiontext) < 26:
            optiontext.append("")

        answers = back_data.get("Answers")
        answerkey = []
        if answers:
            for answer in answers:
                answerkey.append(answer[0])

        passed_variables = [question + desc + answers + feedback + [images] + [backimages], images, stats, desc, question, "".join(answerkey), feedback, backimages, "", url, filename, *optiontext]

        def process_field(field):
            if isinstance(field, list):
                # Join list items with <br><br> for HTML separation
                field = ''.join(f"{item}" for item in field)
            # Ensure the field is a string, replace None with ""
            return str(field or "")

        sanitized_fields = [process_field(field) for field in passed_variables]
        #print(sanitized_fields)

        # Create a card (note)
        #print("Output:", *sanitized_fields)
        note = genanki.Note(
            model=anki_model,
            fields=[*sanitized_fields],
        )
        anki_deck.add_note(note)
    # Save the deck as an Anki package
    output_file = (filename + ".apkg").replace("::", "__")
    genanki.Package(anki_deck).write_to_file(output_file)
    return output_file
    print(f"Anki deck created: {output_file}")

"""
if os.path.basename(__file__) == "fancycreate.py":
    from gitignore.userdetails import *

    deck = "https://cards.ucalgary.ca/printdeck/865?bag_id=79"
    deckcreate(username, password, deck)
"""