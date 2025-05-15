from flask import Flask, render_template, request, jsonify
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
import re
import string
import logging
import tempfile
import os
import webbrowser
import json
from datetime import datetime
import random
import requests
from gtts import gTTS
import base64
import io

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Website categories and URLs
WEBSITES = {
    'search': {
        'google': 'https://www.google.com',
        'google maps': 'https://www.google.com/maps',
        'google drive': 'https://drive.google.com',
        'google docs': 'https://docs.google.com',
        'google sheets': 'https://sheets.google.com',
        'google slides': 'https://slides.google.com',
        'google calendar': 'https://calendar.google.com',
        'google photos': 'https://photos.google.com',
        'google translate': 'https://translate.google.com',
        'google meet': 'https://meet.google.com',
        'google classroom': 'https://classroom.google.com',
        'google news': 'https://news.google.com',
        'google books': 'https://books.google.com',
        'google scholar': 'https://scholar.google.com',
        'google earth': 'https://earth.google.com',
        'google flights': 'https://www.google.com/flights',
        'google shopping': 'https://shopping.google.com',
        'google finance': 'https://finance.google.com',
        'google analytics': 'https://analytics.google.com',
        'google ads': 'https://ads.google.com'
    },
    'social': {
        'facebook': 'https://www.facebook.com',
        'twitter': 'https://www.twitter.com',
        'linkedin': 'https://www.linkedin.com',
        'instagram': 'https://www.instagram.com',
        'pinterest': 'https://www.pinterest.com',
        'reddit': 'https://www.reddit.com',
        'tiktok': 'https://www.tiktok.com',
        'whatsapp': 'https://www.whatsapp.com',
        'telegram': 'https://www.telegram.org',
        'discord': 'https://www.discord.com'
    },
    'entertainment': {
        'youtube': 'https://www.youtube.com',
        'netflix': 'https://www.netflix.com',
        'spotify': 'https://www.spotify.com',
        'amazon prime': 'https://www.primevideo.com',
        'disney plus': 'https://www.disneyplus.com',
        'hulu': 'https://www.hulu.com',
        'twitch': 'https://www.twitch.tv',
        'soundcloud': 'https://www.soundcloud.com',
        'apple music': 'https://music.apple.com',
        'deezer': 'https://www.deezer.com'
    },
    'news': {
        'bbc': 'https://www.bbc.com',
        'cnn': 'https://www.cnn.com',
        'reuters': 'https://www.reuters.com',
        'the guardian': 'https://www.theguardian.com',
        'new york times': 'https://www.nytimes.com',
        'washington post': 'https://www.washingtonpost.com',
        'al jazeera': 'https://www.aljazeera.com',
        'bloomberg': 'https://www.bloomberg.com',
        'forbes': 'https://www.forbes.com',
        'techcrunch': 'https://techcrunch.com'
    },
    'education': {
        'coursera': 'https://www.coursera.org',
        'udemy': 'https://www.udemy.com',
        'khan academy': 'https://www.khanacademy.org',
        'edx': 'https://www.edx.org',
        'duolingo': 'https://www.duolingo.com',
        'wikipedia': 'https://www.wikipedia.org',
        'github': 'https://www.github.com',
        'stack overflow': 'https://stackoverflow.com',
        'codecademy': 'https://www.codecademy.com'
    },
    'shopping': {
        'amazon': 'https://www.amazon.com',
        'ebay': 'https://www.ebay.com',
        'walmart': 'https://www.walmart.com',
        'etsy': 'https://www.etsy.com',
        'aliexpress': 'https://www.aliexpress.com',
        'best buy': 'https://www.bestbuy.com',
        'target': 'https://www.target.com',
        'newegg': 'https://www.newegg.com',
        'wayfair': 'https://www.wayfair.com',
        'shopify': 'https://www.shopify.com'
    },
    'travel': {
        'booking': 'https://www.booking.com',
        'airbnb': 'https://www.airbnb.com',
        'expedia': 'https://www.expedia.com',
        'tripadvisor': 'https://www.tripadvisor.com',
        'kayak': 'https://www.kayak.com',
        'skyscanner': 'https://www.skyscanner.com',
        'hotels': 'https://www.hotels.com',
        'hostelworld': 'https://www.hostelworld.com',
        'vrbo': 'https://www.vrbo.com'
    },
    'food': {
        'youtube cooking': 'https://www.youtube.com/results?search_query=cooking',
        'allrecipes': 'https://www.allrecipes.com',
        'food network': 'https://www.foodnetwork.com',
        'epicurious': 'https://www.epicurious.com',
        'bon appetit': 'https://www.bonappetit.com',
        'serious eats': 'https://www.seriouseats.com',
        'tasty': 'https://tasty.co',
        'delish': 'https://www.delish.com',
        'food52': 'https://food52.com',
        'cooking light': 'https://www.cookinglight.com'
    },
    'sports': {
        'espn': 'https://www.espn.com',
        'nba': 'https://www.nba.com',
        'nfl': 'https://www.nfl.com',
        'mlb': 'https://www.mlb.com',
        'nhl': 'https://www.nhl.com',
        'fifa': 'https://www.fifa.com',
        'nascar': 'https://www.nascar.com',
        'olympics': 'https://www.olympics.com',
        'sports illustrated': 'https://www.si.com',
        'bleacher report': 'https://bleacherreport.com'
    }
}

