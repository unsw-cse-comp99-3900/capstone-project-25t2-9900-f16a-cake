import React, { useEffect, useState } from "react";
import { Box, Button, Typography, Paper, Dialog, DialogTitle, DialogContent, DialogActions } from "@mui/material";

function FileManagement() {
  const [pdfs, setPdfs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState("");

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

  useEffect(() => {
    fetchPdfs();
  }, []);

  const handleDelete = async (filename) => {
    setDeleteLoading(true);
    setDeleteError("");
    try {
      const res = await fetch(`/api/admin/deletepdf/${encodeURIComponent(filename)}`, {
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
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>PDF File Management</Typography>
      {loading ? (
        <Typography>Loading...</Typography>
      ) : error ? (
        <Typography color="error">{error}</Typography>
      ) : pdfs.length === 0 ? (
        <Typography>No PDF files found.</Typography>
      ) : (
        <Box>
          {pdfs.map(pdf => (
            <Box key={pdf.filename} sx={{ display: 'flex', alignItems: 'center', mb: 1, borderBottom: '1px solid #eee', pb: 1 }}>
              <Typography sx={{ flex: 1 }}>{pdf.filename}</Typography>
              <Typography sx={{ width: 120, mr: 2 }} variant="body2">{(pdf.size/1024).toFixed(1)} KB</Typography>
              <Typography sx={{ width: 200, mr: 2 }} variant="body2">{new Date(pdf.upload_time).toLocaleString()}</Typography>
              <Button variant="outlined" color="error" onClick={() => setDeleteTarget(pdf.filename)}>Delete</Button>
            </Box>
          ))}
        </Box>
      )}
      {/* 删除确认弹窗 */}
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Confirm deletion</DialogTitle>
        <DialogContent>
          <Typography>Are you sure to delete <b>{deleteTarget}</b> ？This action cannot be recovered.</Typography>
          {deleteError && <Typography color="error">{deleteError}</Typography>}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)} disabled={deleteLoading}>Cancel</Button>
          <Button onClick={() => handleDelete(deleteTarget)} color="error" disabled={deleteLoading}>
            {deleteLoading ? "Deleting..." : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}

export default FileManagement; 