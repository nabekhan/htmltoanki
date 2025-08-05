import html2text
import markdown2
import csv
from bs4 import BeautifulSoup
import requests
import logging
import genanki
import pypandoc
import bleach
from collectdeck import get_deck_links
from tqdm import tqdm
import re
from prints import *

#logging.basicConfig(level=logging.DEBUG)

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
    # Step 1: Convert HTML to plain text using html2text
    text_maker = html2text.HTML2Text()
    text_maker.ignore_links = False  # Remove links if unnecessary
    text_maker.ignore_images = False  # Remove images if unnecessary
    text_maker.body_width = 0  # Prevent line wrapping
    markdown_text = text_maker.handle(str(souphtml))

    # Step 2: Sanitize the Markdown
    markdown_text = markdown_text.replace('\u200b', '')  # Remove zero-width spaces

    # Step 3: Convert back to minimal HTML
    html_output = markdown2.markdown(markdown_text, extras=["break-on-newline"])

    # Step 4: Simplify further using BeautifulSoup
    soup = BeautifulSoup(html_output, "html.parser")

    # Remove <h2> tags specifically
    for h2 in soup.find_all('h2'):
        # Replace <h2> with <p> if needed, or just remove it entirely
        new_tag = soup.new_tag("p")
        new_tag.string = h2.get_text()  # Preserve text inside <h2>
        h2.replace_with(new_tag)

    # Strip attributes from all tags
    for tag in soup.find_all(True):
        tag.attrs = {}  # Clear attributes

    # Ensure consistent spacing
    simplified_html = soup.prettify(formatter="minimal").strip()

    return simplified_html

def processtomd(souphtml):
    """
    1. Clean HTML with bleach (remove non-standard attributes like ccp_infra_*).
    2. Convert cleaned HTML to Markdown (using Pandoc via pypandoc).

    :param souphtml: BeautifulSoup object or raw HTML string.
    :return: Markdown string.
    """
    # If souphtml is a BeautifulSoup object, convert it to a string
    if hasattr(souphtml, 'prettify'):
        html_str = souphtml.prettify()
    else:
        html_str = str(souphtml)

    # Define which tags and attributes you want to ALLOW
    # Everything else will be removed or stripped.
    allowed_tags = [
        'p', 'br', 'div', 'span', 'td', 'th', 'tr', 'table', 'thead', 'tbody',
        'strong', 'em', 'b', 'i', 'u', 'ul', 'ol', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'img', 'a',
    ]
    allowed_attributes = {
        '*': ['class', 'href', 'width', 'height', 'colspan', 'rowspan'],
        # for example, keep 'src' and 'alt' on images:
        'img': ['src', 'alt'],
    }

    # Clean the HTML, removing anything not in allowed_tags/attributes
    cleaned_html = bleach.clean(
        html_str,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True  # remove disallowed tags (rather than escaping them)
    )

    # Convert to Markdown. Here we use GitHub Flavored Markdown (gfm)
    markdown_text = pypandoc.convert_text(
        cleaned_html,
        to='gfm',
        format='html'
    )
    return pypandoc.convert_text(markdown_text, to='html', format='md')

def find_sublist_with_string(list_of_lists, target_string):
    for sublist in list_of_lists:
        if target_string in sublist:
            return sublist
    return ""  # Return None if the string is not found in any sublist


# Import files
with open("src/frontside.html", "r", encoding="utf-8") as f:
    qfmt_content = f.read()

with open("src/backside.html", "r", encoding="utf-8") as f:
    afmt_content = f.read()

