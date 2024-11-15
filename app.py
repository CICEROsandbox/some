import streamlit as st
import requests
import os

# Set up your API key and endpoint
API_KEY = os.getenv("CLAUDE_API_KEY")
API_ENDPOINT = "https://api.anthropic.com/v1/complete"
API_KEY = st.secrets["API_KEY"]


st.title("Norwegian Text Utilities")

# Sidebar navigation
option = st.sidebar.selectbox(
    "Choose an option:",
    ("Translate Norwegian to English", "Clean Up Norwegian Text")
)

if option == "Translate Norwegian to English":
    st.header("Translate Norwegian to English")

    # Input field for Norwegian text
    norwegian_text = st.text_area("Enter Norwegian text:")

    if st.button("Translate"):
        if norwegian_text.strip() == "":
            st.warning("Please enter some text to translate.")
        else:
            # Prepare the prompt for the API
            prompt = f"Translate the following Norwegian text to English:\n\n{norwegian_text}"

            # Set up headers and payload for the API request
            headers = {
                "x-api-key": API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"  # Replace with the correct API version
            }

            payload = {
                "prompt": prompt,
                "model": "claude-v1",
                "max_tokens_to_sample": 1000,
                "temperature": 0.7,
                "stop_sequences": [],
                "stream": False
            }

            # Make the API request
            response = requests.post(API_ENDPOINT, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                translated_text = result.get("completion", "").strip()
                st.subheader("Translated Text:")
                st.write(translated_text)
            else:
                error_info = response.json().get('error', {})
                error_message = error_info.get('message', 'An unknown error occurred.')
                st.error(f"Error: {response.status_code} - {error_message}")

elif option == "Clean Up Norwegian Text":
    st.header("Clean Up Norwegian Text")

    # Input field for Norwegian text
    norwegian_text = st.text_area("Enter text to clean up:")

    if st.button("Clean Up"):
        if norwegian_text.strip() == "":
            st.warning("Please enter some text to clean up.")
        else:
            # Prepare the prompt for the API
            prompt = f"Please proofread and suggest improvements for the following Norwegian text. Provide your suggestions:\n\n{norwegian_text}"

            # Set up headers and payload for the API request
            headers = {
                "x-api-key": API_KEY,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"  # Replace with the correct API version
            }

            payload = {
                "prompt": prompt,
                "model": "claude-v1",
                "max_tokens_to_sample": 1000,
                "temperature": 0.7,
                "stop_sequences": [],
                "stream": False
            }

            # Make the API request
            response = requests.post(API_ENDPOINT, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                cleaned_text = result.get("completion", "").strip()
                st.subheader("Suggested Improvements:")
                st.write(cleaned_text)

                # Accept or decline suggestions
                accept = st.button("Accept Suggestions")
                decline = st.button("Decline Suggestions")

                if accept:
                    st.success("You have accepted the suggestions.")
                    # Additional code to handle acceptance
                elif decline:
                    st.info("You have declined the suggestions.")
                    # Additional code to handle declination
            else:
                error_info = response.json().get('error', {})
                error_message = error_info.get('message', 'An unknown error occurred.')
                st.error(f"Error: {response.status_code} - {error_message}")
