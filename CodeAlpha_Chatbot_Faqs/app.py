from flask import Flask, render_template, request, jsonify
from chatbot import FAQChatbot
import traceback
import sys

app = Flask(__name__)

# Initialize the chatbot engine
print("Initializing FAQ Chatbot Engine...")
try:
    bot = FAQChatbot()
except Exception as e:
    print(f"Failed to initialize Chatbot: {e}")
    traceback.print_exc()
    bot = None

@app.route("/")
def home():
    """Render the main chat interface."""
    # Pass sample questions to the template for quick replies
    samples = bot.get_sample_questions() if bot else []
    return render_template("index.html", samples=samples)

@app.route("/chat", methods=["POST"])
def chat():
    """
    API endpoint to handle incoming chat messages.
    Expects JSON: {"message": "user's question"}
    Returns JSON: {"response": "bot's answer", "confidence": 0.8, ...}
    """
    if not bot:
        return jsonify({
            "response": "Error: Chatbot engine is not initialized. Please check server logs.",
            "confidence": 0.0,
            "category": "System Error"
        }), 500

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "No message provided"}), 400

    user_message = data["message"]
    
    try:
        # Get response from the chatbot engine
        result = bot.get_response(user_message)
        return jsonify(result)
    except Exception as e:
        print(f"Error processing message '{user_message}': {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({
            "response": "I encountered an internal error while processing your request. Please try again later.",
            "confidence": 0.0,
            "category": "System Error"
        }), 500

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True, port=5000)
