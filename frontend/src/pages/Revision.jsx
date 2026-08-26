// frontend/src/pages/Revision.jsx
// --------------------------------
// Phase 4 — Exam Revision Mode
// Enter days left → get priority topics, study plan,
// formula sheet, confused concepts, quick notes.

import { useState } from "react";
import { useApp } from "../context/AppContext";
import {
  getPriorityTopics, getStudyPlan, getFormulaSheet,
  getConfusedConcepts, getRevisionNotes,
} from "../services/api";
import ReactMarkdown from "react-markdown";
import toast from "react-hot-toast";
import { Target, Calendar, FlaskConical, AlertTriangle, BookOpen, Download } from "lucide-react";

// ── Tab button ────────────────────────────────────────────────────────────────
function Tab({ active, onClick, icon: Icon, label }) {
  return (
    <button onClick={onClick} style={{
      display: "flex", alignItems: "center", gap: 6,
      padding: "8px 16px", borderRadius: "var(--radius)",
      border: "none", cursor: "pointer", fontSize: 13, fontWeight: active ? 600 : 400,
      background: active ? "rgba(108,99,255,0.15)" : "transparent",
      color: active ? "var(--accent2)" : "var(--text2)",
      transition: "all .15s",
    }}>
      <Icon size={14} /> {label}
    </button>
  );
}

// ── Priority topic row ────────────────────────────────────────────────────────
function TopicRow({ topic, rank, frequency, totalMarks, studyMins, priorityScore, questionTypes }) {
  const color = rank < 3 ? "var(--red)" : rank < 7 ? "var(--amber)" : "var(--green)";
  const emoji = rank < 3 ? "🔴" : rank < 7 ? "🟡" : "🟢";
  return (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "12px 16px", background: "var(--bg3)",
      border: `1px solid var(--border)`, borderLeft: `3px solid ${color}`,
      borderRadius: "var(--radius)", marginBottom: 8,
    }}>
      <div>
        <div style={{ fontSize: 14, fontWeight: 500, color: "var(--text)" }}>
          {emoji} #{rank + 1} &nbsp; {topic}
        </div>
        <div style={{ fontSize: 11, color: "var(--text3)", marginTop: 3 }}>
          Asked {frequency}× · {totalMarks} total marks · {questionTypes} · ~{studyMins} min
        </div>
      </div>
      <div style={{ textAlign: "right", flexShrink: 0, marginLeft: 12 }}>
        <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text)" }}>{priorityScore}</div>
        <div style={{ fontSize: 10, color: "var(--text3)" }}>priority score</div>
      </div>
    </div>
  );
}

