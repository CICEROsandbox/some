# Part 1: Imports, Configuration, and Core Classes

import streamlit as st
import requests
import difflib
import re
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple

# API Configuration
API_KEY = os.getenv("CLAUDE_API_KEY") or st.secrets["API_KEY"]
API_ENDPOINT = "https://api.anthropic.com/v1/messages"

# Reference Sources
REFERENCE_SITES = [
    "https://www.miljodirektoratet.no/ansvarsomrader/klima/fns-klimapanel-ipcc/dette-sier-fns-klimapanel/klimabegreper-pa-norsk/",
    "https://www.ipcc.ch/glossary/",
    "https://unfccc.int/process-and-meetings/the-convention/glossary-of-climate-change-acronyms-and-terms"
]

# Initialize session state
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
    }

class TranslationQuality:
    def __init__(self):
        self.reference_sites = REFERENCE_SITES
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

    def validate_translation(self, original: str, translated: str, direction: str) -> List[Dict]:
        """Enhanced validation that includes existing checks plus new ones."""
        issues = []
        
        # Technical term checks
        if direction == "no-to-en":
            for term, details in self.technical_terms.items():
                if term.lower() in original.lower() and details['english'].lower() not in translated.lower():
                    issues.append({
                        'type': 'technical_term',
                        'severity': 'high',
                        'message': f"Warning: '{term}' might not be correctly translated as '{details['english']}'",
                        'source': details['source'],
                        'reference': details['reference']
                    })
        
        # Formatting checks
        if len(translated.split()) < len(original.split()) * 0.5:
            issues.append({
                'type': 'formatting',
                'severity': 'medium',
                'message': "Warning: Translation appears too short"
            })
        
        # Norwegian character check
        if direction == "no-to-en":
            norwegian_chars = set('æøåÆØÅ')
            if any(char in translated for char in norwegian_chars):
                issues.append({
                    'type': 'formatting',
                    'severity': 'high',
                    'message': "Warning: Some Norwegian characters remain in the translation"
                })
        
        return issues

# Part 2: Translation Memory and Core Translation Functions

def get_word_diffs(original: str, suggested: str) -> List[Dict]:
    """Get word-level differences between original and suggested texts."""
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

def update_translation_memory(original: str, translated: str, direction: str) -> None:
    """Update translation memory with new translations."""
    key = f"{original.strip().lower()}_{direction}"
    if key not in st.session_state.translation_memory:
        st.session_state.translation_memory[key] = {
            'translation': translated,
            'timestamp': datetime.now().isoformat(),
            'direction': direction
        }

def get_from_translation_memory(text: str, direction: str) -> str:
    """Retrieve translation from memory if available."""
    key = f"{text.strip().lower()}_{direction}"
    if key in st.session_state.translation_memory:
        return st.session_state.translation_memory[key]['translation']
    return None

def translate_with_context(text: str, direction: str, sources: List[str]) -> Dict:
    """
    Translate text with context while checking quality and terminology.
    """
    quality_checker = TranslationQuality()
    
    # First check translation memory
    cached_translation = get_from_translation_memory(text, direction)
    if cached_translation:
        st.info("Retrieved from translation memory")
        return {'status_code': 200, 'content': [{'text': cached_translation}]}

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
        "temperature": 0.3
    }

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            translated_text = result["content"][0]["text"]
            
            # Validate translation using our quality checker
            validation_results = quality_checker.validate_translation(text, translated_text, direction)
            
            # Update translation memory
            update_translation_memory(text, translated_text, direction)
            
            # Create a modified response that includes both translation and validation
            return {
                'status_code': 200,
                'content': [{'text': translated_text}],
                'validation': validation_results
            }
        else:
            return {
                'status_code': response.status_code,
                'error': {'message': f"API error: {response.text}"}
            }
    except Exception as e:
        return {
            'status_code': 500,
            'error': {'message': f"Translation error: {str(e)}"}
        }

