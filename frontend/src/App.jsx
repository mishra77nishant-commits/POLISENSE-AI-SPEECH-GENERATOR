import { useState } from "react";
import "./App.css";
import "./manifesto_styles.css";

const API_BASE_URL = "https://polisense-ai-speech-generator.onrender.com/api/speech";

const MANIFESTO_API_URL = import.meta.env.VITE_MANIFESTO_API_URL || "http://127.0.0.1:8000";

function humanizeManifestoKey(key) {
  return String(key)
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function normalizeManifesto(payload) {
  if (payload && typeof payload === "object") return payload;
  if (typeof payload === "string") {
    try {
      const parsed = JSON.parse(payload);
      if (parsed && typeof parsed === "object") return parsed;
    } catch {
      // The backend may return plain text rather than JSON.
    }
    return { content: payload };
  }
  return { content: String(payload ?? "") };
}

function flattenManifestoValue(value) {
  if (Array.isArray(value)) {
    return value.map((item) => flattenManifestoValue(item)).filter(Boolean).join(" • ");
  }
  if (value && typeof value === "object") {
    return Object.entries(value)
      .map(([key, nestedValue]) => `${humanizeManifestoKey(key)}: ${flattenManifestoValue(nestedValue)}`)
      .filter((item) => !item.endsWith(": "))
      .join(" · ");
  }
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function truncatePreview(value, maxLength = 260) {
  const text = flattenManifestoValue(value);
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength).trimEnd()}…`;
}

function ManifestoPage() {
  const [form, setForm] = useState({
    leader_name: "", party_name: "", party_tagline: "", election_type: "State Assembly Election",
    state: "", constituency: "", language: "English", page_count: 3, vision: "",
    key_issues: "Education\nHealthcare\nEmployment", education: "", healthcare: "",
    employment: "", infrastructure: "", women_empowerment: "", agriculture: "",
    environment: "", primary_color: "#174A35"
  });
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const [manifestoError, setManifestoError] = useState("");

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });

  const requestBody = () => ({
    ...form,
    page_count: Number(form.page_count),
    key_issues: form.key_issues.split(/\n|,/).map((item) => item.trim()).filter(Boolean)
  });

  const generate = async (event) => {
    event.preventDefault();
    setBusy(true);
    setManifestoError("");
    setResult("");
    try {
      const response = await fetch(`${MANIFESTO_API_URL}/generate-manifesto`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody())
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Manifesto generation failed.");
      setResult(normalizeManifesto(data.manifesto ?? data));
    } catch (err) {
      setManifestoError(err.message || "Could not connect to Manifesto backend. Make sure it is running.");
    } finally {
      setBusy(false);
    }
  };

  const downloadPdf = async () => {
    setPdfBusy(true);
    setManifestoError("");
    try {
      const response = await fetch(`${MANIFESTO_API_URL}/generate-manifesto-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody())
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(typeof data.detail === "string" ? data.detail : "PDF download failed.");
      }
      const blob = await response.blob();
      const contentType = response.headers.get("content-type") || "";
      if (!blob.size) throw new Error("The backend returned an empty PDF. Please try again.");
      if (!contentType.toLowerCase().includes("application/pdf")) {
        const errorText = await blob.text();
        let message = errorText || "The backend did not return a PDF file.";
        try {
          const parsed = JSON.parse(errorText);
          if (typeof parsed.detail === "string") message = parsed.detail;
        } catch {
          // Use the returned text if the response is not JSON.
        }
        throw new Error(message);
      }
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "polisense_manifesto.pdf";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      setManifestoError(err.message || "Could not download the PDF.");
    } finally {
      setPdfBusy(false);
    }
  };

  return (
    <section className="page-content manifesto-page">
      <div className="page-heading">
        <div><h1>AI Manifesto Generator</h1><p>Create a structured election manifesto using AI.</p></div>
        <div className="demo-badge"><span></span> MANIFESTO STUDIO</div>
      </div>
      <div className="manifesto-layout">
        <form className="manifesto-form" onSubmit={generate}>
          <h2>Manifesto Details</h2>
          <div className="manifesto-grid">
            <label>Leader Name<input name="leader_name" value={form.leader_name} onChange={update} minLength={2} required /></label>
            <label>Party Name<input name="party_name" value={form.party_name} onChange={update} minLength={2} required /></label>
            <label>Party Tagline<input name="party_tagline" value={form.party_tagline} onChange={update} /></label>
            <label>Election Type<select name="election_type" value={form.election_type} onChange={update}><option>State Assembly Election</option><option>Lok Sabha Election</option><option>Local Body Election</option><option>Municipal Election</option><option>Student Election</option></select></label>
            <label>State<input name="state" value={form.state} onChange={update} required /></label>
            <label>Constituency<input name="constituency" value={form.constituency} onChange={update} /></label>
            <label>Language<select name="language" value={form.language} onChange={update}><option>English</option><option>Hindi</option><option>Hinglish</option></select></label>
            <label>Pages<select name="page_count" value={form.page_count} onChange={update}><option value="2">2 pages</option><option value="3">3 pages</option></select></label>
            <label className="manifesto-wide">Vision<textarea name="vision" value={form.vision} onChange={update} rows="3" required /></label>
            <label className="manifesto-wide">Key Issues (comma or new-line separated)<textarea name="key_issues" value={form.key_issues} onChange={update} rows="3" required /></label>
            <label>Education<input name="education" value={form.education} onChange={update} /></label>
            <label>Healthcare<input name="healthcare" value={form.healthcare} onChange={update} /></label>
            <label>Employment<input name="employment" value={form.employment} onChange={update} /></label>
            <label>Infrastructure<input name="infrastructure" value={form.infrastructure} onChange={update} /></label>
            <label>Women Empowerment<input name="women_empowerment" value={form.women_empowerment} onChange={update} /></label>
            <label>Agriculture<input name="agriculture" value={form.agriculture} onChange={update} /></label>
            <label>Environment<input name="environment" value={form.environment} onChange={update} /></label>
            <label>Primary Color<input name="primary_color" type="color" value={form.primary_color} onChange={update} /></label>
          </div>
          <button className="generate-button" type="submit" disabled={busy}>{busy ? "Generating..." : "Generate Manifesto"}</button>
          <p className="form-note">Connects to your Manifesto backend at {MANIFESTO_API_URL}.</p>
        </form>
        <section className="manifesto-result">
          <h2>Your Manifesto</h2>
          {manifestoError && <div className="error-message" role="alert">{manifestoError}</div>}
          {result ? (() => {
            const title = result.title || `${form.party_name || "Election"} Manifesto`;
            const subtitle = result.subtitle || form.party_tagline || `${form.state || "Your state"}${form.constituency ? ` · ${form.constituency}` : ""}`;
            const introduction = result.introduction || result.executive_summary || result.overview || result.content || "";
            const hiddenKeys = new Set([
              "title", "subtitle", "introduction", "executive_summary", "overview", "content",
              "leader_name", "party_name", "party_tagline", "election_type", "state", "constituency",
              "language", "page_count", "primary_color", "generated_at", "metadata"
            ]);
            const sections = Object.entries(result).filter(([key, value]) =>
              !hiddenKeys.has(key.toLowerCase()) && value !== null && value !== "" && flattenManifestoValue(value)
            );
            const previewSections = sections.slice(0, 2);
            return (
              <>
                <button type="button" className="generate-button pdf-download-button" onClick={downloadPdf} disabled={pdfBusy}>
                  {pdfBusy ? "Preparing PDF..." : "Download Full Manifesto PDF"}
                </button>
                <p className="manifesto-download-hint">The full designed manifesto is in the PDF. This is a short preview.</p>

                <div className="manifesto-preview" style={{ "--manifesto-primary": form.primary_color }}>
                  <div className="manifesto-preview-cover">
                    <span className="manifesto-preview-kicker">POLISENSE AI · MANIFESTO PREVIEW</span>
                    <h3>{title}</h3>
                    {subtitle && <p className="manifesto-preview-subtitle">{subtitle}</p>}
                    <div className="manifesto-preview-meta">
                      <span>{form.leader_name || "Candidate / Leader"}</span>
                      {form.party_name && <span>{form.party_name}</span>}
                      <span>{form.language} · {form.page_count} pages in PDF</span>
                    </div>
                  </div>

                  {introduction && (
                    <section className="manifesto-preview-section manifesto-intro-card">
                      <span className="manifesto-section-label">OUR VISION</span>
                      <h4>Introduction</h4>
                      <p>{truncatePreview(introduction, 330)}</p>
                    </section>
                  )}

                  {previewSections.map(([key, value], index) => (
                    <section className="manifesto-preview-section manifesto-policy-card" key={key}>
                      <span className="manifesto-section-label">PRIORITY {String(index + 1).padStart(2, "0")}</span>
                      <h4>{humanizeManifestoKey(key)}</h4>
                      <p>{truncatePreview(value, 225)}</p>
                    </section>
                  ))}

                  <div className="manifesto-preview-locked">
                    <div className="manifesto-lock-icon">PDF</div>
                    <div>
                      <strong>Full manifesto and policy details</strong>
                      <p>Detailed commitments, implementation points, expected outcomes, and the complete design are available in the downloaded PDF.</p>
                    </div>
                  </div>
                </div>
                <p className="form-note">PDF generation uses the details currently entered in the form.</p>
              </>
            );
          })() : <p>Your generated manifesto will appear here.</p>}
        </section>
      </div>
    </section>
  );
}

