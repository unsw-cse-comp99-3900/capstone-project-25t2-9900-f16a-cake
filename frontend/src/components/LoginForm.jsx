import React from "react";
import { Box, Typography, TextField, Button, Paper, Divider } from "@mui/material";

function LoginForm({
  title = "Login",
  username,
  password,
  setUsername,
  setPassword,
  onSubmit,
  onSSOLogin,
  usernameLabel = "Username",
  passwordLabel = "Password",
  loginButtonText = "Login",
  ssoButtonText = "Using UNSW SSO"
}) {
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
          {title}
        </Typography>
        <form onSubmit={onSubmit}>
          <TextField
            label={usernameLabel}
            variant="outlined"
            fullWidth
            margin="normal"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <TextField
            label={passwordLabel}
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
            {loginButtonText}
          </Button>
        </form>
        <Divider sx={{ my: 2 }}>or</Divider>
        <Button
          variant="outlined"
          fullWidth
          onClick={onSSOLogin}
          sx={{
            borderColor: '#FFD600',
            color: '#FFD600',
            '&:hover': {
              borderColor: '#FFE44D',
              backgroundColor: 'rgba(255, 214, 0, 0.1)'
            }
          }}
        >
          {ssoButtonText}
        </Button>
      </Box>
    </Box>
  );
}

export default LoginForm; 