// staff 登录页面
import React, { useEffect } from "react";
import LoginForm from "../components/LoginForm";
import useLogin from "../components/useLogin";
import { Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions, Button } from "@mui/material";

function StaffLogin() {
  useEffect(() => {
    document.title = "Staff Login";
  }, []);

  const {
    username,
    setUsername,
    password,
    setPassword,
    handleSubmit, // general login
    handleSSOLogin, // sso login
    loading, // loading state
    ssoDialogOpen,
    handleCloseSsoDialog
  } = useLogin({
    api: "/api/login",
    successRedirect: "/staff-landing",
    role: "staff"
  });

  return (
    <>
      <LoginForm
        title="Staff Login"
        username={username}
        password={password}
        setUsername={setUsername}
        setPassword={setPassword}
        onSubmit={handleSubmit}
        onSSOLogin={handleSSOLogin}
        usernameLabel="Username"
        passwordLabel="Password"
        loginButtonText={loading ? "Logging in..." : "Login"}
        ssoButtonText="Using UNSW SSO"
      />
      
      {/* sso login dialog */}    
      <Dialog 
        open={ssoDialogOpen} 
        onClose={handleCloseSsoDialog}
        PaperProps={{
          sx: {
            borderRadius: 3,
            minWidth: 340
          }
        }}
      >
        <DialogTitle sx={{ fontWeight: 700, textAlign: 'center', pt: 3 }}>
          SSO Login
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ textAlign: 'center', fontSize: 17, color: '#444', py: 1 }}>
            Sorry, We don't have UNSW authentication for SSO login now.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', pb: 2 }}>
          <Button 
            onClick={handleCloseSsoDialog} 
            variant="contained" 
            sx={{ 
              color: '#fff', 
              fontWeight: 600, 
              boxShadow: 'none',
              bgcolor: '#FFD600',
              '&:hover': {
                bgcolor: '#FFE44D'
              }
            }}
          >
            OK
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default StaffLogin;