with open("src/css.html", "r", encoding="utf-8") as f:
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
                # logging.error(f" Failed to load. Check your network connectivity or if print is enabled for the deck.")
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
    filename = details_div.find("p").text.strip() +"::"+  details_div.find("h1").text.strip()
    #print(filename)

    # Select records
    records_div = S.find("div", class_="records")

    # Find all <div> elements with the class "page"
    page_divs = records_div.find_all("div", class_="page", recursive=False)

    # Check if any <div class="page"> elements are found
    if page_divs:
        notes = {}
        #print(f"Found {len(page_divs)} 'page' divs.")
        # Iterate and print the content of each
        for i, div in enumerate(page_divs, start=1):
            if i % 2 != 0:
                # Define Question
                #print(f"Question {int(i / 2 + 0.5)} Content:")
                front = {}

                # print stats
                stats = div.find_all("div", class_="stats")
                listofstats = []
                for stat in stats:
                    stat.attrs = {}
                    #print(stat)
                    listofstats.append(stat)
                front["Stats"] = listofstats

                # print pt description
                descriptions = div.find_all("div", class_="block group")
                listofdesc = []
                for description in descriptions:
                    description = processtomd(description)
                    listofdesc.append(description)
                front["Desc"] = listofdesc

                # print question
                headers = div.find_all("h3")
                listofheaders = []
                for header in headers:
                    header = header.text.strip()
                    #print(header)
                    listofheaders.append(header)
                front["Question"] = listofheaders

                # print options
                options = div.select('div[class*="option"]')
                option_list = [div.text.strip() for div in options][1:]
                listofoptions = []
                for index, option in enumerate(option_list):
                    option = option.strip("\u200b")
                    #print(option)
                    listofoptions.append([alphaUpper[index], option])
                front["Options"] = listofoptions

                # find images
                images = div.find_all("img")
                listofimages = []
                for image in images:
                    urlstub = image.get("src")
                    if not urlstub.startswith("https"):
                        url = "https://cards.ucalgary.ca/" + urlstub[1:]
                    #print(url)
                    listofimages.append(url)
                front["Images"] = listofimages
            else:
                back = {}

                # print answers
                #print(f"Question {int(i / 2)} Answer:")
                answers = div.find_all("div", class_="correct")
                listofanswers = []
                for answer in answers:
                    answer = answer.text.strip().strip("\u200b")
                    #print(answer)
                    findanswerindex = find_sublist_with_string(listofoptions, answer)
                    if findanswerindex:
                        answerletter = findanswerindex[0]
                        listofanswers.append([answerletter, answer])
                back["Answers"] = listofanswers

                # print feedback
                feedbacks = div.find_all("div", class_="results container")
                listoffeed = []
                for feedback in feedbacks:
                    feedback = processtxt(feedback)
                    #print(feedback)
                    listoffeed.append(feedback)
                back["Feedback"] = listoffeed

                # find images
                backimages = div.find_all("img")
                listofbackimages = []
                for image in backimages:
                    bkurlstub = image.get("src")
                    bkurl = "https://cards.ucalgary.ca/" + bkurlstub[1:]
                    #print(bkurl)
                    if bkurl in listofimages:
                        continue
                    else:
                        listofbackimages.append(bkurl)
                back["BackImages"] = listofbackimages

                notes[int(i / 2)] = [front, back]
                #print("-" * 50)
        #print(notes)
    else:
        print()
        #print("No <div> elements with class 'page' found.")
    cards_dict = notes

    def process_images(images):
        if not isinstance(images, list):
            return ""
        return "<br>".join([f"<img src='{img}'>" for img in images if img])

    # Define a model for the Anki cards
    anki_model = genanki.Model(
        1607345344,  # Unique model ID
        "MC Calgary",
        fields=[
            {"name": "ID"},
            {"name": "Stats"},
            {"name": "Front Image"},
            {"name": "Description"},
            {"name": "Question"},
            {"name": "Feedback"},
            {"name": "Back Image"},
            {"name": "Notes"},
            {"name": "URL"},
            {"name": "Tags"},
            {"name": "Answers"},
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
                "name": "MC Calgary",
                "qfmt": qfmt_content,
                "afmt": afmt_content,
            },
        ],
        css=css_content,
    )


    # Create the deck
    anki_deck = genanki.Deck(
        2059488112,
        filename
    )

    # Add cards from the dictionary
    for card_id, card_data in cards_dict.items():
        front_data = card_data[0]
        back_data = card_data[1]

        stats = front_data.get("Stats")
        desc = front_data.get("Desc")
        question = front_data.get("Question")
        images = process_images(front_data.get("Images", []))
        feedback = back_data.get("Feedback")
        backimage = process_images(back_data.get("BackImages", []))
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

        passed_variables = [question + desc + answers + feedback, stats, images, desc, question, feedback, backimage, "", url, filename, "".join(answerkey), *optiontext]


        def process_field(field):
            if isinstance(field, list):
                # Join list items with <br><br> for HTML separation
                field = ''.join(f"{item}" for item in field)
            # Ensure the field is a string, replace None with ""
            return str(field or "")

        sanitized_fields = [process_field(field) for field in passed_variables]


        #print(f'Output: {sanitized_fields}')
        note = genanki.Note(
            model=anki_model,
            fields=[*sanitized_fields],
        )
        anki_deck.add_note(note)

    # Save the deck as an Anki package
    output_file = (filename + ".apkg").replace("::", "__").replace('/', '_')
    output_file = ("decks/"+output_file)
    #genanki.Package(anki_deck).write_to_file(f"gitignore/{output_file}")
    genanki.Package(anki_deck).write_to_file(output_file)
    print(f"Anki deck created: {output_file}")
    return output_file


