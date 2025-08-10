import React, { useEffect, useState, useImperativeHandle, forwardRef } from "react";
import { Box, Button, Typography, Dialog, DialogTitle, DialogContent, DialogActions } from "@mui/material";

const FileManagement = forwardRef((props, ref) => {
  const [pdfs, setPdfs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  // 日期格式化函数：将日期格式化为 DD/MM/YYYY
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0'); // getMonth() 返回 0-11
      const year = date.getFullYear();
      return `${day}/${month}/${year}`;
    } catch (error) {
      console.error('Date formatting error:', error);
      return 'Invalid Date';
    }
  };

  const fetchPdfs = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/admin/getpdfs");
      const data = await res.json();
      if (data.success) {
        setPdfs(data.pdfs);
      } else {
        setError(data.error || "Failed to fetch PDF list");
      }
    } catch {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  useImperativeHandle(ref, () => ({
    refreshPdfs: fetchPdfs
  }));

  useEffect(() => {
    fetchPdfs();
  }, []);

  const handleDelete = async (documentId) => {
    setDeleteLoading(true);
    setDeleteError("");
    try {
      const res = await fetch(`/api/admin/deletepdf/${documentId}`, {
        method: "DELETE"
      });
      const data = await res.json();
      if (data.success) {
        setDeleteTarget(null);
        fetchPdfs();
      } else {
        setDeleteError(data.error || "Delete failed");
      }
    } catch {
      setDeleteError("Network error");
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>PDF File Management</Typography>
      {loading ? (
        <Typography variant="body2">Loading...</Typography>
      ) : error ? (
        <Typography variant="body2" color="error">{error}</Typography>
      ) : pdfs.length === 0 ? (
        <Typography variant="body2">No PDF files found.</Typography>
      ) : (
        <Box sx={{ maxHeight: 500, overflow: 'auto' }}>
          {pdfs.map(pdf => (
            <Box key={pdf.id} sx={{ display: 'flex', alignItems: 'center', mb: 1, borderBottom: '1px solid #eee', pb: 1 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" sx={{ fontSize: 12, fontWeight: 'bold' }}>{pdf.title}</Typography>
                <Typography variant="caption" sx={{ fontSize: 10, color: 'text.secondary' }}>{pdf.filename}</Typography>
                {pdf.keywords && (
                  <Typography variant="caption" sx={{ fontSize: 10, color: 'text.secondary', display: 'block' }}>
                    Keywords: {pdf.keywords}
                  </Typography>
                )}
              </Box>
              <Typography sx={{ width: 80, mr: 1 }} variant="caption">{(pdf.size/1024).toFixed(1)} KB</Typography>
              <Typography sx={{ width: 120, mr: 1 }} variant="caption">{formatDate(pdf.upload_time)}</Typography>
              <Button variant="outlined" color="error" size="small" onClick={() => setDeleteTarget(pdf.id)}>Delete</Button>
            </Box>
          ))}
        </Box>
      )}
      
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Confirm deletion</DialogTitle>
        <DialogContent>
          <Typography>Are you sure to delete this document? This action cannot be recovered.</Typography>
          {deleteError && <Typography color="error">{deleteError}</Typography>}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)} disabled={deleteLoading}>Cancel</Button>
          <Button onClick={() => handleDelete(deleteTarget)} color="error" disabled={deleteLoading}>
            {deleteLoading ? "Deleting..." : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
});

export default FileManagement; 