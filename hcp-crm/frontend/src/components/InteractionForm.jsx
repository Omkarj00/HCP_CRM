import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Sparkles, X, Save, ListChecks, Tag, Lightbulb } from "lucide-react";
import { fieldChanged, clearRecentlyUpdated, resetForm } from "../store/slices/interactionSlice";
import { updateInteraction } from "../api/client";
import { SentimentPill, StatusBadge } from "./StatusPill";

const INTERACTION_TYPES = ["Meeting", "Call", "Email", "Conference", "Virtual"];
const SENTIMENTS = ["Positive", "Neutral", "Negative"];

function ChipField({ label, values, onAdd, onRemove, aiTouched, placeholder }) {
  const [draft, setDraft] = useState("");

  function commit() {
    const v = draft.trim();
    if (v) {
      onAdd(v);
      setDraft("");
    }
  }

  return (
    <div className={`field ${aiTouched ? "ai-touched" : ""}`}>
      {aiTouched && (
        <span className="ai-touched-badge">
          <Sparkles size={10} /> AI
        </span>
      )}
      <label>{label}</label>
      <div className="chip-input">
        {values.map((v, idx) => (
          <span className="chip" key={`${v}-${idx}`}>
            {v}
            <button type="button" onClick={() => onRemove(idx)}>
              <X size={11} />
            </button>
          </span>
        ))}
        <input
          value={draft}
          placeholder={values.length ? "" : placeholder}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === ",") {
              e.preventDefault();
              commit();
            }
          }}
          onBlur={commit}
        />
      </div>
    </div>
  );
}

