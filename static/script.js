function sendMessage() {
    let inputField = document.getElementById("user-input");
    let message = inputField.value.trim();
    let chatBox = document.getElementById("chat-box");

    if (message === "") return;

    // Hiển thị tin nhắn của người dùng
    let userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.innerText = message;
    chatBox.appendChild(userMessage);

    inputField.value = ""; // Xóa nội dung ô nhập

    // Gửi tin nhắn đến Flask server
    fetch("/chat", {
        method: "POST",
        body: JSON.stringify({ user_id: "user123", message: message }),
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        let botMessage = document.createElement("div");
        botMessage.className = "bot-message";
        botMessage.innerText = data.bot;
        chatBox.appendChild(botMessage);
        
        // Cuộn xuống tin nhắn mới nhất
        chatBox.scrollTop = chatBox.scrollHeight;
    });
}
