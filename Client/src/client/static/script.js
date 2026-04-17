// pollInterval holds the ID of the timer that repeatedly refreshes data from the server.
let pollInterval = null;

// currentGroup stores the selected group's UUID so we know which chat to load and send messages to.
let currentGroup = null;

// userUUID stores the local user's UUID once we get it from the server.
let userUUID = "";

// groups is an object where the keys are group UUIDs and the values are group names.
let groups = {};

// When the web page is ready, load saved config if it exists.
window.addEventListener("DOMContentLoaded", () => {
  loadConfig();
});

// loadConfig asks the backend for any saved username/UUID configuration.
function loadConfig() {
  fetch("/load-config")
    .then((res) => res.json())
    .then((data) => {
      // If the backend says we have saved config, fill the username field.
      if (data.status === "success") {
        document.getElementById("username").value = data.username;
        userUUID = data.uuid;
      }
    })
    .catch((err) => console.log("No saved config found", err));
}

// setStatus updates the small status message shown under the login form.
function setStatus(msg) {
  document.getElementById("login-status").textContent = msg;
}

// connectToServer is called when the user presses Connect.
// It reads the username and server IP, sends them to the backend, and then prepares the UI.
function connectToServer() {
  // Read the username from the input field.
  const username = document.getElementById("username").value.trim();

  // Read the server IP, or default to localhost if the field is empty.
  const ip = document.getElementById("server-ip").value.trim() || "127.0.0.1";

  // If the user did not enter a username, show an error message and do nothing.
  if (!username) {
    setStatus("Must enter username.");
    return;
  }

  // Send a POST request to /connect with the username and server IP.
  fetch("/connect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ip, username }),
  })
    .then((res) => res.json())
    .then((data) => {
      // If the backend successfully connected, update the UI and start polling.
      if (data.status === "success") {
        userUUID = data.uuid;

        // Hide the login form and show the group chat controls.
        document.getElementById("login-section").style.display = "none";
        document.getElementById("group-section").style.display = "block";
        document.getElementById("user-info").style.display = "block";

        // Show the current username and UUID on screen.
        document.getElementById("current-user").textContent = username;
        document.getElementById("user-uuid").textContent = userUUID;

        // Clear any status message.
        setStatus("");

        // Update the group drop-down now.
        updateGroupSelect();

        // If polling is already running from a previous connection, stop it.
        if (pollInterval) clearInterval(pollInterval);

        // Start polling every second for new messages and groups.
        pollInterval = setInterval(() => {
          fetchMessages();
          fetchGroups();
        }, 1000);

        // Immediately fetch data once after connecting.
        fetchMessages();
        fetchGroups();
      } else {
        // If the backend returned an error, show it to the user.
        setStatus("Connect error: " + (data.message || "unknown"));
      }
    })
    .catch((err) => setStatus("Connect failed: " + err));
}

// createGroup sends a request to create a new chat group.
function createGroup() {
  const groupName = document.getElementById("group-name").value.trim();

  if (!groupName) {
    alert("Enter group name");
    return;
  }

  fetch("/create_group", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: groupName }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success") {
        // Clear the group name input after success.
        document.getElementById("group-name").value = "";
        // The new group will show up when the next poll fetches groups.
      } else {
        alert("Create failed: " + (data.message || "unknown"));
      }
    });
}

// addUser sends the selected UUID to the backend so the current group admin can add a user.
function addUser() {
  const uuid = document.getElementById("add-uuid").value.trim();

  if (!uuid) {
    alert("Enter UUID");
    return;
  }

  fetch("/add_user", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ uuid }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success") {
        document.getElementById("add-uuid").value = "";
      } else {
        alert("Add failed: " + (data.message || "unknown"));
      }
    });
}

// switchGroup is called when the user selects a different group from the drop-down.
function switchGroup() {
  // Read the selected option value from the group select field.
  const select = document.getElementById("group-select");
  const groupUUID = select.value;

  if (groupUUID) {
    // Store the selected group so sendChatMessage knows where to send messages.
    currentGroup = groupUUID;

    // Show the group name and UUID in the UI.
    document.getElementById("current-chat").textContent =
      `${groups[groupUUID]}(${groupUUID})`;

    // Show the chat section now that a group is selected.
    document.getElementById("chat-section").style.display = "block";

    // Load messages for this group immediately.
    fetchMessages();
  } else {
    // If no group is selected, hide the chat panel.
    currentGroup = null;
    document.getElementById("chat-section").style.display = "none";
  }
}

// sendChatMessage sends the text input to the backend for the selected group.
function sendChatMessage() {
  if (!currentGroup) {
    alert("Select a group first");
    return;
  }

  const msgInput = document.getElementById("message-input");
  const text = msgInput.value.trim();

  if (!text) return;

  fetch("/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text, group: currentGroup }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success") {
        // Clear the message input after successful send.
        msgInput.value = "";
        // Immediately refresh the message view.
        fetchMessages();
      } else {
        alert("Send failed: " + (data.message || "unknown"));
      }
    });
}

// disconnectFromServer tells the backend to disconnect and resets the UI.
function disconnectFromServer() {
  fetch("/disconnect", { method: "POST" }).then(() => {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = null;

    // Reset the UI back to the login state.
    document.getElementById("login-section").style.display = "block";
    document.getElementById("group-section").style.display = "none";
    document.getElementById("chat-section").style.display = "none";
    document.getElementById("user-info").style.display = "none";
    document.getElementById("chat-box").value = "";
    document.getElementById("username").value = "";
    document.getElementById("current-user").textContent = "";
    document.getElementById("user-uuid").textContent = "";

    currentGroup = null;
    groups = {};
    updateGroupSelect();
  });
}

// fetchMessages requests the current group's messages from the backend.
function fetchMessages() {
  if (!currentGroup) return;

  fetch(`/messages?group=${currentGroup}`)
    .then((res) => res.json())
    .then((data) => {
      const chatBox = document.getElementById("chat-box");
      // The backend returns an array of message strings.
      chatBox.value = data.messages.join("\n");
      // Scroll to the bottom so the newest messages are visible.
      chatBox.scrollTop = chatBox.scrollHeight;
    });
}

// fetchGroups asks the backend for the available groups and updates the drop-down.
function fetchGroups() {
  fetch("/groups")
    .then((res) => res.json())
    .then((data) => {
      groups = data;
      updateGroupSelect();
    });
}

// updateGroupSelect rebuilds the group selector element with fresh data.
function updateGroupSelect() {
  const select = document.getElementById("group-select");

  // Start by clearing existing options.
  select.innerHTML = '<option value="">Select a chat</option>';

  // Add one option per group found in the groups object.
  for (const [uuid, name] of Object.entries(groups)) {
    const option = document.createElement("option");
    option.value = uuid;
    option.textContent = `${name}(${uuid})`;
    select.appendChild(option);
  }

  // Listen for when the user picks a different group.
  select.addEventListener("change", switchGroup);
}
