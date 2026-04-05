import axios from "axios";

const BASE_URL = "http://127.0.0.1:8000";
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
});

export const getApiErrorMessage = (error, fallbackMessage) => {
  if (error?.code === "ECONNABORTED") {
    return "Request timed out. Please try again.";
  }

  return error?.response?.data?.detail || fallbackMessage;
};

export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    return;
  }
  delete api.defaults.headers.common.Authorization;
};

export const registerUser = async (full_name, email, password) => {
  return await api.post("/auth/register", { full_name, email, password });
};

export const loginUser = async (email, password) => {
  return await api.post("/auth/login", { email, password });
};

export const getProfile = async () => {
  return await api.get("/auth/profile");
};

export const updateProfile = async (payload) => {
  return await api.put("/auth/profile", payload);
};

export const uploadProfilePhoto = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  return await api.post("/auth/profile/photo", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const logoutUser = async () => {
  return await api.post("/auth/logout");
};

export const fetchGithub = async (username, jobDescription = "", maxProjects = 4) => {
  return await api.post(
    "/github/github",
    {
      username,
      job_description: jobDescription,
      max_projects: maxProjects,
    },
    { timeout: 25000 }
  );
};

export const parseResumeFile = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  return await api.post("/resume/parse-file", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const generateResume = async (
  text,
  oldResumeText = "",
  jobDescription = "",
  template = "ATS Professional"
) => {
  return await api.post(
    "/resume/generate",
    {
      text,
      old_resume_text: oldResumeText,
      job_description: jobDescription,
      template,
    },
    {
      timeout: 90000,
    }
  );
};

export const downloadResumePdf = async (resumeText, template, fileName = "tailored_resume.pdf") => {
  return await api.post(
    "/resume/download-pdf",
    {
      resume_text: resumeText,
      template,
      file_name: fileName,
    },
    {
      responseType: "blob",
      timeout: 45000,
    }
  );
};