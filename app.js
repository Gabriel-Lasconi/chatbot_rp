/* ----------------------------------------------------
   Global variable to track previous distribution
---------------------------------------------------- */
let previousDistribution = null;

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
  document.getElementById("memberName").value = "";
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
  document.getElementById("memberName").value = "";
  document.getElementById("analysisInput").value = "";
  document.getElementById("userInput").value = "";
  resetStageUI();
}

function clearConversation() {
  const conversationElem = document.getElementById("conversation");
  conversationElem.innerHTML = "";
}

/********************************************************
  STAGE / EMOTIONS / FEEDBACK UI UPDATES
********************************************************/
function resetStageUI() {
  // Reset stage bars to 0
  const defaultStages = ["Forming", "Storming", "Norming", "Performing", "Adjourning"];
  const stageBarsElem = document.getElementById("stageBars");
  stageBarsElem.innerHTML = "";
  defaultStages.forEach(st => {
    stageBarsElem.innerHTML += createStageBarHTML(st, 0, 0);
  });
  document.getElementById("finalStageSpan").textContent = "Uncertain";
  document.getElementById("stageFeedback").textContent = "";

  // Reset last message emotion bars
  const emotionBarsElem = document.getElementById("emotionBars");
  emotionBarsElem.innerHTML = "<p style='font-size:14px;color:#777;'>No emotions detected.</p>";

  // Reset our previous distribution
  previousDistribution = null;
}

/**
 * Update the stage UI with a new distribution, final stage, and feedback.
 * We compute the delta from previousDistribution to show (+/-).
 */
function updateStageUI(distribution, finalStage, feedback) {
  const stageBarsElem = document.getElementById("stageBars");
  stageBarsElem.innerHTML = "";

  const stageOrder = ["Forming", "Storming", "Norming", "Performing", "Adjourning"];

  stageOrder.forEach(stageName => {
    // Current value (0..1)
    const currentVal = distribution[stageName] || 0;
    const currentPercent = (currentVal * 100).toFixed(2);

    // Compute difference if we have a previousDistribution
    let diffHtml = "";
    if (previousDistribution) {
      const oldVal = previousDistribution[stageName] || 0;
      const oldPercent = oldVal * 100;
      const diff = (currentVal * 100) - oldPercent; // difference in percentage points

      if (Math.abs(diff) > 0.001) {
        // Show difference if it's not trivial
        const sign = diff > 0 ? "+" : "";
        const diffColor = diff > 0 ? "#28a745" : "#dc3545"; // green for +, red for -
        diffHtml = ` <span style="color:${diffColor}; font-size:0.9em;">
          (${sign}${diff.toFixed(2)}%)
        </span>`;
      }
    }

    stageBarsElem.innerHTML += createStageBarHTML(stageName, currentPercent, currentPercent, diffHtml);
  });

  // Update final stage and feedback
  document.getElementById("finalStageSpan").textContent = finalStage || "Uncertain";
  document.getElementById("stageFeedback").textContent = feedback || "";

  // Update previousDistribution
  previousDistribution = { ...distribution };
}

/**
 * Create a bar row for a given label, widthPercent, actualPercent, and optional diffHtml.
 */
function createStageBarHTML(label, widthPercent, actualPercent, diffHtml = "") {
  return `
    <div class="stageBarContainer">
      <span class="stageLabel">${label}:</span>
      <div class="stageBar">
        <div class="stageBarFill" style="width: ${widthPercent}%;"></div>
      </div>
      <span class="stagePercentage">${actualPercent}%</span>
      ${diffHtml}
    </div>
  `;
}

/**
 * Update the last message's emotions in a separate panel.
 */
function updateEmotionsUI(emotions) {
  const emotionBarsElem = document.getElementById("emotionBars");
  emotionBarsElem.innerHTML = "";

  if (!emotions || Object.keys(emotions).length === 0) {
    emotionBarsElem.innerHTML = "<p style='font-size:14px;color:#777;'>No emotions detected.</p>";
    return;
  }

  for (const [emotionLabel, rawValue] of Object.entries(emotions)) {
    const widthPercent = (rawValue * 100).toFixed(2);
    // Reuse the same bar-creation approach
    emotionBarsElem.innerHTML += createStageBarHTML(emotionLabel, widthPercent, widthPercent);
  }
}

/********************************************************
  AUTO LOAD TEAM INFO (onblur from teamName)
********************************************************/
async function autoLoadTeamInfo() {
  const teamNameElem = document.getElementById("teamName");
  const teamName = teamNameElem.value.trim();
  if (!teamName) return;

  try {
    const resp = await fetch(`http://127.0.0.1:8000/teaminfo?team_name=${encodeURIComponent(teamName)}`);
    if (!resp.ok) throw new Error("Could not load team info");
    const data = await resp.json();
    // data: { distribution, final_stage, feedback }
    updateStageUI(data.distribution, data.final_stage, data.feedback);
  } catch (err) {
    console.error("Error loading team info:", err);
    alert(err.message);
  }
}

