import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  items: [],
  loading: false,
  query: "",
};

const historySlice = createSlice({
  name: "history",
  initialState,
  reducers: {
    historyLoading: (state) => {
      state.loading = true;
    },
    historyLoaded: (state, action) => {
      state.items = action.payload;
      state.loading = false;
    },
    setHistoryQuery: (state, action) => {
      state.query = action.payload;
    },
  },
});

export const { historyLoading, historyLoaded, setHistoryQuery } = historySlice.actions;
export default historySlice.reducer;
