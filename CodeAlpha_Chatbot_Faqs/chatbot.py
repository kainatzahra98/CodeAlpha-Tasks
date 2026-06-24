"""
FAQ Chatbot Engine
==================
Core NLP engine for the FAQ Chatbot.
Uses NLTK for tokenization & stopword removal, SpaCy for lemmatization,
and scikit-learn's TF-IDF + Cosine Similarity for question matching.
"""

import json
import os
import string
import re
import ssl
import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# Ensure required NLTK data is available
# ---------------------------------------------------------------------------
# Bypass SSL verification on macOS for NLTK downloads
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

NLTK_PACKAGES = ["punkt", "punkt_tab", "stopwords", "wordnet"]
for pkg in NLTK_PACKAGES:
    try:
        nltk.data.find(f"tokenizers/{pkg}" if "punkt" in pkg else f"corpora/{pkg}")
    except LookupError:
        nltk.download(pkg, quiet=True)

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


# ============================================================================
# Text Preprocessor
# ============================================================================
class TextPreprocessor:
    """Handles all NLP text preprocessing using NLTK and SpaCy."""

    def __init__(self):
        # Load SpaCy English model for lemmatization
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading SpaCy 'en_core_web_sm' model...")
            from spacy.cli import download  # type: ignore
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        self.stop_words = set(stopwords.words("english"))
        # Keep some question words that carry intent
        self.keep_words = {
            "what", "when", "where", "how", "who", "why", "which",
            "do", "does", "can", "could", "is", "are", "not", "no",
        }
        self.stop_words -= self.keep_words

    def preprocess(self, text: str) -> str:
        """
        Full preprocessing pipeline:
        1. Lowercase
        2. Remove special characters (keep alphanumeric + spaces)
        3. Tokenize (NLTK)
        4. Remove stopwords
        5. Lemmatize (SpaCy)
        6. Rejoin into a clean string
        """
        # Lowercase
        text = text.lower().strip()

        # Remove punctuation & special chars but keep spaces
        text = re.sub(r"[^a-z0-9\s]", "", text)

        # Tokenize with NLTK
        tokens = word_tokenize(text)

        # Remove stopwords
        tokens = [t for t in tokens if t not in self.stop_words and t not in string.punctuation]

        # Lemmatize with SpaCy
        doc = self.nlp(" ".join(tokens))
        lemmatized = [token.lemma_ for token in doc]

        return " ".join(lemmatized)