/********************************************************
  CONVERSATION MODE
********************************************************/
async function sendMessage() {
  const teamNameElem = document.getElementById("teamName");
  const memberNameElem = document.getElementById("memberName");
  const userInputElem = document.getElementById("userInput");
  const conversationElem = document.getElementById("conversation");

  const teamName = teamNameElem.value.trim();
  const memberName = memberNameElem.value.trim();
  const userMsg = userInputElem.value.trim();

  if (!teamName) {
    alert("Please enter a team name!");
    return;
  }
  if (!memberName) {
    alert("Please enter your (member) name!");
    return;
  }
  if (!userMsg) {
    alert("Please enter a message!");
    return;
  }

  // Clear input immediately
  userInputElem.value = "";

  // Show user's message in the chat
  conversationElem.innerHTML += `<div class="bubble user">${userMsg}</div>`;
  conversationElem.scrollTop = conversationElem.scrollHeight;

  // Show a "Thinking..." bubble (with spinner)
  const thinkingDiv = document.createElement("div");
  thinkingDiv.classList.add("bubble", "bot");
  thinkingDiv.innerHTML = `
    <span class="spinner"></span>
    <span style="margin-left:5px;">Thinking...</span>
  `;
  conversationElem.appendChild(thinkingDiv);
  conversationElem.scrollTop = conversationElem.scrollHeight;

  const payload = {
    text: userMsg,
    team_name: teamName,
    member_name: memberName
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

    // Remove the "Thinking..." bubble
    conversationElem.removeChild(thinkingDiv);

    // Display the bot's actual response
    const data = await response.json();
    const botMessage = data.bot_message || "No response available.";
    conversationElem.innerHTML += `<div class="bubble bot">${botMessage}</div>`;
    conversationElem.scrollTop = conversationElem.scrollHeight;

    // Update stage distribution
    const distribution = data.distribution || {};
    const finalStage = data.stage || "Uncertain";
    const feedback = data.feedback || "";
    updateStageUI(distribution, finalStage, feedback);

    // Update last message’s emotions
    const lastEmotions = data.last_emotion_dist || {};
    updateEmotionsUI(lastEmotions);

  } catch (error) {
    console.error("Error sending message:", error);
    alert(error.message);

    // If error, remove the "Thinking..." bubble
    if (conversationElem.contains(thinkingDiv)) {
      conversationElem.removeChild(thinkingDiv);
    }
  }
}

/********************************************************
  ANALYSIS MODE
********************************************************/
async function analyzeConversation() {
  const teamNameElem = document.getElementById("teamName");
  const memberNameElem = document.getElementById("memberName");
  const analysisInputElem = document.getElementById("analysisInput");
  const conversationElem = document.getElementById("conversation");

  const teamName = teamNameElem.value.trim();
  const memberName = memberNameElem.value.trim();
  const bulkText = analysisInputElem.value.trim();

  if (!teamName) {
    alert("Please enter a team name!");
    return;
  }
  if (!memberName) {
    alert("Please enter your (member) name!");
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
    member_name: memberName,
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

    // Show a short note in conversation
    conversationElem.innerHTML += `
      <div class="bubble user" style="font-style:italic;">
        (Analyzed ${lines.length} lines for team: ${teamName}, member: ${memberName})
      </div>
    `;
    conversationElem.scrollTop = conversationElem.scrollHeight;

    // Update stage distribution
    updateStageUI(distribution, finalStage, feedback);

    // If you want to show lastEmotions here, you'd need the server to return them.
    // For now, we assume it doesn't.

  } catch (error) {
    console.error("Error analyzing conversation:", error);
    alert(error.message);
  }

  analysisInputElem.value = "";
}

/********************************************************
  FILE UPLOAD HANDLING
********************************************************/
function processFileUpload() {
  const fileInput = document.getElementById("fileUpload");
  const analysisInput = document.getElementById("analysisInput");

  if (fileInput.files.length === 0) {
    alert("No file selected. Please upload a valid text file.");
    return;
  }

  const file = fileInput.files[0];
  const reader = new FileReader();

  reader.onload = function (event) {
    const fileContents = event.target.result;
    analysisInput.value = fileContents;
  };

  reader.onerror = function () {
    alert("Failed to read the file. Please try again.");
  };

  reader.readAsText(file);
}

async function uploadFileForAnalysis() {
  const fileInput = document.getElementById("fileUpload");
  const teamNameElem = document.getElementById("teamName");
  const memberNameElem = document.getElementById("memberName");
  const conversationElem = document.getElementById("conversation");

  const teamName = teamNameElem.value.trim();
  const memberName = memberNameElem.value.trim();

  if (!teamName) {
    alert("Please enter a team name!");
    return;
  }
  if (!memberName) {
    alert("Please enter your (member) name!");
    return;
  }
  if (fileInput.files.length === 0) {
    alert("Please upload a valid text file.");
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("team_name", teamName);
  formData.append("member_name", memberName);
  formData.append("file", file);

  try {
    const response = await fetch("http://127.0.0.1:8000/analyze-file", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Failed to analyze the uploaded file.");
    }

    const data = await response.json();
    const finalStage = data.final_stage || "Uncertain";
    const feedback = data.feedback || "";
    const distribution = data.distribution || {};

    conversationElem.innerHTML += `
      <div class="bubble user" style="font-style:italic;">
        (Analyzed uploaded chat log for team: ${teamName}, member: ${memberName})
      </div>
    `;
    conversationElem.scrollTop = conversationElem.scrollHeight;

    updateStageUI(distribution, finalStage, feedback);

  } catch (error) {
    console.error("Error uploading file for analysis:", error);
    alert(error.message);
  }
}
