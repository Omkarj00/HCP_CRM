import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Search, Calendar } from "lucide-react";
import { fetchInteractions } from "../api/client";
import { historyLoaded, historyLoading, setHistoryQuery } from "../store/slices/historySlice";
import { loadInteraction } from "../store/slices/interactionSlice";
import { SentimentPill } from "./StatusPill";

export default function HistoryView({ onOpenInteraction }) {
  const dispatch = useDispatch();
  const { items, loading, query } = useSelector((s) => s.history);
  const [localQuery, setLocalQuery] = useState(query);

  async function load(hcp_name) {
    dispatch(historyLoading());
    try {
      const data = await fetchInteractions(hcp_name ? { hcp_name } : {});
      dispatch(historyLoaded(data));
    } catch (e) {
      console.error(e);
      dispatch(historyLoaded([]));
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSearch(e) {
    e.preventDefault();
    dispatch(setHistoryQuery(localQuery));
    load(localQuery);
  }

  return (
    <section className="panel" style={{ gridColumn: "1 / -1" }}>
      <div className="panel-header">
        <div>
          <h2>Interaction History</h2>
          <div className="desc">All logged HCP interactions, most recent first</div>
        </div>
      </div>
      <div className="panel-body">
        <form className="history-toolbar" onSubmit={handleSearch}>
          <input
            placeholder="Search by HCP name..."
            value={localQuery}
            onChange={(e) => setLocalQuery(e.target.value)}
          />
          <button className="btn primary" type="submit">
            <Search size={13} style={{ marginRight: 6, verticalAlign: -2 }} />
            Search
          </button>
        </form>

        {loading && <p className="empty-hint">Loading...</p>}
        {!loading && items.length === 0 && <p className="empty-hint">No interactions logged yet.</p>}

        {items.map((i) => (
          <div
            className="history-card"
            key={i.id}
            onClick={() => {
              dispatch(loadInteraction(i));
              onOpenInteraction?.();
            }}
          >
            <div className="history-card-top">
              <span className="name">{i.hcp_name || "Unnamed HCP"}</span>
              <SentimentPill sentiment={i.sentiment} />
            </div>
            <div className="meta">
              <Calendar size={11} style={{ verticalAlign: -1, marginRight: 4 }} />
              {i.interaction_date || "No date"} &middot; {i.interaction_type || "Meeting"}
              {i.hospital ? ` \u00b7 ${i.hospital}` : ""}
            </div>
            <div className="summary">{i.summary || i.topics_discussed || "No summary available."}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
