import streamlit as st
import requests
import difflib
import re
import os

API_KEY = os.getenv("CLAUDE_API_KEY") or st.secrets["API_KEY"]
API_ENDPOINT = "https://api.anthropic.com/v1/messages"

st.title("Klimaforhandlinger Oversetter")

option = st.sidebar.selectbox(
    "Velg funksjon:",
    ("Oversett Engelsk til Norsk", "Korrektur Norsk Tekst")
)

if option == "Oversett Engelsk til Norsk":
    st.header("Oversett Engelsk til Norsk")
    english_text = st.text_area("Skriv inn engelsk tekst:")

    if st.button("Oversett"):
        if english_text.strip() == "":
            st.warning("Vennligst skriv inn tekst som skal oversettes.")
        else:
            headers = {
                "anthropic-version": "2023-06-01",
                "x-api-key": API_KEY,
                "content-type": "application/json",
            }

            prompt = """Du er en ekspert på å oversette klimaforhandlingstekster fra engelsk til norsk. 
            Vær spesielt oppmerksom på tekniske termer og etablerte uttrykk innen klimapolitikk.
            Hvis det finnes flere mulige oversettelser eller hvis noen termer mangler etablerte norske oversettelser, 
            inkluder dette i parentes etter ordet. Oversett følgende tekst:

            {text}"""

            payload = {
                "messages": [{
                    "role": "user",
                    "content": prompt.format(text=english_text)
                }],
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 1000,
                "temperature": 0.7
            }

            response = requests.post(API_ENDPOINT, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                translated_text = result["content"][0]["text"]
                st.subheader("Oversatt tekst:")
                st.write(translated_text)
            else:
                error_info = response.json().get('error', {})
                error_message = error_info.get('message', 'En ukjent feil oppstod.')
                st.error(f"Feil: {response.status_code} - {error_message}")

def get_word_diffs(original, suggested):
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

elif option == "Korrektur Norsk Tekst":
    st.header("Korrektur Norsk Tekst")
    
    if 'final_text' not in st.session_state:
        st.session_state.final_text = ''
    
    norwegian_text = st.text_area("Skriv inn tekst som skal korrekturleses:")

    if st.button("Korriger"):
        if norwegian_text.strip() == "":
            st.warning("Vennligst skriv inn tekst som skal korrekturleses.")
        else:
            headers = {
                "anthropic-version": "2023-06-01",
                "x-api-key": API_KEY,
                "content-type": "application/json",
            }

            payload = {
                "messages": [{
                    "role": "user",
                    "content": f"Korriger følgende norske tekst med fokus på klimaforhandlingsterminologi. Gi kun korrigert versjon uten forklaringer:\n\n{norwegian_text}"
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
                
                st.subheader("Gjennomgå endringer:")
                
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
                                st.markdown(f"**Foreslått:** _{change['suggested']}_")
                        
                        with col3:
                            key = f"change_{i}"
                            if st.button("Godta", key=f"accept_{i}"):
                                final_text = final_text.replace(
                                    change['original'] if change['type'] != 'insertion' else '',
                                    change['suggested']
                                )
                                st.session_state.final_text = final_text
                            
                            if st.button("Avslå", key=f"decline_{i}"):
                                st.session_state.final_text = final_text
                
                st.subheader("Endelig tekst:")
                st.write(st.session_state.final_text or final_text)
            else:
                error_info = response.json().get('error', {})
                error_message = error_info.get('message', 'En ukjent feil oppstod.')
                st.error(f"Feil: {response.status_code} - {error_message}")
