import React, { useState, useEffect } from "react";
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
import RequireAdmin from "./components/RequireAdmin";
import RequireStaff from "./components/RequireStaff";
import Feedback from "./pages/Feedback";
import HumanHelp from "./pages/HumanHelp";

function AppContent() {
  const location = useLocation();
  const showTopBar = ["/", "/staff-login", "/admin-login"].includes(location.pathname);
  const isLoggedIn = !!localStorage.getItem("role");
  const isStaff = localStorage.getItem("role") === "staff";
  const [layout, setLayout] = useState("old");

  // Fetch layout configuration
  useEffect(() => {
    const fetchLayoutConfig = async () => {
      try {
        const response = await fetch('/api/readconfig');
        const config = await response.json();
        setLayout(config.layout);
      } catch (error) {
        console.error('Failed to fetch layout config:', error);
      }
    };

    if (isLoggedIn && isStaff) {
      fetchLayoutConfig();
    }
  }, [isLoggedIn, isStaff]);

  // Determine whether AIchat should be displayed
  const shouldShowAIchat = isLoggedIn && !(isStaff && location.pathname === "/staff-landing" && layout === "new") && !(location.pathname === "/admin-landing");

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {showTopBar ? <TopBar /> : <TopNavBar />}
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <Routes>
          {/* Accessible without login */}
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

          {/* Requires login to access */}
          <Route path="/staff-landing" element={
            <RequireAuth>
              <RequireStaff>
                <LandingPage />
              </RequireStaff>
            </RequireAuth>
          } />
          <Route path="/search" element={
            <RequireAuth>
              <RequireStaff>
                <SearchPage />
              </RequireStaff>
            </RequireAuth>
          } />
          <Route path="/staff-profile" element={
            <RequireAuth>
              <RequireStaff>
                <StaffProfile />
              </RequireStaff>
            </RequireAuth>
          } />
          <Route path="/admin-landing" element={
            <RequireAuth>
              <RequireAdmin>
                <AdminLanding />
              </RequireAdmin>
            </RequireAuth>
          } />
          <Route path="/feedback" element={
            <RequireAuth>
              <RequireStaff>
                <Feedback />
              </RequireStaff>
            </RequireAuth>
          } />
          <Route path="/human-help" element={<HumanHelp />} />
        </Routes>
      </Box>
      
      {/* Only show feedback on staff side */}
      {isStaff && <SuggestButton />}
      
      {shouldShowAIchat && <AIchat />}
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
