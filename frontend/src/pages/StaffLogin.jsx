import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Box, Typography, TextField, Button, Paper, Divider } from "@mui/material";

function StaffLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Staff Login";
  }, []);

const handleSubmit = async (e) => {
  e.preventDefault(); // 阻止表单默认提交行为（页面刷新）

  try {
    // 通过 fetch 向后端 Flask 发送 POST 登录请求
    const res = await fetch("/api/staff-login", {
      method: "POST", // 请求方法
      headers: { "Content-Type": "application/json" }, // 指定请求体为 JSON 格式
      body: JSON.stringify({ username, password }), // 发送用户名和密码
    });

    // 如果返回 401，表示用户名或密码错误
    if (res.status === 401) {
      const data = await res.json();
      alert(data.message || "用户名或密码错误！");
      return; // 直接返回，不再往下执行
    }

    // 其它状态码（如 200），解析返回 JSON 数据
    const data = await res.json();
    if (data.success) {
      // 登录成功，跳转到主页面
      console.log(data)
      localStorage.setItem("role", data.role);
      navigate("/staff-landing");
    } else {
      // 登录失败，提示具体信息
      alert(data.message || "登录失败！");
    }
  } catch (err) {
    // 网络或服务器异常
    console.error(err);
    alert("网络或服务器异常，请稍后再试！");
  }
};

const handleSSOLogin = async () => {
  try {
    // 通过 fetch 向后端 Flask 发送 GET 请求，请求 SSO 登录接口
    const res = await fetch("/api/sso-login");
    const data = await res.json(); // 解析后端返回的 JSON 数据

    if (data.success) {
      // SSO 登录成功，跳转到主页面
      navigate("/staff-landing");
    } else {
      // SSO 登录失败，弹窗提示
      alert("SSO 登录失败！");
    }
  } catch (err) {
    // 网络或服务器异常
    console.error(err);
    alert("网络或服务器异常，请稍后再试！");
  }
};

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: "#f7f7fa",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Box
        component={Paper}
        sx={{
          maxWidth: 350,
          width: "100%",
          p: 4,
          mt: { xs: 8, md: 0 },
        }}
      >
        <Typography variant="h5" align="center" gutterBottom>
          Staff Login
        </Typography>
        <form onSubmit={handleSubmit}>
          <TextField
            label="Username"
            variant="outlined"
            fullWidth
            margin="normal"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <TextField
            label="Password"
            type="password"
            variant="outlined"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            sx={{ mt: 2 }}
          >
            Login
          </Button>
        </form>
        <Divider sx={{ my: 2 }}>or</Divider>
        <Button
          variant="outlined"
          color="secondary"
          fullWidth
          onClick={handleSSOLogin}
        >
          Using UNSW SSO
        </Button>
      </Box>
    </Box>
  );
}

export default StaffLogin;
