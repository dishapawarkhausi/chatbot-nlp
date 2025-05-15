import streamlit as st
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
import re
import string
import plotly.express as px
import pandas as pd
from datetime import datetime
import speech_recognition as sr
import pyttsx3
import pyjokes
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
import logging
import webbrowser
import sys
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def ensure_nltk_data():
    """Ensure NLTK data is available in the correct location for production."""
    try:
        # Create a temporary directory for NLTK data if it doesn't exist
        nltk_data_dir = os.path.join(tempfile.gettempdir(), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        
        # Set NLTK data path
        nltk.data.path.append(nltk_data_dir)
        
        # Required NLTK packages with their correct paths
        required_packages = {
            'punkt': 'tokenizers/punkt',
            'stopwords': 'corpora/stopwords',
            'wordnet': 'corpora/wordnet',
            'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger'
        }
        
        def verify_wordnet():
            """Verify WordNet is properly initialized."""
            try:
                from nltk.corpus import wordnet
                # Try to access a known synset to verify WordNet is working
                test_synset = wordnet.synsets('test')[0]
                return True
            except Exception as e:
                logger.error(f"WordNet verification failed: {str(e)}")
                return False
        
        # Download each package if not present
        for package, path in required_packages.items():
            try:
                # Special handling for wordnet
                if package == 'wordnet':
                    if verify_wordnet():
                        logger.info("WordNet is already downloaded and initialized")
                        continue
                
                # Check if package is already downloaded
                nltk.data.find(path)
                logger.info(f"Package {package} already downloaded")
            except LookupError:
                try:
                    # Download package to the temporary directory
                    nltk.download(package, download_dir=nltk_data_dir, quiet=True)
                    logger.info(f"Successfully downloaded NLTK package: {package}")
                    
                    # Special handling for wordnet after download
                    if package == 'wordnet':
                        if not verify_wordnet():
                            raise Exception("WordNet downloaded but not properly initialized")
                            
                except Exception as e:
                    logger.error(f"Error downloading NLTK package {package}: {str(e)}")
                    st.error(f"Error downloading required NLTK data: {package}. Please try again.")
                    # Try alternative download method
                    try:
                        nltk.download(package, quiet=True)
                        logger.info(f"Successfully downloaded {package} using alternative method")
                        
                        # Special handling for wordnet after alternative download
                        if package == 'wordnet':
                            if not verify_wordnet():
                                raise Exception("WordNet downloaded but not properly initialized")
                                
                    except Exception as e2:
                        logger.error(f"Alternative download failed for {package}: {str(e2)}")
                        st.error(f"Failed to download {package} using both methods. Please contact support.")
        
        # Final verification of all packages
        for package, path in required_packages.items():
            try:
                if package == 'wordnet':
                    if not verify_wordnet():
                        raise Exception("WordNet not properly initialized")
                else:
                    nltk.data.find(path)
            except Exception as e:
                logger.error(f"Package {package} not found or not properly initialized: {str(e)}")
                st.error(f"Critical error: Required NLTK package {package} is not available.")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Critical error in NLTK data setup: {str(e)}")
        st.error("Critical error in setting up NLTK data. Please contact support.")
        sys.exit(1)

# Call the ensure_nltk_data function at startup
ensure_nltk_data()

# Initialize session states
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'sentiment_history' not in st.session_state:
    st.session_state.sentiment_history = []
if 'intent_history' not in st.session_state:
    st.session_state.intent_history = []
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = False
if 'is_listening' not in st.session_state:
    st.session_state.is_listening = False
if 'conversation_context' not in st.session_state:
    st.session_state.conversation_context = []

# Initialize text-to-speech engine
def init_tts_engine():
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.9)
    return engine

def get_joke() -> str:
    """Get a random joke."""
    return pyjokes.get_joke()

def speak_text(text: str) -> None:
    """Convert text to speech using a new engine instance."""
    if st.session_state.voice_enabled:
        try:
            engine = init_tts_engine()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            logger.error(f"Text-to-speech error: {str(e)}")
            st.error(f"Error in text-to-speech: {str(e)}")

