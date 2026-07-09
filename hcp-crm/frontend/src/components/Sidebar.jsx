import { ClipboardList, History, Stethoscope, LayoutDashboard, Activity } from "lucide-react";

export default function Sidebar({ view, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="mark">Rx</div>
        <div className="name">
          AI CRM
          <span>HCP Module</span>
        </div>
      </div>

      <div className="nav-section-label">Workspace</div>
      <button
        className={`nav-item ${view === "log" ? "active" : ""}`}
        onClick={() => onNavigate("log")}
      >
        <ClipboardList size={16} />
        Log Interaction
      </button>
      <button
        className={`nav-item ${view === "history" ? "active" : ""}`}
        onClick={() => onNavigate("history")}
      >
        <History size={16} />
        Interaction History
      </button>

      <div className="nav-section-label">Coming soon</div>
      <button className="nav-item" disabled style={{ opacity: 0.45, cursor: "default" }}>
        <LayoutDashboard size={16} />
        Analytics Dashboard
      </button>
      <button className="nav-item" disabled style={{ opacity: 0.45, cursor: "default" }}>
        <Stethoscope size={16} />
        HCP Directory
      </button>

      <div className="sidebar-footer">
        <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
          <Activity size={12} />
          Groq · gemma2-9b-it
        </div>
        Powered by LangGraph
      </div>
    </aside>
  );
}
