import React, { useEffect } from "react";
import LoginForm from "../components/LoginForm";
import useLogin from "../components/useLogin";

function AdminLogin() {
  useEffect(() => {
    document.title = "Admin Login";
  }, []);

  const {
    username,
    setUsername,
    password,
    setPassword,
    handleSubmit,
    handleSSOLogin,
    loading
  } = useLogin({
    api: "/api/login", // 这里请根据后端实际API调整
    ssoApi: "/api/sso-login",
    successRedirect: "/admin-landing", // 这里请根据实际跳转路径调整
    role: "admin"
  });

  return (
    <LoginForm
      title="Admin Login"
      username={username}
      password={password}
      setUsername={setUsername}
      setPassword={setPassword}
      onSubmit={handleSubmit}
      onSSOLogin={handleSSOLogin}
      usernameLabel="Username"
      passwordLabel="Password"
      loginButtonText={loading ? "Logging in..." : "Login"}
      ssoButtonText="Using UNSW SSO"
    />
  );
}

export default AdminLogin;
