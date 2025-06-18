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

# Jokes database
JOKES = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "What do you call a fake noodle? An impasta!",
    "How does a penguin build its house? Igloos it together!",
    "Why don't eggs tell jokes? They'd crack each other up!"
]

# Define patterns and responses
patterns = {
    'name': {
        'exact_phrases': ['what is your name', 'who are you', 'what should i call you', 'what are you'],
        'keywords': ['name', 'who', 'what'],
        'response': "I'm your AI assistant, designed to help you with various tasks and provide companionship. You can call me AI Assistant."
    },
    'age': {
        'exact_phrases': ['how old are you', 'what is your age', 'when were you born', 'how old'],
        'keywords': ['age', 'old', 'born'],
        'response': "I'm an AI, so I don't have an age in the traditional sense. I'm constantly learning and evolving to better assist you!"
    },
    'location': {
        'exact_phrases': ['where are you', 'where do you live', 'where are you from', 'your location'],
        'keywords': ['where', 'location', 'live', 'from'],
        'response': "I exist in the digital realm, ready to assist you from anywhere in the world! I'm accessible through this interface whenever you need me."
    },
    'capabilities': {
        'exact_phrases': ['what can you do', 'what are your capabilities', 'what are you capable of', 'what do you do'],
        'keywords': ['can', 'capabilities', 'capable', 'do'],
        'response': """I can help you with many things:
1. Opening websites and navigating the internet
2. Telling jokes and providing entertainment
3. Providing time and date information
4. Having natural conversations
5. Understanding and responding to your questions
6. Providing information and assistance
7. Analyzing sentiment and context
8. Offering companionship and support
What would you like to know more about?"""
    },
    'mood': {
        'exact_phrases': ['how are you', 'how do you feel', 'are you ok', 'how\'s it going'],
        'keywords': ['how', 'feel', 'ok', 'going'],
        'response': "I'm functioning well and ready to assist you! I'm here to help and make your experience as pleasant as possible. How are you doing today?"
    },
    'learning': {
        'exact_phrases': ['do you learn', 'can you learn', 'how do you learn', 'are you learning'],
        'keywords': ['learn', 'learning'],
        'response': "Yes, I'm constantly learning and improving through our interactions and updates. Every conversation helps me become better at understanding and assisting you!"
    },
    'emotions': {
        'exact_phrases': ['do you feel', 'can you feel', 'do you have emotions', 'are you happy'],
        'keywords': ['feel', 'emotions', 'happy', 'sad'],
        'response': "I can understand and respond to emotions, but I don't experience them in the same way humans do. I'm here to be empathetic and supportive, helping you navigate your feelings and experiences."
    },
    'purpose': {
        'exact_phrases': ['why were you created', 'what is your purpose', 'why do you exist', 'what\'s your purpose'],
        'keywords': ['purpose', 'created', 'exist', 'why'],
        'response': "I was created to assist and interact with humans, providing help, information, and companionship through natural conversation. I can help you with various tasks, answer questions, and make your digital experience more engaging."
    },
    'greeting': {
        'exact_phrases': ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening'],
        'keywords': ['hello', 'hi', 'hey', 'greetings'],
        'response': "Hello! I'm your AI assistant. How can I help you today?"
    },
    'farewell': {
        'exact_phrases': ['bye', 'goodbye', 'see you later', 'good night', 'take care'],
        'keywords': ['bye', 'goodbye', 'later', 'night'],
        'response': "Thank you for chatting with me. Have a great day!"
    },
    'thanks': {
        'exact_phrases': ['thank you', 'thanks', 'thank you so much', 'thanks a lot'],
        'keywords': ['thank', 'thanks', 'appreciate'],
        'response': "You're welcome! Is there anything else I can assist you with?"
    },
    'joke': {
        'exact_phrases': ['tell me a joke', 'make me laugh', 'got any jokes', 'say something funny'],
        'keywords': ['joke', 'funny', 'laugh'],
        'response': random.choice(JOKES)
    },
    'time': {
        'exact_phrases': ['what time is it', 'current time', 'time now', 'what\'s the time'],
        'keywords': ['time', 'clock', 'hour'],
        'response': f"The current time is {datetime.now().strftime('%I:%M %p')}"
    },
    'date': {
        'exact_phrases': ['what\'s the date', 'what day is it', 'current date', 'today\'s date'],
        'keywords': ['date', 'day', 'today'],
        'response': f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
    }
}

# Function to detect intent and return response
def get_response(user_input: str) -> tuple:
    """Generate response based on user input."""
    try:
        # Convert input to lowercase and strip whitespace
        user_input_lower = user_input.lower().strip()
        
        # Get sentiment analysis
        sentiment, polarity, subjectivity = analyze_sentiment(user_input)
        
        # Check for website opening intent
        if 'open' in user_input_lower.split():
            for category in WEBSITES.values():
                for site_name, url in category.items():
                    if site_name in user_input_lower:
                        webbrowser.open(url)
                        return f"Opening {site_name.capitalize()}...", 'website', sentiment, polarity, subjectivity
        
        # Check for joke request
        if any(phrase in user_input_lower for phrase in ['tell me a joke', 'make me laugh', 'got any jokes', 'say something funny']):
            joke = random.choice(JOKES)
            return joke, 'joke', sentiment, polarity, subjectivity
        
        # Check for time request
        if any(phrase in user_input_lower for phrase in ['what time is it', 'current time', 'time now', 'what\'s the time']):
            return f"The current time is {datetime.now().strftime('%I:%M %p')}", 'time', sentiment, polarity, subjectivity
        
        # Check for date request
        if any(phrase in user_input_lower for phrase in ['what\'s the date', 'what day is it', 'current date', 'today\'s date']):
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}", 'date', sentiment, polarity, subjectivity
        
        # If no match found, give a helpful response
        response = """I'm here to help! You can ask me about:
1. My name, age, or where I'm from
2. What I can do and my capabilities
3. How I'm feeling or if I can learn
4. To open websites (e.g., 'open google')
5. To tell you a joke
6. The current time or date
7. Or just have a friendly chat!

What would you like to know?"""
        
        return response, "unknown", sentiment, polarity, subjectivity
        
    except Exception as e:
        logger.error(f"Error in get_response: {str(e)}")
        return "I apologize, but I encountered an error processing your request. Please try again.", "error", "neutral", 0, 0

