import React, { useState, useEffect } from "react";
import { AppBar, Toolbar, Button, Box, IconButton, Avatar, Typography, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Switch, FormControlLabel } from "@mui/material";
import { useNavigate, useLocation } from 'react-router-dom';
import { Auth } from "../utils/Auth";

function TopNavBar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [useNewLayout, setUseNewLayout] = useState(false);
  const [profile, setProfile] = useState(null);
  const role = localStorage.getItem("role");
  
  // 控制staff用户是否能看到布局切换按钮
  const SHOW_LAYOUT_SWITCH_TO_STAFF = false;
  // const SHOW_LAYOUT_SWITCH_TO_STAFF = true;

  // 点击 Log out 按钮时弹出 Dialog
  const handleLogoutClick = () => {
    setOpen(true);
  };

  // 确认登出, 因为用的 JWT 登录, 所以不需要后端登出接口, 直接清除 localStorage 即可
  const handleConfirmLogout = () => {
    Auth.clear();
    setOpen(false);
    navigate("/");
  };

  // 取消登出
  const handleCancelLogout = () => {
    setOpen(false);
  };

  // 获取配置
  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/readconfig');
      const config = await response.json();
      setUseNewLayout(config.layout === 'new');
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  };

  // 更新配置
  const updateConfig = async (layout) => {
    try {
      const response = await fetch('/api/updateconfig', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ layout })
      });
      const result = await response.json();
      if (result.success) {
        console.log('Config updated successfully');
      }
    } catch (error) {
      console.error('Failed to update config:', error);
    }
  };

  // 处理布局切换
  const handleLayoutChange = (event) => {
    const newLayout = event.target.checked ? 'new' : 'old';
    setUseNewLayout(event.target.checked);
    updateConfig(newLayout);
  };

  // 判断当前是否在 search 页面
  const isSearchPage = location.pathname === "/search";
  // 判断当前是否在 profile 页面
  const isProfilePage = location.pathname === "/staff-profile";
  // 判断当前是否在 staff-landing 页面
  const isLandingPage = location.pathname === "/staff-landing";

  // 获取用户信息
  const fetchProfile = async () => {
    const token = Auth.getToken();
    if (!token) return;

    try {
      const response = await fetch('http://localhost:8000/api/profile', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setProfile(data.profile);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    }
  };

  // 组件加载时获取配置和用户信息
  useEffect(() => {
    if (role === "admin" || role === "staff") {
      fetchConfig();
      fetchProfile();
    }
  }, [role]);

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
        {/* admin 端显示 Admin Dashboard  以及后续需要的 admin 专属按钮 */}
        {role === "admin" ? (
          <>
            <Typography
              variant="h6"
              component="div"
              sx={{ color: "#222", fontWeight: 600, mr: 2 }}
            >
              Admin Dashboard
            </Typography>
            {/* 更多 admin 专属按钮 */}
            <Box sx={{ flexGrow: 1 }} />
            <FormControlLabel
              control={
                <Switch
                  checked={useNewLayout}
                  onChange={handleLayoutChange}
                  color="primary"
                />
              }
              label={useNewLayout ? "new layout" : "old layout"}
              sx={{ mr: 2 }}
            />
            <Button variant="outlined" sx={{ ml: 1 }} onClick={handleLogoutClick}>Log out</Button>
          </>
        ) : (
          // staff 端的导航栏
          <>
            {/* 标题和中间按钮 */}
            <Typography
              variant="h6"
              component="div"
              sx={{ color: "#222", fontWeight: 600, mr: 2 }}
            >
              {isProfilePage ? "My Profile" : isSearchPage ? "Search" : "Homepage"}
            </Typography>
            <Button variant="outlined" sx={{ mx: 1 }} onClick={() => navigate('/search')}>Search</Button>
            {/* 右侧头像和登出 */}
            <Box sx={{ flexGrow: 1 }} />
            {/* 除了 staff-landing 页面外都显示 Back Home 按钮 */}
            {!isLandingPage && (
              <Button variant="outlined" sx={{ mr: 1 }} onClick={() => navigate('/staff-landing')}>Back Home</Button>
            )}
            {/* 根据配置决定是否显示布局切换按钮 */}
            {SHOW_LAYOUT_SWITCH_TO_STAFF && (
              <FormControlLabel
                control={
                  <Switch
                    checked={useNewLayout}
                    onChange={handleLayoutChange}
                    color="primary"
                  />
                }
                label={useNewLayout ? "new layout" : "old layout"}
                sx={{ mr: 2 }}
              />
            )}
            <IconButton onClick={() => navigate('/staff-profile')}>
              <Avatar sx={{ 
                bgcolor: '#FFD600', 
                color: '#222', 
                fontSize: 16,
                width: 32,
                height: 32
              }}>
                {profile ? profile.firstName[0] : "U"}
              </Avatar>
            </IconButton>
            <Button variant="outlined" sx={{ ml: 1 }} onClick={handleLogoutClick}>Log out</Button>
          </>
        )}
      </Toolbar>
      {/* logout 确认弹窗 */}
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