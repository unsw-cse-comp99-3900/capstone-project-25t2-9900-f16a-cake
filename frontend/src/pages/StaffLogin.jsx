import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Box, Typography, TextField, Button, Paper, Divider } from "@mui/material";

function StaffLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    // 这里可以调用后端API进行登录验证
    // 暂时模拟登录成功
    if (username && password) {
      alert(`Staff 登录成功！\n用户名: ${username}`);
      // 登录成功后跳转到LandingPage
      navigate("/staff-landing");
    } else {
      alert("请输入用户名和密码");
    }
  };

  const handleSSOLogin = () => {
    // 这里写 SSO 登录逻辑，比如跳转到 SSO 登录页
    alert("跳转到 SSO 登录");
    // SSO登录成功后也可以跳转到LandingPage
    // navigate("/staff-landing");
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
