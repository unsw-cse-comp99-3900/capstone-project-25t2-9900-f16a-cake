import React, { useEffect, useState } from "react";
import { Box, Typography, Paper, Snackbar } from "@mui/material";

function StaffLandingOld() {
  const [subrole, setSubrole] = useState("");

  useEffect(() => {
    const storedRole = localStorage.getItem("subrole");
    setSubrole(storedRole || "");
    document.title = "Homepage";
  }, []);

  // show different content based on role
  let greeting = "Welcome to the staff homepage!";
  let description = "This is the onboarding system for new staff.";
  if (subrole === "PhD Student") {
    greeting = "Welcome, PhD!";
    description = "You can find the onboarding guide for new PhD staff here and chat with our AI bot for any questions!";
  } else if (subrole === "Tutor") {
    greeting = "Welcome, Tutor!";
    description = "You can find the onboarding guide for new tutors here and chat with our AI bot for any questions!";
  } else if (subrole === "Lecturer") {
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