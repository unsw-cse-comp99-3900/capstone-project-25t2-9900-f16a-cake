import React from "react";
import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import { Box } from "@mui/material";
import TopBar from "./components/TopBar";
import TopNavBar from "./components/TopNavBar";
import AIchat from "./components/AIchat";
import Entry from "./pages/Entry";
import StaffLogin from "./pages/StaffLogin";
import AdminLogin from "./pages/AdminLogin";
import LandingPage from "./pages/LandingPage";
import SearchPage from "./pages/SearchPage";
import RequireNoAuth from "./components/RequireNoAuth";
import RequireAuth from "./components/RequireAuth";
import StaffProfile from "./pages/StaffProfile";
import SuggestButton from "./components/SuggestButton";
import AdminLanding from "./pages/AdminLanding";

function AppContent() {
  const location = useLocation();
  const showTopBar = ["/", "/staff-login", "/admin-login"].includes(location.pathname);
  const isLoggedIn = !!localStorage.getItem("role");

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {showTopBar ? <TopBar /> : <TopNavBar />}
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <Routes>
          {/* 未登录可访问 */}
          <Route path="/" element={
            <RequireNoAuth>
              <Entry />
            </RequireNoAuth>
          } />
          <Route path="/staff-login" element={
            <RequireNoAuth>
              <StaffLogin />
            </RequireNoAuth>
          } />
          <Route path="/admin-login" element={
            <RequireNoAuth>
              <AdminLogin />
            </RequireNoAuth>
          } />

          {/* 需要登录才能访问 */}
          <Route path="/staff-landing" element={
            <RequireAuth>
              <LandingPage />
            </RequireAuth>
          } />
          <Route path="/search" element={
            <RequireAuth>
              <SearchPage />
            </RequireAuth>
          } />
          <Route path="/staff-profile" element={
            <RequireAuth>
              <StaffProfile />
            </RequireAuth>
          } />
          <Route path="/admin-landing" element={
            <RequireAuth>
              <AdminLanding />
            </RequireAuth>
          } />
        </Routes>
      </Box>
      
      {isLoggedIn && <SuggestButton />}
      {isLoggedIn && <AIchat />}
    </Box>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
