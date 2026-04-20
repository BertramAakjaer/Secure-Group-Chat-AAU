let pollingInterval = null;
let localUsername = "Guest";

// Helper to quickly toggle lobby sections
function showSection(sectionId) {
  const sections = [
    "login-section",
    "group-section",
    "create-group-section",
    "join-group-section",
    "waiting-section",
  ];
  sections.forEach((id) => {
    document.getElementById(id).style.display =
      id === sectionId ? "block" : "none";
  });

  // Clear status messages
  document.getElementById("group-status").innerText = "";
  document.getElementById("login-status").innerText = "";
}

function connectToServer() {
  const usernameInput = document.getElementById("username").value.trim();
  localUsername = usernameInput || "Guest";
  const serverIp = document.getElementById("server-ip").value.trim();
  const statusEl = document.getElementById("login-status");

  statusEl.innerText = "Connecting...";

  fetch("/connect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: localUsername, ip: serverIp }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "success") {
        // Populate User Info
        document.getElementById("current-user").innerText = data.username;
        document.getElementById("user-uuid").innerText = data.uuid;
        document.getElementById("sidebar-username").innerText = data.username;

        showSection("group-section");

        // Start the polling loop
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

function createGroup() {
  const groupName = document.getElementById("group-name").value.trim();
  const statusEl = document.getElementById("group-status"); // Route errors back to main menu view for simplicity

  if (!groupName) return;

  fetch("/create_group", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group_name: groupName }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "requested") {
        pollMessages(); // Check for response
      } else {
        showSection("group-section");
        document.getElementById("group-status").innerText =
          "Error: " + (data.error || data.reason);
      }
    })
    .catch((error) => console.error("Create group error:", error));
}

function joinGroup() {
  const groupUuid = document.getElementById("group-uuid").value.trim();

  if (!groupUuid) return;

  fetch("/join_group", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group_uuid: groupUuid }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "requested") {
        pollMessages(); // Check for response
      } else {
        showSection("group-section");
        document.getElementById("group-status").innerText =
          "Error: " + (data.error || data.reason);
      }
    })
    .catch((error) => console.error("Join group error:", error));
}

function disconnect() {
  // Reload page to reset state (Flask backend handles socket close on timeout/disconnect)
  location.reload();
}

function pollMessages() {
  fetch("/poll")
    .then((response) => response.json())
    .then((data) => {
      // Layout switching based on state
      if (data.waiting) {
        document.getElementById("lobby-wrapper").style.display = "flex";
        document.getElementById("chat-wrapper").style.display = "none";
        showSection("waiting-section");
      } else if (data.group_uuid) {
        // Enter chat interface
        document.getElementById("lobby-wrapper").style.display = "none";
        document.getElementById("chat-wrapper").style.display = "flex";

        document.getElementById("chat-title").innerText =
          `Chat: ${data.group_name}`;
        document.getElementById("display-group-uuid").innerText =
          data.group_uuid;
      }

      renderMessages(data.messages);
    })
    .catch((error) => console.error("Polling error:", error));
}

function renderMessages(messagesList) {
  const container = document.getElementById("messages-container");
  const isScrolledToBottom =
    container.scrollHeight - container.clientHeight <= container.scrollTop + 50;

  container.innerHTML = ""; // Clear existing

  messagesList.forEach((msgStr) => {
    const div = document.createElement("div");
    div.className = "message";

    // Parse the message format from connection.py
    if (msgStr.startsWith("You: ")) {
      div.classList.add("my-message");
      div.innerHTML = `<strong>You:</strong> ${msgStr.substring(5)}`;
    } else if (
      msgStr.startsWith("System: ") ||
      msgStr.startsWith("System Error: ")
    ) {
      div.classList.add("system-message");
      div.innerHTML = `<em>${msgStr}</em>`;
    } else {
      // Try to extract [Username] Message
      const match = msgStr.match(/^\[(.*?)\] (.*)$/);
      if (match) {
        div.innerHTML = `<strong>${match[1]}:</strong> ${match[2]}`;
      } else {
        // Fallback
        div.textContent = msgStr;
      }
    }

    container.appendChild(div);
  });

  // Auto-scroll if user was already at the bottom
  if (isScrolledToBottom) {
    container.scrollTop = container.scrollHeight;
  }
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
      if (data.status === "sent" || data.status === "command_executed") {
        inputField.value = "";
        pollMessages(); // Force immediate update
      } else {
        alert("Failed to send message: " + (data.reason || data.error));
      }
    })
    .catch((error) => console.error("Send error:", error));
}

// Trigger send when Enter is pressed
document.addEventListener("DOMContentLoaded", () => {
  const msgInput = document.getElementById("messageInput");
  if (msgInput) {
    msgInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") sendMessage();
    });
  }
});
