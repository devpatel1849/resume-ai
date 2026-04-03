import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

function LogoutPage() {
  const { token, logout } = useAuth();
  const [status, setStatus] = useState("processing");
  const [error, setError] = useState("");
  const [countdown, setCountdown] = useState(3);

  useEffect(() => {
    let active = true;

    if (!token) {
      if (active) {
        setStatus("success");
      }
      return;
    }

    logout()
      .then(() => {
        if (active) {
          setStatus("success");
        }
      })
      .catch(() => {
        if (active) {
          setStatus("failed");
          setError("We could not end your server session, but local sign out is complete.");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (status !== "success" || countdown <= 0) {
      return;
    }

    const timeout = setTimeout(() => {
      setCountdown((current) => current - 1);
    }, 1000);

    return () => clearTimeout(timeout);
  }, [status, countdown]);

  if (status === "success" && countdown <= 0) {
    return <Navigate to="/login" replace />;
  }

  const isProcessing = status === "processing";
  const isSuccess = status === "success";
  const isFailed = status === "failed";

  return (
    <main className="auth-shell">
      <section className="auth-card logout-card">
        <p className="eyebrow">Session</p>
        <h1 className="auth-heading">
          {isProcessing && "Signing You Out"}
          {isSuccess && "Logged Out Successfully"}
          {isFailed && "Signed Out With Warning"}
        </h1>
        <p className="auth-subtitle">
          {isProcessing && "Please wait while we close your session securely."}
          {isSuccess && "Your account session has been closed. Redirecting you to login."}
          {isFailed && "You are signed out locally. Please login again to continue."}
        </p>

        {isProcessing && (
          <div className="logout-loader" aria-label="logging out" />
        )}

        {isSuccess && (
          <p className="helper-text logout-note">Redirecting to login in {countdown}s...</p>
        )}

        {isFailed && <p className="error-banner auth-error">{error}</p>}

        <div className="logout-actions">
          {(isSuccess || isFailed) && (
            <Link to="/login" className="button button-primary auth-submit">
              Go to Login
            </Link>
          )}
          {isFailed && (
            <Link to="/dashboard" className="button button-secondary auth-submit">
              Return to Dashboard
            </Link>
          )}
        </div>
      </section>
    </main>
  );
}

export default LogoutPage;
