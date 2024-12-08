async function sendMessage() {
    const userInput = document.getElementById("userInput").value;
    if (!userInput.trim()) {
        alert("Please enter a message!");
        return;
    }

    const conversation = document.getElementById("conversation");
    conversation.innerHTML += `<p><strong>You:</strong> ${userInput}</p>`;

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
        const feedback = data.feedback || "No feedback available.";

        conversation.innerHTML += `<p><strong>Bot:</strong> ${botMessage} (Stage: ${stage})</p>`;
        conversation.scrollTop = conversation.scrollHeight;
    } catch (error) {
        console.error("Error:", error);
        alert("Could not connect to the chatbot. Ensure the server is running.");
    }

    document.getElementById("userInput").value = "";
}