def review_norwegian_text(text: str) -> Dict:
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

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        return response.json() if response.status_code == 200 else {
            'status_code': response.status_code,
            'error': {'message': f"Review error: {response.text}"}
        }
    except Exception as e:
        return {
            'status_code': 500,
            'error': {'message': f"Review error: {str(e)}"}
        }

def render_translation_ui():
    """Render the translation interface with side-by-side comparison and editable results."""
    st.header("Translation")
    
    # Initialize session states if they don't exist
    if 'translation_result' not in st.session_state:
        st.session_state.translation_result = ""
        st.session_state.original_translation = ""
        st.session_state.last_response = None  # Store the last translation response
    
    with st.expander("Reference Sources"):
        st.write("The translation uses terminology from the following sources:")
        for site in REFERENCE_SITES:
            st.write(f"- {site}")
    
    # Create two columns for side-by-side view
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Text")
        input_text = st.text_area(
            "Enter text to translate:",
            placeholder="Enter the text you want to translate...",
            height=300,
            key="input_text"
        )

    with col2:
        st.subheader("Translation")
        # Editable translation area
        edited_translation = st.text_area(
            "Translated text (editable):",
            value=st.session_state.translation_result,
            height=300,
            key="edited_translation"
        )
        
        # Update session state with edited translation
        st.session_state.translation_result = edited_translation
        
        # Show edit indicator if translation has been modified
        if (st.session_state.get('original_translation') and 
            st.session_state.original_translation != edited_translation):
            st.caption("✏️ Translation has been edited")
    
    # Put the translate button below both columns
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Translate", type="primary"):
            if input_text.strip() == "":
                st.warning("Please enter text to translate.")
            else:
                with st.spinner('Translating...'):
                    option = st.session_state.get('current_option', 'Norwegian to English')
                    direction = "no-to-en" if option == "Norwegian to English" else "en-to-no"
                    response = translate_with_context(input_text, direction, REFERENCE_SITES)
                    
                    if response.get('status_code') == 200:
                        translated_text = response['content'][0]['text']
                        st.session_state.translation_result = translated_text
                        st.session_state.original_translation = translated_text
                        st.session_state.last_response = response  # Store the response
                        st.rerun()
                    else:
                        error_info = response.get('error', {})
                        error_message = error_info.get('message', 'An unknown error occurred.')
                        st.error(f"Error: {response.get('status_code')} - {error_message}")
    
    with col2:
        if st.button("Reset Translation"):
            if st.session_state.get('original_translation'):
                st.session_state.translation_result = st.session_state.original_translation
                st.rerun()
    
    with col3:
        if st.button("Clear All"):
            st.session_state.translation_result = ""
            st.session_state.original_translation = ""
            st.session_state.last_response = None
            st.session_state.input_text = ""
            st.rerun()
    
    # Create a separate section for feedback and analysis
    if st.session_state.translation_result and st.session_state.last_response:
        with st.expander("Translation Analysis", expanded=True):
            # Display validation results with severity levels
            if 'validation' in st.session_state.last_response:
                st.subheader("Quality Check Results")
                for issue in st.session_state.last_response['validation']:
                    severity_icon = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🔵'
                    }.get(issue['severity'], '🔵')
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.write(severity_icon)
                    with col2:
                        st.markdown(f"**{issue['type'].title()}:** {issue['message']}")
                        if 'source' in issue:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Source:* {issue['source']}")
                        if 'reference' in issue:
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;*Reference:* [{issue['source']}]({issue['reference']})")
            
            # Show technical terms in a more organized way
            st.subheader("Technical Terms Analysis")
            quality_checker = TranslationQuality()
            terms = quality_checker.technical_terms
            used_terms = [term for term in terms.keys() if term.lower() in input_text.lower()]
            
            if used_terms:
                for term in used_terms:
                    term_info = terms[term]
                    with st.container():
                        cols = st.columns([2, 2, 3])
                        with cols[0]:
                            st.markdown(f"**{term}**")
                        with cols[1]:
                            st.markdown(f"→ {term_info['english']}")
                        with cols[2]:
                            st.markdown(f"*{term_info['context']}*")
            else:
                st.info("No technical terms were identified in the text.")
            
            # Add copy buttons for convenience
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Copy Original"):
                    st.write("Original text copied to clipboard!")
                    st.clipboard(input_text)
            with col2:
                if st.button("Copy Translation"):
                    st.write("Translation copied to clipboard!")
                    st.clipboard(st.session_state.translation_result)

    # Display memory cache info in a subtle way
    if st.session_state.get('translation_result'):
        st.markdown("---")
        st.caption("💾 Translation saved to memory cache")

