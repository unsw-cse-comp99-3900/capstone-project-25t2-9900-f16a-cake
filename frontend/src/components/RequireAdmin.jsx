import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const RequireAdmin = ({ children }) => {
  const navigate = useNavigate();
  useEffect(() => {
    const role = localStorage.getItem("role");
    if (role !== "admin") {
      navigate("/staff-landing", { replace: true });
    }
  }, [navigate]);
  return children;
};

export default RequireAdmin; 