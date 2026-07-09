export function SentimentPill({ sentiment }) {
  if (!sentiment) return null;
  const key = sentiment.toLowerCase();
  const cls = key.includes("pos") ? "positive" : key.includes("neg") ? "negative" : "neutral";
  return <span className={`pill ${cls}`}>{sentiment}</span>;
}

export function StatusBadge({ status }) {
  if (!status) return null;
  const cls = status.toLowerCase() === "logged" ? "status" : "draft";
  return <span className={`pill ${cls}`}>{status}</span>;
}
