import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
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
import { Auth } from "../utils/Auth";

function HumanHelp() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // 从 URL 参数或路由状态中获取 session_id
  const searchParams = new URLSearchParams(location.search);
  const sessionId = searchParams.get('session_id') || location.state?.session_id || 'human-help-' + Date.now();
  
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
      const token = Auth.getToken();
      if (!token) {
        setError('Please log in to submit a help request');
        return;
      }

      const response = await fetch('/api/save_ticket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          session_id: sessionId,
          content: formData.description
        })
      });

      const data = await response.json();

      if (data.success) {
        // 设置localStorage标记，表示需要显示成功popup
        localStorage.setItem('showHumanHelpSuccess', 'true');
        // 跳转到staff-landing页面
        navigate('/staff-landing');
      } else {
        setError(data.message || 'Failed to submit help request, please try again later');
      }
    } catch (error) {
      console.error('Error submitting help request:', error);
      setError('Network error, please try again later');
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
          onClick={() => navigate('/staff-landing')}
          sx={{ mb: 3 }}
        >
          Back to Chat
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
