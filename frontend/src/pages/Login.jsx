import React, { useState } from "react";
import { Button, TextField, Box, Typography, Paper } from "@mui/material";

function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    // 这里可以调用后端API进行登录验证
    alert(`用户名: ${username}\n密码: ${password}`);
  };

  return (
    <Box
      component={Paper}
      elevation={3}
      sx={{ maxWidth: 350, mx: "auto", mt: 10, p: 4 }}
    >
      <Typography variant="h5" align="center" gutterBottom>
        Current staff
      </Typography>
      <form onSubmit={handleSubmit}>
        <TextField
          label="用户名"
          variant="outlined"
          fullWidth
          margin="normal"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <TextField
          label="密码"
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
          Login in as a staff
        </Button>
      </form>
    </Box>
  );
}

export default Login;
