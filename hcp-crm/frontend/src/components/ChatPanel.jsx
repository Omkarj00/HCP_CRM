import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Send, Bot, User, Wrench } from "lucide-react";
import { userMessageSent, assistantMessageReceived, chatErrored } from "../store/slices/chatSlice";
import { applyFormUpdate } from "../store/slices/interactionSlice";
import { sendChatMessage } from "../api/client";

const STARTER_PROMPTS = [
  "Met Dr. Sharma today, discussed our diabetes medication, positive sentiment, shared brochure",
  "Actually his name is Dr. John and the sentiment was negative",
  "What should I do next with Dr. Sharma?",
  "Show my recent interactions with Dr. Sharma",
];

function ToolChips({ toolCalls }) {
  if (!toolCalls || toolCalls.length === 0) return null;
  const labels = {
    log_interaction: "Logged interaction",
    edit_interaction: "Updated form",
    view_interaction_history: "Fetched history",
    search_hcp: "Searched HCPs",
    generate_followup_suggestions: "Generated suggestions",
    schedule_followup_visit: "Scheduled follow-up",
  };
  return (
    <div className="tool-chip-row">
      {toolCalls.map((tc, i) => (
        <span className="tool-chip" key={i}>
          <Wrench size={10} />
          {labels[tc] || tc}
        </span>
      ))}
    </div>
  );
}

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, loading, sessionId } = useSelector((s) => s.chat);
  const form = useSelector((s) => s.interaction.form);
  const [input, setInput] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(text) {
    const message = (text ?? input).trim();
    if (!message || loading) return;
    setInput("");
    dispatch(userMessageSent(message));

    try {
      const res = await sendChatMessage({
        sessionId,
        message,
        currentForm: form,
        currentInteractionId: form.id,
      });
      if (res.form_update) {
        dispatch(applyFormUpdate(res.form_update));
      }
      dispatch(assistantMessageReceived({ reply: res.reply, toolCalls: res.tool_calls }));
    } catch (e) {
      dispatch(chatErrored(e.message));
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <section className="panel chat-panel">
      <div className="panel-header">
        <div>
          <h2 style={{ display: "flex", alignItems: "center", gap: 7 }}>
            <Bot size={17} color="var(--ai)" /> AI Assistant
          </h2>
          <div className="desc">Describe a visit, or ask it to edit, search, or plan follow-ups</div>
        </div>
      </div>

      <div className="panel-body" ref={scrollRef}>
        {messages.map((m) => (
          <div className={`chat-msg ${m.role}`} key={m.id}>
            <div className={`avatar ${m.role}`}>{m.role === "assistant" ? <Bot size={14} /> : <User size={14} />}</div>
            <div>
              <div className={`bubble ${m.isError ? "error" : ""}`}>{m.content}</div>
              <ToolChips toolCalls={m.toolCalls} />
            </div>
          </div>
        ))}

        {loading && (
          <div className="chat-msg assistant">
            <div className="avatar assistant">
              <Bot size={14} />
            </div>
            <div className="bubble">
              <span className="typing-indicator">
                <span />
                <span />
                <span />
              </span>
            </div>
          </div>
        )}

        {messages.length <= 1 && (
          <div className="suggestion-row">
            {STARTER_PROMPTS.map((p) => (
              <button className="suggestion-chip" key={p} onClick={() => handleSend(p)}>
                {p.length > 46 ? p.slice(0, 46) + "…" : p}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="chat-input-bar">
        <div className="chat-input-wrap">
          <textarea
            rows={1}
            placeholder="Describe the interaction, or ask me to edit / search / plan a follow-up..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button className="send-btn" disabled={!input.trim() || loading} onClick={() => handleSend()}>
            <Send size={15} />
          </button>
        </div>
      </div>
    </section>
  );
}
