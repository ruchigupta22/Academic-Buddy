"""
app.py — Full Streamlit frontend (Phase 1 through 5)
Place at ROOT: ACADEMIC CHATBOT/app.py
Run: streamlit run app.py
"""

import streamlit as st
import requests
import time

API = "http://localhost:8000/api/v1"

st.set_page_config(page_title="StudyAI", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f0c29 0%,#302b63 50%,#24243e 100%)}
[data-testid="stSidebar"] *{color:#e0e0e0 !important}
[data-testid="stSidebar"] .stTextInput input{background:rgba(255,255,255,0.1)!important;border:1px solid rgba(255,255,255,0.3)!important;color:white!important;border-radius:8px!important}

/* Cards */
.card{background:white;border:1px solid #E5E7EB;border-radius:12px;padding:18px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.quiz-card{background:white;border:1px solid #e0e0e0;border-radius:12px;padding:20px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.question-number{font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px}
.question-text{font-size:16px;font-weight:500;color:#111827;line-height:1.6;margin-bottom:14px}

/* Badges */
.badge-mcq{background:#EDE9FE;color:#5B21B6;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:600}
.badge-short{background:#D1FAE5;color:#065F46;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:600}
.badge-num{background:#FEF3C7;color:#92400E;padding:2px 10px;border-radius:999px;font-size:11px;font-weight:600}
.badge-easy{background:#DCFCE7;color:#166534;padding:2px 8px;border-radius:999px;font-size:10px}
.badge-medium{background:#FEF9C3;color:#854D0E;padding:2px 8px;border-radius:999px;font-size:10px}
.badge-hard{background:#FEE2E2;color:#991B1B;padding:2px 8px;border-radius:999px;font-size:10px}
.score-correct{background:#DCFCE7;border-left:4px solid #16A34A;padding:12px 16px;border-radius:0 8px 8px 0}
.score-partial{background:#FEF9C3;border-left:4px solid #CA8A04;padding:12px 16px;border-radius:0 8px 8px 0}
.score-incorrect{background:#FEE2E2;border-left:4px solid #DC2626;padding:12px 16px;border-radius:0 8px 8px 0}
.source-pill{display:inline-block;background:#F3F4F6;border:1px solid #E5E7EB;border-radius:999px;padding:3px 10px;font-size:11px;color:#374151;margin:3px}

/* Revision */
.topic-row{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-radius:8px;margin-bottom:6px;background:#F9FAFB;border:1px solid #E5E7EB}
.topic-name{font-size:14px;font-weight:500;color:#111827}
.priority-high{border-left:3px solid #DC2626}
.priority-mid{border-left:3px solid #CA8A04}
.priority-low{border-left:3px solid #16A34A}
.stat-box{background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:12px 14px;text-align:center}
.stat-val{font-size:24px;font-weight:700;color:#1F2937}
.stat-lbl{font-size:11px;color:#6B7280;margin-top:2px}

/* Profile / dashboard */
.rec-card-high{background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:14px;margin-bottom:8px}
.rec-card-med{background:#FFFBEB;border:1px solid #FDE68A;border-radius:10px;padding:14px;margin-bottom:8px}
.rec-card-low{background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;padding:14px;margin-bottom:8px}
.rec-topic{font-size:14px;font-weight:600;color:#1F2937;margin-bottom:4px}
.rec-reason{font-size:12px;color:#6B7280;margin-bottom:4px}
.rec-action{font-size:12px;font-weight:500;color:#4F46E5}
.acc-bar-wrap{background:#E5E7EB;border-radius:999px;height:8px;margin-top:4px}
.avatar{width:48px;height:48px;border-radius:50%;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;font-size:20px;color:white;font-weight:700;flex-shrink:0}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
defaults = {
    "messages":[], "course_code":"CHE301", "username":"",
    "quiz_questions":[], "quiz_answers":{}, "quiz_results":{},
    "quiz_submitted":False, "quiz_topic":"", "quiz_difficulty":"medium",
    "quiz_score":0, "quiz_max":0,
    "rev_priority":None, "rev_plan":None, "rev_formula":None,
    "rev_confused":None, "rev_notes_cache":{},
    "profile_data":None, "recs_data":None,
}
for k,v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 StudyAI")
    st.markdown("---")

    # Phase 5: username
    username = st.text_input("👤 Your Name", value=st.session_state.username, placeholder="e.g. Arjun")
    st.session_state.username = username.strip()

    course_code = st.text_input("📚 Course Code", value=st.session_state.course_code, placeholder="e.g. CHE301")
    st.session_state.course_code = course_code.upper().strip()

    # Init user when both are set
    if st.session_state.username and st.session_state.course_code:
        try:
            requests.post(f"{API}/profile/init",
                json={"username": st.session_state.username, "course_code": st.session_state.course_code},
                timeout=5)
        except: pass

    st.markdown("---")
    st.markdown("**Upload Lecture Notes**")
    uploaded = st.file_uploader("PDF or PPTX", type=["pdf","pptx","ppt"], key="lec_up")
    if st.button("⚡ Upload Notes", use_container_width=True, disabled=not uploaded):
        with st.spinner("Processing..."):
            try:
                res=requests.post(f"{API}/upload/lecture",
                    files={"file":(uploaded.name,uploaded.getvalue())},
                    data={"course_code":st.session_state.course_code}, timeout=120)
                st.success(f"✅ {res.json().get('chunks_stored','?')} chunks stored") if res.status_code==200 else st.error(res.json().get("detail","Failed"))
            except: st.error("❌ Backend not running")

    st.markdown("---")
    st.markdown("**Upload PYQ Paper**")
    pyq_up = st.file_uploader("PDF", type=["pdf"], key="pyq_up")
    pyq_yr = st.number_input("Year", min_value=2000, max_value=2030, value=None)
    if st.button("⚡ Upload PYQ", use_container_width=True, disabled=not pyq_up):
        with st.spinner("Extracting questions..."):
            try:
                form={"course_code":st.session_state.course_code}
                if pyq_yr: form["year"]=pyq_yr
                res=requests.post(f"{API}/pyq/upload",
                    files={"file":(pyq_up.name,pyq_up.getvalue())},
                    data=form, timeout=180)
                st.success(f"✅ {res.json().get('questions_extracted','?')} questions extracted") if res.status_code==200 else st.error(res.json().get("detail","Failed"))
            except: st.error("❌ Backend not running")

    st.markdown("---")
    if st.session_state.username:
        st.caption(f"👤 **{st.session_state.username}** · {st.session_state.course_code}")
    else:
        st.caption(f"Course: **{st.session_state.course_code}**")


# ── Main tabs ──────────────────────────────────────────────────────────────────
tab_dash, tab_chat, tab_quiz, tab_rev, tab_pyq = st.tabs([
    "🏠  Dashboard", "💬  Chat", "📝  Quiz", "🎯  Revision", "📊  PYQ"
])


# ══ TAB 0 — DASHBOARD (Phase 5) ═══════════════════════════════════════════════
with tab_dash:
    if not st.session_state.username:
        st.markdown("""
        <div style="text-align:center;padding:60px;background:#F9FAFB;border-radius:16px;border:1px dashed #D1D5DB">
          <div style="font-size:56px;margin-bottom:16px">🎓</div>
          <div style="font-size:22px;font-weight:700;color:#1F2937;margin-bottom:8px">Welcome to StudyAI</div>
          <div style="font-size:15px;color:#6B7280;max-width:420px;margin:0 auto;line-height:1.7">
            Enter your <b>name</b> and <b>course code</b> in the sidebar to get started.<br>
            Upload lecture notes and PYQ papers, then take quizzes to unlock personalised recommendations.
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_refresh, _ = st.columns([1, 4])
        with col_refresh:
            if st.button("🔄 Refresh dashboard"):
                st.session_state.profile_data = None
                st.session_state.recs_data = None

        # Load profile data
        if not st.session_state.profile_data:
            try:
                res = requests.get(f"{API}/profile/summary",
                    params={"username": st.session_state.username, "course_code": st.session_state.course_code},
                    timeout=10)
                st.session_state.profile_data = res.json() if res.status_code == 200 else {}
            except: st.session_state.profile_data = {}

        if not st.session_state.recs_data:
            try:
                res = requests.get(f"{API}/profile/recommendations",
                    params={"username": st.session_state.username, "course_code": st.session_state.course_code},
                    timeout=10)
                st.session_state.recs_data = res.json() if res.status_code == 200 else {}
            except: st.session_state.recs_data = {}

        profile = st.session_state.profile_data or {}
        recs    = st.session_state.recs_data    or {}
        stats   = profile.get("quiz_stats", {})

        # ── Header with avatar ─────────────────────────────────────────────────
        initials = st.session_state.username[:2].upper()
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px">
          <div class="avatar">{initials}</div>
          <div>
            <div style="font-size:22px;font-weight:700;color:#1F2937">Hi, {st.session_state.username.title()}! 👋</div>
            <div style="font-size:14px;color:#6B7280">{st.session_state.course_code} · Personal Learning Dashboard</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Stats row ──────────────────────────────────────────────────────────
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="stat-box"><div class="stat-val">{stats.get('total_quizzes',0)}</div><div class="stat-lbl">Quizzes taken</div></div>""", unsafe_allow_html=True)
        with c2:
            avg = stats.get('avg_score') or 0
            st.markdown(f"""<div class="stat-box"><div class="stat-val">{avg:.0f}%</div><div class="stat-lbl">Average score</div></div>""", unsafe_allow_html=True)
        with c3:
            best = stats.get('best_score') or 0
            st.markdown(f"""<div class="stat-box"><div class="stat-val">{best:.0f}%</div><div class="stat-lbl">Best score</div></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="stat-box"><div class="stat-val">{profile.get('chat_count',0)}</div><div class="stat-lbl">Questions asked</div></div>""", unsafe_allow_html=True)

        st.markdown("")

        col_left, col_right = st.columns([1,1], gap="large")

        # ── Left: AI coaching message ──────────────────────────────────────────
        with col_left:
            st.markdown("#### 🤖 Your AI Coach")
            if st.button("Get personalised advice", use_container_width=True):
                with st.spinner("Generating your personalised advice..."):
                    try:
                        res = requests.get(f"{API}/profile/ai-message",
                            params={"username": st.session_state.username, "course_code": st.session_state.course_code},
                            timeout=30)
                        if res.status_code == 200:
                            msg = res.json().get("message","")
                            st.markdown(f"""
                            <div style="background:linear-gradient(135deg,#667eea22,#764ba222);
                                border:1px solid #764ba244;border-radius:12px;padding:16px;
                                font-size:14px;color:#1F2937;line-height:1.7">
                              {msg}
                            </div>
                            """, unsafe_allow_html=True)
                    except: st.error("❌ Backend not running.")

            # Weak topics
            st.markdown("#### ❌ Weak Topics")
            weak = profile.get("weak_topics", [])
            if weak:
                for t in weak:
                    acc = t.get("accuracy_pct", 0)
                    bar_w = int(acc)
                    st.markdown(f"""
                    <div style="margin-bottom:10px">
                      <div style="display:flex;justify-content:space-between;font-size:13px;color:#1F2937;font-weight:500">
                        <span>{t['topic']}</span><span style="color:#DC2626">{acc:.0f}%</span>
                      </div>
                      <div class="acc-bar-wrap">
                        <div style="width:{bar_w}%;background:#DC2626;height:8px;border-radius:999px"></div>
                      </div>
                      <div style="font-size:11px;color:#9CA3AF;margin-top:2px">{t.get('total_attempts',0)} attempts · {t.get('wrong_count',0)} wrong</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Take quizzes to identify weak topics!")

            # Strong topics
            strong = profile.get("strong_topics", [])
            if strong:
                st.markdown("#### ✅ Strong Topics")
                for t in strong:
                    acc = t.get("accuracy_pct", 0)
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:8px 12px;background:#F0FDF4;border:1px solid #BBF7D0;
                        border-radius:8px;margin-bottom:6px">
                      <span style="font-size:13px;font-weight:500;color:#166534">{t['topic']}</span>
                      <span style="font-size:13px;font-weight:700;color:#16A34A">{acc:.0f}%</span>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Right: Recommendations ─────────────────────────────────────────────
        with col_right:
            st.markdown("#### 🎯 What to Study Next")
            if recs.get("mode") == "cold_start":
                st.info(recs.get("message",""))

            rec_list = recs.get("recommendations", [])
            if rec_list:
                for r in rec_list[:7]:
                    priority = r.get("priority","medium")
                    css = {"high":"rec-card-high","medium":"rec-card-med","low":"rec-card-low"}.get(priority,"rec-card-med")
                    icon = {"high":"🔴","medium":"🟡","low":"🟢"}.get(priority,"🟡")
                    acc_str = f" · {r['accuracy']:.0f}% accuracy" if r.get("accuracy") is not None else ""
                    st.markdown(f"""
                    <div class="{css}">
                      <div class="rec-topic">{icon} {r['topic']}</div>
                      <div class="rec-reason">{r['reason']}{acc_str}</div>
                      <div class="rec-action">→ {r['action']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Take quizzes to get personalised recommendations!")

            # Recent quiz history
            recent = profile.get("recent_quizzes", [])
            if recent:
                st.markdown("#### 📈 Recent Quizzes")
                for q in recent:
                    pct = q.get("pct_score", 0) or 0
                    colour = "#16A34A" if pct >= 80 else "#CA8A04" if pct >= 60 else "#DC2626"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:8px 12px;background:#F9FAFB;border:1px solid #E5E7EB;
                        border-radius:8px;margin-bottom:6px">
                      <div>
                        <div style="font-size:13px;font-weight:500;color:#1F2937">{q.get('topic','?')}</div>
                        <div style="font-size:11px;color:#9CA3AF">{q.get('difficulty','?')} · {q.get('attempted_at','')[:10]}</div>
                      </div>
                      <div style="font-size:16px;font-weight:700;color:{colour}">{pct:.0f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── Accuracy breakdown chart ───────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📊 Topic Accuracy Breakdown")
        try:
            res = requests.get(f"{API}/profile/accuracy",
                params={"username": st.session_state.username, "course_code": st.session_state.course_code},
                timeout=10)
            if res.status_code == 200:
                acc_data = res.json()
                if acc_data:
                    import json as _json
                    topics_list = [d["topic"][:25] for d in acc_data]
                    acc_list    = [d["accuracy_pct"] for d in acc_data]

                    # Simple HTML bar chart (no matplotlib needed)
                    bars_html = ""
                    for t, a in zip(topics_list, acc_list):
                        colour = "#16A34A" if a >= 80 else "#CA8A04" if a >= 60 else "#DC2626"
                        bars_html += f"""
                        <div style="margin-bottom:8px">
                          <div style="display:flex;justify-content:space-between;font-size:12px;color:#374151;margin-bottom:3px">
                            <span>{t}</span><span style="font-weight:600;color:{colour}">{a:.0f}%</span>
                          </div>
                          <div style="background:#E5E7EB;border-radius:999px;height:10px">
                            <div style="width:{int(a)}%;background:{colour};height:10px;border-radius:999px;transition:width .3s"></div>
                          </div>
                        </div>"""
                    st.markdown(f'<div style="max-height:300px;overflow-y:auto;padding-right:8px">{bars_html}</div>', unsafe_allow_html=True)
                else:
                    st.info("Take quizzes to see your topic accuracy breakdown.")
        except: pass


# ══ TAB 1 — CHAT ══════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown(f"### 💬 Ask about {st.session_state.course_code or 'your course'}")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                for s in msg["sources"]:
                    st.markdown(f'<span class="source-pill">📄 {s["source"]} · p.{s["page"]} · {s["similarity"]:.0%}</span>', unsafe_allow_html=True)

    if prompt := st.chat_input("Ask anything about your lecture notes..."):
        if not st.session_state.course_code:
            st.warning("Set course code in sidebar.")
        else:
            st.session_state.messages.append({"role":"user","content":prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Searching your notes..."):
                    try:
                        res=requests.post(f"{API}/chat/",
                            json={"question":prompt,"course_code":st.session_state.course_code}, timeout=60)
                        if res.status_code==200:
                            d=res.json()
                            st.markdown(d["answer"])
                            if d["sources"]:
                                for s in d["sources"]:
                                    st.markdown(f'<span class="source-pill">📄 {s["source"]} · p.{s["page"]} · {s["similarity"]:.0%}</span>', unsafe_allow_html=True)
                            st.session_state.messages.append({"role":"assistant","content":d["answer"],"sources":d["sources"]})
                            # Phase 5: save chat to history
                            if st.session_state.username:
                                try:
                                    requests.post(f"{API}/profile/save-chat",
                                        json={"username":st.session_state.username,"course_code":st.session_state.course_code,
                                              "question":prompt,"answer":d["answer"]}, timeout=5)
                                except: pass
                        else: st.error(res.json().get("detail","Error"))
                    except requests.exceptions.ConnectionError: st.error("❌ Backend not running.")
    if st.session_state.messages:
        if st.button("🗑️ Clear chat"): st.session_state.messages=[]; st.rerun()


# ══ TAB 2 — QUIZ ══════════════════════════════════════════════════════════════
with tab_quiz:
    if not st.session_state.quiz_questions:
        st.markdown("### 📝 Generate a Quiz")
        # Show weak-topic quick picks if user has profile
        if st.session_state.recs_data and st.session_state.recs_data.get("recommendations"):
            high_recs = [r["topic"] for r in st.session_state.recs_data["recommendations"] if r.get("priority")=="high"]
            if high_recs:
                st.markdown("**🔴 Recommended (your weak topics):**")
                cols = st.columns(min(len(high_recs), 3))
                for i, t in enumerate(high_recs[:3]):
                    with cols[i]:
                        if st.button(f"Quiz: {t[:20]}", use_container_width=True, key=f"quick_{i}"):
                            st.session_state["_quick_topic"] = t
                            st.rerun()

        col1,col2=st.columns([2,1])
        with col1:
            default_topic = st.session_state.pop("_quick_topic", "")
            topic=st.text_input("Topic", value=default_topic, placeholder="e.g. Fick's Law, Heat Transfer")
        with col2:
            difficulty=st.selectbox("Difficulty",["easy","medium","hard"],index=1)

        ca,cb,cc=st.columns(3)
        want_mcq=ca.checkbox("MCQ",value=True); want_short=cb.checkbox("Short Answer",value=True); want_num=cc.checkbox("Numerical",value=True)
        count=st.slider("Questions per type",1,5,3)

        if st.button("🚀 Generate Quiz",type="primary",use_container_width=True):
            if not topic: st.warning("Enter a topic.")
            elif not st.session_state.course_code: st.warning("Set course code in sidebar.")
            elif not any([want_mcq,want_short,want_num]): st.warning("Select a question type.")
            else:
                types=[t for t,w in [("mcq",want_mcq),("short",want_short),("numerical",want_num)] if w]
                with st.spinner(f"Generating questions on '{topic}'..."):
                    try:
                        res=requests.post(f"{API}/quiz/generate",
                            json={"course_code":st.session_state.course_code,"topic":topic,
                                  "question_types":types,"count_per_type":count,"difficulty":difficulty}, timeout=120)
                        if res.status_code==200:
                            data=res.json()
                            if data.get("error"): st.error(data["error"])
                            elif data["total_questions"]==0: st.warning("No questions generated.")
                            else:
                                st.session_state.quiz_questions=data["questions"]
                                st.session_state.quiz_topic=data["topic"]
                                st.session_state.quiz_difficulty=difficulty
                                st.session_state.quiz_answers={}; st.session_state.quiz_results={}
                                st.session_state.quiz_submitted=False; st.session_state.quiz_score=0
                                st.session_state.quiz_max=sum(q["marks"] for q in data["questions"])
                                st.rerun()
                        else: st.error(res.json().get("detail","Failed"))
                    except requests.exceptions.ConnectionError: st.error("❌ Backend not running.")
    else:
        questions=st.session_state.quiz_questions; total_q=len(questions)
        col_h1,_,col_h3=st.columns([3,1,1])
        with col_h1: st.markdown(f"### 📝 {st.session_state.quiz_topic.title()}")
        with col_h3:
            if st.button("🔄 New Quiz"):
                st.session_state.quiz_questions=[]; st.session_state.quiz_answers={}
                st.session_state.quiz_results={}; st.session_state.quiz_submitted=False; st.rerun()

        if st.session_state.quiz_submitted:
            score=st.session_state.quiz_score; max_s=st.session_state.quiz_max
            pct=int(score/max_s*100) if max_s else 0
            colour,emoji,grade=("#16A34A","🎉","Excellent!") if pct>=80 else ("#CA8A04","👍","Good") if pct>=60 else ("#EA580C","📖","Needs revision") if pct>=40 else ("#DC2626","❗","Review required")
            st.markdown(f"""<div style="background:{colour}18;border:1px solid {colour}44;border-radius:12px;
                padding:16px 20px;margin-bottom:16px;display:flex;align-items:center;gap:16px">
                <div style="font-size:32px">{emoji}</div>
                <div><div style="font-size:22px;font-weight:700;color:{colour}">{score}/{max_s} marks · {pct}%</div>
                <div style="font-size:14px;color:#6B7280">{grade} — results saved to your profile</div></div></div>""",unsafe_allow_html=True)
        else:
            answered=len([a for a in st.session_state.quiz_answers.values() if a])
            st.progress(answered/total_q if total_q else 0)

        st.markdown("---")
        for idx,q in enumerate(questions):
            qtype=q["type"]; diff=q.get("difficulty","medium")
            badge={"mcq":'<span class="badge-mcq">MCQ</span>',"short":'<span class="badge-short">Short Answer</span>',"numerical":'<span class="badge-num">Numerical</span>'}.get(qtype,"")
            diffb=f'<span class="badge-{diff}">{diff.title()}</span>'
            st.markdown(f"""<div class="quiz-card"><div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">{badge} {diffb} <span style="font-size:11px;color:#6B7280">{q.get('marks',2)} marks</span></div>
                <div class="question-number">Question {idx+1} of {total_q}</div><div class="question-text">{q['question']}</div></div>""",unsafe_allow_html=True)
            key=f"ans_{idx}"
            if qtype=="mcq":
                opts=q.get("options",[])
                if not st.session_state.quiz_submitted:
                    choice=st.radio("Answer:",opts,key=key,label_visibility="collapsed")
                    st.session_state.quiz_answers[idx]=choice[0] if choice else ""
                else:
                    student=st.session_state.quiz_answers.get(idx,""); correct=q["correct_answer"].strip().upper()[:1]
                    for opt in opts:
                        ol=opt[0].upper()
                        if ol==correct: st.markdown(f"✅ **{opt}** ← Correct")
                        elif ol==(student or "").upper()[:1] and ol!=correct: st.markdown(f"❌ ~~{opt}~~ ← Your answer")
                        else: st.markdown(f"&nbsp;&nbsp;{opt}")
                    if q.get("explanation"): st.info(f"💡 {q['explanation']}")
            else:
                ph="Show all steps and units..." if qtype=="numerical" else "Write your answer..."
                if not st.session_state.quiz_submitted:
                    ans=st.text_area("Answer:",key=key,placeholder=ph,height=100,label_visibility="collapsed")
                    st.session_state.quiz_answers[idx]=ans
                else:
                    result=st.session_state.quiz_results.get(idx,{}); student=st.session_state.quiz_answers.get(idx,"")
                    if student: st.markdown(f"**Your answer:** {student}")
                    sv=result.get("score",0); mv=q.get("marks",5); pct_q=sv/mv if mv else 0
                    css="score-correct" if pct_q>=0.8 else ("score-partial" if pct_q>=0.4 else "score-incorrect")
                    st.markdown(f'<div class="{css}"><b>Score: {sv}/{mv}</b><br>{result.get("feedback","")}</div>',unsafe_allow_html=True)
                    if q.get("correct_answer"):
                        with st.expander("📖 Model answer"):
                            st.markdown(q["correct_answer"])
                            if q.get("explanation"): st.markdown(f"**Explanation:** {q['explanation']}")
            st.markdown("")

        if not st.session_state.quiz_submitted:
            st.markdown("---")
            answered=len([a for a in st.session_state.quiz_answers.values() if a])
            if answered<total_q: st.warning(f"⚠️ {answered}/{total_q} answered.")
            if st.button("✅ Submit Quiz",type="primary",use_container_width=True):
                with st.spinner("Evaluating answers..."):
                    total_score=0; total_max=0
                    for idx,q in enumerate(questions):
                        student=st.session_state.quiz_answers.get(idx,"")
                        try:
                            r=requests.post(f"{API}/quiz/check",
                                json={"question":q["question"],"question_type":q["type"],
                                      "model_answer":q["correct_answer"],"student_answer":student or "(no answer)","marks":q.get("marks",2)},timeout=30)
                            result=r.json() if r.status_code==200 else {"score":0,"feedback":"Could not evaluate.","is_correct":False}
                        except: result={"score":0,"feedback":"Could not evaluate.","is_correct":False}
                        st.session_state.quiz_results[idx]=result; total_score+=result.get("score",0); total_max+=q.get("marks",2)
                    st.session_state.quiz_score=total_score; st.session_state.quiz_max=total_max
                    st.session_state.quiz_submitted=True

                    # Phase 5: save quiz to profile
                    if st.session_state.username:
                        try:
                            requests.post(f"{API}/profile/save-quiz",
                                json={"username":st.session_state.username,
                                      "course_code":st.session_state.course_code,
                                      "topic":st.session_state.quiz_topic,
                                      "difficulty":st.session_state.quiz_difficulty,
                                      "questions":questions,
                                      "results":{str(k):v for k,v in st.session_state.quiz_results.items()}},
                                timeout=10)
                            st.session_state.profile_data = None  # Force dashboard refresh
                            st.session_state.recs_data = None
                        except: pass
                    st.rerun()
        else:
            st.markdown("---")
            c1,c2=st.columns(2)
            with c1:
                if st.button("🔄 Try Again",use_container_width=True):
                    st.session_state.quiz_answers={}; st.session_state.quiz_results={}; st.session_state.quiz_submitted=False; st.rerun()
            with c2:
                if st.button("📝 New Quiz",use_container_width=True):
                    st.session_state.quiz_questions=[]; st.session_state.quiz_answers={}
                    st.session_state.quiz_results={}; st.session_state.quiz_submitted=False; st.rerun()
            score=st.session_state.quiz_score; max_s=st.session_state.quiz_max
            pct=int(score/max_s*100) if max_s else 0
            if pct<70:
                st.markdown("---")
                st.info(f"💡 You scored {pct}%. Check **Dashboard** for personalised recommendations on what to study next.")


# ══ TAB 3 — REVISION ══════════════════════════════════════════════════════════
with tab_rev:
    st.markdown("### 🎯 Exam Revision Mode")
    col1,col2,col3=st.columns(3)
    with col1: days_left=st.number_input("📅 Days until exam",min_value=1,max_value=30,value=3)
    with col2: hours_per_day=st.number_input("⏱️ Hours per day",min_value=1,max_value=12,value=4)
    with col3:
        st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
        gen_btn=st.button("🚀 Build Revision Plan",type="primary",use_container_width=True)

    if gen_btn:
        if not st.session_state.course_code: st.warning("Set course code in sidebar.")
        else:
            code=st.session_state.course_code
            with st.spinner("📊 Ranking topics..."): 
                try:
                    r=requests.get(f"{API}/revision/priority",params={"course_code":code,"days_left":days_left},timeout=60)
                    st.session_state.rev_priority=r.json() if r.status_code==200 else None
                except: st.session_state.rev_priority=None
            with st.spinner("📅 Building schedule..."):
                try:
                    r=requests.get(f"{API}/revision/plan",params={"course_code":code,"days_left":days_left,"hours_per_day":hours_per_day},timeout=60)
                    st.session_state.rev_plan=r.json() if r.status_code==200 else None
                except: st.session_state.rev_plan=None
            with st.spinner("📐 Extracting formulas..."):
                try:
                    r=requests.get(f"{API}/revision/formula-sheet",params={"course_code":code},timeout=90)
                    st.session_state.rev_formula=r.json().get("formula_sheet") if r.status_code==200 else None
                except: st.session_state.rev_formula=None
            with st.spinner("⚠️ Finding confused concepts..."):
                try:
                    r=requests.get(f"{API}/revision/confused",params={"course_code":code},timeout=90)
                    st.session_state.rev_confused=r.json().get("confused_concepts") if r.status_code==200 else None
                except: st.session_state.rev_confused=None
            st.success("✅ Revision plan ready!"); st.rerun()

    if st.session_state.rev_priority or st.session_state.rev_plan:
        rev_tabs=st.tabs(["🏆 Priority Topics","📅 Study Plan","📐 Formula Sheet","⚠️ Confused Concepts","📖 Quick Notes"])
        with rev_tabs[0]:
            data=st.session_state.rev_priority
            if data and data.get("topics"):
                st.info(data.get("strategy",""))
                topics=data["topics"]; total_mins=sum(t.get("study_time_mins",30) for t in topics)
                st.markdown(f"""<div style="display:flex;gap:12px;margin:12px 0">
                  <div class="stat-box"><div class="stat-val">{len(topics)}</div><div class="stat-lbl">Topics</div></div>
                  <div class="stat-box"><div class="stat-val">{total_mins//60}h {total_mins%60}m</div><div class="stat-lbl">Total study time</div></div>
                  <div class="stat-box"><div class="stat-val">{data.get('days_left',3)}</div><div class="stat-lbl">Days left</div></div></div>""",unsafe_allow_html=True)
                st.markdown("---")
                for i,t in enumerate(topics):
                    border="priority-high" if i<3 else "priority-mid" if i<7 else "priority-low"
                    emoji="🔴" if i<3 else "🟡" if i<7 else "🟢"
                    st.markdown(f"""<div class="topic-row {border}">
                      <div><div class="topic-name">{emoji} #{i+1} &nbsp; {t['topic']}</div>
                      <div style="font-size:11px;color:#6B7280;margin-top:3px">Asked {t.get('frequency',0)}× · {t.get('total_marks',0)} total marks · {t.get('question_types','')} · ~{t.get('study_time_mins',30)} min</div></div>
                      <div style="text-align:right;flex-shrink:0;margin-left:12px">
                        <div style="font-size:18px;font-weight:700;color:#1F2937">{t.get('priority_score',0)}</div>
                        <div style="font-size:10px;color:#9CA3AF">priority</div></div></div>""",unsafe_allow_html=True)
            else: st.warning("No PYQ data. Upload previous year papers first.")
        with rev_tabs[1]:
            plan=st.session_state.rev_plan
            if plan and plan.get("days"):
                st.markdown(f"**{plan.get('summary','')}**")
                for day in plan["days"]:
                    day_topics=day.get("topics",[])
                    is_rev="Revision" in day.get("date_label","")
                    with st.expander(f"{'🔁' if is_rev else '📅'} {day['date_label']} — {len(day_topics)} topics · {day.get('total_minutes',0)//60}h {day.get('total_minutes',0)%60}m",expanded=(day["day"]==1)):
                        for task in day.get("tasks",[]): st.markdown(f"• {task}")
                        if day_topics:
                            st.markdown("**Topics:**")
                            for t in day_topics: st.markdown(f"&nbsp;&nbsp;`{t['topic']}` — ~{t.get('study_time_mins',30)} min")
        with rev_tabs[2]:
            if st.session_state.rev_formula:
                st.download_button("⬇️ Download Formula Sheet",data=st.session_state.rev_formula,
                    file_name=f"{st.session_state.course_code}_formulas.md",mime="text/markdown")
                st.markdown("---"); st.markdown(st.session_state.rev_formula)
            else: st.warning("Upload lecture notes first.")
        with rev_tabs[3]:
            if st.session_state.rev_confused:
                st.markdown(st.session_state.rev_confused)
            else: st.warning("Upload notes and PYQ papers first.")
        with rev_tabs[4]:
            topic_options=[]
            if st.session_state.rev_priority and st.session_state.rev_priority.get("topics"):
                topic_options=[t["topic"] for t in st.session_state.rev_priority["topics"]]
            col_a,col_b=st.columns([3,1])
            with col_a:
                sel_topic=st.selectbox("Select topic",topic_options) if topic_options else st.text_input("Enter topic")
            with col_b:
                st.markdown("<div style='height:28px'></div>",unsafe_allow_html=True)
                notes_btn=st.button("📖 Get Notes",use_container_width=True)
            if notes_btn and sel_topic:
                ck=f"{st.session_state.course_code}_{sel_topic}"
                if ck not in st.session_state.rev_notes_cache:
                    with st.spinner(f"Generating notes for '{sel_topic}'..."):
                        try:
                            r=requests.get(f"{API}/revision/notes",
                                params={"course_code":st.session_state.course_code,"topic":sel_topic},timeout=60)
                            if r.status_code==200: st.session_state.rev_notes_cache[ck]=r.json().get("notes","")
                        except: pass
                notes=st.session_state.rev_notes_cache.get(ck)
                if notes:
                    st.download_button(f"⬇️ Download",data=notes,file_name=f"{sel_topic.replace(' ','_')}_notes.md",mime="text/markdown")
                    st.markdown("---"); st.markdown(notes)
            for ck,notes in st.session_state.rev_notes_cache.items():
                lbl=ck.split("_",1)[-1]
                with st.expander(f"📄 {lbl}"): st.markdown(notes)
    elif not gen_btn:
        st.markdown("""<div style="text-align:center;padding:48px;background:#F9FAFB;border-radius:16px;border:1px dashed #D1D5DB">
          <div style="font-size:48px;margin-bottom:12px">🎯</div>
          <div style="font-size:18px;font-weight:600;color:#1F2937;margin-bottom:8px">Exam Revision Mode</div>
          <div style="font-size:14px;color:#6B7280">Enter days left and click Build Revision Plan.<br>Upload lecture notes + PYQ papers for best results.</div>
        </div>""",unsafe_allow_html=True)


# ══ TAB 4 — PYQ ═══════════════════════════════════════════════════════════════
with tab_pyq:
    st.markdown("### 📊 PYQ Intelligence")
    sub1,sub2=st.tabs(["🔍 Ask Patterns","📑 Full Report"])
    with sub1:
        examples=["What topics are most frequently asked?","Which topics carry the most marks?","What type of questions appear most?","What should I prioritise?"]
        sel=st.selectbox("Example",[""] + examples)
        q_in=st.text_input("Or type your own",value=sel)
        if st.button("🔍 Analyze",disabled=not q_in):
            with st.spinner("Querying..."):
                try:
                    res=requests.post(f"{API}/pyq/ask",json={"question":q_in,"course_code":st.session_state.course_code},timeout=60)
                    if res.status_code==200:
                        d=res.json(); st.markdown(d["answer"])
                        if d.get("data",{}).get("top_topics"):
                            with st.expander("📊 Raw data"): st.json(d["data"])
                    else: st.error(res.json().get("detail","Error"))
                except: st.error("❌ Backend not running.")
    with sub2:
        if st.button("📝 Generate Report",use_container_width=True):
            with st.spinner("Analysing PYQ papers..."):
                try:
                    res=requests.get(f"{API}/pyq/report",params={"course_code":st.session_state.course_code},timeout=90)
                    if res.status_code==200: st.markdown(res.json()["report"])
                    else: st.error(res.json().get("detail","Error"))
                except: st.error("❌ Backend not running.")