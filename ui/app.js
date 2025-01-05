async function sendMessage() {
    const userInput = document.getElementById("userInput").value.trim();
    const conversation = document.getElementById("conversation");

    if (!userInput) {
        alert("Please enter a message!");
        return;
    }

    conversation.innerHTML += `<div class="bubble user">${userInput}</div>`;
    conversation.scrollTop = conversation.scrollHeight;

    try {
        const response = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: userInput }),
        });

        if (!response.ok) {
            throw new Error("Failed to connect to the chatbot.");
        }

        const data = await response.json();
        const botMessage = data.bot_message || "No response available.";
        const stage = data.stage || "Uncertain";
        const feedback = data.feedback || "";

        conversation.innerHTML += `<div class="bubble bot">${botMessage}</div>`;
        if (stage && feedback) {
            conversation.innerHTML += `<div class="bubble bot"><strong>Stage:</strong> ${stage}<br><strong>Feedback:</strong> ${feedback}</div>`;
        }

        conversation.scrollTop = conversation.scrollHeight;
    } catch (error) {
        console.error("Error:", error);
        alert("Could not connect to the chatbot. Ensure the server is running.");
    }

    document.getElementById("userInput").value = "";
}