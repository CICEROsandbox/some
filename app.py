import streamlit as st
import requests
import difflib
import re
import os
import json
from datetime import datetime

API_KEY = os.getenv("CLAUDE_API_KEY") or st.secrets["API_KEY"]
API_ENDPOINT = "https://api.anthropic.com/v1/messages"

REFERENCE_SITES = [
    "https://www.miljodirektoratet.no/ansvarsomrader/klima/fns-klimapanel-ipcc/dette-sier-fns-klimapanel/klimabegreper-pa-norsk/",
    "https://www.ipcc.ch/glossary/",
    "https://unfccc.int/process-and-meetings/the-convention/glossary-of-climate-change-acronyms-and-terms"
]

class TranslationQuality:
    def __init__(self):
        self.reference_sites = REFERENCE_SITES  # Use your existing REFERENCE_SITES
        
        # Extend your existing technical terms with more metadata
        self.technical_terms = {
            "klimaendringer": {
                "english": "climate change",
                "source": "Miljødirektoratet",
                "context": "General term for climate change",
                "reference": self.reference_sites[0]
            },
            "klimatilpasning": {
                "english": "climate adaptation",
                "source": "IPCC",
                "context": "Adaptation to climate change",
                "reference": self.reference_sites[1]
            },
            # Add your existing terms with metadata
            "utslippsreduksjon": {
                "english": "emission reduction",
                "source": "Miljødirektoratet",
                "context": "Used in mitigation contexts",
                "reference": self.reference_sites[0]
            },
            "klimafinansiering": {
                "english": "climate finance",
                "source": "UNFCCC",
                "context": "Financial flows related to climate action",
                "reference": self.reference_sites[2]
            },
            "karbonbudsjett": {
                "english": "carbon budget",
                "source": "IPCC",
                "context": "Remaining carbon emissions allowance",
                "reference": self.reference_sites[1]
            }
        }

# Initialize session state for translation memory
if 'translation_memory' not in st.session_state:
    st.session_state.translation_memory = {}

def load_technical_terms():
    """Load technical terms and their translations."""
    return {
        "klimaendringer": "climate change",
        "klimatilpasning": "climate adaptation",
        "utslippsreduksjon": "emission reduction",
        "klimafinansiering": "climate finance",
        "karbonbudsjett": "carbon budget",
        # Add more terms as needed
    }

 def validate_translation(self, original: str, translated: str, direction: str) -> List[Dict]:
        """Enhanced validation that includes your existing checks plus new ones."""
        issues = []
        
        # Your existing technical term checks
        if direction == "no-to-en":
            for term, details in self.technical_terms.items():
                if term.lower() in original.lower() and details['english'].lower() not in translated.text.lower():
                    issues.append({
                        'type': 'technical_term',
                        'severity': 'high',
                        'message': f"Warning: '{term}' might not be correctly translated as '{details['english']}'",
                        'source': details['source'],
                        'reference': details['reference']
                    })
        
        # Your existing formatting checks
        if len(translated.split()) < len(original.split()) * 0.5:
            issues.append({
                'type': 'formatting',
                'severity': 'medium',
                'message': "Warning: Translation appears too short"
            })
        
        # Your existing Norwegian character check
        if direction == "no-to-en":
            norwegian_chars = set('æøåÆØÅ')
            if any(char in translated for char in norwegian_chars):
                issues.append({
                    'type': 'formatting',
                    'severity': 'high',
                    'message': "Warning: Some Norwegian characters remain in the translation"
                })
        
        return issues

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

def update_translation_memory(original, translated, direction):
    """Update translation memory with new translations."""
    key = f"{original.strip().lower()}_{direction}"
    if key not in st.session_state.translation_memory:
        st.session_state.translation_memory[key] = {
            'translation': translated,
            'timestamp': datetime.now().isoformat(),
            'direction': direction
        }

