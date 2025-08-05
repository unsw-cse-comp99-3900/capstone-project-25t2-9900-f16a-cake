import React, { useEffect, useState } from "react";
import { Box, Typography, Paper, Snackbar } from "@mui/material";

function StaffLandingOld() {
  const [role, setRole] = useState("");

  useEffect(() => {
    const storedRole = localStorage.getItem("role");
    setRole(storedRole || "");
    document.title = "Homepage";
    
    // 移除 human help 成功提示逻辑，因为现在直接在 HumanHelp 页面处理
  }, []);

  // 根据不同角色显示不同内容
  let greeting = "Welcome to the staff homepage!";
  let description = "This is the onboarding system for new staff.";
  if (role === "phd") {
    greeting = "Welcome, PhD!";
    description = "You can find the onboarding guide for new PhD staff here and chat with our AI bot for any questions!";
  } else if (role === "tutor") {
    greeting = "Welcome, Tutor!";
    description = "You can find the onboarding guide for new tutors here and chat with our AI bot for any questions!";
  } else if (role === "lecturer") {
    greeting = "Welcome, Lecturer!";
    description = "You can find the onboarding guide for new lecturers here and chat with our AI bot for any questions!";
  }
  let search_info = "You can search for the information you need by clicking the search button in nva bar, we will provide you with the most relevant PDF files.";

  return (
    <Box
      sx={{
        width: "100%",
        height: "calc(100vh - 64px)",
        background: "#f7f7fa",
        position: "relative",
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        mt: "64px",
      }}
    >
      {/* 主体内容 */}
      <Box sx={{ mb: 8 }}>
        <Paper sx={{ p: 3, minHeight: 300, maxWidth: 600 }}>
          <Typography variant="h6" gutterBottom>{greeting}</Typography>
          <Typography variant="body1">{description}</Typography>
          <br />
          <Typography variant="body1">{search_info}</Typography>
        </Paper>
      </Box>
      

    </Box>
  );
}

export default StaffLandingOld; 