import streamlit as st
from main import deckcreate
import pypandoc
import os

# Set Pandoc path explicitly (needed on Streamlit Cloud)
pypandoc.PANDOC_PATH = os.path.join(os.getcwd(), "pandoc")

# Set page configuration
st.set_page_config(page_title="Anki Deck Generator", page_icon="assets/favicon.webp", layout="centered")

# Page title and description
st.title("🔹 Anki Deck Generator")
st.write(
    "Easily generate Anki decks by logging in, fetching your deck, and downloading the Anki package."
)

# Input form with styled container
st.markdown("---")
st.header("🔐 Login and Fetch Deck")
st.write("Fill in the form below to start generating your Anki deck.")

with st.form("login_form"):
    username = st.text_input("👤 Cards Username", placeholder="Enter your username")
    password = st.text_input("🔒 Cards Password", type="password", placeholder="Enter your password")
    deck_url = st.text_input(
        "🌐 Deck URL",
        value="https://cards.ucalgary.ca/printdeck/1020?bag_id=81",
        placeholder="Paste your deck URL here"
    )
    submitted = st.form_submit_button("📈 Generate Deck")

# Processing the form submission
if submitted:
    if not username or not password or not deck_url:
        st.error("Please fill in all fields to proceed.")
    else:
        with st.spinner("Logging in and fetching the deck. Please wait..."):
            try:
                # Call the deck creation function
                output_file = deckcreate(username, password, deck_url)

                # Display success message and download button
                st.success("Anki deck created successfully! 🎉")
                with open(output_file, "rb") as f:
                    st.download_button(
                        label="🔗 Download Anki Deck",
                        data=f,
                        file_name=output_file,
                        mime="application/octet-stream",
                    )
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Footer section for aesthetics
st.markdown("---")
st.caption("Built with 💪 by your friendly flashcard generator.")
