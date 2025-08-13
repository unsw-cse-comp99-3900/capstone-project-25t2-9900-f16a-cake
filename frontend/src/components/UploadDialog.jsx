import React, { useState, useRef } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Alert
} from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import enLocale from 'date-fns/locale/en-US';

function UploadDialog({ open, onClose, onUpload }) {
  const [title, setTitle] = useState('');
  const [keywords, setKeywords] = useState('');
  const [documentDate, setDocumentDate] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef();

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError('');
    } else {
      setError('Please select a valid PDF file');
      setSelectedFile(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a PDF file');
      return;
    }
    if (!title.trim()) {
      setError('Please enter a title');
      return;
    }
    if (!keywords.trim()) {
      setError('Please enter keywords');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('title', title.trim());
    formData.append('keywords', keywords.trim());
    if (documentDate) {
      // Format to yyyy-MM-dd
      const formattedDate = documentDate instanceof Date ? documentDate.toISOString().slice(0, 10) : documentDate;
      formData.append('document_date', formattedDate);
    }

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (data.success) {
        onUpload(data);
        handleClose();
      } else {
        setError(data.message || 'Upload failed');
      }
    } catch (err) {
      console.error('Error uploading document:', err);
      setError('Network error occurred');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setTitle('');
    setKeywords('');
    setDocumentDate(null);
    setSelectedFile(null);
    setError('');
    setUploading(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Upload PDF Document</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 1 }}>
          {/* File Selection */}
          <Button
            variant="outlined"
            component="label"
            fullWidth
            sx={{ mb: 2 }}
          >
            {selectedFile ? selectedFile.name : 'Select PDF File'}
            <input
              type="file"
              hidden
              accept="application/pdf"
              ref={fileInputRef}
              onChange={handleFileSelect}
            />
          </Button>

          {/* Title Input */}
          <TextField
            label="Document Title"
            fullWidth
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            sx={{ mb: 2 }}
            required
          />

          {/* Keywords Input */}
          <TextField
            label="Keywords (comma separated)"
            fullWidth
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="e.g., home, directory, files, upload"
            sx={{ mb: 2 }}
            required
            helperText="Enter keywords separated by commas"
          />

          {/* Document Date Input (English DatePicker) */}
          <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={enLocale}>
            <DatePicker
              label="Document Date (optional)"
              value={documentDate}
              onChange={(newValue) => setDocumentDate(newValue)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  fullWidth
                  sx={{ mb: 2 }}
                />
              )}
              inputFormat="yyyy-MM-dd"
              disableFuture
              clearable
            />
          </LocalizationProvider>

          {/* Error Display */}
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Help Text
          <Typography variant="caption" color="text.secondary">
            This file will be used to generate RAG index so that AI bot can use it as knowledge base to answer staff's questions.
          </Typography> */}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={uploading}>
          Cancel
        </Button>
        <Button 
          onClick={handleUpload} 
          variant="contained" 
          disabled={uploading || !selectedFile || !title.trim() || !keywords.trim()}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default UploadDialog; 