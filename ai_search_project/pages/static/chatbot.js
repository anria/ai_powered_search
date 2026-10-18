(function () {
    "use strict";

    // --- Config injected by Django template ---
    const CFG = Object.assign(
        {
            ollamaHost:   "http://localhost:11434",
            ollamaModel:  "granite3.1-moe:1b",
            chatEndpoint: "/api/chat",
            feedbackEndpoint: "/api/feedback",
            timeoutMs:    180000,
        },
        window.CHATBOT_CONFIG || {}
    );


    console.log(
        "[chatbot] Ollama host:", CFG.ollamaHost,
        "chatEndpoint", CFG.chatEndpoint,
        "model:", CFG.ollamaModel,
        "timeout:", CFG.timeoutMs + "ms"
    );

    // --- Element refs ---
    const toggle        = document.getElementById("chat-toggle");
    const win           = document.getElementById("chat-window");
    const closeBtn      = document.getElementById("chat-close");
    const fullscreenBtn = document.getElementById("chat-fullscreen");
    const form          = document.getElementById("chat-form");
    const input         = document.getElementById("chat-input");
    const sendBtn       = document.getElementById("chat-send");
    const messages      = document.getElementById("chat-messages");

    // --- CSRF helper ---
    function getCookie(name) {
        const m = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
        return m ? decodeURIComponent(m[2]) : "";
    }

    // --- Conversation state ---
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

    function addStreamingBotBubble() {
        const div = document.createElement("div");
        div.className = "chat-msg chat-bot chat-typing";
        div.textContent = "…";
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
    }

    function openChat()  {
        win.classList.remove("chat-hidden");
        input.focus();
    }
    function closeChat() {
        win.classList.add("chat-hidden");
    }

    // --- Wire up toggle / close / fullscreen ---
    toggle.addEventListener("click", () => {
        win.classList.contains("chat-hidden") ? openChat() : closeChat();
    });
    closeBtn.addEventListener("click", closeChat);

    fullscreenBtn.addEventListener("click", () => {
        win.classList.toggle("chat-fullscreen");
        input.focus();
    });

    document.addEventListener("keydown", (e) => {
        if (e.key !== "Escape") return;
        if (win.classList.contains("chat-fullscreen")) {
            win.classList.remove("chat-fullscreen");
        } else {
            closeChat();
        }
    });

    // --- Feedback row appended under an assistant reply ---
    function finalizeBotMessage(bubble, reply, userPrompt) {
        bubble.classList.remove("chat-typing");
        if (!reply) return;

        history.push({ role: "assistant", content: reply });

        const row = document.createElement("div");
        row.className = "chat-feedback";

        const upBtn = document.createElement("button");
        upBtn.type = "button";
        upBtn.textContent = "👍";
        upBtn.title = "Helpful";
        upBtn.setAttribute("aria-label", "Helpful");

        const downBtn = document.createElement("button");
        downBtn.type = "button";
        downBtn.textContent = "👎";
        downBtn.title = "Not helpful";
        downBtn.setAttribute("aria-label", "Not helpful");

        async function sendJudgement(judgement, chosenBtn, otherBtn) {
            upBtn.disabled = true;
            downBtn.disabled = true;
            chosenBtn.classList.add(judgement === 1 ? "selected-up" : "selected-down");
            otherBtn.classList.remove("selected-up", "selected-down");

            const note = window.prompt(
                "Optional note about this answer (leave blank to skip):", ""
            ) || "";

            try {
                await fetch(CFG.feedbackEndpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                    body: JSON.stringify({
                        prompt: userPrompt,
                        answer: reply,
                        judgement: judgement,
                        notes: note,
                    }),
                });
            } catch (err) {
                console.warn("[chatbot] feedback failed:", err);
            }
        }

        upBtn.addEventListener("click",   () => sendJudgement(1, upBtn, downBtn));
        downBtn.addEventListener("click", () => sendJudgement(0, downBtn, upBtn));

        row.appendChild(upBtn);
        row.appendChild(downBtn);
        messages.appendChild(row);
        messages.scrollTop = messages.scrollHeight;
    }

    // --- Submit handler ---

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, "user");
        history.push({ role: "user", content: text });
        input.value = "";
        input.focus();

        sendBtn.disabled = true;
        input.disabled   = true;

        const bubble = addStreamingBotBubble();
        let   replySoFar  = "";
        let   gotAnyChunk = false;
        let   finished    = false;

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), CFG.timeoutMs);

        // Helper: process one already-decoded SSE frame
        function handleFrame(rawEvent) {
            let evt;
            try { 
                evt = JSON.parse(rawEvent); 
                finished = true;
                bubble.classList.remove("chat-typing");
                bubble.textContent = evt.reply;
                messages.scrollTop = messages.scrollHeight;
                finalizeBotMessage(bubble, evt.reply, text);

            } catch (err) {
                console.warn("[chatbot] non-JSON SSE payload:", rawEvent);
                bubble.classList.remove("chat-typing");
                bubble.textContent = "Error: " + evt.error;
                finalizeBotMessage(bubble, "Error", text);
                finished = true;
            }
            return;

        }

        function handleFrame_nah(rawEvent) {
            const dataLines = rawEvent
                .split(/\r?\n/)
                .filter(l => l.startsWith("data:"))
                .map(l => l.slice(5).trimStart());
            if (dataLines.length === 0) return;
            const payload = dataLines.join("\n");

            let evt;
            try { evt = JSON.parse(payload); }
            catch (err) {
                console.warn("[chatbot] non-JSON SSE payload:", payload);
                return;
            }

            if (evt.done) {
                if (!finished) {
                    finished = true;
                    finalizeBotMessage(bubble, replySoFar, text);
                }
                return;
            }
            if (evt.error) {
                bubble.classList.remove("chat-typing");
                bubble.textContent = "Error: " + evt.error;
                finished = true;
                return;
            }
            if (typeof evt.delta === "string" && evt.delta.length) {
                if (!gotAnyChunk) {
                    bubble.classList.remove("chat-typing");
                    bubble.textContent = "";
                    gotAnyChunk = true;
                }
                replySoFar += evt.delta;
                bubble.textContent = replySoFar;
                messages.scrollTop = messages.scrollHeight;
            }
        }

        try {
            const resp = await fetch(CFG.chatEndpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: JSON.stringify({ messages: history }),
                signal: controller.signal,
            });

            if (!resp.ok) {
                let errMsg = resp.statusText;
                try { const j = await resp.json(); errMsg = j.error || errMsg; } catch (_) {}
                bubble.classList.remove("chat-typing");
                bubble.textContent = "Sorry, something went wrong: " + errMsg;
                return;
            }

            // Fallback: no ReadableStream support (very old browsers)
            if (!resp.body) {
                const data = await resp.json();
                if (data.error) {
                    bubble.classList.remove("chat-typing");
                    bubble.textContent = "Error: " + data.error;
                } else {
                    finalizeBotMessage(bubble, data.reply || "", text);
                }
                return;
            }

            const reader  = resp.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let   buffer  = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                console.log("buffer - " , buffer)
                // Normalise CRLF → LF so a single separator check works
                buffer = buffer.replace(/\r\n/g, "\n");

                let idx;
                while ((idx = buffer.indexOf("\n\n")) !== -1) {
                    const rawEvent = buffer.slice(0, idx);
                    buffer = buffer.slice(idx + 2);
                    handleFrame(rawEvent);
                }
            }

            // Flush any trailing frame that wasn't terminated by a blank line
            if (buffer.trim()) {
                handleFrame(buffer);
            }

            // If the server closed the stream without sending {"done": true}
            if (!finished) {
                finished = true;
                finalizeBotMessage(bubble, replySoFar, text);
            }

        } catch (err) {
            bubble.classList.remove("chat-typing");

            if (err.name === "AbortError") {
                const secs = Math.round(CFG.timeoutMs / 1000);
                bubble.textContent = replySoFar
                    ? replySoFar + `\n\n[stopped after ${secs}s]`
                    : `The model took longer than ${secs}s to respond. Try again or use a shorter question.`;
            } else {
                console.error("[chatbot] fetch/stream error:", err);
                bubble.textContent = "Network error — please try again.";
            }
        } finally {
            clearTimeout(timer);
            sendBtn.disabled = false;
            input.disabled   = false;
            input.focus();
        }
    });

    // --- Submit handler ---
    form.addEventListener("submit_Shitty_soft", async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        addMessage(text, "user");
        history.push({ role: "user", content: text });
        input.value = "";
        input.focus();

        sendBtn.disabled = true;
        input.disabled   = true;

        const bubble = addStreamingBotBubble();
        let   replySoFar  = "";
        let   gotAnyChunk = false;

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), CFG.timeoutMs);

        try {
            console.log( "___ endpoint = ", CFG.chatEndpoint)
            console.log( "___messages = " , JSON.stringify(history) )

            const resp = await fetch(CFG.chatEndpoint, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: JSON.stringify({ messages: history }),
                signal: controller.signal,
            });

            console.log( "\nresp = ", JSON.stringify(resp) )

            if (!resp.ok || !resp.body) {
                let errMsg = resp.statusText;
                try { const j = await resp.json(); errMsg = j.error || errMsg; } catch (_) {}
                bubble.classList.remove("chat-typing");
                bubble.textContent = "Sorry, something went wrong: " + errMsg;
                return;
            }

            const reader  = resp.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let   buffer  = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                let idx;
                if ( buffer.indexOf("\n\n") == -1 ) {
                    // buffer {"reply": "Ollama returned HTTP 307: Temporary Redirect"}
                    //alert("buffer " + buffer)
                    // replySoFar = buffer
                    //text = buffer.reply
                }

                while ((idx = buffer.indexOf("\n\n")) !== -1) {
                    const rawEvent = buffer.slice(0, idx);
                    buffer = buffer.slice(idx + 2);

                    const dataLines = rawEvent
                        .split("\n")
                        .filter(l => l.startsWith("data:"))
                        .map(l => l.slice(5).trimStart());

                    if (dataLines.length === 0) continue;

                    const payload = dataLines.join("\n");
                    let evt;
                    try { evt = JSON.parse(payload); } catch (_) { continue; }

                    if (evt.done) {
                        finalizeBotMessage(bubble, replySoFar, text);
                        return;
                    }

                    if (evt.error) {
                        bubble.classList.remove("chat-typing");
                        bubble.textContent = "Error: " + evt.error;
                        return;
                    }

                    if (typeof evt.delta === "string" && evt.delta.length) {
                        if (!gotAnyChunk) {
                            bubble.classList.remove("chat-typing");
                            bubble.textContent = "";
                            gotAnyChunk = true;
                        }
                        replySoFar += evt.delta;
                        bubble.textContent = replySoFar;
                        messages.scrollTop = messages.scrollHeight;
                    }
                }
            }

            // Stream ended without an explicit {"done": true}
            finalizeBotMessage(bubble, replySoFar, text);

        } catch (err) {
            bubble.classList.remove("chat-typing");
            console.log("Error ", err)
            if (err.name === "AbortError") {
                const secs = Math.round(CFG.timeoutMs / 1000);
                bubble.textContent = replySoFar
                    ? replySoFar + `\n\n[stopped after ${secs}s]`
                    : `The model took longer than ${secs}s to respond. Try again or use a shorter question.`;
            } else if (err.name === "TypeError") {
                bubble.textContent = err;
            } else {
                bubble.textContent = err + "\nNetwork error — please try again.";
            }
        } finally {
            clearTimeout(timer);
            sendBtn.disabled = false;
            input.disabled   = false;
            input.focus();
        }
    });
})();