# Jokes database
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "What do you call a fake noodle? An impasta!",
    "How does a penguin build its house? Igloos it together!",
    "Why don't eggs tell jokes? They'd crack each other up!"
]

def ensure_nltk_data():
    """Ensure NLTK data is available in the correct location."""
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
        
        # Download each package if not present
        for package, path in required_packages.items():
            try:
                nltk.data.find(path)
                logger.info(f"Package {package} already downloaded")
            except LookupError:
                try:
                    nltk.download(package, download_dir=nltk_data_dir, quiet=True)
                    logger.info(f"Successfully downloaded NLTK package: {package}")
                except Exception as e:
                    logger.error(f"Error downloading NLTK package {package}: {str(e)}")
                    return False
    except Exception as e:
        logger.error(f"Critical error in NLTK data setup: {str(e)}")
        return False
    
    return True

def preprocess_text(text: str) -> list:
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

def text_to_speech(text: str) -> str:
    """Convert text to speech using gTTS and return base64 audio."""
    try:
        tts = gTTS(text=text, lang='en')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        return audio_base64
    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {str(e)}")
        return None

def get_response(user_input: str) -> tuple:
    """Generate response based on user input."""
    tokens = preprocess_text(user_input)
    sentiment, polarity, subjectivity = analyze_sentiment(user_input)
    
    # Define patterns and responses
    patterns = {
        'greeting': {
            'keywords': ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening'],
            'response': "Hello! I'm your AI assistant. How can I help you today?"
        },
        'capabilities': {
            'keywords': ['what', 'can', 'you', 'do', 'help', 'capabilities', 'features'],
            'response': """I can assist you with:
- Natural Language Processing and AI discussions
- Sentiment analysis of text
- Voice interaction
- Contextual conversation
- Professional assistance and guidance
- Opening websites (just say 'open [website name]')
- Telling jokes
- Providing time and date information"""
        },
        'goodbye': {
            'keywords': ['bye', 'goodbye', 'see', 'later', 'exit', 'quit'],
            'response': "Thank you for chatting with me. Have a great day!"
        },
        'thanks': {
            'keywords': ['thank', 'thanks', 'appreciate', 'grateful'],
            'response': "You're welcome! Is there anything else I can assist you with?"
        },
        'joke': {
            'keywords': ['joke', 'funny', 'humor', 'laugh'],
            'response': random.choice(JOKES)
        },
        'time': {
            'keywords': ['time', 'clock', 'hour'],
            'response': f"The current time is {datetime.now().strftime('%I:%M %p')}"
        },
        'date': {
            'keywords': ['date', 'day', 'today'],
            'response': f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
        },
        'weather': {
            'keywords': ['weather', 'temperature', 'forecast'],
            'response': "I'm sorry, I don't have access to real-time weather data at the moment."
        }
    }
    
    # Check for website opening intent
    website_intent = None
    for word in tokens:
        if word == 'open':
            # Look for website name in the next word
            website_index = tokens.index(word) + 1
            if website_index < len(tokens):
                website_name = tokens[website_index]
                for category in WEBSITES.values():
                    if website_name in category:
                        website_intent = website_name
                        break
    
    # Check for pattern matches
    matched_intent = None
    response = None
    
    if website_intent:
        matched_intent = 'website'
        response = f"Opening {website_intent.capitalize()}..."
        # Open the website
        for category in WEBSITES.values():
            if website_intent in category:
                webbrowser.open(category[website_intent])
                break
    else:
        for intent, data in patterns.items():
            if any(keyword in tokens for keyword in data['keywords']):
                matched_intent = intent
                response = data['response']
                break
    
    if not matched_intent:
        # Try to find a website in the input
        for category in WEBSITES.values():
            for site_name in category.keys():
                if site_name in user_input.lower():
                    matched_intent = 'website'
                    response = f"Opening {site_name.capitalize()}..."
                    webbrowser.open(category[site_name])
                    return response, matched_intent, sentiment, polarity, subjectivity
        
        # If no website found, give a general response
        response = "I understand you're asking about something. Could you please provide more context or rephrase your question?"
        matched_intent = "unknown"
    
    return response, matched_intent, sentiment, polarity, subjectivity

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error loading page'}), 500