// ── Day card ──────────────────────────────────────────────────────────────────
function DayCard({ day }) {
  const [open, setOpen] = useState(day.day === 1);
  const isRevDay = day.date_label?.includes("Revision");
  return (
    <div style={{ border: "1px solid var(--border)", borderRadius: "var(--radius)", marginBottom: 10, overflow: "hidden" }}>
      <button onClick={() => setOpen(o => !o)} style={{
        width: "100%", padding: "12px 16px", background: isRevDay ? "rgba(34,197,94,0.06)" : "var(--bg3)",
        border: "none", cursor: "pointer", textAlign: "left",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text)" }}>
          {isRevDay ? "🔁" : "📅"} {day.date_label}
        </span>
        <span style={{ fontSize: 12, color: "var(--text3)" }}>
          {day.topics?.length} topics · {Math.floor(day.total_minutes / 60)}h {day.total_minutes % 60}m
        </span>
      </button>
      {open && (
        <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)", background: "var(--bg2)" }}>
          {day.tasks?.map((t, i) => (
            <div key={i} style={{ fontSize: 13, color: "var(--text2)", marginBottom: 6 }}>• {t}</div>
          ))}
          {day.topics?.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 6, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".04em" }}>Topics</div>
              {day.topics.map((t, i) => (
                <div key={i} style={{ fontSize: 12, color: "var(--text2)", marginBottom: 4 }}>
                  <code style={{ background: "var(--bg3)", padding: "1px 6px", borderRadius: 4, fontSize: 11 }}>{t.topic}</code>
                  &nbsp;~{t.study_time_mins} min · asked {t.frequency}×
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Revision page ────────────────────────────────────────────────────────
export default function Revision() {
  const { courseCode } = useApp();
  const [days, setDays]         = useState(3);
  const [hours, setHours]       = useState(4);
  const [loading, setLoading]   = useState(false);
  const [activeTab, setActiveTab] = useState("priority");

  const [priority, setPriority] = useState(null);
  const [plan, setPlan]         = useState(null);
  const [formula, setFormula]   = useState(null);
  const [confused, setConfused] = useState(null);

  // Quick notes state
  const [notesTopic, setNotesTopic] = useState("");
  const [notes, setNotes]           = useState("");
  const [notesLoading, setNotesLoading] = useState(false);
  const [notesCache, setNotesCache]     = useState({});

  const generate = async () => {
    if (!courseCode) return toast.error("Set your course code first");
    setLoading(true);
    try {
      toast.loading("Building your revision plan...", { id: "rev" });

      const [p, pl, f, c] = await Promise.all([
        getPriorityTopics(courseCode, days),
        getStudyPlan(courseCode, days, hours),
        getFormulaSheet(courseCode),
        getConfusedConcepts(courseCode),
      ]);

      setPriority(p.data); setPlan(pl.data);
      setFormula(f.data?.formula_sheet); setConfused(c.data?.confused_concepts);
      toast.success("✅ Revision plan ready!", { id: "rev" });
      setActiveTab("priority");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed", { id: "rev" });
    } finally { setLoading(false); }
  };

  const loadNotes = async () => {
    if (!notesTopic.trim()) return toast.error("Enter a topic");
    if (notesCache[notesTopic]) { setNotes(notesCache[notesTopic]); return; }
    setNotesLoading(true);
    try {
      const res = await getRevisionNotes(courseCode, notesTopic);
      const n = res.data.notes;
      setNotes(n);
      setNotesCache(p => ({ ...p, [notesTopic]: n }));
    } catch { toast.error("Could not generate notes"); }
    finally { setNotesLoading(false); }
  };

  const downloadText = (text, filename) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: "text/markdown" }));
    a.download = filename; a.click();
  };

  const hasData = priority || plan || formula || confused;

  return (
    <div style={{ padding: "32px 32px 48px", maxWidth: 900, margin: "0 auto" }}>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 29, fontWeight: 700 }}>🎯 Exam Revision Mode</h1>
        <p style={{ color: "var(--text2)", fontSize: 13, marginTop: 4 }}>
          Tell us your exam countdown — we'll build a personalised revision plan from your notes and PYQ data.
        </p>
      </div>

      {/* Config */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: 16, alignItems: "flex-end" }}>
          <div>
            <label className="label">📅 Days until exam</label>
            <input className="input" type="number" min={1} max={30}
              value={days} onChange={e => setDays(Number(e.target.value))} />
          </div>
          <div>
            <label className="label">⏱️ Study hours per day</label>
            <input className="input" type="number" min={1} max={12}
              value={hours} onChange={e => setHours(Number(e.target.value))} />
          </div>
          <button className="btn btn-primary" onClick={generate} disabled={loading}
            style={{ padding: "10px 20px", alignSelf: "flex-end" }}>
            {loading ? <><span className="spinner" /> Building...</> : "🚀 Build Plan"}
          </button>
        </div>
      </div>

      {/* Empty state */}
      {!hasData && (
        <div style={{ textAlign: "center", padding: "60px 24px", background: "var(--bg2)", borderRadius: "var(--radius-lg)", border: "1px dashed var(--border)" }}>
          <Target size={44} color="var(--text3)" style={{ margin: "0 auto 16px" }} />
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>Enter your exam countdown above</div>
          <div style={{ fontSize: 13, color: "var(--text2)" }}>
            Upload lecture notes + PYQ papers first for the best results
          </div>
        </div>
      )}

      {/* Tabs + content */}
      {hasData && (
        <>
          {/* Tab bar */}
          <div style={{ display: "flex", gap: 4, marginBottom: 20, flexWrap: "wrap" }}>
            <Tab active={activeTab === "priority"} onClick={() => setActiveTab("priority")} icon={Target}        label="Priority Topics" />
            <Tab active={activeTab === "plan"}     onClick={() => setActiveTab("plan")}     icon={Calendar}      label="Study Plan" />
            <Tab active={activeTab === "formula"}  onClick={() => setActiveTab("formula")}  icon={FlaskConical}  label="Formula Sheet" />
            <Tab active={activeTab === "confused"} onClick={() => setActiveTab("confused")} icon={AlertTriangle} label="Confused Concepts" />
            <Tab active={activeTab === "notes"}    onClick={() => setActiveTab("notes")}    icon={BookOpen}      label="Quick Notes" />
          </div>

          {/* Priority Topics */}
          {activeTab === "priority" && priority && (
            <div>
              {priority.strategy && (
                <div style={{ background: "rgba(108,99,255,0.08)", border: "1px solid rgba(108,99,255,0.2)", borderRadius: "var(--radius)", padding: "12px 16px", marginBottom: 20, fontSize: 13, color: "var(--text2)" }}>
                  {priority.strategy}
                </div>
              )}
              {/* Stats */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 20 }}>
                {[
                  ["Topics to cover", priority.topics?.length],
                  ["Total study time", `${Math.floor(priority.topics?.reduce((s, t) => s + (t.study_time_mins || 30), 0) / 60)}h ${priority.topics?.reduce((s, t) => s + (t.study_time_mins || 30), 0) % 60}m`],
                  ["Days left", priority.days_left],
                ].map(([label, val]) => (
                  <div key={label} className="card" style={{ textAlign: "center", padding: "14px 12px" }}>
                    <div style={{ fontSize: 22, fontWeight: 700 }}>{val}</div>
                    <div style={{ fontSize: 11, color: "var(--text3)", marginTop: 2 }}>{label}</div>
                  </div>
                ))}
              </div>
              {priority.topics?.map((t, i) => (
                <TopicRow key={i} rank={i} topic={t.topic} frequency={t.frequency}
                  totalMarks={t.total_marks} studyMins={t.study_time_mins}
                  priorityScore={t.priority_score} questionTypes={t.question_types} />
              ))}
              {!priority.topics?.length && (
                <div style={{ color: "var(--text3)", fontSize: 13 }}>No PYQ data found. Upload previous year papers first.</div>
              )}
            </div>
          )}

          {/* Study Plan */}
          {activeTab === "plan" && plan && (
            <div>
              <div style={{ fontSize: 14, color: "var(--text2)", marginBottom: 16 }}>
                {plan.summary} · {plan.hours_per_day}h/day · Last day reserved for full revision
              </div>
              {plan.days?.map((d, i) => <DayCard key={i} day={d} />)}
            </div>
          )}

          {/* Formula Sheet */}
          {activeTab === "formula" && (
            <div>
              {formula ? (
                <>
                  <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
                    <button className="btn btn-secondary"
                      onClick={() => downloadText(formula, `${courseCode}_formula_sheet.md`)}>
                      <Download size={13} /> Download
                    </button>
                  </div>
                  <div className="card markdown"><ReactMarkdown>{formula}</ReactMarkdown></div>
                </>
              ) : (
                <div style={{ color: "var(--text3)", fontSize: 13 }}>Upload lecture notes first to generate a formula sheet.</div>
              )}
            </div>
          )}

          {/* Confused Concepts */}
          {activeTab === "confused" && (
            <div>
              {confused ? (
                <div className="card markdown"><ReactMarkdown>{confused}</ReactMarkdown></div>
              ) : (
                <div style={{ color: "var(--text3)", fontSize: 13 }}>Upload notes and PYQ papers first.</div>
              )}
            </div>
          )}

          {/* Quick Notes */}
          {activeTab === "notes" && (
            <div>
              <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
                <input className="input" placeholder="Enter topic e.g. Fick's Law"
                  value={notesTopic} onChange={e => setNotesTopic(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && loadNotes()} />
                <button className="btn btn-primary" onClick={loadNotes} disabled={notesLoading}>
                  {notesLoading ? <><span className="spinner" /></> : <><BookOpen size={14} /> Get Notes</>}
                </button>
              </div>

              {/* Quick-pick from priority topics */}
              {priority?.topics?.length > 0 && (
                <div style={{ marginBottom: 16 }}>
                  <div className="label">Quick pick from your priority topics:</div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {priority.topics.slice(0, 5).map(t => (
                      <button key={t.topic} className="btn btn-secondary"
                        onClick={() => { setNotesTopic(t.topic); }}
                        style={{ fontSize: 12 }}>
                        {t.topic}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {notes && (
                <>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <div style={{ fontSize: 14, fontWeight: 600 }}>{notesTopic}</div>
                    <button className="btn btn-secondary"
                      onClick={() => downloadText(notes, `${notesTopic.replace(/ /g, "_")}_notes.md`)}>
                      <Download size={13} /> Download
                    </button>
                  </div>
                  <div className="card markdown"><ReactMarkdown>{notes}</ReactMarkdown></div>
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}