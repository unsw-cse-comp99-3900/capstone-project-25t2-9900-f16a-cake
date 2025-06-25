import React, { useState } from "react";
import { Box, Typography, TextField, Button, Paper, Divider } from "@mui/material";

function StaffLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    // 这里可以调用后端API进行登录验证
    alert(`Staff 用户名: ${username}\n密码: ${password}`);
  };

  const handleSSOLogin = () => {
    // 这里写 SSO 登录逻辑，比如跳转到 SSO 登录页
    alert("跳转到 SSO 登录");
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
