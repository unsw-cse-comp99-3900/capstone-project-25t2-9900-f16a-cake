import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const RequireNoAuth = ({ children }) => {
  const navigate = useNavigate();
  useEffect(() => {
    const role = localStorage.getItem("role");
    if (role) {
      navigate("/staff-landing", { replace: true });
    }
  }, [navigate]);
  return children;
};

export default RequireNoAuth; 