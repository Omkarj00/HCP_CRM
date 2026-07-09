import { useState } from "react";
import Sidebar from "./components/Sidebar";
import InteractionForm from "./components/InteractionForm";
import ChatPanel from "./components/ChatPanel";
import HistoryView from "./components/HistoryView";

export default function App() {
  const [view, setView] = useState("log");

  return (
    <div className="app-shell">
      <Sidebar view={view} onNavigate={setView} />
      <div className="main-area">
        <div className="topbar">
          <div>
            <h1>{view === "log" ? "Log HCP Interaction" : "Interaction History"}</h1>
            <div className="subtitle">
              {view === "log"
                ? "Talk to the AI Assistant \u2014 it fills the form for you"
                : "Browse and reopen past interactions"}
            </div>
          </div>
        </div>

        <div className="workspace">
          {view === "log" ? (
            <>
              <InteractionForm />
              <ChatPanel />
            </>
          ) : (
            <HistoryView onOpenInteraction={() => setView("log")} />
          )}
        </div>
      </div>
    </div>
  );
}
