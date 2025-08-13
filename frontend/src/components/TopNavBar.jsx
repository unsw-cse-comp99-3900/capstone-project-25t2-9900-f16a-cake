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
  
  // Control whether staff users can see the layout switch button
  const SHOW_LAYOUT_SWITCH_TO_STAFF = false;
  // const SHOW_LAYOUT_SWITCH_TO_STAFF = true;

  // Show Dialog when Log out button is clicked
  const handleLogoutClick = () => {
    setOpen(true);
  };

  // Confirm logout, since using JWT login, no backend logout API needed, just clear localStorage
  const handleConfirmLogout = () => {
    Auth.clear();
    setOpen(false);
    navigate("/");
  };

  // Cancel logout
  const handleCancelLogout = () => {
    setOpen(false);
  };

  // Fetch configuration
  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/readconfig');
      const config = await response.json();
      setUseNewLayout(config.layout === 'new');
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  };

  // Update configuration
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

  // Handle layout change
  const handleLayoutChange = (event) => {
    const newLayout = event.target.checked ? 'new' : 'old';
    setUseNewLayout(event.target.checked);
    updateConfig(newLayout);
  };

  // Determine current page
  const isSearchPage = location.pathname === "/search";
  const isProfilePage = location.pathname === "/staff-profile";
  const isLandingPage = location.pathname === "/staff-landing";
  const isFeedbackPage = location.pathname === "/feedback";
  const isHumanHelpPage = location.pathname === "/human-help";

  // Fetch user profile
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

  // Fetch configuration and user profile when component loads
  useEffect(() => {
    if (role === "admin" || role === "staff") {
      fetchConfig();
      fetchProfile();
    }
  }, [role]);

  // Update browser tab title based on current page
  useEffect(() => {
    if (role === "admin") {
      document.title = "Admin Dashboard";
    } else if (role === "staff") {
      if (isProfilePage) {
        document.title = "My Profile";
      } else if (isSearchPage) {
        document.title = "Search";
      } else if (isFeedbackPage) {
        document.title = "Feedback";
      } else if (isHumanHelpPage) {
        document.title = "Human Help";
      } else if (isLandingPage) {
        document.title = "Homepage";
      } else {
        document.title = "HDingo";
      }
    }
  }, [role, isProfilePage, isSearchPage, isFeedbackPage, isHumanHelpPage, isLandingPage]);

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
        {/* Left Logo */}
        <Box
          component="img"
          src="../../assets/unswlogo.png"
          alt="Logo"
          sx={{ height: 40, mr: 2 }}
        />
        {role === "admin" ? (
          <>
            <Typography
              variant="h6"
              component="div"
              sx={{ color: "#222", fontWeight: 600, mr: 2 }}
            >
              Admin Dashboard
            </Typography>
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
          <>
            <Typography
              variant="h6"
              component="div"
              sx={{ color: "#222", fontWeight: 600, mr: 2 }}
            >
              {isProfilePage ? "My Profile" : isSearchPage ? "Search" : isFeedbackPage ? "Feedback" : isHumanHelpPage ? "Human Help" : "Homepage"}
            </Typography>
            <Button variant="outlined" sx={{ mx: 1 }} onClick={() => navigate('/search')}>Search</Button>
            {/* Right avatar and logout */}
            <Box sx={{ flexGrow: 1 }} />
            {/* Show Back Home button on all pages except staff-landing */}
            {!isLandingPage && (
              <Button variant="outlined" sx={{ mr: 1 }} onClick={() => navigate('/staff-landing')}>Back Home</Button>
            )}
            {/* Show layout switch button based on configuration */}
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
      {/* Logout confirmation dialog */}
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