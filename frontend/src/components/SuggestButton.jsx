import React from "react";
import { Button, Box } from "@mui/material";
import { useNavigate } from "react-router-dom";

const SuggestButton = () => {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/feedback');
  };

  return (
    <Box sx={{ position: "fixed", left: 16, bottom: 16, zIndex: 1200 }}>
      <Button 
        variant="contained" 
        color="secondary"
        onClick={handleClick}
      >
        Suggest an Update
      </Button>
    </Box>
  );
};

export default SuggestButton; 