import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Auth } from "../utils/Auth";
import { Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button } from "@mui/material";

/**
 * 通用登录Hook
 * @param {Object} options
 * @param {string} options.api 登录API路径，如"/api/staff-login"
 * @param {string} options.successRedirect 登录成功后跳转路径
 * @param {string} options.role 角色（staff/admin），会一并发送给后端
 * @param {function} [options.onSuccess] 登录成功后的回调
 * @param {function} [options.onError] 登录失败/异常的回调
 * @returns {Object}
 */
function useLogin({ api, successRedirect, role, onSuccess, onError }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [ssoDialogOpen, setSsoDialogOpen] = useState(false);
  const navigate = useNavigate();

  // 普通登录
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
        // json 解析失败
        if (onError) onError("Server error, please try again later!");
        else alert("Server error, please try again later!");
        setLoading(false);
        return;
      }
      // 登录成功
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

  // SSO登录
  const handleSSOLogin = () => {
    setSsoDialogOpen(true);
  };

  // 关闭SSO对话框
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