import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Auth } from "../utils/Auth";
import { Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button } from "@mui/material";

/**
 * Universal Login Hook
 * @param {Object} options
 * @param {string} options.api Login API path, e.g. "/api/staff-login"
 * @param {string} options.successRedirect Redirect path after successful login
 * @param {string} options.role Role (staff/admin), will be sent to backend
 * @param {function} [options.onSuccess] Callback after successful login
 * @param {function} [options.onError] Callback after login failure/error
 * @returns {Object}
 */
function useLogin({ api, successRedirect, role, onSuccess, onError }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [ssoDialogOpen, setSsoDialogOpen] = useState(false);
  const navigate = useNavigate();

  // Regular login
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(api, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, role }),
      });
      let data;
      try {
        data = await res.json();
      } catch {
        // JSON parsing failed
        if (onError) onError("Server error, please try again later!");
        else alert("Server error, please try again later!");
        setLoading(false);
        return;
      }
      // Login successful
      if (res.status === 200 && data.success) {
        Auth.save(data.token, data.user);
        if (onSuccess) onSuccess(data);
        if (successRedirect) navigate(successRedirect);
      } else if (res.status === 401) {
        if (onError) onError(data.message || "Username or password error!");
        else alert(data.message || "Username or password error!");
      } else if (res.status === 400) {
        if (onError) onError(data.message || "Request parameter error!");
        else alert(data.message || "Request parameter error!");
      } else {
        if (onError) onError(data.message || "Login failed!");
        else alert(data.message || "Login failed!");
      }
    } catch {
      if (onError) onError("Internal server error, please try again later!");
      else alert("Internal server error, please try again later!");
    } finally {
      setLoading(false);
    }
  };

  // SSO login
  const handleSSOLogin = () => {
    setSsoDialogOpen(true);
  };

  // Close SSO dialog
  const handleCloseSsoDialog = () => {
    setSsoDialogOpen(false);
  };

  return {
    username,
    setUsername,
    password,
    setPassword,
    handleSubmit,
    handleSSOLogin,
    loading,
    ssoDialogOpen,
    handleCloseSsoDialog,
  };
}

export default useLogin; 