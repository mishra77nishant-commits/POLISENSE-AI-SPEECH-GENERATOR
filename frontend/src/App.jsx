import { useState } from "react";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000/api/speech";

function App() {
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
          "Could not connect to the backend. Ensure it is running at http://127.0.0.1:8000."
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
        <div className="nav-item active">
          <span className="nav-icon">♩</span>
          <span>Speech Generator</span>
        </div>

        <div className="sidebar-footer">
          <span className="status-dot"></span>
          Backend Connected Demo
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumb">
            Strategy <span>/</span> <strong>Speech Generator</strong>
          </div>
          <div className="topbar-right">
            <span className="online-dot"></span>
            <span>Strategy User</span>
            <div className="avatar">S</div>
          </div>
        </header>

        <section className="page-content">
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
                <p className="form-note">Uses your POLISENSE backend and Groq AI. Keep the backend server running while using this app.</p>
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
      </main>
    </div>
  );
}

export default App;
