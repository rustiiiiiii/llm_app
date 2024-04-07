document.addEventListener("DOMContentLoaded", function () {
    const submitBtn = document.getElementById("submitBtn");
    const userInput = document.getElementById("userInput");
    const scenarioSelector = document.getElementById("scenarioSelector");
    const conversationIdInput = document.getElementById("conversationIdInput");
    const responseOutput = document.getElementById("responseOutput"); // New line

    submitBtn.addEventListener("click", function () {
        const scenario = scenarioSelector.value;
        const inputText = userInput.value;
        const conversationId = conversationIdInput.value;

        if (!inputText.trim()) {
            alert("Please enter some text!");
            return;
        }

        if (!conversationId.trim()) {
            alert("Please enter a conversation ID!");
            return;
        }

        // Replace `http://localhost:8000` with your actual FastAPI server URL
        fetch("http://localhost:8000/process/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    user_input: inputText,
                    prompt_template: scenario,
                    input_method: "Text",
                    output_method: "Text",
                    conversation_id: conversationId,
                }),
            })
            .then(response => response.json())
            .then(data => {
                console.log("Response:", data);
                responseOutput.innerText = data.response; // New line
            });
    });
});