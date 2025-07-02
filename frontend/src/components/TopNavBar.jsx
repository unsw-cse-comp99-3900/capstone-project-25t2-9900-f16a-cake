import React, { useState } from "react";
import { AppBar, Toolbar, Button, Box, IconButton, Avatar, Typography, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions } from "@mui/material";
import { useNavigate } from 'react-router-dom';

function TopNavBar() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  // 点击 Log out 按钮时弹出 Dialog
  const handleLogoutClick = () => {
    setOpen(true);
  };

  // 确认登出
  const handleConfirmLogout = () => {
    localStorage.removeItem("role");
    setOpen(false);
    navigate("/");
  };

  // 取消登出
  const handleCancelLogout = () => {
    setOpen(false);
  };

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
        <Button variant="outlined" sx={{ ml: 1 }} onClick={handleLogoutClick}>Log out</Button>
      </Toolbar>
      {/* 登出确认弹窗 */}
      <Dialog open={open} onClose={handleCancelLogout} PaperProps={{ sx: { borderRadius: 3, minWidth: 340 } }}>
        <DialogTitle sx={{ fontWeight: 700, textAlign: 'center', pt: 3 }}>Confirm Logout</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ textAlign: 'center', fontSize: 17, color: '#444', py: 1 }}>
            Are you sure you want to log out?
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', pb: 2 }}>
          <Button onClick={handleCancelLogout} variant="outlined" sx={{ color: '#666', borderColor: '#ccc', background: '#f5f5f5', '&:hover': { background: '#eee', borderColor: '#bbb' } }}>
            Cancel
          </Button>
          <Button onClick={handleConfirmLogout} variant="contained" color="error" sx={{ color: '#fff', fontWeight: 600, boxShadow: 'none' }} autoFocus>
            Log out
          </Button>
        </DialogActions>
      </Dialog>
    </AppBar>
  );
}

export default TopNavBar; 