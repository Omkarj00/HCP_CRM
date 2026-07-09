import { createSlice, nanoid } from "@reduxjs/toolkit";

function getOrCreateSessionId() {
  const key = "hcp-crm-session-id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = nanoid();
    localStorage.setItem(key, id);
  }
  return id;
}

const initialState = {
  sessionId: getOrCreateSessionId(),
  messages: [
    {
      id: nanoid(),
      role: "assistant",
      content:
        "Hi, I'm your CRM assistant. Tell me about a meeting, call, or email with an HCP and I'll fill out the form for you \u2014 e.g. \"Met Dr. Sharma today, discussed our diabetes medication, he requested clinical studies and a follow-up next Tuesday.\"",
      toolCalls: [],
    },
  ],
  loading: false,
  error: null,
};

const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    userMessageSent: (state, action) => {
      state.messages.push({
        id: nanoid(),
        role: "user",
        content: action.payload,
        toolCalls: [],
      });
      state.loading = true;
      state.error = null;
    },
    assistantMessageReceived: (state, action) => {
      const { reply, toolCalls } = action.payload;
      state.messages.push({
        id: nanoid(),
        role: "assistant",
        content: reply,
        toolCalls: toolCalls || [],
      });
      state.loading = false;
    },
    chatErrored: (state, action) => {
      state.messages.push({
        id: nanoid(),
        role: "assistant",
        content: `Sorry, something went wrong: ${action.payload}`,
        toolCalls: [],
        isError: true,
      });
      state.loading = false;
      state.error = action.payload;
    },
  },
});

export const { userMessageSent, assistantMessageReceived, chatErrored } = chatSlice.actions;
export default chatSlice.reducer;