def listen_to_speech() -> str:
    """Listen to user's speech and convert to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.session_state.is_listening = True
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            st.session_state.is_listening = False
            return text
        except sr.WaitTimeoutError:
            st.session_state.is_listening = False
            return "No speech detected"
        except sr.UnknownValueError:
            st.session_state.is_listening = False
            return "Could not understand audio"
        except Exception as e:
            logger.error(f"Speech recognition error: {str(e)}")
            st.session_state.is_listening = False
            return f"Error: {str(e)}"

def preprocess_text(text: str) -> List[str]:
    """Enhanced text preprocessing."""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    return tokens

def analyze_sentiment(text: str) -> tuple:
    """Analyze sentiment of the text."""
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    subjectivity = analysis.sentiment.subjectivity
    
    if polarity > 0.1:
        sentiment = "Positive"
    elif polarity < -0.1:
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
    
    return sentiment, polarity, subjectivity

# Website dictionary with categories
WEBSITES = {
    'search': {
        'google': 'https://www.google.com',
        'bing': 'https://www.bing.com',
        'duckduckgo': 'https://duckduckgo.com'
    },
    'social': {
        'linkedin': 'https://www.linkedin.com',
        'twitter': 'https://www.twitter.com',
        'facebook': 'https://www.facebook.com',
        'instagram': 'https://www.instagram.com'
    },
    'development': {
        'github': 'https://www.github.com',
        'stackoverflow': 'https://www.stackoverflow.com',
        'medium': 'https://www.medium.com',
        'dev.to': 'https://dev.to'
    },
    'entertainment': {
        'youtube': 'https://www.youtube.com',
        'netflix': 'https://www.netflix.com',
        'spotify': 'https://www.spotify.com'
    },
    'shopping': {
        'amazon': 'https://www.amazon.com',
        'ebay': 'https://www.ebay.com'
    },
    'utilities': {
        'gmail': 'https://mail.google.com',
        'wikipedia': 'https://www.wikipedia.org',
        'reddit': 'https://www.reddit.com'
    }
}

def open_website(site_name: str) -> str:
    """Open a website in the default browser."""
    site_name = site_name.lower()
    
    # Search through all categories
    for category, sites in WEBSITES.items():
        if site_name in sites:
            try:
                webbrowser.open(sites[site_name])
                return f"I've opened {site_name.capitalize()} for you."
            except Exception as e:
                logger.error(f"Error opening website: {str(e)}")
                return f"I encountered an error while trying to open {site_name}."
    
    return f"I'm not sure how to open {site_name}. You can ask me to open any of these categories: search, social, development, entertainment, shopping, or utilities."

def get_website_categories() -> str:
    """Get a formatted string of website categories and their sites."""
    categories = []
    for category, sites in WEBSITES.items():
        sites_list = ", ".join(sites.keys())
        categories.append(f"{category.capitalize()}: {sites_list}")
    return "\n".join(categories)

def get_response(user_input: str) -> tuple:
    """Enhanced response generation with more patterns and context awareness."""
    tokens = preprocess_text(user_input)
    sentiment, polarity, subjectivity = analyze_sentiment(user_input)
    
    # Update conversation context
    st.session_state.conversation_context.append({"role": "user", "content": user_input})
    
    # Define patterns and responses
    patterns = {
        'greeting': {
            'keywords': ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening'],
            'response': "Hello! I'm your AI assistant. How can I help you today?"
        },
        'nlp_question': {
            'keywords': ['what', 'nlp', 'natural', 'language', 'processing'],
            'response': "Natural Language Processing (NLP) is a branch of artificial intelligence that enables computers to understand, interpret, and generate human language. It combines computational linguistics, machine learning, and deep learning to process and analyze large amounts of natural language data."
        },
        'capabilities': {
            'keywords': ['what', 'can', 'you', 'do', 'help', 'capabilities', 'features'],
            'response': """I can assist you with:
