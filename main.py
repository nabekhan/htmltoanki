# Import Packages
from bs4 import BeautifulSoup
import requests
import logging
import genanki

logging.basicConfig(level=logging.DEBUG)


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
                    listofbackimages.append(bkurl)
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
            {"name": "Multiple Choice"},
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
                "qfmt": """
<div class="bar">
	<div class="subdeck">{{#Subdeck}}{{Subdeck}}{{/Subdeck}}</div>
	<div class="tag">{{#Tags}}{{Tags}}{{/Tags}}</div>
</div>
<div class="background">
	<div class="chart">
		<div class="frontimg images">{{Image}}</div>{{Stats}}
		<div class="background desc" style="margin: 8px 8px;">
			<br />{{Description}}
		</div>
	</div>
	<br /><div id="question">{{Question}}</div>
	<br />{{Multiple Choice}}
	<div class="Options">{{Options}}</div>
</div>
<!-- Stats Fix -->
<script>
document.querySelectorAll('div.stats').forEach(div => {
	// Get the inner HTML of the target div
	let content = div.innerHTML;
	// Replace three consecutive <br> tags with three tabs
	content = content.replace(/(<br\s*\/?>\s*){3}/g, ' &nbsp;&nbsp; ');
	// Replace single or remaining <br> tags with one tab
	content = content.replace(/<br\s*\/?>/g, '&nbsp;');
	// Update the div content
	div.innerHTML = content;
});
</script>
<!-- Text Colour Script -->
<script>
setTimeout(function() {
	console.log("Applying white text color to all elements...");
	// Select all elements in the card
	const allElements = document.querySelectorAll('*');
	// Loop through each element and set the text color to white
	allElements.forEach(function(element) {
		element.style.color = 'white';
	});
}, 10);
</script>
<!-- Shuffle Script -->
<script>
// v1.1.8 - https://github.com/SimonLammer/anki-persistence/blob/584396fea9dea0921011671a47a0fdda19265e62/script.js
if(void 0 === window.Persistence) {
	var e = "github.com/SimonLammer/anki-persistence/",
		t = "_default";
	if(window.Persistence_sessionStorage = function() {
			var i = !1;
			try {
				"object" == typeof window.sessionStorage && (i = !0, this.clear = function() {
					for(var t = 0; t < sessionStorage.length; t++) {
						var i = sessionStorage.key(t);
						0 == i.indexOf(e) && (sessionStorage.removeItem(i), t--);
					}
				}, this.setItem = function(i, n) {
					void 0 == n && (n = i, i = t),
						sessionStorage.setItem(e + i, JSON.stringify(n));
				}, this.getItem = function(i) {
					return void 0 == i && (i = t),
						JSON.parse(sessionStorage.getItem(e + i));
				}, this.removeItem = function(i) {
					void 0 == i && (i = t),
						sessionStorage.removeItem(e + i);
				}, this.getAllKeys = function() {
					for(var t = [], i = Object.keys(sessionStorage), n = 0; n < i.length; n++) {
						var s = i[n];
						0 == s.indexOf(e) && t.push(s.substring(e.length, s.length));
					}
					return t.sort();
				});
			} catch (n) {}
			this.isAvailable = function() {
				return i;
			}
		}, window.Persistence_windowKey = function(i) {
			var n = window[i],
				s = !1;
			"object" == typeof n && (s = !0, this.clear = function() {
					n[e] = {};
				}, this.setItem = function(i, s) {
					void 0 == s && (s = i, i = t),
						n[e][i] = s;
				}, this.getItem = function(i) {
					return void 0 == i && (i = t),
						void 0 == n[e][i] ? null : n[e][i];
				}, this.removeItem = function(i) {
					void 0 == i && (i = t),
						delete n[e][i];
				}, this.getAllKeys = function() {
					return Object.keys(n[e]);
				}, void 0 == n[e] && this.clear()),
				this.isAvailable = function() {
					return s;
				}
		}, window.Persistence = new Persistence_sessionStorage, Persistence.isAvailable() || (window.Persistence = new Persistence_windowKey("py")), !Persistence.isAvailable()) {
		var i = window.location.toString().indexOf("title"),
			n = window.location.toString().indexOf("main", i);
		i > 0 && n > 0 && n - i < 10 && (window.Persistence = new Persistence_windowKey("qt"));
	}
}
// Clear persistence when the front side loads
(function clearPersistenceOnLoad() {
	if(typeof Persistence !== "undefined" && Persistence.isAvailable()) {
		console.log("Clearing persistence data on front side...");
		Persistence.clear();
	} else {
		console.warn("Persistence is not available.");
	}
})();

function shuffleList() {
	const listContainer = document.querySelector('.choices');
	if(!listContainer) return;
	const items = Array.from(listContainer.querySelectorAll('li'));
	if(Persistence.isAvailable()) {
		let shuffleOrder = Persistence.getItem('shuffleOrder'); // Retrieve existing shuffle order
		if(!shuffleOrder) {
			// Generate a new shuffle order using Fisher-Yates algorithm
			shuffleOrder = items.map((_, i) => i);
			for(let i = shuffleOrder.length - 1; i > 0; i--) {
				const j = Math.floor(Math.random() * (i + 1));
				[shuffleOrder[i], shuffleOrder[j]] = [shuffleOrder[j], shuffleOrder[i]];
			}
			Persistence.setItem('shuffleOrder', shuffleOrder); // Save the shuffle order
		}
		// Apply the shuffle order
		const shuffledItems = shuffleOrder.map(i => items[i]);
		listContainer.innerHTML = ''; // Clear original container
		shuffledItems.forEach(item => listContainer.appendChild(item)); // Append shuffled items
	}
}
shuffleList(); // Call the function
</script>
                """,
                "afmt": """
<div class="bar">
	<div class="subdeck">{{#Subdeck}}{{Subdeck}}{{/Subdeck}}</div>
	<div class="tag">{{#Tags}}{{Tags}}{{/Tags}}</div>
</div>
<div class="background">
	<div class="chart">
		<div class="frontimg images">{{Image}}</div>{{Stats}}
		<div class="background desc" style="margin: 8px 8px;">
			<br />{{Description}}
		</div>
	</div>
	<br /><div id="question">{{Question}}</div>
	<br />{{Multiple Choice}}
	<div class="Options">{{Options}}</div>
	<div class="Options answers">{{Answers}}</div>
	<br />{{Feedback}}
	<br /><div class="notes">{{Notes}}</div>
	<br />
	<div class="chart">
		<div class="backimg images">{{Back Image}}</div>
		<div style="text-align: center;"><a href="{{URL}}"><u>Link To Card</u></a></div>
	</div>
</div>
</div>
<!-- Stats Fix -->
<script>
document.querySelectorAll('div.stats').forEach(div => {
	// Get the inner HTML of the target div
	let content = div.innerHTML;
	// Replace three consecutive <br> tags with three tabs
	content = content.replace(/(<br\s*\/?>\s*){3}/g, ' &nbsp;&nbsp; ');
	// Replace single or remaining <br> tags with one tab
	content = content.replace(/<br\s*\/?>/g, '&nbsp;');
	// Update the div content
	div.innerHTML = content;
});
</script>
<!-- Text Colour Script -->
<script>
setTimeout(function() {
	console.log("Applying white text color to all elements...");
	// Select all elements in the card
	const allElements = document.querySelectorAll('*');
	// Loop through each element and set the text color to white
	allElements.forEach(function(element) {
		element.style.color = 'white';
	});
}, 10);
</script>
<!-- Shuffle Script -->
<script>
// v1.1.8 - https://github.com/SimonLammer/anki-persistence/blob/584396fea9dea0921011671a47a0fdda19265e62/script.js
if(void 0 === window.Persistence) {
	var e = "github.com/SimonLammer/anki-persistence/",
		t = "_default";
	if(window.Persistence_sessionStorage = function() {
			var i = !1;
			try {
				"object" == typeof window.sessionStorage && (i = !0, this.clear = function() {
					for(var t = 0; t < sessionStorage.length; t++) {
						var i = sessionStorage.key(t);
						0 == i.indexOf(e) && (sessionStorage.removeItem(i), t--)
					}
				}, this.setItem = function(i, n) {
					void 0 == n && (n = i, i = t), sessionStorage.setItem(e + i, JSON.stringify(n))
				}, this.getItem = function(i) {
					return void 0 == i && (i = t), JSON.parse(sessionStorage.getItem(e + i))
				}, this.removeItem = function(i) {
					void 0 == i && (i = t), sessionStorage.removeItem(e + i)
				}, this.getAllKeys = function() {
					for(var t = [], i = Object.keys(sessionStorage), n = 0; n < i.length; n++) {
						var s = i[n];
						0 == s.indexOf(e) && t.push(s.substring(e.length, s.length))
					}
					return t.sort()
				})
			} catch (n) {}
			this.isAvailable = function() {
				return i
			}
		}, window.Persistence_windowKey = function(i) {
			var n = window[i],
				s = !1;
			"object" == typeof n && (s = !0, this.clear = function() {
				n[e] = {}
			}, this.setItem = function(i, s) {
				void 0 == s && (s = i, i = t), n[e][i] = s
			}, this.getItem = function(i) {
				return void 0 == i && (i = t), void 0 == n[e][i] ? null : n[e][i]
			}, this.removeItem = function(i) {
				void 0 == i && (i = t), delete n[e][i]
			}, this.getAllKeys = function() {
				return Object.keys(n[e])
			}, void 0 == n[e] && this.clear()), this.isAvailable = function() {
				return s
			}
		}, window.Persistence = new Persistence_sessionStorage, Persistence.isAvailable() || (window.Persistence = new Persistence_windowKey("py")), !Persistence.isAvailable()) {
		var i = window.location.toString().indexOf("title"),
			n = window.location.toString().indexOf("main", i);
		i > 0 && n > 0 && n - i < 10 && (window.Persistence = new Persistence_windowKey("qt"))
	}
}

function applyShuffleFromPersistence() {
	const listContainer = document.querySelector('.choices');
	if(!listContainer || !Persistence.isAvailable()) return;
	const items = Array.from(listContainer.querySelectorAll('li'));
	const shuffleOrder = Persistence.getItem('shuffleOrder'); // Retrieve saved shuffle order
	if(shuffleOrder) {
		const shuffledItems = shuffleOrder.map(i => items[i]);
		listContainer.innerHTML = ''; // Clear original container
		shuffledItems.forEach(item => listContainer.appendChild(item)); // Append shuffled items
		Persistence.removeItem('shuffleOrder'); // Clear the shuffle order for the next card
	}
}
applyShuffleFromPersistence(); // Call the function
</script>
<!-- Clean Duplicate Images -->
<script>
setTimeout(function() {
	console.log("Checking image elements...");
	// Get the elements containing the front and back images
	var frontImgElement = document.querySelector(".frontimg");
	var backImgElement = document.querySelector(".backimg");
	// Validate that both elements exist
	if(!frontImgElement) {
		console.error("Front image element (.frontimg) not found.");
		return;
	}
	if(!backImgElement) {
		console.error("Back image element (.backimg) not found.");
		return;
	}
	// Extract URLs from the images inside frontimg and backimg
	var frontImgUrls = Array.from(frontImgElement.querySelectorAll('img')).map(el => el.src);
	var backImgUrls = Array.from(backImgElement.querySelectorAll('img'));
	// Iterate through back images and hide matching ones
	backImgUrls.forEach(function(img) {
		if(frontImgUrls.includes(img.src)) {
			console.log(`Hiding matching image: ${img.src}`);
			img.style.display = "none"; // Hide the matching image
		}
	});
	console.log("Image comparison and hiding completed.");
}, 10);
</script>
<!-- Select Answers and Highlight Green -->
<script>
setTimeout(function() {
	console.log("Checking DOM elements...");
	var questionElement = document.querySelector(".choices");
	var answerElement = document.querySelector(".answers");
	if(!questionElement) {
		console.error("Question element not found.");
		return;
	}
	if(!answerElement) {
		console.error("Answer element not found.");
		return;
	}
	// Split the contents into lists by <li> tags
	var questionList = Array.from(questionElement.querySelectorAll('li')).map(el => el.innerHTML.trim());
	var answerList = Array.from(answerElement.querySelectorAll('li')).map(el => el.innerHTML.trim());
	// Iterate over the question list and compare with the answer list
	var modifiedQuestionList = questionList.map(function(item) {
		return answerList.includes(item) ? `<div class="green-highlight"><li>${item}</li></div>` : `<li>${item}</li>`;
	});
	// Join the modified list back into HTML and set it
	questionElement.innerHTML = modifiedQuestionList.join('');
}, 100);
</script>
<!-- Scroll to the question -->
<script>
  (function () {
    const questionElement = document.getElementById('question');
    if (questionElement) {
      questionElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  })();
</script>
                """,
            },
        ],
        css="""
div:empty {
     display: none;
}
 .card {
     padding: 15px 20px;
     font: 20px Arial, sans-serif;
     color: white;
}
 .background {
     border-radius: 9px;
     padding: 20px;
     background: #1e1e1e;
}
 .background img {
     width: auto;
     height: auto;
     display: block;
     margin-left: auto;
     margin-right: auto;
}
 .background.night_mode {
     border-radius: 9px;
     padding: 20px;
     background: #1e1e1e;
}
 .cloze {
     font-weight: bold;
     color: orange;
}
 .bar {
     margin-bottom: -25px;
     background: #121212;
     border-top-right-radius: 9px;
     border-top-left-radius: 9px;
     padding-top: 10px;
     padding-bottom: 30px;
     z-index: -1;
     text-align: center;
}
 .subdeck {
     color: rgba(255, 255, 255, 0.6);
     font-size: 14px;
}
 .tag {
     color: rgba(255, 255, 255, 0.87);
     font-size: 13px;
     font-style: italic;
}
 .images {
     max-width: 800px;
     display: flex;
     flex-flow: row wrap;
     margin: auto;
     justify-content: center;
}
 .images > div {
     width: 50%;
}
 img {
     display: block;
     width: 100%;
     height: 100%;
     object-fit: cover;
     max-width: 100%;
}
 .notes {
     font: 15px Arial, sans-serif;
}
/* Options */
 .Options li {
     margin: 5px 0;
     display: flex;
     align-items: center;
     border: 1px solid #ddd;
     padding: 10px;
     border-radius: 5px;
     box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
     min-width: 10em;
}
 .green-highlight {
     background-color: green !important;
     color: white !important;
}
/* Desc */
 .desc {
     box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}
 .desc br {
     display: none;
}
/* Stats */
 .stats {
     border-radius: 8px;
     font-weight: bold;
     box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
     margin: 8px 8px;
     padding: 10px;
     font-size: 14px;
     background: #1e1e1e;
     text-align: center;
}
/* Pt Chart */
 .chart {
     background-color: #444;
     border-radius: 8px;
     box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
     margin: 8px 0;
     padding: 10px;
     margin: 8px 8px;
     flex-direction: column;
}
/* Answers */
 .answers {
     display: none;
}
        """,
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

        # Create a card (note)
        if len(back_data.get("Answers", [])) > 1:
            multi = "(Select All That Apply)"
        else:
            multi = ""
        print(f'Output: {question+desc+answers+feedback, stats, desc, question, multi, options, images, answers, feedback, backimage, url, filename}')
        note = genanki.Note(
            model=anki_model,
            fields=[question+desc+answers+feedback, stats, desc, question, multi, options, images, answers, feedback, backimage, url, filename, ""],
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