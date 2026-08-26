

import { NavLink } from "react-router-dom";
import { useState } from "react";
import { useApp } from "../context/AppContext";
import UploadModal from "./UploadModal";
import {
  LayoutDashboard, MessageSquare, BookOpen,
  Target, BarChart2, Upload, User, GraduationCap
} from "lucide-react";

const NAV = [
  { to: "/",         icon: LayoutDashboard, label: "Dashboard"  },
  { to: "/chat",     icon: MessageSquare,   label: "Chat"        },
  { to: "/quiz",     icon: BookOpen,        label: "Quiz"        },
  { to: "/revision", icon: Target,          label: "Revision"    },
  { to: "/pyq",      icon: BarChart2,       label: "PYQ"         },
];

export default function Layout({ children }) {
  const { username, setUsername, courseCode, setCourseCode } = useApp();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(false);

  return (
    <div className="app-shell" style={{ display: "flex", minHeight: "100vh" }}>

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className="sidebar card" style={{
        width: 220, display: "flex", flexDirection: "column", flexShrink: 0,
        position: "sticky", top: 0, height: "100vh", overflowY: "auto",
      }}>

        {/* Logo */}
        <div className="sidebar-brand" style={{ padding: "20px 16px 12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <GraduationCap size={22} color="var(--accent)" />
            <span style={{ fontSize: 26, fontWeight: 700, color: "var(--text)" }}>Exam Dost</span>
          </div>
        </div>

        {/* User info */}
        <div className="sidebar-user" style={{ padding: "14px 16px" }}>
          {editingUser ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <input className="input" placeholder="Your name"
                defaultValue={username}
                onBlur={e => { setUsername(e.target.value); }}
                autoFocus style={{ fontSize: 22, padding: "6px 10px" }} />
              <input className="input" placeholder="Course code e.g. CHE301"
                defaultValue={courseCode}
                onBlur={e => setCourseCode(e.target.value)}
                style={{ fontSize: 22, padding: "6px 10px" }} />
            </div>
          ) : (
            <button onClick={() => setEditingUser(true)}
              style={{ display: "flex", alignItems: "center", gap: 10, background: "none",
                border: "none", cursor: "pointer", width: "100%", padding: 0 }}>
              <div style={{
                width: 34, height: 34, borderRadius: "50%",
                background: "linear-gradient(135deg,var(--accent),#9333ea)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 13, fontWeight: 700, color: "white", flexShrink: 0,
              }}>
                {username ? username.slice(0, 2).toUpperCase() : <User size={14} />}
              </div>
              <div style={{ textAlign: "left", overflow: "hidden" }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text)",
                  overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {username || "Set your name"}
                </div>
                <div style={{ fontSize: 11, color: "var(--text3)" }}>
                  {courseCode || "No course set"}
                </div>
              </div>
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav" style={{ flex: 1, padding: "12px 10px" }}>
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === "/"}
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
              style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "9px 12px", borderRadius: "var(--radius)",
                marginBottom: 2, textDecoration: "none", fontSize: 13,
                transition: "all .15s",
              }}>
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Upload button */}
        <div className="sidebar-actions" style={{ padding: "12px 10px" }}>
          <button className="btn btn-primary btn-full" onClick={() => setUploadOpen(true)}>
            <Upload size={18} /> Upload Files
          </button>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────────── */}
      <main style={{ flex: 1, overflowY: "auto", minWidth: 0 }}>
        {children}
      </main>

      {uploadOpen && <UploadModal onClose={() => setUploadOpen(false)} />}
    </div>
  );
}


