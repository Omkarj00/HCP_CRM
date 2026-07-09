import { createSlice } from "@reduxjs/toolkit";

const emptyForm = {
  id: null,
  hcpName: "",
  hospital: "",
  specialty: "",
  interactionType: "Meeting",
  date: "",
  time: "",
  attendees: [],
  topicsDiscussed: "",
  sentiment: "",
  materialsShared: [],
  followUpActions: "",
  followUpDate: "",
  notes: "",
  summary: "",
  keyPoints: [],
  entities: {},
  suggestedNextSteps: [],
  meetingOutcome: "",
  status: "Draft",
};

const initialState = {
  form: emptyForm,
  recentlyUpdatedFields: [],
  dirty: false,
};

const interactionSlice = createSlice({
  name: "interaction",
  initialState,
  reducers: {
    applyFormUpdate: (state, action) => {
      const update = action.payload || {};
      state.form = { ...state.form, ...update };
      state.recentlyUpdatedFields = Object.keys(update);
      state.dirty = false;
    },
    fieldChanged: (state, action) => {
      const { field, value } = action.payload;
      state.form[field] = value;
      state.dirty = true;
    },
    clearRecentlyUpdated: (state) => {
      state.recentlyUpdatedFields = [];
    },
    resetForm: (state) => {
      state.form = emptyForm;
      state.recentlyUpdatedFields = [];
      state.dirty = false;
    },
    loadInteraction: (state, action) => {
      const i = action.payload;
      state.form = {
        id: i.id,
        hcpName: i.hcp_name || "",
        hospital: i.hospital || "",
        specialty: i.specialty || "",
        interactionType: i.interaction_type || "Meeting",
        date: i.interaction_date || "",
        time: i.interaction_time || "",
        attendees: i.attendees || [],
        topicsDiscussed: i.topics_discussed || "",
        sentiment: i.sentiment || "",
        materialsShared: i.materials_shared || [],
        followUpActions: i.follow_up_actions || "",
        followUpDate: i.follow_up_date || "",
        notes: i.notes || "",
        summary: i.summary || "",
        keyPoints: i.key_points || [],
        entities: i.entities || {},
        suggestedNextSteps: i.suggested_next_steps || [],
        meetingOutcome: i.meeting_outcome || "",
        status: i.status || "Logged",
      };
      state.recentlyUpdatedFields = [];
      state.dirty = false;
    },
  },
});

export const { applyFormUpdate, fieldChanged, clearRecentlyUpdated, resetForm, loadInteraction } =
  interactionSlice.actions;
export default interactionSlice.reducer;
