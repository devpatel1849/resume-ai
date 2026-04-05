import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
  downloadResumePdf,
  fetchGithub,
  generateResume,
  getApiErrorMessage,
  parseResumeFile,
} from "../api";
import { useAuth } from "../context/AuthContext";

function DashboardPage() {
  const githubSectionStart = "[GITHUB_PROJECTS_START]";
  const githubSectionEnd = "[GITHUB_PROJECTS_END]";
  const { user } = useAuth();
  const [username, setUsername] = useState("");
  const [text, setText] = useState("");
  const [output, setOutput] = useState("");
  const [repos, setRepos] = useState([]);
  const [oldResumeText, setOldResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState("ATS Professional");
  const [error, setError] = useState("");
  const [lastSync, setLastSync] = useState("");
  const [isFetchingGithub, setIsFetchingGithub] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isUploadingResume, setIsUploadingResume] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const resumePatterns = [
    {
      name: "ATS Professional",
      description: "Best for applicant tracking systems and corporate hiring workflows.",
    },
    {
      name: "Modern Impact",
      description: "Achievement-first flow with concise, high-energy highlights.",
    },
    {
      name: "Executive Brief",
      description: "Leadership-forward style for manager and senior positions.",
    },
    {
      name: "Technical Deep",
      description: "Technical detail and delivery outcomes for engineering roles.",
    },
    {
      name: "Classic Serif",
      description: "Traditional formal look with balanced content density.",
    },
  ];

  const generationLocked = isGenerating || isUploadingResume;

  const languageCount = useMemo(() => {
    return new Set(repos.map((repo) => repo.language).filter(Boolean)).size;
  }, [repos]);

  const topLanguages = useMemo(() => {
    const languageMap = repos.reduce((acc, repo) => {
      const language = repo.language || "Unknown";
      acc[language] = (acc[language] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(languageMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([language, count]) => `${language} (${count})`)
      .join(", ");
  }, [repos]);

  const readinessScore = useMemo(() => {
    let score = 25;
    if (text.trim()) {
      score += 35;
    }
    if (oldResumeText.trim()) {
      score += 20;
    }
    if (jobDescription.trim()) {
      score += 20;
    }
    return score;
  }, [text, oldResumeText, jobDescription]);

  const buildGithubSection = (repoList) => {
    const describedRepos = repoList.filter((repo) => {
      const description = (repo?.description || "").trim().toLowerCase();
      return Boolean(description) && !["no description", "no description provided", "n/a", "na", "none"].includes(description);
    });

    if (!describedRepos.length) {
      return `${githubSectionStart}\nGitHub Projects: no repositories with valid descriptions found.\n${githubSectionEnd}`;
    }

    const lines = describedRepos.map((repo, index) => {
      const name = repo.name || "Untitled";
      const description = repo.description;
      const language = repo.language || "Unknown";
      return `${index + 1}. ${name} | ${language}\n   ${description}`;
    });

    return [
      githubSectionStart,
      "GitHub Projects (Auto-imported):",
      ...lines,
      githubSectionEnd,
    ].join("\n");
  };

  const mergeWithGithubSection = (existingText, githubSection) => {
    const blockRegex = /\[GITHUB_PROJECTS_START\][\s\S]*?\[GITHUB_PROJECTS_END\]/g;
    const baseText = existingText.replace(blockRegex, "").trim();
    return baseText ? `${baseText}\n\n${githubSection}` : githubSection;
  };

  const handleGithub = async () => {
    const normalizedInput = username.trim();
    const normalizedUsername = normalizedInput
      .replace(/^https?:\/\/github\.com\//i, "")
      .replace(/\/$/, "")
      .split("/")[0]
      .replace(/^@/, "")
      .split("?")[0]
      .split("#")[0];

    if (!normalizedUsername) {
      setError("Enter a GitHub username before fetching projects.");
      return;
    }

    setError("");
    setIsFetchingGithub(true);
    try {
      const res = await fetchGithub(normalizedUsername, jobDescription, 4);
      const repoList = Array.isArray(res.data) ? res.data : [];
      const githubSection = buildGithubSection(repoList);
      setRepos(repoList);
      setText((previousText) => mergeWithGithubSection(previousText, githubSection));
      setLastSync(new Date().toLocaleString());
    } catch (githubError) {
      setError(getApiErrorMessage(githubError, "GitHub fetch failed. Please check the username and try again."));
    } finally {
      setIsFetchingGithub(false);
    }
  };

  const handleGenerate = async () => {
    if (!text.trim()) {
      setError("Add source content before generating a resume.");
      return;
    }

    setError("");
    setIsGenerating(true);
    try {
      const res = await generateResume(
        text,
        oldResumeText,
        jobDescription,
        selectedTemplate
      );
      setOutput(res.data?.resume || "");
    } catch (generateError) {
      setError(getApiErrorMessage(generateError, "Resume generation failed. Please try again."));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleOldResumeUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setError("");
    setIsUploadingResume(true);
    try {
      const res = await parseResumeFile(file);
      setOldResumeText(res.data?.text || "");
    } catch (uploadError) {
      const fallback = "Failed to parse old resume file. Please try .pdf, .txt, or .md.";
      setError(getApiErrorMessage(uploadError, fallback));
    } finally {
      setIsUploadingResume(false);
    }
    event.target.value = "";
  };

  const handleDownloadPdf = async () => {
    if (!output.trim()) {
      setError("Generate a resume before downloading PDF.");
      return;
    }

    setError("");
    setIsDownloadingPdf(true);

    try {
      const baseName = user?.full_name?.trim().replace(/\s+/g, "_") || "tailored_resume";
      const fileName = `${baseName}_${selectedTemplate.replace(/\s+/g, "_")}.pdf`;
      const response = await downloadResumePdf(output, selectedTemplate, fileName);

      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (downloadError) {
      setError(getApiErrorMessage(downloadError, "PDF download failed. Please try again."));
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  return (
    <div className="dashboard-shell">
      <nav className="app-nav">
        <div>
          <p className="nav-title">Welcome, {user?.full_name || "User"}</p>
          <p className="nav-subtitle">Manage your resume workflow and account</p>
        </div>
        <div className="nav-links">
          <Link to="/profile" className="button button-secondary">Profile</Link>
          <Link to="/logout" className="button button-secondary">Logout</Link>
        </div>
      </nav>

      <header className="topbar">
        <div>
          <p className="eyebrow">Resume Intelligence</p>
          <h1>Career Targeting Dashboard</h1>
          <p className="subtitle">
            Blend your background, old resume, and target role requirements to generate a stronger job-specific resume.
          </p>
        </div>
        <div className="sync-badge">
          <span>Last sync</span>
          <strong>{lastSync || "Not synced yet"}</strong>
        </div>
      </header>

      <section className="kpi-grid" aria-label="Workspace summary">
        <article className="kpi-card">
          <p>Total Projects</p>
          <h2>{repos.length}</h2>
        </article>
        <article className="kpi-card">
          <p>Languages Tracked</p>
          <h2>{languageCount}</h2>
        </article>
        <article className="kpi-card">
          <p>Input Characters</p>
          <h2>{text.length}</h2>
        </article>
        <article className="kpi-card">
          <p>Resume Length</p>
          <h2>{output.length}</h2>
        </article>
        <article className="kpi-card">
          <p>Tailoring Readiness</p>
          <h2>{readinessScore}%</h2>
        </article>
      </section>

      <section className="workspace-grid">
        <article className="panel">
          <div className="panel-header">
            <h3>Source Builder</h3>
            <span className="status-chip">{isFetchingGithub ? "Syncing GitHub" : "Ready"}</span>
          </div>

          <label className="field-label" htmlFor="githubUsername">GitHub Username</label>
          <div className="input-row">
            <input
              id="githubUsername"
              className="text-input"
              placeholder="e.g. octocat"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <button className="button button-secondary" onClick={handleGithub} disabled={isFetchingGithub}>
              {isFetchingGithub ? "Fetching..." : "Fetch Projects"}
            </button>
          </div>

          <label className="field-label" htmlFor="sourceText">Career Source Text</label>
          <textarea
            id="sourceText"
            className="text-area"
            rows={13}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste your work history, achievements, or edit imported GitHub summaries..."
          />

          <div className="targeting-block">
            <h4>Targeted Resume Inputs</h4>

            <label className="field-label" htmlFor="oldResumeUpload">Upload Old Resume</label>
            <div className="input-row">
              <input
                id="oldResumeUpload"
                type="file"
                className="text-input"
                accept=".pdf,.txt,.md"
                onChange={handleOldResumeUpload}
                disabled={isUploadingResume}
              />
            </div>
            <textarea
              className="text-area text-area-compact"
              rows={6}
              value={oldResumeText}
              onChange={(event) => setOldResumeText(event.target.value)}
              placeholder="Your old resume text will appear here after upload, or you can paste it manually."
            />

            <label className="field-label" htmlFor="jobDescription">Job Description</label>
            <textarea
              id="jobDescription"
              className="text-area text-area-compact"
              rows={6}
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              placeholder="Paste the target job description to tailor the generated resume."
            />

            <label className="field-label">Choose Resume Template</label>
            <div className="template-picker" role="radiogroup" aria-label="Resume template options">
              {resumePatterns.map((pattern) => {
                const isSelected = selectedTemplate === pattern.name;
                return (
                  <button
                    key={pattern.name}
                    type="button"
                    className={`template-option ${isSelected ? "active" : ""}`}
                    onClick={() => setSelectedTemplate(pattern.name)}
                    role="radio"
                    aria-checked={isSelected}
                  >
                    <strong>{pattern.name}</strong>
                    <span>{pattern.description}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="actions-row">
            <div className="action-buttons">
              <button className="button button-primary" onClick={handleGenerate} disabled={generationLocked}>
                {isGenerating ? "Generating..." : "Generate Resume"}
              </button>
              <button
                className="button button-secondary"
                onClick={handleDownloadPdf}
                disabled={isDownloadingPdf || !output.trim()}
              >
                {isDownloadingPdf ? "Preparing PDF..." : "Download PDF"}
              </button>
            </div>
            <p className="helper-text">
              {isUploadingResume
                ? "Parsing your uploaded resume..."
                : `Pattern: ${selectedTemplate}. Top tech stack: ${topLanguages || "Add projects to detect language trends"}. GitHub import keeps only 3-4 job-relevant projects.`}
            </p>
          </div>
        </article>

        <article className="panel output-panel">
          <div className="panel-header">
            <h3>Generated Resume</h3>
            <span className="status-chip">{isGenerating ? "In Progress" : "Updated"}</span>
          </div>

          {output ? (
            <pre className="output-block">{output}</pre>
          ) : (
            <div className="empty-state">
              <p>Your generated resume will appear here.</p>
              <small>Use the source builder panel and click Generate Resume.</small>
            </div>
          )}
        </article>
      </section>

      <section className="panel repo-panel">
        <div className="panel-header">
          <h3>Repository Snapshot</h3>
          <span className="status-chip">{repos.length} records</span>
        </div>

        {repos.length > 0 ? (
          <ul className="repo-list">
            {repos.slice(0, 8).map((repo) => (
              <li key={repo.name} className="repo-item">
                <div>
                  <strong>{repo.name || "Untitled repository"}</strong>
                  <p>{repo.description || "No description provided."}</p>
                </div>
                <span>{repo.language || "Unknown"}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="helper-text">No repositories loaded yet.</p>
        )}
      </section>

      {error && <p className="error-banner">{error}</p>}
    </div>
  );
}

export default DashboardPage;
