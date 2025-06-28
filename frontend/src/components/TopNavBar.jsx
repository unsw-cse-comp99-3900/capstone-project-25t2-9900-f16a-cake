import React from "react";
import { AppBar, Toolbar, Button, Box, IconButton, Avatar, Typography } from "@mui/material";
import { useNavigate } from 'react-router-dom';

function TopNavBar() {
  const navigate = useNavigate();
  return (
    <AppBar
      position="fixed"
      color="default"
      elevation={1}
      sx={{
        backgroundColor: "#fff",
        boxShadow: "0 2px 4px rgba(0,0,0,0.04)",
        px: 0,
      }}
    >
      <Toolbar sx={{ minHeight: 64, px: { xs: 2, sm: 3 } }}>
        {/* 左侧 Logo */}
        <Box
          component="img"
          src="../../assets/unswlogo.png"
          alt="Logo"
          sx={{ height: 40, mr: 2 }}
        />
        {/* 标题和中间按钮 */}
        <Typography
          variant="h6"
          component="div"
          sx={{ color: "#222", fontWeight: 600, mr: 2 }}
        >
          Staff Landing
        </Typography>
        <Button variant="outlined" sx={{ mx: 1 }} onClick={() => navigate('/search')}>Search</Button>
        <Button variant="outlined" sx={{ mx: 1 }}>scenario</Button>
        {/* 右侧头像和登出 */}
        <Box sx={{ flexGrow: 1 }} />
        <IconButton>
          <Avatar />
        </IconButton>
        <Button variant="outlined" sx={{ ml: 1 }}>Log out</Button>
      </Toolbar>
    </AppBar>
  );
}

export default TopNavBar; 