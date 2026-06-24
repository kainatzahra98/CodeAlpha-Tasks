document.addEventListener("DOMContentLoaded", () => {
    const chatMessages = document.getElementById("chatMessages");
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const typingIndicator = document.getElementById("typingIndicator");
    const quickRepliesContainer = document.getElementById("quickReplies");

    // Auto-focus input
    userInput.focus();

    // Event listeners
    sendBtn.addEventListener("click", handleSend);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleSend();
    });

    // Handle Quick Reply Click
    window.sendQuickReply = (btn) => {
        const text = btn.innerText;
        
        // Hide quick replies temporarily while typing
        if (quickRepliesContainer) {
            quickRepliesContainer.style.display = "none";
        }

        userInput.value = text;
        handleSend();
    };

    async function handleSend() {
        const message = userInput.value.trim();
        if (!message) return;

        // 1. Add user message to UI
        addMessage(message, "user-message");
        userInput.value = "";
        
        // Hide quick replies while the bot is "typing"
        if (quickRepliesContainer) {
            quickRepliesContainer.style.display = "none";
        }

        // 2. Show typing indicator
        showTypingIndicator();
        scrollToBottom();

        try {
            // 3. Send request to Flask API
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            // 4. Hide typing indicator & add bot response
            // Artificial delay to make it feel more human (min 500ms, max 1500ms based on length)
            const delay = Math.min(Math.max(data.response.length * 10, 500), 1500);
            
            setTimeout(() => {
                hideTypingIndicator();
                addMessage(data.response, "bot-message");
                
                // Show quick replies again and move them to the bottom
                if (quickRepliesContainer) {
                    quickRepliesContainer.style.display = "flex";
                    chatMessages.appendChild(quickRepliesContainer);
                    scrollToBottom();
                }
            }, delay);

        } catch (error) {
            console.error("Error communicating with chatbot API:", error);
            hideTypingIndicator();
            addMessage("Sorry, I'm having trouble connecting to the server right now. Please try again later.", "bot-message");
            
            // Show quick replies again on error
            if (quickRepliesContainer) {
                quickRepliesContainer.style.display = "flex";
                chatMessages.appendChild(quickRepliesContainer);
                scrollToBottom();
            }
        }
    }

    function addMessage(text, className) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${className}`;

        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";
        contentDiv.innerHTML = `<p>${escapeHTML(text)}</p>`;

        const timeDiv = document.createElement("div");
        timeDiv.className = "message-time";
        timeDiv.innerText = getCurrentTime();

        msgDiv.appendChild(contentDiv);
        msgDiv.appendChild(timeDiv);
        
        // Insert before typing indicator
        chatMessages.insertBefore(msgDiv, typingIndicator);
        scrollToBottom();
    }

    function showTypingIndicator() {
        typingIndicator.style.display = "flex";
        // Move to the end of the messages
        chatMessages.appendChild(typingIndicator);
        scrollToBottom();
    }

    function hideTypingIndicator() {
        typingIndicator.style.display = "none";
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Simple HTML escaper to prevent XSS
    function escapeHTML(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
