# FAQ Chatbot

An intelligent FAQ chatbot built with Python, NLTK, SpaCy, scikit-learn, and Flask. It uses a combination of TF-IDF Cosine Similarity and Intent Matching to provide accurate answers to user questions.

## Features
- **NLP Engine**: Uses NLTK for tokenization and SpaCy for lemmatization.
- **Matching System**: TF-IDF vectorization and Cosine Similarity to find the best matching FAQ.
- **Intent Fallback**: Keyword-based intent matching for short or ambiguous queries.
- **Premium UI**: Modern, responsive chat interface with glassmorphism design.
- **Extensive Dataset**: Comes with 50+ curated FAQs across 8 categories.

## Setup Instructions

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Download NLP Models**:
   The `chatbot.py` script will automatically try to download the SpaCy and NLTK models on first run. If it fails, you can download them manually:
   ```bash
   python -m nltk.downloader punkt punkt_tab stopwords wordnet
   python -m spacy download en_core_web_sm
   ```

3. **Run the Server**:
   ```bash
   python app.py
   ```

4. **Access the Chatbot**:
   Open your browser and navigate to `http://localhost:5000` or `http://127.0.0.1:5000`.

## Architecture
- `data/faqs.json`: Dataset containing questions, variations, and answers.
- `chatbot.py`: Core NLP processing and matching logic.
- `app.py`: Flask web server and API endpoints.
- `templates/index.html`: Chat interface layout.
- `static/style.css` & `static/script.js`: UI styling and interactivity.
