import streamlit as st
from main import deckcreate

st.title("Anki Deck Generator")
st.write("Log in, fetch your deck, and generate an Anki package.")

# Input form
with st.form("login_form"):
    username = st.text_input("Cards Username")
    password = st.text_input("Cards Password", type="password")
    deck_url = st.text_input("Deck URL", value="https://cards.ucalgary.ca/printdeck/1020?bag_id=81")
    submitted = st.form_submit_button("Generate Deck")

if submitted:
    if not username or not password or not deck_url:
        st.error("Please fill in all fields.")
    else:
        try:
            st.info("Logging in and fetching the deck...")
            output_file = deckcreate(username, password, deck_url)

            st.success("Anki deck created successfully!")
            with open(output_file, "rb") as f:
                st.download_button(
                    label="Download Anki Deck",
                    data=f,
                    file_name=output_file,
                    mime="application/octet-stream",
                )
        except Exception as e:
            st.error(f"An error occurred: {e}")