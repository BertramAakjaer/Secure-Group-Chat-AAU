let pollInterval = null;

function setStatus(msg) {
  document.getElementById("login-status").textContent = msg;
}

function connectToServer() {
  const username = document.getElementById("username").value.trim();
  const ip = document.getElementById("server-ip").value.trim() || "127.0.0.1";

  if (!username) {
    setStatus("Must enter username.");
    return;
  }

  fetch("/connect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ip, username }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success") {
        document.getElementById("login-section").style.display = "none";
        document.getElementById("chat-section").style.display = "block";
        document.getElementById("current-user").textContent = username;
        setStatus("");
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(fetchMessages, 1000);
        fetchMessages();
      } else {
        setStatus("Connect error: " + (data.message || "unknown"));
      }
    })
    .catch((err) => setStatus("Connect failed: " + err));
}

function sendChatMessage() {
  const msgInput = document.getElementById("message-input");
  const text = msgInput.value.trim();
  if (!text) return;

  fetch("/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success") {
        msgInput.value = "";
        fetchMessages();
      } else {
        alert("Send failed: " + (data.message || "unknown"));
      }
    });
}

function disconnectFromServer() {
  fetch("/disconnect", { method: "POST" }).then(() => {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = null;
    document.getElementById("login-section").style.display = "block";
    document.getElementById("chat-section").style.display = "none";
    document.getElementById("chat-box").value = "";
    document.getElementById("username").value = "";
    document.getElementById("current-user").textContent = "";
  });
}

function fetchMessages() {
  fetch("/messages")
    .then((res) => res.json())
    .then((data) => {
      const chatBox = document.getElementById("chat-box");
      chatBox.value = data.messages.join("\n");
      chatBox.scrollTop = chatBox.scrollHeight;
    });
}
