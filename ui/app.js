async function sendMessage() {
  const teamNameElem = document.getElementById("teamName");
  const userInputElem = document.getElementById("userInput");
  const conversationElem = document.getElementById("conversation");

  const teamName = teamNameElem.value.trim();
  const userMsg = userInputElem.value.trim();

  if (!teamName) {
    alert("Please enter a team name!");
    return;
  }
  if (!userMsg) {
    alert("Please enter a message!");
    return;
  }

  // Display user's message in the chat
  conversationElem.innerHTML += `<div class="bubble user">${userMsg}</div>`;
  conversationElem.scrollTop = conversationElem.scrollHeight;

  // Prepare payload
  const payload = {
    text: userMsg,
    team_name: teamName
  };

  try {
    // Call the conversation mode endpoint
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error("Failed to connect to the chatbot (conversation mode).");
    }

    const data = await response.json();
    const botMessage = data.bot_message || "No response available.";
    const stage = data.stage || "";
    const feedback = data.feedback || "";

    // Display bot message
    conversationElem.innerHTML += `<div class="bubble bot">${botMessage}</div>`;
    if (stage && feedback) {
      conversationElem.innerHTML +=
        `<div class="bubble bot"><strong>Stage:</strong> ${stage}<br><strong>Feedback:</strong> ${feedback}</div>`;
    }
    conversationElem.scrollTop = conversationElem.scrollHeight;
  } catch (error) {
    console.error("Error:", error);
    alert(error.message);
  }

  userInputElem.value = "";
}

async function analyzeConversation() {
  const teamNameElem = document.getElementById("teamName");
  const analysisInputElem = document.getElementById("analysisInput");
  const conversationElem = document.getElementById("conversation");

  const teamName = teamNameElem.value.trim();
  const bulkText = analysisInputElem.value.trim();

  if (!teamName) {
    alert("Please enter a team name!");
    return;
  }
  if (!bulkText) {
    alert("Please enter multiple lines to analyze!");
    return;
  }

  // Split lines by newline
  const lines = bulkText.split("\n").map(line => line.trim()).filter(line => line !== "");
  if (lines.length === 0) {
    alert("Please provide at least one line of text for analysis!");
    return;
  }

  // Prepare payload
  const payload = {
    team_name: teamName,
    lines: lines
  };

  try {
    // POST to /analyze
    const response = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error("Failed to connect to the chatbot (analysis mode).");
    }

    const data = await response.json();
    const finalStage = data.final_stage || "Uncertain";
    const feedback = data.feedback || "";

    // We might want to display in conversation
    conversationElem.innerHTML += `<div class="bubble user" style="font-style:italic;">(Analyzed ${lines.length} lines)</div>`;

    if (finalStage !== "Uncertain") {
      conversationElem.innerHTML += `<div class="bubble bot"><strong>Final Stage:</strong> ${finalStage}<br><strong>Feedback:</strong> ${feedback}</div>`;
    } else {
      conversationElem.innerHTML += `<div class="bubble bot">No definitive stage concluded from these lines (still uncertain).</div>`;
    }
    conversationElem.scrollTop = conversationElem.scrollHeight;
  } catch (error) {
    console.error("Error:", error);
    alert(error.message);
  }

  // Optionally clear the input
  analysisInputElem.value = "";
}
