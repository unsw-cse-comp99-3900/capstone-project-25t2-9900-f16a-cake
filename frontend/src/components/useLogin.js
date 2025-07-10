import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Auth } from "../utils/Auth";

/**
 * 通用登录Hook
 * @param {Object} options
 * @param {string} options.api 登录API路径，如"/api/staff-login"
 * @param {string} options.ssoApi SSO登录API路径，如"/api/sso-login"
 * @param {string} options.successRedirect 登录成功后跳转路径
 * @param {string} options.role 角色（staff/admin），会一并发送给后端
 * @param {function} [options.onSuccess] 登录成功后的回调
 * @param {function} [options.onError] 登录失败/异常的回调
 * @returns {Object}
 */
function useLogin({ api, ssoApi, successRedirect, role, onSuccess, onError }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
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
        console.log("登录请求返回的数据：" , res.status, data)
      } catch {
        // json 解析失败
        if (onError) onError("服务器异常，请稍后再试！");
        else alert("服务器异常，请稍后再试！");
        setLoading(false);
        return;
      }
      // 登录成功
      if (res.status === 200 && data.success) {
        Auth.save(data.token, data.user);
        if (onSuccess) onSuccess(data);
        if (successRedirect) navigate(successRedirect);
      } else if (res.status === 401) {
        if (onError) onError(data.message || "用户名或密码错误！");
        else alert(data.message || "用户名或密码错误！");
      } else if (res.status === 400) {
        if (onError) onError(data.message || "请求参数有误！");
        else alert(data.message || "请求参数有误！");
      } else {
        if (onError) onError(data.message || "登录失败！");
        else alert(data.message || "登录失败！");
      }
    } catch {
      // 网络或服务器异常, api 请求异常
      if (onError) onError("网络或服务器异常，请稍后再试！");
      else alert("网络或服务器异常，请稍后再试！");
    } finally {
      setLoading(false);
    }
  };

  // SSO登录
  const handleSSOLogin = async () => {
    setLoading(true);
    try {
      const res = await fetch(ssoApi);
      const data = await res.json();
      if (data.success) {
        Auth.save(data.token, data); // 保存token和用户信息
        if (data.role) localStorage.setItem("role", data.role);
        if (onSuccess) onSuccess(data);
        if (successRedirect) navigate(successRedirect);
      } else {
        if (onError) onError("SSO 登录失败！");
        else alert("SSO 登录失败！");
      }
    } catch {
      if (onError) onError("网络或服务器异常，请稍后再试！");
      else alert("网络或服务器异常，请稍后再试！");
    } finally {
      setLoading(false);
    }
  };

  return {
    username,
    setUsername,
    password,
    setPassword,
    handleSubmit,
    handleSSOLogin,
    loading,
  };
}

export default useLogin; 