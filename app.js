/********************************************************
  MODE SWITCHING + CLEARING
********************************************************/
function switchToConversationMode() {
  const confirmed = confirm("Switch to conversation mode? This will erase the current chat history. Continue?");
  if (!confirmed) return;
  clearConversation();
  document.getElementById("analysisMode").classList.add("hidden");
  document.getElementById("conversationMode").classList.remove("hidden");
  document.getElementById("teamName").value = "";
  document.getElementById("analysisInput").value = "";
  document.getElementById("userInput").value = "";
  resetStageUI();
}

function switchToAnalysisMode() {
  const confirmed = confirm("Switch to analysis mode? This will erase the current chat history. Continue?");
  if (!confirmed) return;
  clearConversation();
  document.getElementById("conversationMode").classList.add("hidden");
  document.getElementById("analysisMode").classList.remove("hidden");
  document.getElementById("teamName").value = "";
  document.getElementById("analysisInput").value = "";
  document.getElementById("userInput").value = "";
  resetStageUI();
}

function clearConversation() {
  const conversationElem = document.getElementById("conversation");
  conversationElem.innerHTML = "";
}

/********************************************************
  STAGE / FEEDBACK UI UPDATES
********************************************************/
function resetStageUI() {
  // Reset bars to 0
  const defaultStages = ["Forming", "Storming", "Norming", "Performing", "Adjourning"];
  const stageBarsElem = document.getElementById("stageBars");
  stageBarsElem.innerHTML = "";
  defaultStages.forEach(st => {
    stageBarsElem.innerHTML += createStageBarHTML(st, 0);
  });
  document.getElementById("finalStageSpan").textContent = "Uncertain";
  document.getElementById("stageFeedback").textContent = "";
}

function createStageBarHTML(stageName, percentage) {
  const percStr = (percentage * 100).toFixed(1) + "%";
  return `
  <div class="stageBarContainer">
    <span class="stageLabel">${stageName}:</span>
    <div class="stageBar" style="width:${percentage * 100}%;"></div>
    <span style="font-size:12px; margin-left:5px;">${percStr}</span>
  </div>
  `;
}

function updateStageUI(distribution, finalStage, feedback) {
  // distribution = { Forming:0.2, Storming:0.5, Norming:0.1, ... }
  // finalStage = "Storming" or "Uncertain"
  // feedback = "some text" or ""

  const stageBarsElem = document.getElementById("stageBars");
  stageBarsElem.innerHTML = "";
  const stageOrder = ["Forming", "Storming", "Norming", "Performing", "Adjourning"];

  stageOrder.forEach(stageName => {
    const val = distribution[stageName] || 0.0;
    stageBarsElem.innerHTML += createStageBarHTML(stageName, val);
  });

  document.getElementById("finalStageSpan").textContent = finalStage || "Uncertain";
  document.getElementById("stageFeedback").textContent = feedback || "";
}

/********************************************************
  AUTO LOAD TEAM INFO (onblur from teamName)
********************************************************/
async function autoLoadTeamInfo() {
  const teamNameElem = document.getElementById("teamName");
  const teamName = teamNameElem.value.trim();
  if (!teamName) return; // do nothing if empty

  try {
    const resp = await fetch(`http://127.0.0.1:8000/teaminfo?team_name=${encodeURIComponent(teamName)}`);
    if (!resp.ok) throw new Error("Could not load team info");
    const data = await resp.json();
    // data: { distribution:{...}, final_stage:..., feedback:... }
    updateStageUI(data.distribution, data.final_stage, data.feedback);
  } catch (err) {
    console.error("Error loading team info", err);
    alert(err.message);
  }
}

/********************************************************
  CONVERSATION MODE
********************************************************/
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

  const payload = {
    text: userMsg,
    team_name: teamName
  };

  try {
    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error("Failed to connect to the chatbot (conversation mode).");
    }

    const data = await response.json();
    const botMessage = data.bot_message || "No response available.";

    // Add chatbot's reply to conversation
    conversationElem.innerHTML += `<div class="bubble bot">${botMessage}</div>`;
    conversationElem.scrollTop = conversationElem.scrollHeight;

    // Update stage distribution in the side panel
    const distribution = data.distribution || {};
    const finalStage = data.stage || "Uncertain";
    const feedback = data.feedback || "";
    updateStageUI(distribution, finalStage, feedback);

  } catch (error) {
    console.error("Error:", error);
    alert(error.message);
  }

  userInputElem.value = "";
}

/********************************************************
  ANALYSIS MODE
********************************************************/
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

  const lines = bulkText.split("\n").map(l => l.trim()).filter(l => l !== "");
  if (lines.length === 0) {
    alert("Please provide at least one line of text for analysis!");
    return;
  }

  const payload = {
    team_name: teamName,
    lines: lines
  };

  try {
    const response = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) {
      throw new Error("Failed to connect to the chatbot (analysis mode).");
    }

    const data = await response.json();
    const finalStage = data.final_stage || "Uncertain";
    const feedback = data.feedback || "";
    const distribution = data.distribution || {};

    // Show a short note in conversation about how many lines were analyzed
    conversationElem.innerHTML += `
      <div class="bubble user" style="font-style:italic;">
        (Analyzed ${lines.length} lines for team: ${teamName})
      </div>
    `;
    conversationElem.scrollTop = conversationElem.scrollHeight;

    // Update side panel
    updateStageUI(distribution, finalStage, feedback);

  } catch (error) {
    console.error("Error:", error);
    alert(error.message);
  }

  analysisInputElem.value = "";
}
