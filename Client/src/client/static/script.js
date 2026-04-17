let pollingInterval = null;

function connectToServer() {
  const username = document.getElementById("username").value.trim() || "Guest";
  const serverIp = document.getElementById("server-ip").value.trim();
  const statusEl = document.getElementById("login-status");

  statusEl.innerText = "Connecting...";

  fetch("/connect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: username, ip: serverIp }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        // Hide login UI and show chat UI
        document.getElementById("login-section").style.display = "none";
        document.getElementById("chat-section").style.display = "block";
        document.getElementById("user-info").style.display = "block";

        // Populate User Info
        document.getElementById("current-user").innerText = data.username;
        document.getElementById("user-uuid").innerText = data.uuid;

        // Start the 2-second polling loop
        pollMessages();
        pollingInterval = setInterval(pollMessages, 2000);
      } else {
        statusEl.innerText = "Error: " + data.message;
      }
    })
    .catch((error) => {
      statusEl.innerText = "Connection Failed: " + error;
    });
}

function pollMessages() {
  fetch("/poll")
    .then((response) => response.json())
    .then((data) => {
      const chatbox = document.getElementById("chatbox");
      chatbox.value = data.messages.join("\n");
      chatbox.scrollTop = chatbox.scrollHeight; // Keep scrolled to bottom
    })
    .catch((error) => console.error("Polling error:", error));
}

function sendMessage() {
  const inputField = document.getElementById("messageInput");
  const message = inputField.value.trim();
  if (!message) return;

  fetch("/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: message }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "sent") {
        inputField.value = ""; // Clear text box
        pollMessages(); // Force immediate screen refresh
      } else {
        alert("Failed to send message: " + (data.reason || data.error));
      }
    })
    .catch((error) => console.error("Send error:", error));
}

// Convenience: Trigger send when Enter is pressed
document.addEventListener("DOMContentLoaded", () => {
  const msgInput = document.getElementById("messageInput");
  if (msgInput) {
    msgInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") sendMessage();
    });
  }
});