@app.route('/process_text', methods=['POST'])
def process_text():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        text = data.get('text', '')
        if not text:
            return jsonify({'status': 'error', 'message': 'No text provided'}), 400
        
        # Get response
        response, intent, sentiment, polarity, subjectivity = get_response(text)
        
        # Convert response to speech
        audio_base64 = text_to_speech(response)
        
        return jsonify({
            'status': 'success',
            'text': text,
            'response': response,
            'intent': intent,
            'sentiment': sentiment,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'timestamp': datetime.now().strftime('%I:%M:%S %p'),
            'audio': audio_base64
        })
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_websites', methods=['GET'])
def get_websites():
    try:
        return jsonify({
            'status': 'success',
            'websites': WEBSITES
        })
    except Exception as e:
        logger.error(f"Error getting websites: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/open_website', methods=['POST'])
def open_website():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        site_name = data.get('site_name', '').lower()
        if not site_name:
            return jsonify({'status': 'error', 'message': 'No site name provided'}), 400
        
        # Find the website URL
        for category in WEBSITES.values():
            if site_name in category:
                url = category[site_name]
                webbrowser.open(url)
                return jsonify({
                    'status': 'success',
                    'message': f"Opening {site_name.capitalize()}..."
                })
        
        return jsonify({
            'status': 'error',
            'message': f"Website {site_name} not found"
        }), 404
    except Exception as e:
        logger.error(f"Error opening website: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_joke', methods=['GET'])
def get_joke():
    try:
        joke = random.choice(JOKES)
        audio_base64 = text_to_speech(joke)
        return jsonify({
            'status': 'success',
            'joke': joke,
            'audio': audio_base64
        })
    except Exception as e:
        logger.error(f"Error getting joke: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure NLTK data is available
    if ensure_nltk_data():
        # Get port from environment variable or use default
        port = int(os.environ.get('PORT', 5000))
        # Run the app
        app.run(host='0.0.0.0', port=port)
    else:
        logger.error("Failed to initialize NLTK data. Application cannot start.") 
