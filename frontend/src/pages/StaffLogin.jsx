// staff 登录页面
import React, { useEffect } from "react";
import LoginForm from "../components/LoginForm";
import useLogin from "../components/useLogin";

function StaffLogin() {
  useEffect(() => {
    document.title = "Staff Login";
  }, []);

  const {
    username,
    setUsername,
    password,
    setPassword,
    handleSubmit, // 普通登录
    handleSSOLogin, // SSO登录
    loading // 是否正在登录
  } = useLogin({
    api: "/api/login",
    ssoApi: "/api/sso-login",
    successRedirect: "/staff-landing",
    role: "staff"
  }); // 还可以传入 onSuccess 和 onError 回调函数

  return (
    <LoginForm
      title="Staff Login"
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

export default StaffLogin;
