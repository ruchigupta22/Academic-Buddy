// frontend/src/pages/PYQ.jsx
// ---------------------------
// Phase 2 — PYQ Intelligence
// Ask about exam patterns or generate a full analysis report.

import { useState } from "react";
import { useApp } from "../context/AppContext";
import { askPYQ, getPYQReport } from "../services/api";
import ReactMarkdown from "react-markdown";
import toast from "react-hot-toast";
import { BarChart2, Search, FileText } from "lucide-react";

const EXAMPLES = [
  "What topics are most frequently asked?",
  "Which topics carry the most marks?",
  "What type of questions appear most — numerical or theory?",
  "What should I prioritise for exam preparation?",
  "Which topics are asked every year without fail?",
];

export default function PYQ() {
  const { courseCode }    = useApp();
  const [tab, setTab]     = useState("ask");  // "ask" | "report"
  const [question, setQ]  = useState("");
  const [answer, setAns]  = useState(null);
  const [rawData, setRaw] = useState(null);
  const [report, setRep]  = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return toast.error("Enter a question");
    if (!courseCode) return toast.error("Set your course code first");
    setLoading(true); setAns(null); setRaw(null);
    try {
      const res = await askPYQ(question, courseCode);
      setAns(res.data.answer);
      setRaw(res.data.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to get answer");
    } finally { setLoading(false); }
  };

  const handleReport = async () => {
    if (!courseCode) return toast.error("Set your course code first");
    setLoading(true); setRep(null);
    try {
      const res = await getPYQReport(courseCode);
      setRep(res.data.report);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to generate report");
    } finally { setLoading(false); }
  };

  return (
    <div style={{ padding: "32px 32px 48px", maxWidth: 860, margin: "0 auto" }}>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 36, fontWeight: 700 }}>📊 PYQ Intelligence</h1>
        <p style={{ color: "var(--text2)", fontSize: 15, marginTop: 4 }}>
          Upload past exam papers to unlock topic frequency analysis, trend detection, and exam pattern insights.
        </p>
      </div>

      {/* Tab toggle */}
      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        {[["ask", Search, "Ask About Patterns"], ["report", FileText, "Full Analysis Report"]].map(([id, Icon, label]) => (
          <button key={id} onClick={() => setTab(id)}
            className={`btn ${tab === id ? "btn-primary" : "btn-secondary"}`}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* ASK TAB */}
      {tab === "ask" && (
        <div>
          {/* Example questions */}
          <div style={{ marginBottom: 16 }}>
            <div className="label">Try an example:</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {EXAMPLES.map(q => (
                <button key={q} className="btn btn-secondary"
                  onClick={() => setQ(q)} style={{ fontSize: 16 }}>
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Input */}
          <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
            <input className="input"
              placeholder="Ask anything about your exam patterns..."
              value={question} onChange={e => setQ(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleAsk()} />
            <button className="btn btn-primary" onClick={handleAsk} disabled={loading}>
              {loading ? <span className="spinner" /> : <Search size={15} />}
            </button>
          </div>

          {/* Answer */}
          {answer && (
            <div>
              <div className="card markdown" style={{ marginBottom: 16 }}>
                <ReactMarkdown>{answer}</ReactMarkdown>
              </div>

              {/* Raw data toggle */}
              {rawData?.top_topics?.length > 0 && (
                <details>
                  <summary style={{ cursor: "pointer", fontSize: 12, color: "var(--accent)", fontWeight: 500, marginBottom: 10 }}>
                    📊 View raw database counts
                  </summary>
                  <div className="card" style={{ marginTop: 10 }}>
                    <div style={{ overflowX: "auto" }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                        <thead>
                          <tr style={{ borderBottom: "1px solid var(--border)" }}>
                            {["Topic", "Frequency", "Total Marks", "Avg Marks", "Types"].map(h => (
                              <th key={h} style={{ textAlign: "left", padding: "8px 10px", color: "var(--text3)", fontWeight: 600, fontSize: 11, textTransform: "uppercase", letterSpacing: ".04em" }}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {rawData.top_topics.map((t, i) => (
                            <tr key={i} style={{ borderBottom: "0.5px solid var(--border)" }}>
                              <td style={{ padding: "8px 10px", color: "var(--text)", fontSize: 13 }}>{t.topic}</td>
                              <td style={{ padding: "8px 10px", color: "var(--accent)", fontWeight: 600 }}>{t.frequency}</td>
                              <td style={{ padding: "8px 10px", color: "var(--text2)" }}>{t.total_marks}</td>
                              <td style={{ padding: "8px 10px", color: "var(--text2)" }}>{t.avg_marks}</td>
                              <td style={{ padding: "8px 10px", color: "var(--text3)", fontSize: 11 }}>{t.question_types}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </details>
              )}
            </div>
          )}

          {/* Empty state */}
          {!answer && !loading && (
            <div style={{ textAlign: "center", padding: "48px 24px", background: "var(--bg2)", borderRadius: "var(--radius-lg)", border: "1px dashed var(--border)" }}>
              <BarChart2 size={40} color="var(--text3)" style={{ margin: "0 auto 12px" }} />
              <div style={{ fontSize: 15, fontWeight: 500, color: "var(--text2)" }}>
                Upload PYQ papers to unlock pattern analysis
              </div>
              <div style={{ fontSize: 12, color: "var(--text3)", marginTop: 6 }}>
                Use the Upload button in the sidebar → PYQ Paper
              </div>
            </div>
          )}
        </div>
      )}

      {/* REPORT TAB */}
      {tab === "report" && (
        <div>
          <p style={{ color: "var(--text2)", fontSize: 13, marginBottom: 20 }}>
            Generates a complete AI-powered analysis of all uploaded PYQ papers —
            covering top topics, exam patterns, trends, and study priorities.
          </p>

          <button className="btn btn-primary" onClick={handleReport} disabled={loading}
            style={{ marginBottom: 24 }}>
            {loading
              ? <><span className="spinner" /> Analysing all PYQ papers...</>
              : <><FileText size={14} /> Generate Full Analysis Report</>}
          </button>

          {report && (
            <div className="card markdown">
              <ReactMarkdown>{report}</ReactMarkdown>
            </div>
          )}
        </div>
      )}
    </div>
  );
}