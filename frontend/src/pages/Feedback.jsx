import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Stack,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Rating,
  Dialog,
  DialogContent
} from "@mui/material";
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { Auth } from "../utils/Auth";

function Feedback() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    category: "",
    subject: "",
    description: "",
    rating: 0
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
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (data.success) {
        setShowSuccessDialog(true);
        setCountdown(5);
      } else {
        setError(data.message || 'Submission failed, please try again');
      }
    } catch (err) {
      console.log('Error submitting feedback:', err);
      setError('Network issue, please check your connection and try again');
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
        {/* Back button */}
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
            sx={{ mb: 1, fontWeight: 'bold', color: '#333' }}
          >
            Feedback & Suggestions
          </Typography>
          
          <Typography 
            variant="body1" 
            sx={{ mb: 4, color: 'text.secondary', lineHeight: 1.6 }}
          >
            Help us improve HDingo by sharing your feedback, suggestions, or reporting issues. 
            Your input is valuable to us!
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Stack spacing={3}>

              {/* Category selection */}
              <FormControl fullWidth required>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  label="Category"
                  onChange={(e) => handleInputChange('category', e.target.value)}
                >
                  <MenuItem value="bug">Bug Report</MenuItem>
                  <MenuItem value="feature">Feature Request</MenuItem>
                  <MenuItem value="improvement">Improvement Suggestion</MenuItem>
                  <MenuItem value="content">Content Update</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>

              {/* Subject */}
              <TextField
                label="Subject"
                fullWidth
                value={formData.subject}
                onChange={(e) => handleInputChange('subject', e.target.value)}
                required
                placeholder="Brief description of your feedback"
              />

              {/* Rating */}
              <Box>
                <Typography component="legend" sx={{ mb: 1 }}>
                  How would you rate your experience with HDingo?
                </Typography>
                <Rating
                  value={formData.rating}
                  onChange={(event, newValue) => {
                    handleInputChange('rating', newValue);
                  }}
                  size="large"
                />
              </Box>

              {/* Detailed description */}
              <TextField
                label="Detailed Description"
                multiline
                rows={6}
                fullWidth
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                required
                placeholder="Please provide detailed information about your feedback, suggestion, or issue..."
              />

              {/* Submit button */}
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={loading}
                sx={{ py: 1.5, fontSize: 16, fontWeight: 'bold' }}
              >
                {loading ? 'Submitting...' : 'Submit Feedback'}
              </Button>
            </Stack>
          </form>
        </Paper>
      </Box>

      {/* Success submit dialog */}
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
              Your feedback has been sent to our team. Thank you!
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

export default Feedback; 