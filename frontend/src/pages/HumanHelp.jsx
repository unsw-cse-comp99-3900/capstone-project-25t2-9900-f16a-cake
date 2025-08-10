import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  Divider,
  Dialog,
  DialogContent
} from "@mui/material";
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { Auth } from "../utils/Auth";

function HumanHelp() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const searchParams = new URLSearchParams(location.search);
  const sessionId = searchParams.get('session_id') || location.state?.session_id || 'human-help-' + Date.now();
  
  const [formData, setFormData] = useState({
    description: ""
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [countdown, setCountdown] = useState(5);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  useEffect(() => {
    let timer;
    if (showSuccessDialog && countdown > 0) {
      timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
    } else if (showSuccessDialog && countdown === 0) {
      navigate('/staff-landing');
    }
    return () => clearTimeout(timer);
  }, [showSuccessDialog, countdown, navigate]);

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
        setShowSuccessDialog(true);
        setCountdown(5);
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

  const handleImmediateRedirect = () => {
    navigate('/staff-landing');
  };

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: '#f7f7fa', 
      pt: 8,
      px: { xs: 2, sm: 4, md: 6 }
    }}>
      <Box sx={{ maxWidth: 800, mx: 'auto', py: 4 }}>
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
            Our AI assistant couldn't fully address your question? <br/>
            Don't worry! Our CSE team are here to help. <br/>
            Please describe your question or issue below, and we'll connect you later!
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Stack spacing={3}>
              
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
                  • What question do you have?<br/>
                  • What did you ask the AI assistant?<br/>
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

      <Dialog
        open={showSuccessDialog}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 3,
            p: 1,
            background: '#ffffff',
            boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
          }
        }}
      >
        <DialogContent sx={{ textAlign: 'center', py: 4 }}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h2" sx={{ color: '#4CAF50', fontWeight: 'bold', mb: 2, fontSize: '3rem' }}>
              {countdown}
            </Typography>
            <Typography variant="h4" sx={{ color: '#4CAF50', fontWeight: 'bold', mb: 1 }}>
              Successfully Submitted!
            </Typography>
            <Typography variant="body1" sx={{ color: '#4CAF50', mb: 3, fontSize: '1.1rem' }}>
              Your help request has been sent to our team!
            </Typography>
          </Box>
          
          <Button
            variant="contained"
            size="large"
            onClick={handleImmediateRedirect}
            sx={{
              bgcolor: '#FFD600',
              color: '#ffffff',
              fontWeight: 'bold',
              px: 4,
              py: 1.5,
              fontSize: '1rem',
              borderRadius: 2,
              textTransform: 'none',
              '&:hover': {
                bgcolor: '#FFE44D'
              }
            }}
          >
            Return to Homepage Now
          </Button>
        </DialogContent>
      </Dialog>
    </Box>
  );
}

export default HumanHelp;