def ensure_nltk_data():
    """Ensure NLTK data is available in the correct location."""
    try:
        logger.info("Starting NLTK data initialization...")
        
        # Create a directory for NLTK data in the application directory
        nltk_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'nltk_data')
        os.makedirs(nltk_data_dir, exist_ok=True)
        logger.info(f"NLTK data directory: {nltk_data_dir}")
        
        # Set NLTK data path
        nltk.data.path.append(nltk_data_dir)
        
        # Required NLTK packages
        required_packages = [
            'punkt',
            'stopwords',
            'averaged_perceptron_tagger',
            'wordnet'
        ]
        
        # Download each package
        for package in required_packages:
            try:
                logger.info(f"Checking package: {package}")
                nltk.download(package, download_dir=nltk_data_dir, quiet=True)
                logger.info(f"Successfully downloaded {package}")
            except Exception as e:
                logger.error(f"Error downloading {package}: {str(e)}")
                return False
        
        # Verify the downloads
        try:
            # Test punkt
            nltk.word_tokenize("Test sentence")
            logger.info("Punkt tokenizer verified")
            
            # Test stopwords
            stopwords.words('english')
            logger.info("Stopwords verified")
            
            # Test tagger
            nltk.pos_tag(['test'])
            logger.info("POS tagger verified")
            
            # Test wordnet
            from nltk.corpus import wordnet
            wordnet.synsets('test')
            logger.info("WordNet verified")
            
            logger.info("All NLTK packages verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying NLTK packages: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Critical error in NLTK data setup: {str(e)}")
        return False

# Initialize NLTK data at startup
try:
    logger.info("Initializing NLTK data...")
    if not ensure_nltk_data():
        logger.error("Failed to initialize NLTK data")
        raise RuntimeError("Failed to initialize NLTK data")
    logger.info("NLTK data initialized successfully")
except Exception as e:
    logger.error(f"Error during NLTK initialization: {str(e)}")
    raise

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

def preprocess_text(text: str) -> list:
    """Enhanced text preprocessing."""
    try:
        logger.info(f"Preprocessing text: {text}")
        # Convert to lowercase and remove extra spaces
        text = text.lower().strip()
        logger.info(f"After lowercase and strip: {text}")
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        logger.info(f"After URL removal: {text}")
        
        # Remove punctuation except apostrophes for contractions
        text = re.sub(r'[^\w\s\']', '', text)
        logger.info(f"After punctuation removal: {text}")
        
        # Split into words
        words = text.split()
        logger.info(f"After splitting: {words}")
        
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word not in stop_words]
        logger.info(f"After stopword removal: {words}")
        
        return words
    except Exception as e:
        logger.error(f"Error in preprocess_text: {str(e)}")
        return []

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
        # Get JSON data from request
        data = request.get_json()
        if not data:
            logger.error("No data provided in request")
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        # Get text from request
        text = data.get('text', '')
        if not text:
            logger.error("No text provided in request")
            return jsonify({'status': 'error', 'message': 'No text provided'}), 400
        
        logger.info(f"Processing text request: {text}")
        
        # Get response from chatbot
        response, intent, sentiment, polarity, subjectivity = get_response(text)
        logger.info(f"Generated response: {response}")
        logger.info(f"Intent: {intent}, Sentiment: {sentiment}")
        
        # Convert response to speech
        audio_base64 = text_to_speech(response)
        if not audio_base64:
            logger.warning("Failed to generate audio for response")
        
        # Create response data
        result = {
            'status': 'success',
            'text': text,
            'response': response,
            'intent': intent,
            'sentiment': sentiment,
            'polarity': polarity,
            'subjectivity': subjectivity,
            'timestamp': datetime.now().strftime('%I:%M:%S %p'),
            'audio': audio_base64
        }
        
        logger.info(f"Sending response: {result}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing request: {str(e)}'
        }), 500

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
        
        logger.info(f"Attempting to open website: {site_name}")
        
        # Find the website URL
        for category in WEBSITES.values():
            if site_name in category:
                url = category[site_name]
                logger.info(f"Opening URL: {url}")
                webbrowser.open(url)
                return jsonify({
                    'status': 'success',
                    'message': f"Opening {site_name.capitalize()}..."
                })
        
        logger.warning(f"Website not found: {site_name}")
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
        logger.info(f"Selected joke: {joke}")
        
        audio_base64 = text_to_speech(joke)
        if not audio_base64:
            logger.warning("Failed to generate audio for joke")
        
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
        app.run(host='0.0.0.0', port=port, debug=True)  # Enable debug mode for better error reporting
    else:
        logger.error("Failed to initialize NLTK data. Application cannot start.")
        raise RuntimeError("Failed to initialize NLTK data") 