def render_sidebar():
    """Render the sidebar with translation memory stats and options."""
    with st.sidebar:
        st.subheader("Translation Memory Stats")
        st.write(f"Cached translations: {len(st.session_state.translation_memory)}")
        if st.button("Clear Translation Memory"):
            st.session_state.translation_memory = {}
            st.success("Translation memory cleared!")

        st.session_state.current_option = st.selectbox(
            "Select function:",
            ("Norwegian to English", "English to Norwegian", "Norwegian Text Review")
        )

def initialize_app():
    """Initialize the application state and configurations."""
    st.set_page_config(
        page_title="Climate Negotiations Translator",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session states if they don't exist
    if 'current_option' not in st.session_state:
        st.session_state.current_option = "Norwegian to English"
    
    if 'final_text' not in st.session_state:
        st.session_state.final_text = ""

    # Set up any required environment variables or configurations
    if not API_KEY:
        st.error("API key not found. Please set the CLAUDE_API_KEY environment variable or add it to your secrets.")
        st.stop()

def display_usage_stats():
    """Display usage statistics in the sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.subheader("Usage Statistics")
        total_translations = len(st.session_state.translation_memory)
        st.metric("Total Translations", total_translations)
        
        # Calculate success rate
        if hasattr(st.session_state, 'translation_attempts'):
            success_rate = (total_translations / st.session_state.translation_attempts) * 100
            st.metric("Success Rate", f"{success_rate:.1f}%")

def main():
    """Main application entry point."""
    try:
        # Initialize the application
        initialize_app()

        # Main title
        st.title("Climate Negotiations Translator")
        
        # Render sidebar
        render_sidebar()
        
        # Display usage statistics
        display_usage_stats()

        # Main content area
        if st.session_state.current_option in ["Norwegian to English", "English to Norwegian"]:
            render_translation_ui()
        else:
            render_review_ui()

    except Exception as e:
        st.error(f"An unexpected error occurred: {str(e)}")
        if st.checkbox("Show error details"):
            st.exception(e)

def handle_keyboard_shortcuts():
    """Handle keyboard shortcuts for the application."""
    # This can be expanded based on needs
    pass

# Add any cleanup or shutdown handlers
def cleanup():
    """Perform any necessary cleanup when the application shuts down."""
    # This can be expanded based on needs
    pass

# Error tracking (optional, for production use)
def log_error(error: Exception, context: str = None):
    """Log errors for monitoring and debugging."""
    timestamp = datetime.now().isoformat()
    error_log = {
        'timestamp': timestamp,
        'error': str(error),
        'type': type(error).__name__,
        'context': context
    }
    
    # In a production environment, you might want to send this to a logging service
    print(f"Error occurred: {error_log}")  # Replace with proper logging

# Development helper functions
def debug_mode():
    """Enable debug mode with additional logging and information."""
    if st.sidebar.checkbox("Enable Debug Mode"):
        st.sidebar.markdown("---")
        st.sidebar.subheader("Debug Information")
        st.sidebar.json(st.session_state.to_dict())

# Entry point of the application
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(e, "Application startup")
        st.error("The application failed to start. Please try refreshing the page.")
    finally:
        cleanup()