if __name__ == "__main__":
    # Create required directories if they don't exist
    os.makedirs("gitignore", exist_ok=True)
    os.makedirs("gitignore/decks", exist_ok=True)

    from gitignore.userdetails import *

    # Enter deck URL
    pattern = r"^https://cards\.ucalgary\.ca/collection/\d+$"
    deckurl = input("Enter collection URL to process decks. Click enter to skip: ").strip()
    if deckurl == "":
        print("Skipping...")
    elif re.match(pattern, deckurl):
        print("Valid collection URL. Processing...")
        # proceed with processing
    else:
        raise ValueError("Invalid URL format. Please use: https://cards.ucalgary.ca/collection/<number> (ex: https://cards.ucalgary.ca/collection/126)")


    processfailed = input("Process previously failed decks? (Y/N): ").strip().lower()
    processfailed = processfailed == "y"
    if processfailed:
        print("Processing failed decks...")
    else:
        print("Skipping...")

    print ("Forming deck list...")
    decklist = []

    if deckurl:
        get_deck_links(username, password, deckurl)
        # Read decklist.csv
        decks = "gitignore/urllist.csv"
        with open(decks, "r") as f:
            reader = list(csv.reader(f))  # convert to list once
            urllist = [row[0] for row in reader if row]  # skip empty rows
            decklist = reader[0] if reader else []  # protect against empty file

    # read failed_items.csv if it exists
    failed_items_file = "gitignore/failed_items.csv"
    if os.path.exists(failed_items_file) and processfailed:
        with open(failed_items_file, "r") as f:
            reader = csv.reader(f)
            failed_list = [row[0] for row in reader if row]  # skip empty rows
            decklist.extend(failed_list)

    # Remove duplicates
    decklist = list(set(decklist))

    print(f"Total decks to be processed: {len(decklist)}")

    # process decks and log failures
    successful_items = []
    failed_items = []
    blockPrint()
    for item in tqdm(decklist, desc="Processing Decks"):
        print(f"Trying: {item}")
        try:
            deckcreate(username, password, item)
            successful_items.append(item)
        except Exception as e:
            print(f"Failed: {item} - {e}")
            failed_items.append(item)
    enablePrint()

    if deckurl:
        with open(decks, "w") as f:
            pass  # truncate the file

    # clear CSVs
    if processfailed:
        with open(failed_items_file, "w") as f:
            pass  # truncate the file

    # save failed items to CSV
    # Load existing items from file (if it exists)
    existing_items = set()
    if os.path.exists(failed_items_file):
        with open(failed_items_file, "r") as f:
            reader = csv.reader(f)
            existing_items = {row[0] for row in reader if row}

    # Merge with current failed items and remove duplicates
    all_failed = existing_items.union(failed_items)

    # Save back to file (overwrite with deduplicated list)
    if all_failed:
        with open(failed_items_file, "w", newline="") as f:
            writer = csv.writer(f)
            for item in sorted(all_failed):
                writer.writerow([item])

    print("Successful items:", successful_items)
    if failed_items:
        print("Failed items:", failed_items)
        print("Please check if failed decks are printable before retrying!")
    else:
        print("All items successful!")

