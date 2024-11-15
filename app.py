import streamlit as st
import requests
import os

API_KEY = os.getenv("CLAUDE_API_KEY") or st.secrets["API_KEY"]
API_ENDPOINT = "https://api.anthropic.com/v1/messages"

st.title("Norwegian Text Utilities")

option = st.sidebar.selectbox(
    "Choose an option:",
    ("Translate Norwegian to English", "Clean Up Norwegian Text")
)

if option == "Translate Norwegian to English":
    st.header("Translate Norwegian to English")
    norwegian_text = st.text_area("Enter Norwegian text:")

    if st.button("Translate"):
        if norwegian_text.strip() == "":
            st.warning("Please enter some text to translate.")
        else:
            headers = {
                "anthropic-version": "2023-06-01",
                "x-api-key": API_KEY,
                "content-type": "application/json",
            }

            payload = {
                "messages": [{
                    "role": "user",
                    "content": f"Translate the following Norwegian text to English:\n\n{norwegian_text}"
                }],
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1000,
                "temperature": 0.7
            }

            response = requests.post(API_ENDPOINT, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                translated_text = result["content"][0]["text"]
                st.subheader("Translated Text:")
                st.write(translated_text)
            else:
                error_info = response.json().get('error', {})
                error_message = error_info.get('message', 'An unknown error occurred.')
                st.error(f"Error: {response.status_code} - {error_message}")

elif option == "Clean Up Norwegian Text":
    st.header("Clean Up Norwegian Text")
    norwegian_text = st.text_area("Enter text to clean up:")

    if st.button("Clean Up"):
        if norwegian_text.strip() == "":
            st.warning("Please enter some text to clean up.")
        else:
            headers = {
                "anthropic-version": "2023-06-01",
                "x-api-key": API_KEY,
                "content-type": "application/json",
            }

            payload = {
                "messages": [{
                    "role": "user",
                    "content": f"Please proofread and suggest improvements for the following Norwegian text:\n\n{norwegian_text}"
                }],
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1000,
                "temperature": 0.7
            }

            response = requests.post(API_ENDPOINT, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                cleaned_text = result["content"][0]["text"]
                st.subheader("Suggested Improvements:")
                st.write(cleaned_text)

                accept = st.button("Accept Suggestions")
                decline = st.button("Decline Suggestions")

                if accept:
                    st.success("You have accepted the suggestions.")
                elif decline:
                    st.info("You have declined the suggestions.")
            else:
                error_info = response.json().get('error', {})
                error_message = error_info.get('message', 'An unknown error occurred.')
                st.error(f"Error: {response.status_code} - {error_message}")
