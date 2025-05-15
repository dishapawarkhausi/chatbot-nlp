# AI ChatBot with Voice Interface

A modern AI chatbot with voice input/output capabilities, sentiment analysis, and website integration. Built with Flask and deployed on Render.

## 🌟 Features

### Voice Interaction
- Voice input using Web Speech API
- Text-to-speech responses using gTTS
- Real-time voice command processing
- Support for voice commands to open websites

### Website Integration
- Quick access to popular websites
- Voice commands to open websites
- Organized categories:
  - Search (Google services)
  - Social Media
  - Entertainment
  - News
  - Education
  - Shopping
  - Travel
  - Food
  - Sports

### Natural Language Processing
- Sentiment analysis of user input
- Intent recognition
- Contextual responses
- Support for multiple languages

### User Interface
- Modern, responsive design
- Dark theme
- Real-time chat interface
- Audio playback controls
- Quick action buttons
- Analytics dashboard

## 🚀 Quick Start

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

### Deployment on Render

1. Create a new Web Service on Render
2. Connect your repository
3. Configure the service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Python Version: 3.9 or higher

## 🛠️ Technology Stack

- **Backend**: Flask, Python
- **Frontend**: HTML, CSS, JavaScript
- **NLP**: NLTK, TextBlob
- **Voice**: Web Speech API, gTTS
- **Deployment**: Render, Gunicorn

## 📦 Dependencies

- Flask==2.3.3
- NLTK==3.8.1
- TextBlob==0.17.1
- gTTS==2.3.2
- requests==2.31.0
- gunicorn==21.2.0
- python-dotenv==1.0.0

## 🎯 Usage Examples

### Voice Commands
- "Open google"
- "Open facebook"
- "Open youtube"
- "Tell me a joke"
- "What time is it?"
- "What's today's date?"

### Website Categories
- Search (Google services)
- Social Media (Facebook, Twitter, Instagram, etc.)
- Entertainment (YouTube, Netflix, Spotify, etc.)
- News (BBC, CNN, Reuters, etc.)
- Education (Coursera, Udemy, Khan Academy, etc.)
- Shopping (Amazon, eBay, Walmart, etc.)
- Travel (Booking.com, Airbnb, Expedia, etc.)
- Food (AllRecipes, Food Network, etc.)
- Sports (ESPN, NBA, NFL, etc.)

## 🔧 Configuration

The application uses environment variables for configuration:
- `PORT`: Server port (default: 5000)
- `FLASK_ENV`: Environment mode (development/production)

## 📝 API Endpoints

- `GET /`: Home page
- `POST /process_text`: Process text input
- `GET /get_websites`: Get list of available websites
- `POST /open_website`: Open a specific website
- `GET /get_joke`: Get a random joke

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- NLTK for natural language processing
- gTTS for text-to-speech conversion
- Web Speech API for voice recognition
- Flask for the web framework
- Render for hosting

## 📞 Support

For support, please open an issue in the repository or contact the maintainers.
