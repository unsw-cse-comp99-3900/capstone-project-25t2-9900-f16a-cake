import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
// 1. 导入您的 Auth 工具
import { Auth } from "../utils/Auth";
import { Box, Paper, Typography, List, ListItem, ListItemText, Divider, CircularProgress } from "@mui/material";

function StaffProfile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "My Profile";

    const fetchProfile = async () => {
      // 2. 使用 Auth.getToken() 来获取 token，确保键名一致
      const token = Auth.getToken();

      if (!token) {
        setError("您尚未登录，将跳转到登录页面...");
        setTimeout(() => navigate('/staff-login'), 2000); 
        setLoading(false);
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/profile', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
          throw new Error(data.message || '获取个人资料失败。');
        }
        setProfile(data.profile); 
      } catch (err) {
        setError(err.message);
        // 如果 token 失效，使用 Auth.clear() 清理所有相关信息
        Auth.clear();
        setTimeout(() => navigate('/staff-login'), 2000);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [navigate]);

  if (loading) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><CircularProgress /></Box>;
  }
  if (error) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><Typography color="error">{error}</Typography></Box>;
  }
  if (!profile) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}><Typography>未能加载个人资料。</Typography></Box>;
  }

  // 渲染逻辑保持不变
  return (
    <Box sx={{ display: 'flex', height: '100vh', background: '#f7f7fa' }}>
      <Box sx={{ width: 220, background: '#fff', borderRight: '1px solid #eee', display: 'flex', flexDirection: 'column', alignItems: 'stretch', pt: 10 }}>
        <List>
          <ListItem selected>
            <ListItemText primary={<Typography sx={{ fontWeight: 600 }}>User profile</Typography>} />
          </ListItem>
        </List>
        <Box sx={{ flexGrow: 1 }} />
      </Box>
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', pt: 10 }}>
        <Paper sx={{ width: 500, p: 3, borderRadius: 2, boxShadow: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, background: '#FFD600', p: 1, borderRadius: 1 }}>HI, {profile.firstName} {profile.lastName}</Typography>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>User profile</Typography>
          <Box component="table" sx={{ width: '100%' }}>
            <tbody>
              <tr><td><b>first name:</b></td><td>{profile.firstName}</td></tr>
              <tr><td><b>last name:</b></td><td>{profile.lastName}</td></tr>
              <tr><td><b>email address:</b></td><td>{profile.email}</td></tr>
              <tr><td><b>phone:</b></td><td>{profile.phone}</td></tr>
              <tr><td><b>department:</b></td><td>{profile.department}</td></tr>
              <tr><td><b>role:</b></td><td>{profile.role}</td></tr>
            </tbody>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
}

export default StaffProfile;
