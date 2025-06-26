import React from "react";
import { useEffect, useState } from 'react';
import { AppBar, Toolbar, Typography, Box } from "@mui/material";

function TopBar() {
  const [message, setMessage] = useState('');
  // api call 的例子, 和后端交换信息
  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/hello')
      .then(res => res.json())
      .then(data => setMessage(data.message));
  }, []);
  
  return (
    <AppBar
      position="fixed"
      color="default"
      elevation={1}
      sx={{
        backgroundColor: "#fff",
        boxShadow: "0 2px 4px rgba(0,0,0,0.04)",
        px: 0, // 去除左右 padding
      }}
    >
      <Toolbar sx={{ minHeight: 64, px: { xs: 2, sm: 3 } }}>
        {/* 左侧 Logo */}
        <Box
          component="img"
          src="../../assets/unswlogo.png" // 这里换成你的 logo 路径
          alt="Logo"
          sx={{ height: 40, mr: 2 }}
        />
        {/* 网站标题 */}
        <Typography
          variant="h6"
          component="div"
          sx={{ flexGrow: 1, color: "#222", fontWeight: 600 }}
        >
          CSE New Joiners Onboarding Hub - {message}
        </Typography>
      </Toolbar>
    </AppBar>
  );
}

export default TopBar;
