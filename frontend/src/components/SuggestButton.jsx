import React from "react";
import { Button, Box } from "@mui/material";

const SuggestButton = () => (
  <Box sx={{ position: "fixed", left: 16, bottom: 16, zIndex: 1200 }}>
    <Button variant="contained" color="secondary">
      Suggest an Update
    </Button>
  </Box>
);

export default SuggestButton; 