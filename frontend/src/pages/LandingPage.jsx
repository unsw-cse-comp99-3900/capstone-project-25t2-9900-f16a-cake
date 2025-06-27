import React from "react";
import { Box, Typography, Paper, Button } from "@mui/material";

function LandingPage() {
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
          <Typography variant="h6" gutterBottom>greeting!</Typography>
          <Typography variant="body1">description of how to use this web site.</Typography>
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