function App() {
  const [activePage, setActivePage] = useState("speech");
  const [template, setTemplate] = useState("Rally Speech");
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("General Public");
  const [language, setLanguage] = useState("Hindi");
  const [duration, setDuration] = useState("5");
  const [tone, setTone] = useState("Formal");
  const [keyTopics, setKeyTopics] = useState("");
  const [speech, setSpeech] = useState("");
  const [speechTitle, setSpeechTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState("");
  const [error, setError] = useState("");

  const buildRequestBody = () => ({
    topic: topic.trim(),
    language,
    audience,
    tone,
    duration_minutes: Number(duration),
    key_points: keyTopics
      .split(/\n|,/)
      .map((point) => point.trim())
      .filter(Boolean),
  });

  const generateSpeech = async () => {
    if (topic.trim().length < 5) {
      setError("Please enter a topic containing at least 5 characters.");
      return;
    }

    setLoading(true);
    setError("");
    setSpeech("");
    setSpeechTitle("");

    try {
      const response = await fetch(`${API_BASE_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildRequestBody()),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Speech generation failed. Check the backend terminal."
        );
      }

      if (!data.speech) {
        throw new Error("The backend returned an empty speech.");
      }

      setSpeech(data.speech);
      setSpeechTitle(data.title || `Speech on ${topic.trim()}`);
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to the backend. Please try again in a moment."
      );
    } finally {
      setLoading(false);
    }
  };

  const copySpeech = async () => {
    if (!speech) return;
    try {
      await navigator.clipboard.writeText(speech);
      alert("Speech copied successfully.");
    } catch {
      setError("Unable to copy automatically. Please select and copy the text manually.");
    }
  };

  const downloadFromBackend = async (format) => {
    if (!speech) return;
    setDownloading(format);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/download/${format}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildRequestBody()),
      });

      if (!response.ok) {
        let message = `${format.toUpperCase()} download failed.`;
        try {
          const data = await response.json();
          if (typeof data.detail === "string") message = data.detail;
        } catch {
          // Keep the fallback message when the response is not JSON.
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = format === "pdf" ? "polisense_speech.pdf" : "polisense_speech.txt";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (err) {
      setError(err.message || `Could not download the ${format.toUpperCase()} file.`);
    } finally {
      setDownloading("");
    }
  };

  const wordCount = speech.trim() ? speech.trim().split(/\s+/).length : 0;

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">P</div>
          <span>POLI<span className="purple">SENSE</span></span>
        </div>

        <div className="user-card">
          <div className="avatar">S</div>
          <div>
            <strong>Strategy User</strong>
            <span>Premium Access</span>
          </div>
        </div>

        <div className="sidebar-label">WORKSPACE</div>
        <button type="button" className={`nav-item ${activePage === "speech" ? "active" : ""}`} onClick={() => setActivePage("speech")}>
          <span className="nav-icon">♩</span>
          <span>Speech Generator</span>
        </button>
        <button type="button" className={`nav-item ${activePage === "manifesto" ? "active" : ""}`} onClick={() => setActivePage("manifesto")}>
          <span className="nav-icon">▤</span>
          <span>Manifesto Generator</span>
        </button>

        <div className="sidebar-footer">
          <span className="status-dot"></span>
          Backend Connected Demo
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumb">
            Strategy <span>/</span> <strong>{activePage === "speech" ? "Speech Generator" : "Manifesto Generator"}</strong>
          </div>
          <div className="topbar-right">
            <span className="online-dot"></span>
            <span>Strategy User</span>
            <div className="avatar">S</div>
          </div>
        </header>

        <section className="page-content" style={{ display: activePage === "speech" ? "block" : "none" }}>
          <div className="page-heading">
            <div>
              <h1>AI Speech Generator</h1>
              <p>Create structured speeches for your audience using AI.</p>
            </div>
            <div className="demo-badge"><span></span> API CONNECTED</div>
          </div>

          <div className="info-strip">
            <span>01&nbsp; Speech Settings</span>
            <span>02&nbsp; Generate Speech</span>
            <span>03&nbsp; Copy or Download</span>
          </div>

          <div className="workspace">
            <section className="settings-card">
              <div className="card-heading">
                <div>
                  <h2>Speech Settings</h2>
                  <p>Configure your speech before generating.</p>
                </div>
                <div className="heading-icon">⚙</div>
              </div>

              <form onSubmit={(event) => { event.preventDefault(); generateSpeech(); }}>
                <label htmlFor="template">SPEECH TEMPLATE</label>
                <select id="template" value={template} onChange={(event) => setTemplate(event.target.value)}>
                  <option>Rally Speech</option>
                  <option>Press Conference</option>
                  <option>Public Address</option>
                  <option>Youth Engagement</option>
                  <option>Campaign Speech</option>
                  <option>Community Meeting</option>
                </select>

                <label htmlFor="topic">SPEECH TOPIC</label>
                <input id="topic" value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="e.g. Importance of education" minLength={5} maxLength={500} required />

                <label htmlFor="audience">TARGET AUDIENCE</label>
                <select id="audience" value={audience} onChange={(event) => setAudience(event.target.value)}>
                  <option>General Public</option>
                  <option>Youth</option>
                  <option>Farmers</option>
                  <option>Women</option>
                  <option>Students</option>
                  <option>Local Community</option>
                </select>

                <label htmlFor="language">LANGUAGE</label>
                <select
                  id="language"
                  value={language}
                  onChange={(event) => setLanguage(event.target.value)}
                >
                  <option value="Hindi">Hindi</option>
                  <option value="English">English</option>
                  <option value="Hindi + English">Hindi + English (Hinglish)</option>
                  <option value="Bengali">Bengali</option>
                  <option value="Marathi">Marathi</option>
                  <option value="Tamil">Tamil</option>
                  <option value="Telugu">Telugu</option>
                  <option value="Gujarati">Gujarati</option>
                  <option value="Punjabi">Punjabi</option>
                  <option value="Urdu">Urdu</option>
                  <option value="Kannada">Kannada</option>
                  <option value="Malayalam">Malayalam</option>
                  <option value="Odia">Odia</option>
                  <option value="Assamese">Assamese</option>
                  <option value="Sanskrit">Sanskrit</option>
                  <option value="French">French</option>
                  <option value="German">German</option>
                  <option value="Spanish">Spanish</option>
                  <option value="Portuguese">Portuguese</option>
                  <option value="Arabic">Arabic</option>
                  <option value="Chinese">Chinese</option>
                  <option value="Japanese">Japanese</option>
                </select>

                <label htmlFor="tone">SPEECH TONE</label>
                <select id="tone" value={tone} onChange={(event) => setTone(event.target.value)}>
                  <option>Formal</option>
                  <option>Persuasive</option>
                  <option>Inspirational</option>
                  <option>Conversational</option>
                  <option>Urgent</option>
                </select>

                <label htmlFor="duration">SPEECH DURATION</label>
                <select id="duration" value={duration} onChange={(event) => setDuration(event.target.value)}>
                  <option value="1">1 minute</option>
                  <option value="3">3 minutes</option>
                  <option value="5">5 minutes</option>
                  <option value="7">7 minutes</option>
                  <option value="10">10 minutes</option>
                  <option value="15">15 minutes</option>
                </select>

                <label htmlFor="keyTopics">KEY POINTS</label>
                <textarea id="keyTopics" value={keyTopics} onChange={(event) => setKeyTopics(event.target.value)} placeholder="Add points separated by commas or new lines..." rows={4} />

                <button className="generate-button" type="submit" disabled={loading}>
                  {loading ? "Generating with AI..." : "✦ Generate Speech"}
                </button>
                <p className="form-note">Uses the deployed POLISENSE backend and Groq AI. The backend may take a moment to wake up on the first request.</p>
              </form>
            </section>

            <section className="output-card">
              <div className="output-header">
                <div>
                  <h2>{speech ? speechTitle || `Speech on ${topic}` : "Your Speech"}</h2>
                  <p>{speech ? `${template} · ${language} · ${tone}` : "Your AI-generated speech will appear here."}</p>
                </div>
                {speech && (
                  <div className="output-actions">
                    <button type="button" onClick={copySpeech}>Copy</button>
                    <button type="button" onClick={() => downloadFromBackend("txt")} disabled={Boolean(downloading)}>
                      {downloading === "txt" ? "Preparing..." : "Download TXT"}
                    </button>
                    <button type="button" onClick={() => downloadFromBackend("pdf")} disabled={Boolean(downloading)}>
                      {downloading === "pdf" ? "Preparing..." : "Download PDF"}
                    </button>
                  </div>
                )}
              </div>

              {error && <div className="error-message" role="alert">{error}</div>}

              <div className={`output-body ${speech ? "has-speech" : ""}`}>
                {loading ? (
                  <div className="empty-state">
                    <div className="microphone">...</div>
                    <h3>Generating your speech</h3>
                    <p>The AI is working on your request. Please wait.</p>
                  </div>
                ) : speech ? (
                  <pre>{speech}</pre>
                ) : (
                  <div className="empty-state">
                    <div className="microphone">♫</div>
                    <h3>Ready to create your speech?</h3>
                    <p>Enter your topic, choose your preferred settings, and click Generate Speech.</p>
                  </div>
                )}
              </div>

              <div className="output-footer">
                <span>{wordCount} words</span>
                <span><span className="status-dot"></span> {speech ? "AI Generated" : "Waiting for generation"}</span>
              </div>
            </section>
          </div>

          <footer className="page-footer">
            <span>POLISENSE AI</span>
            <span>Speech Generator · Prototype v1.0</span>
          </footer>
        </section>
        {activePage === "manifesto" && <ManifestoPage />}
      </main>
    </div>
  );
}

export default App;
