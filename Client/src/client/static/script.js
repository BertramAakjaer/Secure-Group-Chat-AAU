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
        // Hide login UI and show group choice UI
        document.getElementById("login-section").style.display = "none";
        document.getElementById("group-section").style.display = "block";
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

function showCreateGroup() {
  document.getElementById("group-section").style.display = "none";
  document.getElementById("create-group-section").style.display = "block";
}

function showJoinGroup() {
  document.getElementById("group-section").style.display = "none";
  document.getElementById("join-group-section").style.display = "block";
}

function backToGroupChoice() {
  document.getElementById("create-group-section").style.display = "none";
  document.getElementById("join-group-section").style.display = "none";
  document.getElementById("group-section").style.display = "block";
}

function createGroup() {
  const groupName = document.getElementById("group-name").value.trim();
  const statusEl = document.getElementById("group-status");

  if (!groupName) {
    statusEl.innerText = "Group name is required.";
    return;
  }

  statusEl.innerText = "Creating group...";

  fetch("/create_group", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group_name: groupName }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "requested") {
        statusEl.innerText = "Group creation requested.";
        pollMessages(); // Check for response
      } else {
        statusEl.innerText = "Error: " + (data.error || data.reason);
      }
    })
    .catch((error) => {
      statusEl.innerText = "Failed to create group: " + error;
    });
}

function joinGroup() {
  const groupUuid = document.getElementById("group-uuid").value.trim();
  const statusEl = document.getElementById("group-status");

  if (!groupUuid) {
    statusEl.innerText = "Group UUID is required.";
    return;
  }

  statusEl.innerText = "Joining group...";

  fetch("/join_group", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ group_uuid: groupUuid }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "requested") {
        statusEl.innerText = "Join request sent.";
        pollMessages(); // Check for response
      } else {
        statusEl.innerText = "Error: " + (data.error || data.reason);
      }
    })
    .catch((error) => {
      statusEl.innerText = "Failed to join group: " + error;
    });
}

function disconnect() {
  // For now, just reload the page to reset
  location.reload();
}

function pollMessages() {
  fetch("/poll")
    .then((response) => response.json())
    .then((data) => {
      const chatbox = document.getElementById("chatbox");
      chatbox.value = data.messages.join("\n");
      chatbox.scrollTop = chatbox.scrollHeight; // Keep scrolled to bottom

      // Update UI based on state
      if (data.waiting) {
        document.getElementById("group-section").style.display = "none";
        document.getElementById("create-group-section").style.display = "none";
        document.getElementById("join-group-section").style.display = "none";
        document.getElementById("waiting-section").style.display = "block";
        document.getElementById("chat-section").style.display = "none";
      } else if (data.group_uuid) {
        document.getElementById("group-section").style.display = "none";
        document.getElementById("create-group-section").style.display = "none";
        document.getElementById("join-group-section").style.display = "none";
        document.getElementById("waiting-section").style.display = "none";
        document.getElementById("chat-section").style.display = "block";
        document.getElementById("chat-title").innerText =
          `Connected to ${data.group_name} [${data.group_uuid}]`;
      }
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
      // FIX: Add check for "command_executed"
      if (data.status === "sent" || data.status === "command_executed") {
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
