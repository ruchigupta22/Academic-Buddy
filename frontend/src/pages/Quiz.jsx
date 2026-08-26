/**
 * pages/Quiz.jsx
 * Phase 3 — Quiz generator with MCQ, short answer, numerical.
 */

import { useState } from "react";
import { useApp } from "../context/AppContext";
import { generateQuiz, checkAnswer, saveQuiz } from "../services/api";
import ReactMarkdown from "react-markdown";
import toast from "react-hot-toast";
import { BookOpen, ChevronRight, RotateCcw, CheckCircle, XCircle, AlertCircle } from "lucide-react";

// ── Config panel ───────────────────────────────────────────────────────────────
function QuizConfig({ onGenerate, weakTopics }) {
  const [topic, setTopic]       = useState("");
  const [difficulty, setDiff]   = useState("medium");
  const [count, setCount]       = useState(3);
  const [types, setTypes]       = useState({ mcq: true, short: true, numerical: true });
  const [loading, setLoading]   = useState(false);

  const toggle = (t) => setTypes(p => ({ ...p, [t]: !p[t] }));

  const generate = async () => {
    if (!topic.trim()) return toast.error("Enter a topic");
    const selected = Object.entries(types).filter(([, v]) => v).map(([k]) => k);
    if (!selected.length) return toast.error("Select at least one question type");
    setLoading(true);
    try { await onGenerate(topic, difficulty, selected, count); }
    finally { setLoading(false); }
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", padding: "40px 24px" }}>
      <div style={{ textAlign: "center", marginBottom: 32 }}>
        <BookOpen size={36} color="var(--accent)" style={{ margin: "0 auto 12px" }} />
        <h1 style={{ fontSize: 36, fontWeight: 700 }}>Generate a Quiz</h1>
        <p style={{ color: "var(--text2)", fontSize: 13, marginTop: 6 }}>
          Questions are written directly from your uploaded lecture notes
        </p>
      </div>

      {/* Weak topic quick picks */}
      {weakTopics?.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <div className="label">🔴 Your weak topics — quick pick:</div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {weakTopics.slice(0, 3).map(t => (
              <button key={t} className="btn btn-secondary" onClick={() => setTopic(t)} style={{ fontSize: 12 }}>{t}</button>
            ))}
          </div>
        </div>
      )}

      <div className="card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <label className="label">Topic</label>
          <input className="input" placeholder="e.g. Fick's Law, Heat Transfer, Reynolds Number"
            value={topic} onChange={e => setTopic(e.target.value)} />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <label className="label">Difficulty</label>
            <select className="input" value={difficulty} onChange={e => setDiff(e.target.value)}>
              <option value="easy">Easy — Definitions &amp; recall</option>
              <option value="medium">Medium — Application</option>
              <option value="hard">Hard — Derivation &amp; analysis</option>
            </select>
          </div>
          <div>
            <label className="label">Questions per type</label>
            <input className="input" type="number" min={1} max={5} value={count}
              onChange={e => setCount(Number(e.target.value))} />
          </div>
        </div>

        <div>
          <label className="label">Question types</label>
          <div style={{ display: "flex", gap: 8 }}>
            {[["mcq", "Multiple Choice"], ["short", "Short Answer"], ["numerical", "Numerical"]].map(([k, label]) => (
              <button key={k} onClick={() => toggle(k)}
                className={`btn ${types[k] ? "btn-primary" : "btn-secondary"}`}
                style={{ flex: 1, justifyContent: "center", fontSize: 12 }}>
                {label}
              </button>
            ))}
          </div>
        </div>

        <button className="btn btn-primary btn-full" onClick={generate} disabled={loading} style={{ marginTop: 4 }}>
          {loading ? <><span className="spinner" /> Generating questions...</> : <>🚀 Generate Quiz</>}
        </button>
      </div>
    </div>
  );
}

