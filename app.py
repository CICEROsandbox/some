import streamlit as st
import requests
import difflib
import re

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

def get_word_diffs(original, suggested):
    """Get word-by-word differences between original and suggested text"""
    def split_into_words(text):
        return re.findall(r'\S+|\s+', text)
    
    original_words = split_into_words(original)
    suggested_words = split_into_words(suggested)
    
    matcher = difflib.SequenceMatcher(None, original_words, suggested_words)
    changes = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            changes.append({
                'type': 'change',
                'original': ''.join(original_words[i1:i2]),
                'suggested': ''.join(suggested_words[j1:j2])
            })
        elif tag == 'delete':
            changes.append({
                'type': 'deletion',
                'original': ''.join(original_words[i1:i2]),
                'suggested': ''
            })
        elif tag == 'insert':
            changes.append({
                'type': 'insertion',
                'original': '',
                'suggested': ''.join(suggested_words[j1:j2])
            })
        elif tag == 'equal':
            changes.append({
                'type': 'equal',
                'text': ''.join(original_words[i1:i2])
            })
    return changes

    elif option == "Clean Up Norwegian Text":
    st.header("Clean Up Norwegian Text")
    
    if 'final_text' not in st.session_state:
        st.session_state.final_text = ''
    
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
                    "content": f"Please proofread and correct the following Norwegian text. Only provide the corrected version without explanations:\n\n{norwegian_text}"
                }],
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1000,
                "temperature": 0.7
            }

            response = requests.post(API_ENDPOINT, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                suggested_text = result["content"][0]["text"]
                
                changes = get_word_diffs(norwegian_text, suggested_text)
                
                st.subheader("Review Changes:")
                
                final_text = norwegian_text
                
                for i, change in enumerate(changes):
                    if change['type'] == 'equal':
                        st.write(change['text'], end='')
                    else:
                        col1, col2, col3 = st.columns([2,2,1])
                        
                        if change['type'] in ['change', 'deletion']:
                            with col1:
                                st.markdown(f"**Original:** _{change['original']}_")
                                
                        if change['type'] in ['change', 'insertion']:
                            with col2:
                                st.markdown(f"**Suggested:** _{change['suggested']}_")
                        
                        with col3:
                            key = f"change_{i}"
                            if st.button("Accept", key=f"accept_{i}"):
                                final_text = final_text.replace(
                                    change['original'] if change['type'] != 'insertion' else '',
                                    change['suggested']
                                )
                                st.session_state.final_text = final_text
                            
                            if st.button("Decline", key=f"decline_{i}"):
                                st.session_state.final_text = final_text
                
                st.subheader("Final Text:")
                st.write(st.session_state.final_text or final_text)
            else:
                error_info = response.json().get('error', {})
                error_message = error_info.get('message', 'An unknown error occurred.')
                st.error(f"Error: {response.status_code} - {error_message}")
