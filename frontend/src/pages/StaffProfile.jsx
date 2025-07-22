import React, { useEffect } from "react";
import { Box, Paper, Typography, Button, List, ListItem, ListItemText, Divider, Avatar, Grid, Stack, ListItemIcon } from "@mui/material";
import EmailIcon from '@mui/icons-material/Email';
import PhoneIcon from '@mui/icons-material/Phone';
import BusinessIcon from '@mui/icons-material/Business';
import PersonIcon from '@mui/icons-material/Person';
import BadgeIcon from '@mui/icons-material/Badge';

const mockProfile = {
  firstName: "Jiaxin",
  lastName: "Weng",
  email: "z5570225@ad.unsw.edu.au",
  phone: "0413962xxx",
  department: "CSE",
  role: "PhD"
};

function StaffProfile() {
  useEffect(() => {
    document.title = "My Profile";
  }, []);

  return (
    <Box sx={{ display: 'flex', minHeight: 'calc(100vh - 64px)', background: '#f7f7fa', pt: 8 }}>
      {/* 左侧边栏 */}
      <Box sx={{ width: 280, background: '#f9fafb', borderRight: '1px solid #eee', display: { xs: 'none', md: 'flex' }, flexDirection: 'column', alignItems: 'flex-start', pt: 0, pb: 4 }}>
        <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4, borderBottom: '1px solid #eee', mb: 2 }}>
          <Avatar sx={{ width: 56, height: 56, bgcolor: '#FFD600', color: '#222', fontSize: 24, mb: 1 }}>{mockProfile.firstName[0]}</Avatar>
          <Typography sx={{ fontWeight: 700, fontSize: 18 }}>{mockProfile.firstName} {mockProfile.lastName}</Typography>
        </Box>
        <List sx={{ width: '100%', mt: 1 }}>
          <ListItem selected sx={{ pl: 4 }}>
            <ListItemText primary={<Typography sx={{ fontWeight: 600, fontSize: 18, color: '#222' }}>User profile</Typography>} />
          </ListItem>
        </List>
        <Box sx={{ flexGrow: 1 }} />
      </Box>

      {/* 右侧主体内容 */}
      <Box sx={{ flex: 1, minHeight: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 0, pl: { xs: 0, md: 8 }, pr: { xs: 0, md: 4 }, pt: 0 }}>
        <Paper sx={{ width: { xs: '100%', sm: '90vw', md: 500 }, maxWidth: 500, p: { xs: 1, sm: 2 }, borderRadius: 4, boxShadow: 6, background: '#fff', display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: 320 }}>
          <Stack spacing={1.2} alignItems="center" sx={{ width: '100%' }}>
            <Avatar sx={{ width: 64, height: 64, bgcolor: '#FFD600', color: '#222', fontSize: 28 }}>
              {mockProfile.firstName[0]}
            </Avatar>
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: 20 }}>{mockProfile.firstName} {mockProfile.lastName}</Typography>
            <Typography variant="subtitle2" sx={{ color: 'text.secondary', mb: 0.5, fontSize: 14 }}><BadgeIcon sx={{ mr: 0.5, fontSize: 16, verticalAlign: 'middle' }} />{mockProfile.role}</Typography>
          </Stack>
          <Divider sx={{ my: 1.5, width: '100%' }} />
          <List sx={{ width: '100%' }}>
            <ListItem sx={{ py: 0.5 }}>
              <ListItemIcon><PersonIcon color="primary" fontSize="small" /></ListItemIcon>
              <ListItemText primary={<b style={{ fontSize: 14 }}>First name</b>} secondary={<span style={{ fontSize: 14 }}>{mockProfile.firstName}</span>} />
            </ListItem>
            <ListItem sx={{ py: 0.5 }}>
              <ListItemIcon><PersonIcon color="primary" fontSize="small" /></ListItemIcon>
              <ListItemText primary={<b style={{ fontSize: 14 }}>Last name</b>} secondary={<span style={{ fontSize: 14 }}>{mockProfile.lastName}</span>} />
            </ListItem>
            <ListItem sx={{ py: 0.5 }}>
              <ListItemIcon><EmailIcon color="action" fontSize="small" /></ListItemIcon>
              <ListItemText primary={<b style={{ fontSize: 14 }}>Email</b>} secondary={<span style={{ fontSize: 14 }}>{mockProfile.email}</span>} />
            </ListItem>
            <ListItem sx={{ py: 0.5 }}>
              <ListItemIcon><PhoneIcon color="action" fontSize="small" /></ListItemIcon>
              <ListItemText primary={<b style={{ fontSize: 14 }}>Phone</b>} secondary={<span style={{ fontSize: 14 }}>{mockProfile.phone}</span>} />
            </ListItem>
            <ListItem sx={{ py: 0.5 }}>
              <ListItemIcon><BusinessIcon color="action" fontSize="small" /></ListItemIcon>
              <ListItemText primary={<b style={{ fontSize: 14 }}>Department</b>} secondary={<span style={{ fontSize: 14 }}>{mockProfile.department}</span>} />
            </ListItem>
          </List>
          <Divider sx={{ my: 1, width: '100%' }} />
        </Paper>
      </Box>
    </Box>
  );
}

export default StaffProfile; 