import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  getProfile,
  loginUser,
  logoutUser,
  registerUser,
  setAuthToken,
  updateProfile,
  uploadProfilePhoto,
} from "../api";

const AuthContext = createContext(null);

function parseStoredUser() {
  const saved = localStorage.getItem("auth_user");
  if (!saved) {
    return null;
  }

  try {
    return JSON.parse(saved);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("auth_token") || "");
  const [user, setUser] = useState(parseStoredUser());
  const [loadingProfile, setLoadingProfile] = useState(false);

  const clearAuth = () => {
    setToken("");
    setUser(null);
    setAuthToken("");
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
  };

  const saveSession = (accessToken, profile) => {
    setToken(accessToken);
    setUser(profile);
    setAuthToken(accessToken);
    localStorage.setItem("auth_token", accessToken);
    localStorage.setItem("auth_user", JSON.stringify(profile));
  };

  const login = async (email, password) => {
    const response = await loginUser(email, password);
    saveSession(response.data.access_token, response.data.user);
    return response.data.user;
  };

  const register = async (fullName, email, password) => {
    const response = await registerUser(fullName, email, password);
    saveSession(response.data.access_token, response.data.user);
    return response.data.user;
  };

  const loadProfile = async () => {
    if (!token) {
      return null;
    }

    setLoadingProfile(true);
    try {
      const response = await getProfile();
      setUser(response.data);
      localStorage.setItem("auth_user", JSON.stringify(response.data));
      return response.data;
    } catch (error) {
      clearAuth();
      throw error;
    } finally {
      setLoadingProfile(false);
    }
  };

  const logout = async () => {
    if (token) {
      try {
        await logoutUser();
      } catch {
        // No-op because local cleanup should still complete.
      }
    }

    clearAuth();
  };

  const saveProfile = async (profileData) => {
    const response = await updateProfile(profileData);
    setUser(response.data);
    localStorage.setItem("auth_user", JSON.stringify(response.data));
    return response.data;
  };

  const saveProfilePhoto = async (file) => {
    const response = await uploadProfilePhoto(file);
    setUser(response.data);
    localStorage.setItem("auth_user", JSON.stringify(response.data));
    return response.data;
  };

  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  useEffect(() => {
    if (token && !user) {
      loadProfile().catch(() => {
        // Ignore network or authorization failures during bootstrap.
      });
    }
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      loadingProfile,
      login,
      register,
      logout,
      loadProfile,
      saveProfile,
      saveProfilePhoto,
      clearAuth,
    }),
    [token, user, loadingProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
