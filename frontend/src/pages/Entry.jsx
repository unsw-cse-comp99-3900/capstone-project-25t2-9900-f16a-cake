import React from "react";
import { Button, Box, Typography, Paper } from "@mui/material";
import { useNavigate } from "react-router-dom";

const NAVBAR_HEIGHT = 64; // TopBar高度

function Entry() {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        width: "100vw",
        height: "100vh",
        display: "flex",
        background: "#f7f7fa",
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      {/* 左侧登录容器 */}
      <Box
        sx={{
          width: { xs: "100%", md: "40%" },
          minWidth: 280,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          px: { xs: 2, md: 4 },
          py: 4,
          gap: 3,
          background: "#fff",
          height: "100%",
          paddingTop: { xs: `${NAVBAR_HEIGHT}px`, md: 0 },
        }}
      >
        <Paper
          elevation={2}
          sx={{
            p: 3,
            width: "100%",
            maxWidth: 400,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" gutterBottom>
            Current Staff
          </Typography>
          <Button
            variant="contained"
            fullWidth
            sx={{
              maxWidth: 300,
              mt: 1,
              backgroundColor: "#000",
              color: "#fff",
              "&:hover": { backgroundColor: "#222" },
            }}
            onClick={() => navigate("/staff-login")}
          >
            Login as a staff
          </Button>
        </Paper>
        <Paper
          elevation={2}
          sx={{
            p: 3,
            width: "100%",
            maxWidth: 400,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" gutterBottom>
            Administrator
          </Typography>
          <Button
            variant="contained"
            fullWidth
            sx={{
              maxWidth: 300,
              mt: 1,
              backgroundColor: "#000",
              color: "#fff",
              "&:hover": { backgroundColor: "#222" },
            }}
            onClick={() => navigate("/admin-login")}
          >
            Login as admin
          </Button>
        </Paper>
      </Box>
      {/* 右侧背景图容器 */}
      <Box
        sx={{
          display: { xs: "none", md: "block" },
          width: "60%",
          height: "100%",
          backgroundImage: "url(/cseimage.jpg)", // 建议放 public 目录，路径写 /cseimage.jpg
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
    </Box>
  );
}

export default Entry;
