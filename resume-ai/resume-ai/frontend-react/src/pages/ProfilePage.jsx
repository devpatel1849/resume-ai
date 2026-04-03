import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../api";

function ProfilePage() {
  const { user, loadProfile, loadingProfile, saveProfile, saveProfilePhoto } = useAuth();
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    mobile_no: "",
    gender: "",
  });

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase())
        .join("")
    : "U";

  const joinedDate = user?.created_at
    ? new Date(user.created_at).toLocaleString()
    : "-";

  const handleRefreshProfile = async () => {
    setError("");
    setSuccess("");
    try {
      const latest = await loadProfile();
      if (latest) {
        setFormData({
          full_name: latest.full_name || "",
          email: latest.email || "",
          mobile_no: latest.mobile_no || "",
          gender: latest.gender || "",
        });
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Failed to refresh profile."));
    }
  };

  const handleInputChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSaveProfile = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);
    try {
      await saveProfile({
        full_name: formData.full_name,
        email: formData.email,
        mobile_no: formData.mobile_no,
        gender: formData.gender,
      });
      setSuccess("Profile updated successfully.");
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "Failed to update profile."));
    } finally {
      setSaving(false);
    }
  };

  const handlePhotoUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setError("");
    setSuccess("");
    setUploading(true);
    try {
      await saveProfilePhoto(file);
      setSuccess("Profile photo updated.");
    } catch (uploadError) {
      setError(getApiErrorMessage(uploadError, "Failed to upload profile photo."));
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        email: user.email || "",
        mobile_no: user.mobile_no || "",
        gender: user.gender || "",
      });
      return;
    }

    handleRefreshProfile();
  }, []);

  return (
    <main className="auth-shell">
      <section className="auth-card profile-card">
        <p className="eyebrow">Account</p>
        <h1 className="auth-heading">User Profile</h1>
        <p className="auth-subtitle">Update your account details, contact information, and profile image.</p>

        <div className="profile-hero">
          {user?.profile_photo_url ? (
            <img className="profile-avatar profile-avatar-image" src={user.profile_photo_url} alt="Profile" />
          ) : (
            <div className="profile-avatar" aria-hidden="true">{initials}</div>
          )}
          <div>
            <h2 className="profile-name">{user?.full_name || "Unknown user"}</h2>
            <p className="helper-text">{user?.email || "Email unavailable"}</p>
          </div>
          <label className="button button-secondary profile-photo-btn" htmlFor="profilePhotoInput">
            {uploading ? "Uploading..." : "Upload Photo"}
          </label>
          <input
            id="profilePhotoInput"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={handlePhotoUpload}
            disabled={uploading}
            className="hidden-file-input"
          />
          <button
            type="button"
            className="button button-tertiary"
            onClick={handleRefreshProfile}
            disabled={loadingProfile}
          >
            {loadingProfile ? "Refreshing..." : "Refresh"}
          </button>
        </div>

        {loadingProfile && <p className="helper-text">Loading profile...</p>}

        {user ? (
          <form className="profile-form" onSubmit={handleSaveProfile}>
            <div className="profile-grid">
              <label className="field-label" htmlFor="fullName">Full Name</label>
              <input
                id="fullName"
                name="full_name"
                className="text-input"
                value={formData.full_name}
                onChange={handleInputChange}
                placeholder="Enter your full name"
              />

              <label className="field-label" htmlFor="email">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                className="text-input"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
              />

              <label className="field-label" htmlFor="mobileNo">Mobile Number</label>
              <input
                id="mobileNo"
                name="mobile_no"
                className="text-input"
                value={formData.mobile_no}
                onChange={handleInputChange}
                placeholder="e.g. +91 9876543210"
              />

              <label className="field-label" htmlFor="gender">Gender</label>
              <select
                id="gender"
                name="gender"
                className="text-input"
                value={formData.gender}
                onChange={handleInputChange}
              >
                <option value="">Select gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
                <option value="Prefer Not To Say">Prefer Not To Say</option>
              </select>

              <div className="profile-row">
                <span>User ID</span>
                <strong>{user.id}</strong>
              </div>
              <div className="profile-row">
                <span>Joined</span>
                <strong>{joinedDate}</strong>
              </div>
            </div>

            <button type="submit" className="button button-primary auth-submit" disabled={saving}>
              {saving ? "Saving..." : "Save Profile"}
            </button>
          </form>
        ) : (
          !loadingProfile && <p className="helper-text">Profile not available.</p>
        )}

        {error && <p className="error-banner auth-error">{error}</p>}
        {success && <p className="success-banner auth-error">{success}</p>}

        <div className="profile-actions">
          <Link to="/dashboard" className="button button-secondary">Back to dashboard</Link>
          <Link to="/logout" className="button button-primary">Logout</Link>
        </div>
      </section>
    </main>
  );
}

export default ProfilePage;
