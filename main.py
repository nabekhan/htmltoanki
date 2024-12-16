"""
suggestion: find a way to pull "correct" for each option. then create div class=correct in anki card and back highlights those cards
"""


# Import Packages
from bs4 import BeautifulSoup
import requests
import logging
import genanki
logging.basicConfig(level=logging.DEBUG)

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
    filename = details_div.find("p").text.strip() +"::"+  details_div.find("h1").text.strip()
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
                    stat = stat.text.strip()
                    print(stat)
                    listofstats.append(stat)
                front["Stats"] = listofstats


                # print pt description
                descriptions = div.find_all("div", class_="block group")
                listofdesc = []
                for description in descriptions:
                    print(description.text.strip())
                    #description = description.text.strip()
                    listofdesc.append(description)
                front["Desc"] = listofdesc

                # print question
                headers = div.find_all("h3")
                listofheaders = []
                for header in headers:
                    header = header.text.strip()
                    print(header)
                    listofheaders.append(header)
                front["Question"] = listofheaders

                # print options
                options = div.select('div[class*="option"]')
                option_list = [div.text.strip() for div in options][1:]
                listofoptions = []
                for option in option_list:
                    option = option.strip("\u200b")
                    print(option)
                    listofoptions.append(option)
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
                    answer = answer.text.strip().strip("\u200b")
                    print(answer)
                    listofanswers.append(answer)
                back["Answers"] = listofanswers

                # print feedback
                feedbacks = div.find_all("div", class_="results container")
                listoffeed = []
                for feedback in feedbacks:
                    feedback = feedback.text.strip().strip("\u200b")
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
                back["BackImages"] = listofbackimages

                notes[int(i / 2)] = [front, back]
                print("-" * 50)
        print(notes)
    else:
        print("No <div> elements with class 'page' found.")
    cards_dict = notes


    #
    # Helper function to process fields with <br> separator
    def process_field(field):
        if isinstance(field, list):
            field = ''.join(f"{item}<br><br>" for item in field)
        return str(field or "").replace("\n", "<br>")

    def process_description(field):
        if isinstance(field, list):
            field = ''.join(f"{item}" for item in field)
        return str(field or "").replace("\n", "<br>")
    def process_choices(field, classtype):
        if not isinstance(field, list):
            return f'<div class="{classtype}"></div>'
        choices = [f"<li>{str(choice)}</li>" for choice in field]
        return f'<div class="{classtype}">' + ''.join(choices) + '</div>'

    def process_stats(field):
        if isinstance(field, list):
            field = ''.join(f"{item}<br>" for item in field)
        return '<div class="stats">'+str(field or "").replace("\n", "<br>")+'</div>'
    def process_images(images):
        if not isinstance(images, list):
            return ""
        return "<br>".join([f"<img src='{img}'>" for img in images if img])

    # Define a model for the Anki cards
    anki_model = genanki.Model(
        1607342344,  # Unique model ID
        "Comprehensive Model",
        fields=[
            {"name": "ID"},
            {"name": "Stats"},
            {"name": "Description"},
            {"name": "Question"},
            {"name": "Options"},
            {"name": "Image"},
            {"name": "Answers"},
            {"name": "Feedback"},
            {"name": "Back Image"},
            {"name": "URL"},
            {"name": "Tags"},
            {"name": "Notes"},
        ],
        templates=[
            {
                "name": "Comprehensive Card",
                "qfmt": qfmt_content,
                "afmt": afmt_content,
            },
        ],
        css=css_content,
    )


    # Create the deck
    anki_deck = genanki.Deck(
        2059400112,
        filename
    )

    # Add cards from the dictionary
    for card_id, card_data in cards_dict.items():
        front_data = card_data[0]
        back_data = card_data[1]

        stats = process_stats(front_data.get("Stats", []))
        desc = process_description(front_data.get("Desc", []))
        question = process_field(front_data.get("Question", []))
        options = process_choices(front_data.get("Options", []), "choices")
        images = process_images(front_data.get("Images", []))
        answers = process_choices(back_data.get("Answers", []), "answers")
        feedback = process_field(back_data.get("Feedback", []))
        backimage = process_images(back_data.get("BackImages", []))
        url = deck

        print(f'Output: {question+desc+answers+feedback, stats, desc, question, options, images, answers, feedback, backimage, url, filename}')
        note = genanki.Note(
            model=anki_model,
            fields=[question+desc+answers+feedback, stats, desc, question, options, images, answers, feedback, backimage, url, filename, ""],
        )
        anki_deck.add_note(note)

    # Save the deck as an Anki package
    output_file = (filename + ".apkg").replace("::", "__")
    #genanki.Package(anki_deck).write_to_file(f"gitignore/{output_file}")
    genanki.Package(anki_deck).write_to_file(output_file)
    return output_file
    print(f"Anki deck created: {output_file}")


if __name__ == "__main__":
    from gitignore.userdetails import *
    deck = "https://cards.ucalgary.ca/printdeck/1020?bag_id=81"
    deckcreate(username, password, deck)