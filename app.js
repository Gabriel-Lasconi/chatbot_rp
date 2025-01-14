/* app.js */

/*
  Wrap everything in an IIFE that returns "App"
  => Only one global variable: "App".
*/
const App = (function() {

  // Private local state in closure
  let previousDistribution = null;
  let lastEmotionsData = null;

  // For toggling: We store the team's distribution vs. member's distribution
  // But we won't keep them globally. We'll fetch them from endpoints on demand.

  /* Reusable UI resets */
  function clearConversation() {
    document.getElementById("conversation").innerHTML = "";
  }

  function resetStageUI() {
    previousDistribution = null;
    document.getElementById("finalStageSpan").textContent = "Uncertain";
    document.getElementById("stageFeedback").textContent = "";
    document.getElementById("stageBars").innerHTML = "";
  }

  /* MODE SWITCHING */
  function switchToConversationMode() {
    const confirmed = confirm("Switch to conversation mode? This will erase the current chat history. Continue?");
    if(!confirmed) return;
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
    if(!confirmed) return;
    clearConversation();
    document.getElementById("conversationMode").classList.add("hidden");
    document.getElementById("analysisMode").classList.remove("hidden");
    document.getElementById("teamName").value = "";
    document.getElementById("memberName").value = "";
    document.getElementById("analysisInput").value = "";
    document.getElementById("userInput").value = "";
    resetStageUI();
  }

  /* STAGE / FEEDBACK UI */
  function updateStageUI(distribution, finalStage, feedback) {
    const stageBarsElem = document.getElementById("stageBars");
    stageBarsElem.innerHTML = "";

    const stageOrder = ["Forming", "Storming", "Norming", "Performing", "Adjourning"];

    stageOrder.forEach(stageName => {
      const currentVal = distribution[stageName] || 0;
      const currentPercent = (currentVal*100).toFixed(2);

      let diffHtml = "";
      if(previousDistribution) {
        const oldVal = previousDistribution[stageName] || 0;
        const oldPercent = oldVal*100;
        const diff = (currentVal*100) - oldPercent;
        if(Math.abs(diff)>0.01){
          const sign = (diff>0)? "+":"";
          const diffColor = (diff>0)? "#28a745":"#dc3545";
          diffHtml = ` <span style="color:${diffColor}; font-size:0.9em;">(${sign}${diff.toFixed(2)}%)</span>`;
        }
      }

      stageBarsElem.innerHTML += createStageBarHTML(stageName, currentPercent, currentPercent, diffHtml);
    });

    document.getElementById("finalStageSpan").textContent = finalStage || "Uncertain";
    document.getElementById("stageFeedback").textContent = feedback || "";

    previousDistribution = {...distribution};
  }

  function createStageBarHTML(label, widthPercent, actualPercent, diffHtml="") {
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

/* Show the TEAM distribution */
async function showTeamStageDistribution() {
  console.log("showTeamStageDistribution() called");

  // 1) Update the heading text
  document.getElementById("stageHeader").textContent = "Stage Distribution (Team Stage)";

  // 2) Get the team name, ensure non-empty
  const teamName = document.getElementById("teamName").value.trim();
  if (!teamName) {
    alert("Please enter a team name first!");
    return;
  }

  // 3) Call /teaminfo to fetch the entire team's distribution
  try {
    const resp = await fetch(`http://127.0.0.1:8000/teaminfo?team_name=${encodeURIComponent(teamName)}`);
    if (!resp.ok) throw new Error("Could not load team distribution");
    const data = await resp.json();
    // data => { distribution, final_stage, feedback }
    updateStageUI(data.distribution, data.final_stage, data.feedback);
  } catch (err) {
    alert(err.message);
  }
}

/* Show the PERSONAL (Member) distribution */
async function showMyStageDistribution() {
  console.log("showMyStageDistribution() called");

  // 1) Update the heading text
  document.getElementById("stageHeader").textContent = "Stage Distribution (My Stage)";

  // 2) Get the team & member name, ensure non-empty
  const teamName = document.getElementById("teamName").value.trim();
  const memberName = document.getElementById("memberName").value.trim();
  if (!teamName || !memberName) {
    alert("Please enter a team and member name first!");
    return;
  }

  // 3) Call /memberinfo to get the personal distribution
  try {
    const resp = await fetch(
      `http://127.0.0.1:8000/memberinfo?team_name=${encodeURIComponent(teamName)}&member_name=${encodeURIComponent(memberName)}`
    );
    if (!resp.ok) throw new Error("Could not load member info");
    const data = await resp.json();
    // data => { distribution, final_stage, accum_emotions? }

    updateStageUI(data.distribution, data.final_stage, "");
  } catch (err) {
    alert(err.message);
  }
}

  /* EMOTIONS TOGGLE => We'll fetch from /chat or do last known?
     We'll keep a small local store for lastEmotions, accumEmotions
     if we want. That might come from /chat or /memberinfo in a
     real bigger design.
  */
  function renderEmotionsInBars(emotions) {
    const emotionBarsElem = document.getElementById("emotionBars");
    emotionBarsElem.innerHTML = "";

    let entries = Object.entries(emotions);
    entries.sort((a,b)=> b[1]-a[1]);
    const top10 = entries.slice(0,10);

    if(top10.length===0){
      emotionBarsElem.innerHTML = "<p style='font-size:14px;color:#777;'>No emotions detected.</p>";
      return;
    }
    for(const [lbl,val] of top10){
      const pct=(val*100).toFixed(2);
      emotionBarsElem.innerHTML += createStageBarHTML(lbl, pct, pct);
    }
  }

  function showLastEmotions() {
  console.log("showLastEmotions() called.");

  // If there's no lastEmotionsData (from /chat) or it's empty, show a note:
  if (!lastEmotionsData || Object.keys(lastEmotionsData).length === 0) {
    document.getElementById("emotionsTitle").textContent = "Emotions (Last Message)";
    const emotionBarsElem = document.getElementById("emotionBars");
    emotionBarsElem.innerHTML = "<p style='font-size:14px;color:#777;'>No emotions detected yet. Please write a message!</p>";
    return;
  }

  // If we do have lastEmotionsData, display them
  document.getElementById("emotionsTitle").textContent = "Emotions (Last Message)";
  renderEmotionsInBars(lastEmotionsData);
}

async function showAccumEmotions() {
  console.log("showAccumEmotions() called.");

  const teamName = document.getElementById("teamName").value.trim();
  const memberName = document.getElementById("memberName").value.trim();
  if (!teamName || !memberName) {
    alert("Please enter both team & member name!");
    return;
  }

  // We'll call /memberinfo to get the personal accum_emotions for this member
  const url = `http://127.0.0.1:8000/memberinfo?team_name=${encodeURIComponent(teamName)}&member_name=${encodeURIComponent(memberName)}`;

  try {
    const resp = await fetch(url);
    if (resp.status === 404) {
      // If the user or team not found in DB
      document.getElementById("emotionsTitle").textContent = "Emotions (Accumulative)";
      document.getElementById("emotionBars").innerHTML = "<p style='font-size:14px;color:#777;'>This member does not exist in the database.</p>";
      return;
    }
    if (!resp.ok) {
      throw new Error("Failed to fetch member info");
    }

    const data = await resp.json();
    // 'data.accum_emotions' might be an object { "enthusiasm":0.2, ... } or empty
    const accumEmotions = data.accum_emotions || {};

    // Now display them or show a note if empty
    document.getElementById("emotionsTitle").textContent = "Emotions (Accumulative)";

    if (!accumEmotions || Object.keys(accumEmotions).length === 0) {
      document.getElementById("emotionBars").innerHTML = "<p style='font-size:14px;color:#777;'>No emotions yet for this member!</p>";
    } else {
      renderEmotionsInBars(accumEmotions);
    }

  } catch (error) {
    console.error("Error in showAccumEmotions():", error);
    alert(error.message);
  }
}

  /* AUTO LOAD TEAM INFO => (unchanged) */
  async function autoLoadTeamInfo(){
    // e.g. fetch /teaminfo
    const teamName = document.getElementById("teamName").value.trim();
    if(!teamName) return;
    try{
      const resp = await fetch(`http://127.0.0.1:8000/teaminfo?team_name=${encodeURIComponent(teamName)}`);
      if(!resp.ok) throw new Error("Could not load team info");
      const data = await resp.json();
      updateStageUI(data.distribution, data.final_stage, data.feedback);
    }catch(err){
      console.error("Error loading team info", err);
      alert(err.message);
    }
  }

  /* ----------------------------------------------------
     CONVERSATION MODE
  ---------------------------------------------------- */
  /*
    The updated sendMessage method:
    - Sends a user message to /chat
    - Displays the returned team distribution
    - Stores lastEmotions, accumEmotions internally, then calls showLastEmotions() by default
  */
  async function sendMessage() {
    const teamName = document.getElementById("teamName").value.trim();
    const memberName = document.getElementById("memberName").value.trim();
    const userMsg = document.getElementById("userInput").value.trim();
    const conversationElem = document.getElementById("conversation");

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

    // Clear the input
    document.getElementById("userInput").value = "";

    // Show the user bubble
    conversationElem.innerHTML += `<div class="bubble user">${userMsg}</div>`;
    conversationElem.scrollTop = conversationElem.scrollHeight;

    // Show a "Thinking..." bubble
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

      // Remove "Thinking..."
      conversationElem.removeChild(thinkingDiv);

      // Insert the bot's reply
      const data = await response.json();
      const botMessage = data.bot_message || "No response available.";
      conversationElem.innerHTML += `<div class="bubble bot">${botMessage}</div>`;
      conversationElem.scrollTop = conversationElem.scrollHeight;

      // The response includes the "team" distribution
      const distribution = data.distribution || {};
      const finalStage = data.stage || "Uncertain";
      const feedback = data.feedback || "";

      // Update the stage bars with the team's distribution
      updateStageUI(distribution, finalStage, feedback);

      // Now we store the last / accum emotions from the response
      lastEmotionsData = data.last_emotion_dist || {};
      accumEmotionsData = data.accum_emotions || {};

      // By default, let's show the last message emotions
      showLastEmotions();

    } catch (error) {
      console.error("Error sending message:", error);
      alert(error.message);
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

    // Add a short note
    conversationElem.innerHTML += `
      <div class="bubble user" style="font-style:italic;">
        (Analyzed ${lines.length} lines for team: ${teamName}, member: ${memberName})
      </div>
    `;
    conversationElem.scrollTop = conversationElem.scrollHeight;

    // Update stage distribution
    updateStageUI(distribution, finalStage, feedback);

    // If you want lastEmotions / accumEmotions after analysis, your server must return them.

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

  /* Return an object so we can call these from HTML, e.g. onclick="App.switchToConversationMode()" */
  return {
    switchToConversationMode,
    switchToAnalysisMode,
    autoLoadTeamInfo,
    sendMessage,
    analyzeConversation,
    processFileUpload,
    uploadFileForAnalysis,

    // Stage distribution toggles
    showTeamStageDistribution,
    showMyStageDistribution,

    // Emotions toggles
    showLastEmotions,
    showAccumEmotions
  };
})();