- Natural Language Processing and AI discussions
- Sentiment analysis of text
- Programming jokes
- Voice interaction
- Contextual conversation
- Data analysis and visualization
- Professional assistance and guidance
- Web browsing and navigation"""
        },
        'goodbye': {
            'keywords': ['bye', 'goodbye', 'see', 'later', 'exit', 'quit'],
            'response': "Thank you for chatting with me. Have a great day!"
        },
        'thanks': {
            'keywords': ['thank', 'thanks', 'appreciate', 'grateful'],
            'response': "You're welcome! Is there anything else I can assist you with?"
        },
        'time': {
            'keywords': ['time', 'current time', 'what time'],
            'response': f"The current time is {datetime.now().strftime('%H:%M:%S')}"
        },
        'date': {
            'keywords': ['date', 'today', 'what day'],
            'response': f"Today is {datetime.now().strftime('%B %d, %Y')}"
        },
        'joke': {
            'keywords': ['joke', 'funny', 'humor', 'laugh', 'tell me a joke'],
            'response': get_joke
        },
        'website': {
            'keywords': ['open', 'go to', 'visit', 'browse', 'website', 'site'] + 
                       [site for category in WEBSITES.values() for site in category.keys()],
            'response': lambda: open_website(next((site for category in WEBSITES.values() 
                                                 for site in category.keys() 
                                                 if site in tokens), 'google'))
        },
        'list_websites': {
            'keywords': ['list', 'show', 'what', 'websites', 'sites', 'available'],
            'response': lambda: f"I can help you access these websites:\n\n{get_website_categories()}"
        }
    }
    
    # Check for pattern matches
    matched_intent = None
    response = None
    
    for intent, data in patterns.items():
        if any(keyword in tokens for keyword in data['keywords']):
            matched_intent = intent
            if callable(data['response']):
                response = data['response']()
            else:
                response = data['response']
            break
    
    if not matched_intent:
        response = "I understand you're asking about something. Could you please provide more context or rephrase your question?"
        matched_intent = "unknown"
    
    # Update conversation context
    st.session_state.conversation_context.append({"role": "assistant", "content": response})
    
    return response, matched_intent, sentiment, polarity, subjectivity

# Set up the Streamlit interface
st.set_page_config(
    page_title="ChatBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background-color: #000000;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #1E1E1E;
        color: white;
        border: 1px solid #333;
    }
    .stButton>button:hover {
        background-color: #2E2E2E;
        border-color: #444;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #1E1E1E;
        color: white;
        border: 1px solid #333;
    }
    .chat-message.bot {
        background-color: #2B2B2B;
        color: white;
        border: 1px solid #444;
    }
    .stTextInput>div>div>input {
        background-color: #1E1E1E;
        color: white;
        border: 1px solid #333;
    }
    .stTextInput>div>div>input:focus {
        border-color: #444;
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🤖 ChatBot")
st.write("Welcome! I'm your professional chatbot, ready to help with your queries.")

# Create three columns for the layout
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    # Voice settings
    voice_col1, voice_col2 = st.columns(2)
    with voice_col1:
        st.session_state.voice_enabled = st.checkbox("Enable Voice Output", value=False)
    with voice_col2:
        if st.button("🎤 Voice Input"):
            with st.spinner("Listening..."):
                voice_input = listen_to_speech()
                if voice_input and voice_input != "No speech detected":
                    st.session_state.user_input = voice_input
    
    # Chat interface
    user_input = st.text_input("Type your message here...", key="user_input")
    
    # Clear chat history button
    if st.button("🗑️ Clear Conversation"):
        st.session_state.chat_history = []
        st.session_state.sentiment_history = []
        st.session_state.intent_history = []
        st.session_state.conversation_context = []
        st.experimental_rerun()
    
    # Process input when user submits
    if user_input:
        # Get bot response
        response, intent, sentiment, polarity, subjectivity = get_response(user_input)
        
        # Speak the response if voice is enabled
        speak_text(response)
        
        # Update histories
        st.session_state.chat_history.append({
            "user": user_input,
            "bot": response,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        st.session_state.sentiment_history.append({
            "text": user_input,
            "sentiment": sentiment,
            "polarity": polarity,
            "subjectivity": subjectivity
        })
        st.session_state.intent_history.append(intent)
    
    # Display chat history
    st.subheader("Conversation History")
    for message in st.session_state.chat_history:
        st.markdown(f"""
            <div class="chat-message user">
                <div>👤 You ({message['timestamp']}): {message['user']}</div>
            </div>
            <div class="chat-message bot">
                <div>🤖 Assistant: {message['bot']}</div>
            </div>
        """, unsafe_allow_html=True)

with col2:
    # Analytics
    st.subheader("Analytics")
    
    if st.session_state.sentiment_history:
        # Sentiment Analysis
        st.write("### Sentiment Analysis")
        latest_sentiment = st.session_state.sentiment_history[-1]
        st.write(f"Latest Message Sentiment: {latest_sentiment['sentiment']}")
        st.write(f"Polarity: {latest_sentiment['polarity']:.2f}")
        st.write(f"Subjectivity: {latest_sentiment['subjectivity']:.2f}")
        
        # Sentiment Trend
        if len(st.session_state.sentiment_history) > 1:
            st.write("### Sentiment Trend")
            sentiment_df = pd.DataFrame(st.session_state.sentiment_history)
            fig = px.line(sentiment_df, y='polarity', title='Sentiment Polarity Over Time')
            st.plotly_chart(fig, use_container_width=True)

with col3:
    # Quick Actions
    st.subheader("Quick Actions")
    
    # Jokes
    if st.button("😄 Joke"):
        joke = get_joke()
        st.write(joke)
        if st.session_state.voice_enabled:
            speak_text(joke)
    
    # Website Categories
    st.subheader("Available Websites")
    for category, sites in WEBSITES.items():
        with st.expander(f"📂 {category.capitalize()}"):
            for site_name in sites.keys():
                if st.button(f"🌐 {site_name.capitalize()}", key=f"btn_{site_name}"):
                    result = open_website(site_name)
                    st.write(result)
                    if st.session_state.voice_enabled:
                        speak_text(result)
    
    # Intent Distribution
    if st.session_state.intent_history:
        st.subheader("Intent Distribution")
        intent_counts = pd.Series(st.session_state.intent_history).value_counts()
        fig = px.pie(values=intent_counts.values, names=intent_counts.index, title='Intent Distribution')
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("ChatBot | Powered by Advanced NLP") 
