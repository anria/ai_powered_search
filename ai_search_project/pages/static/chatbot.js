(function () {
    "use strict";

    // --- Config injected by Django template ---
    const CFG = Object.assign(
        {
            ollamaHost:   "http://localhost:11434",
            ollamaModel:  "FableForge-AI/nexus-legal",
            chatEndpoint: "/api/chat/",
            timeoutMs:    180000,   // 3 minutes — local LLMs can be slow to start
        },
        window.CHATBOT_CONFIG || {}
    );

    console.log(
        "[chatbot] Ollama host:", CFG.ollamaHost,
        "model:", CFG.ollamaModel,
        "timeout:", CFG.timeoutMs + "ms"
    );

    // --- Element refs ---
    const toggle   = document.getElementById("chat-toggle");
    const win      = document.getElementById("chat-window");
    const closeBtn = document.getElementById("chat-close");
    const form     = document.getElementById("chat-form");
    const input    = document.getElementById("chat-input");
    const sendBtn  = document.getElementById("chat-send");
    const messages = document.getElementById("chat-messages");

    function getCookie(name) {
        const m = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
        return m ? decodeURIComponent(m[2]) : "";
    }

    const history = [];

    // --- UI helpers ---
    function addMessage(text, role) {
        const div = document.createElement("div");
        div.className = "chat-msg " + (role === "user" ? "chat-user" : "chat-bot");
        div.textContent = text;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
    }

    function addTyping() {
        const div = document.createElement("div");
        div.className = "chat-msg chat-bot chat-typing";
        div.textContent = "…";
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
    }

    function openChat()  { win.classList.remove("chat-hidden"); input.focus(); }
    function closeChat() { win.classList.add("chat-hidden"); }

    toggle.addEventListener("click", () => {
        win.classList.contains("chat-hidden") ? openChat() : closeChat();
    });
    closeBtn.addEventListener("click", closeChat);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeChat(); });

    // --- Fetch with timeout ------------------------------------------------
    async function fetchWithTimeout(url, options, timeoutMs) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);
        try {
            const resp = await fetch(url, { ...options, signal: controller.signal });
            return resp;
        } finally {
            clearTimeout(timer);
        }
    }

    // --- Submit handler ----------------------------------------------------
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, "user");
        history.push({ role: "user", content: text });
        input.value = "";
        input.focus();

        sendBtn.disabled = true;
        input.disabled   = true;   // prevent queuing more messages mid-request
        const typingEl = addTyping();

        try {
            const resp = await fetchWithTimeout(
                CFG.chatEndpoint,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    body: JSON.stringify({ messages: history }),
                },
                CFG.timeoutMs
            );

            const data = await resp.json();
            typingEl.remove();

            if (!resp.ok) {
                addMessage("Sorry, something went wrong: " + (data.error || resp.statusText), "bot");
            } else {
                addMessage(data.reply, "bot");
                history.push({ role: "assistant", content: data.reply });
            }
        } catch (err) {
            typingEl.remove();

            if (err.name === "AbortError") {
                const secs = Math.round(CFG.timeoutMs / 1000);
                addMessage(
                    `The model is taking too long to respond (over ${secs}s). ` +
                    "Try a shorter question, or check that Ollama is running.",
                    "bot"
                );
            } else {
                addMessage("Network error — please try again.", "bot");
            }
        } finally {
            sendBtn.disabled = false;
            input.disabled   = false;
            input.focus();
        }
    });
})();