def get_from_translation_memory(text, direction):
    """Retrieve translation from memory if available."""
    key = f"{text.strip().lower()}_{direction}"
    if key in st.session_state.translation_memory:
        return st.session_state.translation_memory[key]['translation']
    return None

def translate_with_context(text, direction, sources):
    # Initialize quality checker
    quality_checker = TranslationQuality()
    
    # First check translation memory (keep your existing code)
    cached_translation = get_from_translation_memory(text, direction)
    if cached_translation:
        st.info("Retrieved from translation memory")
        return {'status_code': 200, 'content': [{'text': cached_translation}]}

    # Your existing translation code...
    response = requests.post(API_ENDPOINT, headers=headers, json=payload)
    
if response.status_code == 200:
    result = response.json()
    translated_text = result["content"][0]["text"]
    
    # Display validation results with severity levels
    if 'validation' in result and result['validation']:
        with st.expander("Translation Quality Check"):
            for issue in result['validation']:
                severity_icon = "🔴" if issue['severity'] == 'high' else "🟡" if issue['severity'] == 'medium' else "🔵"
                st.write(f"{severity_icon} {issue['message']}")
                if 'source' in issue:
                    st.write(f"Source: {issue['source']}")
                if 'reference' in issue:
                    st.write(f"Reference: {issue['reference']}")
    
    st.subheader("Translated text:")
    st.write(translated_text)

    if direction == "no-to-en":
        prompt_template = """You are a specialist in translating climate negotiation texts from Norwegian to English. Your task is to:

        1. First check the reference pages for how similar concepts and expressions are translated:
        {sources}

        2. For technical terms:
        - Use established English translations from authoritative sources
        - For terms without direct translations, describe the concept in English and keep Norwegian term in parentheses
        - When multiple translations exist, use the most widely accepted one
        - Maintain consistency with IPCC and UNFCCC terminology

        3. Focus on conveying the same meaning as the original text, not word-for-word translation

        4. Ensure the translation:
        - Uses appropriate formal language for climate negotiations
        - Maintains technical precision
        - Follows standard English capitalization and punctuation rules
        - Preserves any specific references to Norwegian policies or institutions

        Translate this text from Norwegian to English:
        {text}

        Note: Pay special attention to how technical terms are used in IPCC reports and UNFCCC documents."""
    else:
        prompt_template = """Du er en spesialist i å oversette klimaforhandlingstekster fra engelsk til norsk. Din oppgave er å:

        1. Først sjekke referansesidene for hvordan lignende begreper og uttrykk er oversatt:
        {sources}

        2. For tekniske termer:
        - Bruk etablerte norske oversettelser fra referansesidene
        - For termer som ikke finnes i kildene, beskriv konseptet på norsk og behold engelsk term i parentes
        - Ved flere brukte oversettelser, vis alternativene

        3. Fokuser på å formidle samme mening som i originalteksten, ikke ord-for-ord oversettelse

        Oversett denne teksten:
        {text}

        Tips: Se spesielt etter hvordan Miljødirektoratet og Regjeringen formulerer lignende konsepter."""

    headers = {
        "anthropic-version": "2023-06-01",
        "x-api-key": API_KEY,
        "content-type": "application/json",
    }

    payload = {
        "messages": [{
            "role": "user",
            "content": prompt_template.format(
                sources="\n".join(f"- {source}" for source in sources),
                text=text
            )
        }],
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1000,
        "temperature": 0.3  # Lower temperature for more consistent translations
    }

    response = requests.post(API_ENDPOINT, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        translated_text = result["content"][0]["text"]
        update_translation_memory(text, translated_text, direction)
        
    return response

def review_norwegian_text(text):
    """Review and correct Norwegian text."""
    headers = {
        "anthropic-version": "2023-06-01",
        "x-api-key": API_KEY,
        "content-type": "application/json",
    }

    prompt = """Du er en ekspert på norsk klimaterminologi. 
    Korriger følgende tekst med fokus på:
    - Presist og korrekt fagspråk i klimaforhandlinger
    - Konsistent bruk av tekniske termer
    - Korrekt grammatikk og tegnsetting
    - Formelt språk passende for offisielle dokumenter
    
    Gi kun korrigert versjon uten forklaringer.
    Behold tekniske termer som er korrekte.

    {text}"""

    payload = {
        "messages": [{
            "role": "user",
            "content": prompt.format(text=text)
        }],
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1000,
        "temperature": 0.3
    }

    return requests.post(API_ENDPOINT, headers=headers, json=payload)

# Streamlit UI
st.title("Climate Negotiations Translator")

# Sidebar with translation memory stats
with st.sidebar:
    st.subheader("Translation Memory Stats")
    st.write(f"Cached translations: {len(st.session_state.translation_memory)}")
    if st.button("Clear Translation Memory"):
        st.session_state.translation_memory = {}
        st.success("Translation memory cleared!")

option = st.sidebar.selectbox(
    "Select function:",
    ("Norwegian to English", "English to Norwegian", "Norwegian Text Review")
)

if option in ["Norwegian to English", "English to Norwegian"]:
    st.header(option)
    
    with st.expander("Reference Sources"):
        st.write("The translation uses terminology from the following sources:")
        for site in REFERENCE_SITES:
            st.write(f"- {site}")
    
    input_text = st.text_area(
        "Enter text to translate:",
        placeholder="Enter the text you want to translate..."
    )

    if st.button("Translate"):
        if input_text.strip() == "":
            st.warning("Please enter text to translate.")
        else:
            with st.spinner('Translating...'):
                direction = "no-to-en" if option == "Norwegian to English" else "en-to-no"
                response = translate_with_context(input_text, direction, REFERENCE_SITES)
                
                if response.status_code == 200:
                    result = response.json()
                    translated_text = result["content"][0]["text"]
                    
                    # Validate translation
                    issues = validate_translation(input_text, translated_text, direction)
                    if issues:
                        st.warning("Potential translation issues:")
                        for issue in issues:
                            st.write(f"- {issue}")
                    
                    st.subheader("Translated text:")
                    st.write(translated_text)
                    
                    # Show technical terms used
                    with st.expander("Technical Terms Used"):
                        terms = load_technical_terms()
                        used_terms = [term for term in terms.keys() if term.lower() in input_text.lower()]
                        if used_terms:
                            st.write("Technical terms identified:")
                            for term in used_terms:
                                st.write(f"- {term} → {terms[term]}")
                else:
                    error_info = response.json().get('error', {})
                    error_message = error_info.get('message', 'An unknown error occurred.')
                    st.error(f"Error: {response.status_code} - {error_message}")

elif option == "Norwegian Text Review":
    st.header("Norwegian Text Review")
    
    if 'final_text' not in st.session_state:
        st.session_state.final_text = ''
    
    norwegian_text = st.text_area("Enter text for review:")

    if st.button("Review"):
        if norwegian_text.strip() == "":
            st.warning("Please enter text for review.")
        else:
            with st.spinner('Reviewing...'):
                response = review_norwegian_text(norwegian_text)
                
                if response.status_code == 200:
                    result = response.json()
                    suggested_text = result["content"][0]["text"]
                    
                    changes = get_word_diffs(norwegian_text, suggested_text)
                    
                    st.subheader("Review changes:")
                    
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
                                if st.button("Accept", key=f"accept_{i}"):
                                    final_text = final_text.replace(
                                        change['original'] if change['type'] != 'insertion' else '',
                                        change['suggested']
                                    )
                                    st.session_state.final_text = final_text
                                
                                if st.button("Reject", key=f"decline_{i}"):
                                    st.session_state.final_text = final_text
                    
                    st.subheader("Final text:")
                    st.write(st.session_state.final_text or final_text)
                else:
                    error_info = response.json().get('error', {})
                    error_message = error_info.get('message', 'An unknown error occurred.')
                    st.error(f"Error: {response.status_code} - {error_message}")