# ============================================================================
# FAQ Chatbot
# ============================================================================
class FAQChatbot:
    """
    FAQ matching engine.
    - Loads FAQ data from a JSON file
    - Expands questions with variations
    - Builds a TF-IDF index over all FAQ questions
    - Matches user queries via cosine similarity
    - Falls back to keyword intent matching for very short queries
    """

    CONFIDENCE_THRESHOLD = 0.15   # Minimum similarity to consider a match
    HIGH_CONFIDENCE = 0.40        # High-confidence threshold

    def __init__(self, faq_path: str = None):
        if faq_path is None:
            faq_path = os.path.join(os.path.dirname(__file__), "data", "faqs.json")

        self.preprocessor = TextPreprocessor()
        self.vectorizer = TfidfVectorizer()

        # Load FAQ dataset
        with open(faq_path, "r", encoding="utf-8") as f:
            self.faq_data = json.load(f)

        # Build expanded question list (question + variations all map to same answer)
        self.questions = []          # Raw question text
        self.processed_questions = []  # Preprocessed question text
        self.answer_map = []         # Index → FAQ entry mapping
        self.category_map = []       # Index → category mapping

        for entry in self.faq_data:
            all_questions = [entry["question"]] + entry.get("variations", [])
            for q in all_questions:
                self.questions.append(q)
                self.processed_questions.append(self.preprocessor.preprocess(q))
                self.answer_map.append(entry["answer"])
                self.category_map.append(entry["category"])

        # Build TF-IDF matrix
        self.tfidf_matrix = self.vectorizer.fit_transform(self.processed_questions)

        # Build keyword → answer index for intent matching fallback
        self._build_intent_index()

        print(f"✅ FAQ Chatbot loaded: {len(self.faq_data)} FAQs, "
              f"{len(self.questions)} total entries (with variations)")

    def _build_intent_index(self):
        """Build a keyword-based intent index for fallback matching."""
        self.intent_keywords = {}
        keyword_groups = {
            "hours": ["hour", "open", "close", "time", "schedule", "working"],
            "location": ["location", "address", "office", "where", "find", "locate"],
            "contact": ["contact", "phone", "email", "reach", "call", "touch"],
            "pricing": ["price", "cost", "plan", "pay", "pricing", "much", "fee"],
            "refund": ["refund", "money back", "return", "cancel"],
            "password": ["password", "reset", "forgot", "login", "log in", "sign in"],
            "security": ["secure", "security", "safe", "encrypt", "privacy", "2fa"],
            "shipping": ["ship", "deliver", "track", "order", "package"],
            "support": ["help", "support", "assist", "issue", "problem", "trouble"],
            "products": ["product", "service", "offer", "feature", "tool"],
            "trial": ["trial", "free", "demo", "try"],
            "hiring": ["hiring", "job", "career", "work", "internship", "position"],
            "api": ["api", "integration", "developer", "sdk", "connect"],
        }

        for intent, keywords in keyword_groups.items():
            for entry in self.faq_data:
                question_lower = entry["question"].lower()
                if any(kw in question_lower for kw in keywords):
                    self.intent_keywords[intent] = entry
                    break

    def get_response(self, user_input: str) -> dict:
        """
        Get the best matching FAQ answer for the user's question.

        Returns:
            dict with keys: response, confidence, category, matched_question
        """
        if not user_input or not user_input.strip():
            return {
                "response": "Please type a question and I'll do my best to help you! 😊",
                "confidence": 0.0,
                "category": None,
                "matched_question": None,
            }

        # 1. Chitchat Check (Greetings, Small Talk)
        chitchat_result = self._chitchat_match(user_input)
        if chitchat_result:
            return chitchat_result

        # Preprocess user input
        processed_input = self.preprocessor.preprocess(user_input)

        # If preprocessing results in empty string, try raw matching
        if not processed_input.strip():
            processed_input = user_input.lower().strip()

        # Vectorize and compute cosine similarity
        input_vector = self.vectorizer.transform([processed_input])
        similarities = cosine_similarity(input_vector, self.tfidf_matrix).flatten()

        # Get best match
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]

        # If cosine similarity is above threshold, return the answer
        if best_score >= self.CONFIDENCE_THRESHOLD:
            return {
                "response": self.answer_map[best_idx],
                "confidence": round(float(best_score), 4),
                "category": self.category_map[best_idx],
                "matched_question": self.questions[best_idx],
            }

        # Fallback: Intent keyword matching for very short or unusual queries
        intent_result = self._intent_match(user_input)
        if intent_result:
            return intent_result

        # No match found
        return {
            "response": (
                "I'm sorry, I couldn't find a matching answer for your question. "
                "Could you try rephrasing it? You can also contact our support team "
                "at support@company.com or call +1 (800) 555-0199 for further assistance."
            ),
            "confidence": round(float(best_score), 4),
            "category": None,
            "matched_question": None,
        }

    def _intent_match(self, user_input: str) -> dict | None:
        """Fallback intent matching using keyword groups."""
        input_lower = user_input.lower()
        for intent, entry in self.intent_keywords.items():
            # Check if any intent-related keyword appears in the user input
            keyword_groups = {
                "hours": ["hour", "open", "close", "time"],
                "location": ["location", "address", "where", "office"],
                "contact": ["contact", "phone", "email", "call"],
                "pricing": ["price", "cost", "much", "plan", "pricing"],
                "refund": ["refund", "money", "return"],
                "password": ["password", "reset", "forgot", "login"],
                "security": ["secure", "security", "safe", "encrypt"],
                "shipping": ["ship", "deliver", "track", "order"],
                "support": ["help", "support", "assist"],
                "products": ["product", "service", "offer"],
                "trial": ["trial", "free", "demo", "try"],
                "hiring": ["hiring", "job", "career", "work"],
                "api": ["api", "integration", "developer"],
            }
            keywords = keyword_groups.get(intent, [])
            if any(kw in input_lower for kw in keywords):
                return {
                    "response": entry["answer"],
                    "confidence": 0.20,
                    "category": entry["category"],
                    "matched_question": entry["question"],
                }
        return None

    def _chitchat_match(self, user_input: str) -> dict | None:
        """Handles common conversational inputs like greetings or small talk."""
        input_lower = user_input.lower()
        # Remove basic punctuation to check phrases
        clean_input = re.sub(r"[^a-z0-9\s]", "", input_lower).strip()

        chitchat_rules = {
            r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening|yo|sup)$": 
                "Hello there! 👋 I'm your virtual assistant. How can I help you today?",
            r"^(how are you|how are you doing|hows it going|how are things)$": 
                "I'm just a bot, but I'm doing great! Thanks for asking. How can I assist you?",
            r"^(thank you|thanks|thx|thanks a lot|thank you so much)$": 
                "You're very welcome! Let me know if you need help with anything else. 😊",
            r"^(bye|goodbye|see ya|cya|take care)$": 
                "Goodbye! Have a fantastic day! 👋",
            r"^(who are you|what are you|are you a bot|are you human)$": 
                "I'm an AI-powered FAQ chatbot designed to help answer your questions quickly!",
            r"^(you are cool|youre awesome|good bot|i like you)$": 
                "Aw, thank you! That makes my virtual day. ✨ What can I help you find?",
            r"^(test|testing|dummy|123|asdf)$":
                "I hear you! Testing loud and clear. 🎙️ If you have a real question, feel free to ask!",
        }

        for pattern, response in chitchat_rules.items():
            if re.match(pattern, clean_input):
                return {
                    "response": response,
                    "confidence": 1.0,
                    "category": "Small Talk",
                    "matched_question": clean_input,
                }
        return None

    def get_categories(self) -> list[str]:
        """Return a list of unique FAQ categories."""
        return list({entry["category"] for entry in self.faq_data})

    def get_sample_questions(self) -> list[str]:
        """Return a curated list of sample questions for quick replies."""
        samples = [
            "What are your office hours?",
            "What products do you offer?",
            "How much does it cost?",
            "Do you offer a free trial?",
            "How do I reset my password?",
            "Is my data secure?",
            "How do I contact support?",
            "Are you hiring?",
        ]
        return samples


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    bot = FAQChatbot()

    test_questions = [
        "What are your office hours?",
        "How much does it cost?",
        "I forgot my password",
        "Do you ship to India?",
        "Tell me about your products",
        "Are there any job openings?",
        "random gibberish xyz abc",
    ]

    print("\n" + "=" * 70)
    print("FAQ CHATBOT — TEST RUN")
    print("=" * 70)

    for q in test_questions:
        result = bot.get_response(q)
        print(f"\n❓ Q: {q}")
        print(f"💬 A: {result['response'][:100]}...")
        print(f"   Confidence: {result['confidence']:.2%} | Category: {result['category']}")
        print(f"   Matched: {result['matched_question']}")
