import React, { useRef, useState } from "react";
import { Box, Button, Typography, Paper, Divider, TextField, Checkbox, FormControlLabel, Stack } from "@mui/material";
import { Auth } from "../utils/Auth";
import FileManagement from "../components/FileManagement";
import Dialog from "@mui/material/Dialog";

function AdminLanding() {
  const fileInputRef = useRef();
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [fileMgmtOpen, setFileMgmtOpen] = useState(false);

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setUploadMsg("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        setUploadMsg("Upload successful: " + data.filename);
      } else {
        setUploadMsg("Upload failed: " + (data.message || "unknow failed"));
      }
    } catch {
      setUploadMsg("Upload failed: Internet problem.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', background: '#f7f7fa', mt: 8, px: { xs: 1, sm: 4, md: 8 } }}>
      {/* 主体内容区域 */}
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={4} sx={{ height: '100%', minHeight: 400, alignItems: 'stretch', justifyContent: 'stretch' }}>
        {/* 左侧区域 */}
        <Stack spacing={4} flex={1} sx={{ justifyContent: 'stretch', height: '100%', py: 2 }}>
          {/* 上传文件 */}
          <Paper sx={{ p: 4, mb: 3, minHeight: 180, display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
            <Button variant="contained" component="label" fullWidth disabled={uploading} sx={{ py: 2, fontSize: 18 }}>
              {uploading ? "Uploading..." : "Upload file to knowledge base"}
              <input
                type="file"
                hidden
                accept="application/pdf"
                ref={fileInputRef}
                onChange={handleFileChange}
              />
            </Button>
            {uploadMsg && (
              <Typography variant="body2" color={uploadMsg.startsWith("Upload successful:") ? "success.main" : "error"} sx={{ mt: 2, fontSize: 16 }}>
                {uploadMsg}
              </Typography>
            )}
          </Paper>
          {/* 内容健康 */}
          <Paper sx={{ p: 4, minHeight: 180, display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
            <Typography variant="subtitle1" sx={{ background: '#FFD600', px: 1, mb: 2, fontSize: 18 }}>Content health</Typography>
            <Button variant="outlined" color="primary" fullWidth sx={{ py: 2, fontSize: 18 }} onClick={() => setFileMgmtOpen(true)}>File Management</Button>
          </Paper>
          {/* 用户活跃度 */}
          <Paper sx={{ p: 4, mb: 3, minHeight: 180, display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
            <Typography variant="subtitle1" sx={{ background: '#FFD600', px: 1, mb: 2, fontSize: 18 }}>User engagement</Typography>
            <Box sx={{ height: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5', borderRadius: 1 }}>
              <Typography variant="caption" sx={{ fontSize: 16 }}>eg. active user over 7 days</Typography>
            </Box>
          </Paper>
        </Stack>
        {/* 右侧区域：未答疑问 */}
        <Stack flex={1} sx={{ height: '100%', py: 2 }}>
          <Paper sx={{ flex: 1, p: 4, minHeight: 400, display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'stretch', height: '100%' }}>
            <Typography variant="subtitle1" sx={{ background: '#FFD600', px: 1, mb: 3, fontSize: 20 }}>Unanswered queries</Typography>
            <Stack spacing={3}>
              {[1,2,3,4].map(i => (
                <Box key={i} sx={{ display: 'flex', alignItems: 'center', border: '1px solid #eee', borderRadius: 1, p: 2 }}>
                  <Typography sx={{ flex: 1, fontSize: 16 }}>{`querie ${i}`}</Typography>
                  <FormControlLabel control={<Checkbox />} label="Checkbox" />
                </Box>
              ))}
            </Stack>
          </Paper>
        </Stack>
      </Stack>
      {/* 文件管理弹窗 */}
      <Dialog open={fileMgmtOpen} onClose={() => setFileMgmtOpen(false)} maxWidth="md" fullWidth>
        <FileManagement />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 2 }}>
          <Button onClick={() => setFileMgmtOpen(false)}>Close</Button>
        </Box>
      </Dialog>
    </Box>
  );
}

export default AdminLanding; 