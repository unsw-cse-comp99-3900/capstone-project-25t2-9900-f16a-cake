import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const RequireStaff = ({ children }) => {
  const navigate = useNavigate();
  useEffect(() => {
    const role = localStorage.getItem("role");
    if (role !== "staff") {
      navigate("/admin-landing", { replace: true });
    }
  }, [navigate]);
  return children;
};

export default RequireStaff; 