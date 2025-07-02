import React, { useEffect, useState } from "react";
import { Box, Typography, Paper, Button } from "@mui/material";

function LandingPage() {
  const [role, setRole] = useState("");

  useEffect(() => {
    const storedRole = localStorage.getItem("role");
    setRole(storedRole || "");
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
        height: "100vh",
        background: "#f7f7fa",
        position: "relative",
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
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

      {/* 左下角 Suggest an Update 按钮 */}
      <Box sx={{ position: "fixed", left: 16, bottom: 16 }}>
        <Button variant="contained" color="secondary">Suggest an Update</Button>
      </Box>
    </Box>
  );
}

export default LandingPage; 