export default function InteractionForm() {
  const dispatch = useDispatch();
  const { form, recentlyUpdatedFields, dirty } = useSelector((s) => s.interaction);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (recentlyUpdatedFields.length === 0) return;
    const t = setTimeout(() => dispatch(clearRecentlyUpdated()), 2600);
    return () => clearTimeout(t);
  }, [recentlyUpdatedFields, dispatch]);

  const touched = (field) => recentlyUpdatedFields.includes(field);

  function set(field, value) {
    dispatch(fieldChanged({ field, value }));
  }

  async function handleSave() {
    if (!form.id) return;
    setSaving(true);
    try {
      await updateInteraction(form.id, {
        hcp_name: form.hcpName,
        hospital: form.hospital,
        specialty: form.specialty,
        interaction_type: form.interactionType,
        interaction_date: form.date || null,
        interaction_time: form.time || null,
        attendees: form.attendees,
        topics_discussed: form.topicsDiscussed,
        sentiment: form.sentiment,
        materials_shared: form.materialsShared,
        follow_up_actions: form.followUpActions,
        follow_up_date: form.followUpDate || null,
        notes: form.notes,
      });
    } catch (e) {
      console.error(e);
      alert(`Couldn't save: ${e.message}`);
    } finally {
      setSaving(false);
    }
  }

  const entityGroups = Object.entries(form.entities || {}).filter(([, v]) => v && v.length);

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <h2>Log HCP Interaction</h2>
          <div className="desc">Driven by the AI Assistant &mdash; ask it to log or edit a visit</div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <SentimentPill sentiment={form.sentiment} />
          <StatusBadge status={form.status} />
        </div>
      </div>

      <div className="panel-body">
        <div className="form-section-title">Interaction Details</div>

        <div className="form-row">
          <div className={`field ${touched("hcpName") ? "ai-touched" : ""}`}>
            {touched("hcpName") && (
              <span className="ai-touched-badge">
                <Sparkles size={10} /> AI
              </span>
            )}
            <label>HCP Name</label>
            <input
              placeholder="Search or select HCP..."
              value={form.hcpName}
              onChange={(e) => set("hcpName", e.target.value)}
            />
          </div>
          <div className={`field ${touched("interactionType") ? "ai-touched" : ""}`}>
            {touched("interactionType") && (
              <span className="ai-touched-badge">
                <Sparkles size={10} /> AI
              </span>
            )}
            <label>Interaction Type</label>
            <select
              value={form.interactionType}
              onChange={(e) => set("interactionType", e.target.value)}
            >
              {INTERACTION_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className={`field ${touched("hospital") ? "ai-touched" : ""}`}>
            {touched("hospital") && (
              <span className="ai-touched-badge">
                <Sparkles size={10} /> AI
              </span>
            )}
            <label>Hospital / Clinic</label>
            <input
              placeholder="e.g. City General Hospital"
              value={form.hospital}
              onChange={(e) => set("hospital", e.target.value)}
            />
          </div>
          <div className={`field ${touched("specialty") ? "ai-touched" : ""}`}>
            {touched("specialty") && (
              <span className="ai-touched-badge">
                <Sparkles size={10} /> AI
              </span>
            )}
            <label>Specialty</label>
            <input
              placeholder="e.g. Endocrinology"
              value={form.specialty}
              onChange={(e) => set("specialty", e.target.value)}
            />
          </div>
        </div>

        <div className="form-row">
          <div className={`field ${touched("date") ? "ai-touched" : ""}`}>
            {touched("date") && (
              <span className="ai-touched-badge">
                <Sparkles size={10} /> AI
              </span>
            )}
            <label>Date</label>
            <input type="date" value={form.date || ""} onChange={(e) => set("date", e.target.value)} />
          </div>
          <div className={`field ${touched("time") ? "ai-touched" : ""}`}>
            {touched("time") && (
              <span className="ai-touched-badge">
                <Sparkles size={10} /> AI
              </span>
            )}
            <label>Time</label>
            <input type="time" value={form.time || ""} onChange={(e) => set("time", e.target.value)} />
          </div>
        </div>

        <div className="form-row">
          <div className={`field ${touched("sentiment") ? "ai-touched" : ""}`}>
            {touched("sentiment") && (
              <span className="ai-touched-badge">
                <Sparkles size={10} /> AI
              </span>
            )}
            <label>Sentiment</label>
            <select value={form.sentiment} onChange={(e) => set("sentiment", e.target.value)}>
              <option value="">Not set</option>
              {SENTIMENTS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div className={`field ${touched("followUpDate") ? "ai-touched" : ""}`}>
            {touched("followUpDate") && (
              <span className="ai-touched-badge">
                <Sparkles size={10} /> AI
              </span>
            )}
            <label>Follow-up Date</label>
            <input
              type="date"
              value={form.followUpDate || ""}
              onChange={(e) => set("followUpDate", e.target.value)}
            />
          </div>
        </div>

        <ChipField
          label="Attendees"
          values={form.attendees}
          aiTouched={touched("attendees")}
          placeholder="Enter names..."
          onAdd={(v) => set("attendees", [...form.attendees, v])}
          onRemove={(idx) => set("attendees", form.attendees.filter((_, i) => i !== idx))}
        />

        <div className={`field ${touched("topicsDiscussed") ? "ai-touched" : ""}`} style={{ marginTop: 14 }}>
          {touched("topicsDiscussed") && (
            <span className="ai-touched-badge">
              <Sparkles size={10} /> AI
            </span>
          )}
          <label>Topics Discussed</label>
          <textarea
            placeholder="Enter key discussion points..."
            value={form.topicsDiscussed}
            onChange={(e) => set("topicsDiscussed", e.target.value)}
          />
        </div>

        <div style={{ marginTop: 14 }}>
          <ChipField
            label="Materials Shared / Samples Distributed"
            values={form.materialsShared}
            aiTouched={touched("materialsShared")}
            placeholder="e.g. Brochure, Sample Pack"
            onAdd={(v) => set("materialsShared", [...form.materialsShared, v])}
            onRemove={(idx) =>
              set("materialsShared", form.materialsShared.filter((_, i) => i !== idx))
            }
          />
        </div>

        <div className={`field ${touched("followUpActions") ? "ai-touched" : ""}`} style={{ marginTop: 14 }}>
          {touched("followUpActions") && (
            <span className="ai-touched-badge">
              <Sparkles size={10} /> AI
            </span>
          )}
          <label>Follow-up Actions</label>
          <textarea
            placeholder="What needs to happen next?"
            value={form.followUpActions}
            onChange={(e) => set("followUpActions", e.target.value)}
          />
        </div>

        <div className={`field ${touched("notes") ? "ai-touched" : ""}`} style={{ marginTop: 14 }}>
          {touched("notes") && (
            <span className="ai-touched-badge">
              <Sparkles size={10} /> AI
            </span>
          )}
          <label>Notes</label>
          <textarea
            placeholder="Additional notes..."
            value={form.notes}
            onChange={(e) => set("notes", e.target.value)}
          />
        </div>

        <div className="form-section-title">AI-Generated Insights</div>
        {form.summary || form.keyPoints?.length || form.suggestedNextSteps?.length ? (
          <div className="ai-summary-card">
            {form.summary && (
              <>
                <div className="label">
                  <Sparkles size={12} /> Interaction Summary
                </div>
                <p>{form.summary}</p>
              </>
            )}

            {form.meetingOutcome && (
              <>
                <div className="label" style={{ marginTop: 12 }}>
                  <Tag size={12} /> Meeting Outcome
                </div>
                <p>{form.meetingOutcome}</p>
              </>
            )}

            {form.keyPoints?.length > 0 && (
              <>
                <div className="label" style={{ marginTop: 12 }}>
                  <ListChecks size={12} /> Key Discussion Points
                </div>
                <ul className="bullet-list">
                  {form.keyPoints.map((k, i) => (
                    <li key={i}>{k}</li>
                  ))}
                </ul>
              </>
            )}

            {entityGroups.length > 0 && (
              <>
                <div className="label" style={{ marginTop: 12 }}>
                  <Tag size={12} /> Extracted Entities
                </div>
                {entityGroups.map(([group, values]) => (
                  <div key={group} style={{ marginBottom: 6 }}>
                    <strong style={{ fontSize: 12, textTransform: "capitalize" }}>{group}: </strong>
                    <span style={{ fontSize: 12.5 }}>{values.join(", ")}</span>
                  </div>
                ))}
              </>
            )}

            {form.suggestedNextSteps?.length > 0 && (
              <>
                <div className="label" style={{ marginTop: 12 }}>
                  <Lightbulb size={12} /> Suggested Next Steps
                </div>
                <ul className="bullet-list">
                  {form.suggestedNextSteps.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        ) : (
          <p className="empty-hint">
            Nothing yet &mdash; log an interaction via the AI Assistant and this section fills in automatically.
          </p>
        )}

        <div style={{ display: "flex", gap: 10, marginTop: 22 }}>
          <button className="btn primary" disabled={!form.id || !dirty || saving} onClick={handleSave}>
            <Save size={13} style={{ marginRight: 6, verticalAlign: -2 }} />
            {saving ? "Saving..." : "Save changes"}
          </button>
          <button className="btn" onClick={() => dispatch(resetForm())}>
            New interaction
          </button>
        </div>
      </div>
    </section>
  );
}
