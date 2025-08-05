import React, { useEffect, useState } from "react";
import { Box, Typography, Paper, Snackbar } from "@mui/material";

function StaffLandingOld() {
  const [role, setRole] = useState("");
  const [showSuccessPopup, setShowSuccessPopup] = useState(false);

  useEffect(() => {
    const storedRole = localStorage.getItem("role");
    setRole(storedRole || "");
    document.title = "Homepage";
    
    // 检查是否需要显示成功popup（仅针对 human help）
    const shouldShowSuccess = localStorage.getItem('showHumanHelpSuccess');
    if (shouldShowSuccess === 'true') {
      setShowSuccessPopup(true);
      localStorage.removeItem('showHumanHelpSuccess'); // 清除标记
    }
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
      
      {/* 成功提示Popup */}
      <Snackbar
        open={showSuccessPopup}
        autoHideDuration={5000}
        onClose={() => setShowSuccessPopup(false)}
        message="Your human help request has been submitted successfully! We'll get back to you soon."
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        sx={{
          '& .MuiSnackbarContent-root': {
            backgroundColor: '#4caf50',
            color: 'white',
            fontWeight: 'bold'
          }
        }}
      />
    </Box>
  );
}

export default StaffLandingOld; 