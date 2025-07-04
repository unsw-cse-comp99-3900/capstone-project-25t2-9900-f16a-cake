import React, { useEffect } from "react";
import { Box, Paper, Typography, Button, List, ListItem, ListItemText, Divider } from "@mui/material";

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
    <Box sx={{ display: 'flex', height: '100vh', background: '#f7f7fa' }}>
      {/* 左侧边栏 */}
      <Box sx={{ width: 220, background: '#fff', borderRight: '1px solid #eee', display: 'flex', flexDirection: 'column', alignItems: 'stretch', pt: 10 }}>
        <List>
          <ListItem selected>
            <ListItemText primary={<Typography sx={{ fontWeight: 600 }}>User profile</Typography>} />
          </ListItem>
          {/* 预留：后续可加更多菜单项 */}
        </List>
        <Box sx={{ flexGrow: 1 }} />
      </Box>

      {/* 右侧主体内容 */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', pt: 10 }}>
        <Paper sx={{ width: 500, p: 3, borderRadius: 2, boxShadow: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 700, mb: 2, background: '#FFD600', p: 1, borderRadius: 1 }}>HI, {mockProfile.firstName} {mockProfile.lastName}</Typography>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>User profile</Typography>
          <Box component="table" sx={{ width: '100%' }}>
            <tbody>
              <tr><td><b>first name:</b></td><td>{mockProfile.firstName}</td></tr>
              <tr><td><b>last name:</b></td><td>{mockProfile.lastName}</td></tr>
              <tr><td><b>email address:</b></td><td>{mockProfile.email}</td></tr>
              <tr><td><b>phone:</b></td><td>{mockProfile.phone}</td></tr>
              <tr><td><b>department:</b></td><td>{mockProfile.department}</td></tr>
              <tr><td><b>role:</b></td><td>{mockProfile.role}</td></tr>
            </tbody>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
}

export default StaffProfile; 