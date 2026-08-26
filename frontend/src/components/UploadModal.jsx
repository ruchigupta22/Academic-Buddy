/**
 * components/UploadModal.jsx
 * Drag-and-drop file upload modal for lecture notes and PYQ papers.
 */

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useApp } from "../context/AppContext";
import { uploadLecture, uploadPYQ } from "../services/api";
import toast from "react-hot-toast";
import { X, Upload, FileText, CheckCircle } from "lucide-react";

export default function UploadModal({ onClose }) {
  const { courseCode } = useApp();
  const [mode, setMode] = useState("lecture"); // "lecture" | "pyq"
  const [file, setFile] = useState(null);
  const [year, setYear] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);

  const onDrop = useCallback((accepted) => {
    if (accepted[0]) { setFile(accepted[0]); setResult(null); }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.presentationml.presentation": [".pptx"] },
    maxFiles: 1,
  });

  const handleUpload = async () => {
    if (!file) return toast.error("Select a file first");
    if (!courseCode) return toast.error("Set your course code first (click your name in sidebar)");

    setLoading(true); setProgress(0);
    try {
      let res;
      if (mode === "lecture") {
        res = await uploadLecture(file, courseCode, setProgress);
        setResult({ label: "Lecture ingested", chunks: res.data.chunks_stored, pages: res.data.pages_extracted });
        toast.success(`✅ ${res.data.chunks_stored} chunks stored!`);
      } else {
        res = await uploadPYQ(file, courseCode, year || undefined);
        setResult({ label: "PYQ ingested", questions: res.data.questions_extracted, chunks: res.data.chunks_stored });
        toast.success(`✅ ${res.data.questions_extracted} questions extracted!`);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,.7)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 1000, padding: 16,
    }} onClick={(e) => e.target === e.currentTarget && onClose()}>

      <div className="card upload-card" style={{ width: "100%", maxWidth: 480, position: "relative" }}>

        {/* Header */}
        <div className="upload-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600 }}>Upload Files</h2>
          <button className="btn btn-ghost" onClick={onClose} style={{ padding: 6 }}>
            <X size={16} />
          </button>
        </div>

        {/* Mode toggle */}
        <div className="upload-tabs" style={{ display: "flex", gap: 8, marginBottom: 20 }}>
          {["lecture", "pyq"].map(m => (
            <button key={m} onClick={() => setMode(m)}
              className={`btn ${mode === m ? "btn-primary" : "btn-secondary"}`}
              style={{ flex: 1, justifyContent: "center" }}>
              {m === "lecture" ? "📚 Lecture Notes" : "📝 PYQ Paper"}
            </button>
          ))}
        </div>

        {/* Drop zone */}
        <div {...getRootProps()} className="upload-dropzone" style={{
          border: `2px dashed ${isDragActive ? "var(--accent)" : "var(--border)"}`,
          borderRadius: "var(--radius)", padding: "32px 20px",
          textAlign: "center", cursor: "pointer", marginBottom: 16,
          background: isDragActive ? "rgba(108,99,255,0.06)" : "var(--bg3)",
          transition: "all .15s",
        }}>
          <input {...getInputProps()} />
          {file ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10 }}>
              <FileText size={20} color="var(--accent)" />
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: "var(--text)" }}>{file.name}</div>
                <div style={{ fontSize: 11, color: "var(--text3)" }}>{(file.size / 1024 / 1024).toFixed(1)} MB</div>
              </div>
            </div>
          ) : (
            <>
              <Upload size={28} color="var(--text3)" style={{ margin: "0 auto 10px" }} />
              <div style={{ color: "var(--text2)", fontSize: 13 }}>
                {isDragActive ? "Drop it here" : "Drag & drop or click to select"}
              </div>
              <div style={{ color: "var(--text3)", fontSize: 11, marginTop: 4 }}>PDF or PPTX · Max 50MB</div>
            </>
          )}
        </div>

        {/* Year input for PYQ */}
        {mode === "pyq" && (
          <div style={{ marginBottom: 16 }}>
            <label className="label">Year (optional)</label>
            <input className="input" type="number" placeholder="e.g. 2022"
              value={year} onChange={e => setYear(e.target.value)} />
          </div>
        )}

        {/* Progress bar */}
        {loading && (
          <div style={{ marginBottom: 16 }}>
            <div className="progress">
              <div className="progress-fill" style={{ width: `${progress}%`, background: "var(--accent)" }} />
            </div>
            <div style={{ fontSize: 11, color: "var(--text3)", marginTop: 6, textAlign: "center" }}>
              {progress < 100 ? `Uploading... ${progress}%` : "Processing — parsing, chunking, embedding..."}
            </div>
          </div>
        )}

        {/* Success result */}
        {result && (
          <div style={{ background: "rgba(34,197,94,0.08)", border: "1px solid rgba(34,197,94,0.2)",
            borderRadius: "var(--radius)", padding: "12px 14px", marginBottom: 16,
            display: "flex", alignItems: "center", gap: 10 }}>
            <CheckCircle size={18} color="var(--green)" />
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: "var(--green)" }}>{result.label}</div>
              <div style={{ fontSize: 11, color: "var(--text2)" }}>
                {result.pages && `${result.pages} pages · `}{result.chunks} chunks stored
                {result.questions !== undefined && ` · ${result.questions} questions extracted`}
              </div>
            </div>
          </div>
        )}

        {/* Upload button */}
        <button className="btn btn-primary btn-full" onClick={handleUpload} disabled={loading || !file}>
          {loading ? <><span className="spinner" /> Processing...</> : <><Upload size={14} /> Upload & Process</>}
        </button>
      </div>
    </div>
  );
}