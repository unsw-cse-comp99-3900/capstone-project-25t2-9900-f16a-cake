import React from "react";
// import { useEffect, useState } from 'react';
import { AppBar, Toolbar, Typography, Box } from "@mui/material";

function TopBar() {
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
        {/* Left Logo */}
        <Box
          component="img"
          src="../../assets/unswlogo.png"
          alt="Logo"
          sx={{ height: 40, mr: 2 }}
        />
        {/* Website Title */}
        <Typography
          variant="h6"
          component="div"
          sx={{ flexGrow: 1, color: "#222", fontWeight: 600 }}
        >
          CSE New Joiners Onboarding Hub
        </Typography>
      </Toolbar>
    </AppBar>
  );
}

export default TopBar;
