import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  Divider
} from "@mui/material";
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

function HumanHelp() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    description: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // 这里暂时只是模拟提交，后续会对接后端
      console.log("Submit human help request:", formData);
      
      // 模拟网络延迟
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 模拟成功响应
      alert("Your help request has been submitted! We'll get back to you within 24 hours.");
      navigate('/staff-landing');
    } catch {
      setError('Submission failed, please try again later');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: '#f7f7fa', 
      pt: 8,
      px: { xs: 2, sm: 4, md: 6 }
    }}>
      <Box sx={{ maxWidth: 800, mx: 'auto', py: 4 }}>
        {/* Back Button */}
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(-1)}
          sx={{ mb: 3 }}
        >
          Back
        </Button>

        <Paper sx={{ p: { xs: 3, md: 4 } }}>
          <Typography 
            variant="h4" 
            sx={{ 
              mb: 1,
              fontWeight: 'bold',
              color: '#333'
            }}
          >
            Request Human Support
          </Typography>
          
          <Typography 
            variant="body1" 
            sx={{ 
              mb: 4, 
              color: 'text.secondary',
              lineHeight: 1.6
            }}
          >
            Our AI assistant couldn't fully address your question. Don't worry! 
            Our CSE team are here to help. Please describe your question or issue below, 
            and we'll connect you with the right person who can provide the assistance you need.
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Stack spacing={3}>
              
              {/* Issue Description */}
              <Box>
                <Typography variant="h6" sx={{ mb: 2, color: '#333', fontWeight: 'bold' }}>
                  Describe your question or issue
                </Typography>
                
                <Typography 
                  variant="body2" 
                  sx={{ 
                    mb: 2, 
                    color: 'text.secondary',
                    lineHeight: 1.5,
                    p: 2,
                    bgcolor: '#f8f9fa',
                    borderRadius: 1,
                    border: '1px solid #e9ecef'
                  }}
                >
                  <strong>Please provide details about your question or issue, including:</strong><br/>
                  • What specific question or problem do you have?<br/>
                  • What did you ask the AI assistant?<br/>
                  • What response did you receive from the AI?<br/>
                  • What additional help or clarification do you need?<br/><br/>
                  This will help our CSE team understand your situation and provide the most relevant assistance.
                </Typography>
                
                <TextField
                  label="Your question or issue"
                  multiline
                  rows={6}
                  fullWidth
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  required
                  placeholder="Type your question or describe your issue here..."
                />
              </Box>

              {/* Submit Button */}
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={loading || !formData.description.trim()}
                sx={{ 
                  py: 1.5,
                  fontSize: 16,
                  fontWeight: 'bold'
                }}
              >
                {loading ? 'Submitting...' : 'Submit Request'}
              </Button>
            </Stack>
          </form>
        </Paper>
      </Box>
    </Box>
  );
}

export default HumanHelp;
