import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Auth } from "../utils/Auth"; // 保持您的 Auth 工具导入
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Divider,
  Avatar,
  Stack,
  ListItemIcon,
  CircularProgress,
  Alert
} from "@mui/material";
import EmailIcon from '@mui/icons-material/Email';
import PhoneIcon from '@mui/icons-material/Phone';
import BusinessIcon from '@mui/icons-material/Business';
import PersonIcon from '@mui/icons-material/Person';
import BadgeIcon from '@mui/icons-material/Badge';

function StaffProfile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  // 您的数据获取和认证逻辑保持不变，因为它很健壮
  useEffect(() => {
    document.title = "My Profile";

    const fetchProfile = async () => {
      const token = Auth.getToken();

      if (!token) {
        setError("您尚未登录，2秒后将跳转到登录页面...");
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
          throw new Error(data.message || '获取个人资料失败，请重新登录。');
        }
        setProfile(data.profile);
      } catch (err) {
        setError(err.message);
        Auth.clear(); // 清理失效的 token
        setTimeout(() => navigate('/staff-login'), 2000);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [navigate]);

  // 采用新的渲染结构，将加载和错误状态置于主内容区
  return (
    <Box sx={{ display: 'flex', minHeight: 'calc(100vh - 64px)', background: '#f7f7fa', pt: { xs: 4, md: 8 } }}>
      {/* 左侧边栏 */}
      <Box sx={{ width: 280, background: '#f9fafb', borderRight: '1px solid #eee', display: { xs: 'none', md: 'flex' }, flexDirection: 'column', alignItems: 'flex-start', pt: 0, pb: 4 }}>
        <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4, borderBottom: '1px solid #eee', mb: 2 }}>
          {/* 安全地渲染头像和姓名，即使 profile 为 null */}
          <Avatar sx={{ width: 56, height: 56, bgcolor: '#FFD600', color: '#222', fontSize: 24, mb: 1 }}>
            {profile ? profile.firstName[0] : "?"}
          </Avatar>
          <Typography sx={{ fontWeight: 700, fontSize: 18 }}>
            {profile ? `${profile.firstName} ${profile.lastName}` : "User"}
          </Typography>
        </Box>
        <List sx={{ width: '100%', mt: 1 }}>
          <ListItem selected sx={{ pl: 4 }}>
            <ListItemText primary={<Typography sx={{ fontWeight: 600, fontSize: 18, color: '#222' }}>User profile</Typography>} />
          </ListItem>
        </List>
        <Box sx={{ flexGrow: 1 }} />
      </Box>

      {/* 右侧主体内容 */}
      <Box sx={{ flex: 1, minHeight: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: { xs: 2, md: 4 } }}>
        {loading ? (
          <CircularProgress />
        ) : error ? (
          <Alert severity="error" sx={{ width: { xs: '90%', sm: 'auto' } }}>{error}</Alert>
        ) : profile && ( // 确保 profile 不为 null 才渲染
          <Paper sx={{ width: '100%', maxWidth: 500, p: { xs: 2, sm: 3 }, borderRadius: 4, boxShadow: 6, background: '#fff', display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: 320 }}>
            <Stack spacing={1.2} alignItems="center" sx={{ width: '100%' }}>
              <Avatar sx={{ width: 64, height: 64, bgcolor: '#FFD600', color: '#222', fontSize: 28 }}>
                {profile.firstName[0]}
              </Avatar>
              <Typography variant="h6" sx={{ fontWeight: 700, fontSize: 20 }}>{profile.firstName} {profile.lastName}</Typography>
              <Typography variant="subtitle2" sx={{ color: 'text.secondary', mb: 0.5, fontSize: 14 }}>
                <BadgeIcon sx={{ mr: 0.5, fontSize: 16, verticalAlign: 'middle' }} />{profile.role}
              </Typography>
            </Stack>
            <Divider sx={{ my: 1.5, width: '100%' }} />
            <List sx={{ width: '100%' }}>
              <ListItem sx={{ py: 0.5 }}>
                <ListItemIcon><PersonIcon color="primary" fontSize="small" /></ListItemIcon>
                <ListItemText primary={<b style={{ fontSize: 14 }}>First name</b>} secondary={<span style={{ fontSize: 14 }}>{profile.firstName}</span>} />
              </ListItem>
              <ListItem sx={{ py: 0.5 }}>
                <ListItemIcon><PersonIcon color="primary" fontSize="small" /></ListItemIcon>
                <ListItemText primary={<b style={{ fontSize: 14 }}>Last name</b>} secondary={<span style={{ fontSize: 14 }}>{profile.lastName}</span>} />
              </ListItem>
              <ListItem sx={{ py: 0.5 }}>
                <ListItemIcon><EmailIcon color="action" fontSize="small" /></ListItemIcon>
                <ListItemText primary={<b style={{ fontSize: 14 }}>Email</b>} secondary={<span style={{ fontSize: 14 }}>{profile.email}</span>} />
              </ListItem>
              <ListItem sx={{ py: 0.5 }}>
                <ListItemIcon><PhoneIcon color="action" fontSize="small" /></ListItemIcon>
                <ListItemText primary={<b style={{ fontSize: 14 }}>Phone</b>} secondary={<span style={{ fontSize: 14 }}>{profile.phone}</span>} />
              </ListItem>
              <ListItem sx={{ py: 0.5 }}>
                <ListItemIcon><BusinessIcon color="action" fontSize="small" /></ListItemIcon>
                <ListItemText primary={<b style={{ fontSize: 14 }}>Department</b>} secondary={<span style={{ fontSize: 14 }}>{profile.department}</span>} />
              </ListItem>
            </List>
          </Paper>
        )}
      </Box>
    </Box>
  );
}

export default StaffProfile;
