// ====================================
// INDHENT BESKEDER OG TJEK MEDLEMSKAB
// ====================================

// Henter alle beskeder og tjekker om brugeren stadig er med i gruppen
async function loadMessages() {
    // Hent beskederne fra serveren
    const response = await fetch(`/get_messages/${chatId}`);
    const messages = await response.json();

    // Tjek også medlemslisten for at se, om vi stadig er "velkomne"
    const memberResponse = await fetch(`/get_members/${chatId}`);
    const members = await memberResponse.json();

    // Hvis chatten ikke findes, eller vores navn ikke længere er i listen, så sender vi brugeren væk fra siden.
    // (currentUser variablen kommer fra din chat.html)
    if (!members.includes(currentUser)) {
        alert("Du er blevet fjernet fra chatten af en admin.");
        // Send brugeren tilbage til login-siden
        window.location.href = "/join";
        return; 
    }

    // Hvis alt er OK, så vis beskederne som normalt
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

// Vi tjekker nu både beskeder og medlemskab hvert sekund
setInterval(loadMessages, 1000);