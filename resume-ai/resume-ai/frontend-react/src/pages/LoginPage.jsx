import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { token, login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (mode === "register" && !fullName.trim()) {
      setError("Full name is required to create an account.");
      return;
    }

    if (!email.trim()) {
      setError("Email is required.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsSubmitting(true);

    try {
      if (mode === "register") {
        await register(fullName.trim(), email.trim(), password);
      } else {
        await login(email.trim(), password);
      }

      const redirectPath = location.state?.from || "/dashboard";
      navigate(redirectPath, { replace: true });
    } catch (submitError) {
      const fallback = mode === "register" ? "Registration failed." : "Login failed.";
      setError(submitError.response?.data?.detail || fallback);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">Secure Access</p>
        <h1 className="auth-heading">{mode === "login" ? "Login" : "Create account"}</h1>
        <p className="auth-subtitle">
          Sign in to access your dashboard, profile, and AI resume tools.
        </p>

        <div className="auth-mode-toggle" role="tablist" aria-label="auth mode">
          <button
            type="button"
            className={`mode-btn ${mode === "login" ? "active" : ""}`}
            onClick={() => {
              setMode("login");
              setError("");
              setPassword("");
              setShowPassword(false);
            }}
            disabled={isSubmitting}
          >
            Login
          </button>
          <button
            type="button"
            className={`mode-btn ${mode === "register" ? "active" : ""}`}
            onClick={() => {
              setMode("register");
              setError("");
              setPassword("");
              setShowPassword(false);
            }}
            disabled={isSubmitting}
          >
            Register
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === "register" && (
            <>
              <label className="field-label" htmlFor="fullName">Full name</label>
              <input
                id="fullName"
                className="text-input"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Enter your full name"
                required
              />
            </>
          )}

          <label className="field-label" htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            className="text-input"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            autoComplete="email"
            required
          />

          <label className="field-label" htmlFor="password">Password</label>
          <div className="password-row">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              className="text-input"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={8}
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              placeholder="Minimum 8 characters"
              required
            />
            <button
              type="button"
              className="button button-tertiary"
              onClick={() => setShowPassword((current) => !current)}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>

          <button type="submit" className="button button-primary auth-submit" disabled={isSubmitting}>
            {isSubmitting ? "Please wait..." : mode === "login" ? "Login" : "Register"}
          </button>
        </form>

        <p className="helper-text auth-note">
          {mode === "login"
            ? "Use your account credentials to continue to the dashboard."
            : "Register to create your account and start generating AI resumes."}
        </p>

        {error && <p className="error-banner auth-error">{error}</p>}
      </section>
    </main>
  );
}

export default LoginPage;