// ── Quiz question card ─────────────────────────────────────────────────────────
function QuestionCard({ q, idx, total, answer, onAnswer, result, submitted }) {
  const typeLabel = { mcq: "MCQ", short: "Short Answer", numerical: "Numerical" };
  const typeColor = { mcq: "badge-purple", short: "badge-green", numerical: "badge-amber" };
  const diffColor = { easy: "badge-green", medium: "badge-amber", hard: "badge-red" };

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <span className={`badge ${typeColor[q.type]}`}>{typeLabel[q.type]}</span>
        <span className={`badge ${diffColor[q.difficulty]}`}>{q.difficulty}</span>
        <span style={{ fontSize: 11, color: "var(--text3)", marginLeft: "auto" }}>
          Q{idx + 1}/{total} · {q.marks} marks
        </span>
      </div>

      <div style={{ fontSize: 15, fontWeight: 500, color: "var(--text)", marginBottom: 16, lineHeight: 1.6 }}>
        {q.question}
      </div>

      {/* MCQ options */}
      {q.type === "mcq" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {q.options?.map((opt, i) => {
            const letter = opt[0].toUpperCase();
            const isCorrect = submitted && letter === q.correct_answer?.toUpperCase()?.trim()[0];
            const isWrong   = submitted && letter === answer?.toUpperCase()?.trim()[0] && !isCorrect;
            return (
              <button key={i} onClick={() => !submitted && onAnswer(letter)}
                style={{
                  padding: "10px 14px", borderRadius: "var(--radius)", border: "1px solid",
                  textAlign: "left", cursor: submitted ? "default" : "pointer", fontSize: 13,
                  background: isCorrect ? "rgba(34,197,94,0.1)" : isWrong ? "rgba(239,68,68,0.1)" : answer === letter && !submitted ? "rgba(108,99,255,0.1)" : "var(--bg3)",
                  borderColor: isCorrect ? "var(--green)" : isWrong ? "var(--red)" : answer === letter && !submitted ? "var(--accent)" : "var(--border)",
                  color: "var(--text)",
                }}>
                <span style={{ color: isCorrect ? "var(--green)" : isWrong ? "var(--red)" : "var(--text2)", marginRight: 8, fontWeight: 600 }}>
                  {isCorrect ? "✓" : isWrong ? "✗" : letter}
                </span>
                {opt.slice(2)}
              </button>
            );
          })}
        </div>
      )}

      {/* Text answer */}
      {(q.type === "short" || q.type === "numerical") && !submitted && (
        <textarea className="input"
          placeholder={q.type === "numerical" ? "Show all steps, formulas, and units..." : "Write your answer..."}
          value={answer || ""} onChange={e => onAnswer(e.target.value)}
          style={{ height: q.type === "numerical" ? 120 : 90 }} />
      )}

      {/* Result after submit */}
      {submitted && result && (
        <div>
          {(q.type === "short" || q.type === "numerical") && answer && (
            <div style={{ background: "var(--bg3)", borderRadius: "var(--radius)", padding: "10px 14px", marginBottom: 10, fontSize: 13 }}>
              <div style={{ color: "var(--text3)", marginBottom: 4, fontSize: 11, fontWeight: 600, textTransform: "uppercase" }}>Your answer</div>
              <div style={{ color: "var(--text)" }}>{answer}</div>
            </div>
          )}
          <div style={{
            background: result.is_correct ? "rgba(34,197,94,0.08)" : result.score > 0 ? "rgba(245,158,11,0.08)" : "rgba(239,68,68,0.08)",
            border: `1px solid ${result.is_correct ? "rgba(34,197,94,0.2)" : result.score > 0 ? "rgba(245,158,11,0.2)" : "rgba(239,68,68,0.2)"}`,
            borderRadius: "var(--radius)", padding: "12px 14px",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontWeight: 600, fontSize: 13,
                color: result.is_correct ? "var(--green)" : result.score > 0 ? "var(--amber)" : "var(--red)" }}>
                {result.is_correct ? <CheckCircle size={15} /> : result.score > 0 ? <AlertCircle size={15} /> : <XCircle size={15} />}
                Score: {result.score}/{q.marks}
              </div>
            </div>
            <div style={{ fontSize: 13, color: "var(--text2)" }}>{result.feedback}</div>
          </div>
          {q.explanation && (
            <div style={{ marginTop: 10, padding: "10px 14px", background: "rgba(108,99,255,0.06)", border: "1px solid rgba(108,99,255,0.15)", borderRadius: "var(--radius)", fontSize: 13, color: "var(--text2)" }}>
              💡 {q.explanation}
            </div>
          )}
          {(q.type === "short" || q.type === "numerical") && q.correct_answer && (
            <details style={{ marginTop: 10 }}>
              <summary style={{ cursor: "pointer", fontSize: 12, color: "var(--accent)", fontWeight: 500 }}>📖 View model answer</summary>
              <div style={{ marginTop: 8, padding: "10px 14px", background: "var(--bg3)", borderRadius: "var(--radius)", fontSize: 13, color: "var(--text2)" }}>
                <ReactMarkdown>{q.correct_answer}</ReactMarkdown>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}

// ── Score banner ───────────────────────────────────────────────────────────────
function ScoreBanner({ score, max }) {
  const pct = max ? Math.round(score / max * 100) : 0;
  const [color, emoji, label] = pct >= 80 ? ["var(--green)", "🎉", "Excellent!"]
    : pct >= 60 ? ["var(--amber)", "👍", "Good"]
    : pct >= 40 ? ["#f97316", "📖", "Needs revision"]
    : ["var(--red)", "❗", "Review required"];
  return (
    <div style={{ background: `${color}15`, border: `1px solid ${color}44`, borderRadius: "var(--radius-lg)", padding: "18px 24px", marginBottom: 24, display: "flex", alignItems: "center", gap: 16 }}>
      <div style={{ fontSize: 36 }}>{emoji}</div>
      <div>
        <div style={{ fontSize: 24, fontWeight: 700, color }}>{score}/{max} marks · {pct}%</div>
        <div style={{ fontSize: 14, color: "var(--text2)" }}>{label}</div>
      </div>
    </div>
  );
}

// ── Main Quiz page ─────────────────────────────────────────────────────────────
export default function Quiz() {
  const { username, courseCode } = useApp();
  const [questions, setQuestions] = useState([]);
  const [topic, setTopic]         = useState("");
  const [difficulty, setDiff]     = useState("medium");
  const [answers, setAnswers]     = useState({});
  const [results, setResults]     = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore]         = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [weakTopics]              = useState([]);

  const handleGenerate = async (topic, difficulty, types, count) => {
    if (!courseCode) return toast.error("Set your course code first");
    const res = await generateQuiz(courseCode, topic, types, count, difficulty);
    if (res.data.error) return toast.error(res.data.error);
    if (!res.data.total_questions) return toast.error("No questions generated — upload more lecture notes");
    setQuestions(res.data.questions);
    setTopic(res.data.topic); setDiff(difficulty);
    setAnswers({}); setResults({}); setSubmitted(false); setScore(0);
    toast.success(`✅ ${res.data.total_questions} questions generated!`);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    let total = 0;
    const newResults = {};
    for (let idx = 0; idx < questions.length; idx++) {
      const q = questions[idx];
      const student = answers[idx] || "(no answer)";
      try {
        const res = await checkAnswer(q.question, q.type, q.correct_answer, student, q.marks);
        newResults[idx] = res.data;
        total += res.data.score || 0;
      } catch {
        newResults[idx] = { score: 0, feedback: "Could not evaluate.", is_correct: false };
      }
    }
    setResults(newResults); setScore(total); setSubmitted(true);

    // Phase 5: save quiz
    if (username) {
      saveQuiz(username, courseCode, topic, difficulty, questions, newResults).catch(() => {});
    }
    setSubmitting(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const reset = () => { setQuestions([]); setAnswers({}); setResults({}); setSubmitted(false); };
  const retry = () => { setAnswers({}); setResults({}); setSubmitted(false); };

  if (!questions.length) return <QuizConfig onGenerate={handleGenerate} weakTopics={weakTopics} />;

  const maxMarks = questions.reduce((s, q) => s + (q.marks || 2), 0);
  const answered = Object.values(answers).filter(Boolean).length;

  return (
    <div style={{ maxWidth: 760, margin: "0 auto", padding: "32px 24px 48px" }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700 }}>{topic}</h1>
          <div style={{ fontSize: 12, color: "var(--text3)", marginTop: 2 }}>
            {questions.length} questions · {difficulty}
          </div>
        </div>
        <button className="btn btn-secondary" onClick={reset}><RotateCcw size={14} /> New Quiz</button>
      </div>

      {/* Score banner */}
      {submitted && <ScoreBanner score={score} max={maxMarks} />}

      {/* Progress */}
      {!submitted && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "var(--text3)", marginBottom: 6 }}>
            <span>{answered}/{questions.length} answered</span>
            <span>{maxMarks} total marks</span>
          </div>
          <div className="progress">
            <div className="progress-fill" style={{ width: `${answered / questions.length * 100}%`, background: "var(--accent)" }} />
          </div>
        </div>
      )}

      {/* Questions */}
      {questions.map((q, i) => (
        <QuestionCard key={i} q={q} idx={i} total={questions.length}
          answer={answers[i]} onAnswer={v => setAnswers(p => ({ ...p, [i]: v }))}
          result={results[i]} submitted={submitted} />
      ))}

      {/* Submit / retry */}
      {!submitted ? (
        <div>
          {answered < questions.length && (
            <div style={{ color: "var(--amber)", fontSize: 13, marginBottom: 12, display: "flex", alignItems: "center", gap: 6 }}>
              <AlertCircle size={14} /> {questions.length - answered} questions unanswered
            </div>
          )}
          <button className="btn btn-primary btn-full" onClick={handleSubmit} disabled={submitting} style={{ padding: "12px" }}>
            {submitting ? <><span className="spinner" /> Evaluating answers...</> : <>✅ Submit Quiz</>}
          </button>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <button className="btn btn-secondary btn-full" onClick={retry}><RotateCcw size={14} /> Try Again</button>
          <button className="btn btn-primary btn-full" onClick={reset}><ChevronRight size={14} /> New Quiz</button>
        </div>
      )}
    </div>
  );
}