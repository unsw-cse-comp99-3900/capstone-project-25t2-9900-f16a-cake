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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Rating,
  FormControlLabel,
  Checkbox
} from "@mui/material";
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { Auth } from "../utils/Auth";

function Feedback() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    category: "",
    subject: "",
    description: "",
    rating: 0,
    allowContact: false
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
        // 设置localStorage标记，表示需要显示成功popup
        localStorage.setItem('showFeedbackSuccess', 'true');
        // 立即跳转到staff-landing页面
        navigate('/staff-landing');
      } else {
        setError(data.message || 'submit failed, please try again later');
      }
    } catch {
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
        {/* 返回按钮 */}
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
            Feedback & Suggestions
          </Typography>
          
          <Typography 
            variant="body1" 
            sx={{ 
              mb: 4, 
              color: 'text.secondary',
              lineHeight: 1.6
            }}
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

              {/* 分类选择 */}
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

              {/* 主题 */}
              <TextField
                label="Subject"
                fullWidth
                value={formData.subject}
                onChange={(e) => handleInputChange('subject', e.target.value)}
                required
                placeholder="Brief description of your feedback"
              />

              {/* 评分 */}
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

              {/* 详细描述 */}
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

              {/* 联系许可 */}
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.allowContact}
                    onChange={(e) => handleInputChange('allowContact', e.target.checked)}
                  />
                }
                label="I allow HDingo team to contact me regarding this feedback"
              />

              {/* 提交按钮 */}
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={loading}
                sx={{ 
                  py: 1.5,
                  fontSize: 16,
                  fontWeight: 'bold'
                }}
              >
                {loading ? 'Submitting...' : 'Submit Feedback'}
              </Button>
            </Stack>
          </form>
        </Paper>
      </Box>
      
    </Box>
  );
}

export default Feedback; 