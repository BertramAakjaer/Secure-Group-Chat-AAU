// ==============================
// INDHENT BESKEDER FRA SERVEREN
// ==============================

// Henter alle beskeder fra serveren via Flask og viser dem i chatten
async function loadMessages() {
    const response = await fetch(`/get_messages/${chatId}`);
    const messages = await response.json();

    const messagesDiv = document.getElementById("messages");
    messagesDiv.innerHTML = "";

    messages.forEach(msg => {
        const div = document.createElement("div");
        div.className = "message";
        div.innerHTML = `<strong>${msg.username}:</strong> ${msg.text}`;
        messagesDiv.appendChild(div);
    });
    // Scroller automatisk ned til nyeste besked
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// ==============================
// SEND BESKED TIL SERVEREN
// ==============================

// Sender en ny besked til Flask backend via POST request
async function sendMessage() {
    const input = document.getElementById("messageInput");
    const message = input.value.trim();

    // Hvis input er tomt, gør ingenting
    if (!message) return;

    await fetch(`/send_message/${chatId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
    });
    // Ryd inputfelt og opdater chat
    input.value = "";
    loadMessages();
}

// ==============================
// OPDATER CHAT AUTOMATISK
// ==============================

setInterval(loadMessages, 1000);