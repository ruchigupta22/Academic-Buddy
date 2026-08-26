/**
 * pages/Dashboard.jsx
 * Phase 5 — Personalised learning dashboard.
 */

import { useState, useEffect, useCallback } from "react";
import { useApp } from "../context/AppContext";
import { getProfileSummary, getRecommendations, getAIMessage, getTopicAccuracy } from "../services/api";
import { Brain, Zap, Target, TrendingUp, BookOpen, MessageSquare, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";

function StatBox({ icon: Icon, value, label, color = "var(--accent)" }) {
  return (
    <div className="card" style={{ textAlign: "center", padding: "20px 26px" }}>
      <Icon size={40} color={color} style={{ margin: "10 auto 8px" }} />
      <div style={{ fontSize: 28, fontWeight: 700, color: "var(--text)" }}>{value ?? "—"}</div>
      <div style={{ fontSize: 20, color: "var(--text3)", marginTop: 2 }}>{label}</div>
    </div>
  );
}

function AccuracyBar({ topic, accuracy, attempts }) {
  const color = accuracy >= 80 ? "var(--green)" : accuracy >= 60 ? "var(--amber)" : "var(--red)";
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span style={{ fontSize: 23, color: "var(--text)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "70%" }}>{topic}</span>
        <span style={{ fontSize: 22, fontWeight: 600, color, flexShrink: 0 }}>{accuracy?.toFixed(0)}% · {attempts} attempts</span>
      </div>
      <div className="progress">
        <div className="progress-fill" style={{ width: `${accuracy}%`, background: color }} />
      </div>
    </div>
  );
}

function RecCard({ topic, reason, action, priority, accuracy }) {
  const colors = { high: "var(--red)", medium: "var(--amber)", low: "var(--green)" };
  const icons  = { high: "🔴", medium: "🟡", low: "🟢" };
  const color  = colors[priority] || "var(--amber)";
  return (
    <div style={{
      background: "var(--bg3)", border: `5px solid var(--border)`,
      borderLeft: `5px solid ${color}`,
      borderRadius: "var(--radius)", padding: "12px 14px", marginBottom: 18,
    }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)", marginBottom: 3 }}>
        {icons[priority]} {topic}
      </div>
      <div style={{ fontSize: 12, color: "var(--text2)", marginBottom: 4 }}>
        {reason}{accuracy != null ? ` · ${accuracy.toFixed(0)}% accuracy` : ""}
      </div>
      <div style={{ fontSize: 20, color, fontWeight: 500 }}>→ {action}</div>
    </div>
  );
}

export default function Dashboard() {
  const { username, courseCode } = useApp();
  const [profile, setProfile]   = useState(null);
  const [recs, setRecs]         = useState(null);
  const [accuracy, setAccuracy] = useState([]);
  const [aiMsg, setAiMsg]       = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [loading, setLoading]   = useState(false);

  const load = useCallback(async () => {
    if (!username || !courseCode) return;
    setLoading(true);
    try {
      const [p, r, a] = await Promise.all([
        getProfileSummary(username, courseCode),
        getRecommendations(username, courseCode),
        getTopicAccuracy(username, courseCode),
      ]);
      setProfile(p.data);
      setRecs(r.data);
      setAccuracy(a.data);
    } catch {
      toast.error("Could not load dashboard");
    } finally {
      setLoading(false);
    }
  }, [username, courseCode]);

  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    load();
  }, [load]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const loadAIMessage = async () => {
    setAiLoading(true);
    try {
      const res = await getAIMessage(username, courseCode);
      setAiMsg(res.data.message);
    } catch { toast.error("Could not generate advice"); }
    finally { setAiLoading(false); }
  };

  if (!username || !courseCode) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", flexDirection: "column", gap: 16 }}>
      <div style={{ fontSize: 56 }}>🎓</div>
      <div style={{ fontSize: 20, fontWeight: 700 }}>Welcome to Exam Dost</div>
      <div style={{ color: "var(--text2)", textAlign: "center", maxWidth: 360 }}>
        Click your name in the sidebar to set your name and course code to get started.
      </div>
    </div>
  );

  const stats = profile?.quiz_stats || {};
  const initials = username.slice(0, 2).toUpperCase();

  return (
    <div style={{ padding: "32px 32px 48px", maxWidth: 1100, margin: "0 auto" }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{
            width: 52, height: 52, borderRadius: "50%",
            background: "linear-gradient(135deg,var(--accent),#9333ea)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 28, fontWeight: 700, color: "white",
          }}>{initials}</div>
          <div>
            <div style={{ fontSize: 32, fontWeight: 700 }}>Hi, {username}! 👋</div>
            <div style={{ color: "var(--text2)", fontSize: 13 }}>{courseCode} · Personal Learning Dashboard</div>
          </div>
        </div>
        <button className="btn btn-secondary" onClick={load} disabled={loading}>
          <RefreshCw size={17} className={loading ? "spinning" : ""} />
          Refresh
        </button>
      </div>

      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginBottom: 28 }}>
        <StatBox icon={BookOpen}      value={stats.total_quizzes ?? 0} label="Quizzes taken"    color="var(--accent)" />
        <StatBox icon={Target}        value={stats.avg_score != null ? `${stats.avg_score.toFixed(0)}%` : "—"} label="Average score" color="var(--green)" />
        <StatBox icon={TrendingUp}    value={stats.best_score != null ? `${stats.best_score.toFixed(0)}%` : "—"} label="Best score"    color="var(--amber)" />
        <StatBox icon={MessageSquare} value={profile?.chat_count ?? 0} label="Questions asked" color="var(--blue)" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>

        {/* Left: AI coach + weak/strong topics */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* AI Coach */}
          <div className="card">
            <div style={{ display: "flex", alignItems: "center", gap: 8, margin: 12 }}>
              <Brain size={24} color="var(--accent)" />
              <span style={{ fontWeight: 700, fontSize: 22 }}>AI Coach</span>
            </div>
            {aiMsg ? (
              <div style={{ fontSize: 20, color: "var(--text2)", lineHeight: 1.7, margin: 12 }}>{aiMsg}</div>
            ) : (
              <button className="btn btn-secondary btn-full" onClick={loadAIMessage} disabled={aiLoading}>
                {aiLoading ? <><span className="spinner" /> Generating...</> : <><Zap size={17} /> Get Personalised Advice</>}
              </button>
            )}
          </div>

          {/* Weak topics */}
          <div className="card">
            <div style={{ fontWeight: 600, fontSize: 22, margin: 12, color: "var(--red)" }}>
              ❌ Weak Topics
            </div>
            {profile?.weak_topics?.length ? profile.weak_topics.map(t => (
              <AccuracyBar key={t.topic} topic={t.topic} accuracy={t.accuracy_pct} attempts={t.total_attempts} />
            )) : (
              <div style={{ color: "var(--text3)", fontSize: 13, margin: 12 }}>Take quizzes to identify weak topics!</div>
            )}
          </div>

          {/* Strong topics */}
          {profile?.strong_topics?.length > 0 && (
            <div className="card">
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12, color: "var(--green)" }}>
                ✅ Strong Topics
              </div>
              {profile.strong_topics.map(t => (
                <div key={t.topic} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "8px 12px", background: "rgba(34,197,94,0.06)",
                  border: "1px solid rgba(34,197,94,0.15)", borderRadius: "var(--radius)", margin: 6,
                }}>
                  <span style={{ fontSize: 13 }}>{t.topic}</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "var(--green)" }}>{t.accuracy_pct?.toFixed(0)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Recommendations + recent quizzes */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

          {/* Recommendations */}
          <div className="card" style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: 19, margin: 4 }}>🎯 What to Study Next</div>
            {recs?.mode === "cold_start" && (
              <div style={{ fontSize: 12, color: "var(--text3)", margin: 12 }}>{recs.message}</div>
            )}
            {recs?.recommendations?.length ? recs.recommendations.slice(0, 6).map((r, i) => (
              <RecCard key={i} {...r} />
            )) : (
              <div style={{ color: "var(--text3)", fontSize: 16, margin: 12 }}>Take quizzes to get personalised recommendations!</div>
            )}
          </div>

          {/* Recent quizzes */}
          {profile?.recent_quizzes?.length > 0 && (
            <div className="card">
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12 }}>📈 Recent Quizzes</div>
              {profile.recent_quizzes.map((q, i) => {
                const pct = q.pct_score || 0;
                const color = pct >= 80 ? "var(--green)" : pct >= 60 ? "var(--amber)" : "var(--red)";
                return (
                  <div key={i} style={{
                    display: "flex", justifyContent: "space-between", alignItems: "center",
                    padding: "8px 12px", background: "var(--bg3)",
                    border: "1px solid var(--border)", borderRadius: "var(--radius)", marginBottom: 6,
                  }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{q.topic}</div>
                      <div style={{ fontSize: 11, color: "var(--text3)" }}>{q.difficulty} · {q.attempted_at?.slice(0, 10)}</div>
                    </div>
                    <div style={{ fontSize: 16, fontWeight: 700, color }}>{pct.toFixed(0)}%</div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Accuracy breakdown */}
      {accuracy.length > 0 && (
        <div className="card">
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 16 }}>📊 Topic Accuracy Breakdown</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 32px" }}>
            {accuracy.map(a => (
              <AccuracyBar key={a.topic} topic={a.topic} accuracy={a.accuracy_pct} attempts={a.total_attempts} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}