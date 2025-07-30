import React, { useRef, useState } from "react";
import { Box, Button, Typography, Paper, Divider, TextField, Checkbox, FormControlLabel, Stack } from "@mui/material";
import { Auth } from "../utils/Auth";
import FileManagement from "../components/FileManagement";

function AdminLanding() {
  const fileInputRef = useRef();
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");

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
        setUploadMsg("Upload failed: " + (data.message || "Unknown error"));
      }
    } catch {
      setUploadMsg("Upload failed: Network error");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', background: '#f7f7fa', mt: 8, px: { xs: 1, sm: 4, md: 8 } }}>
      {/* 主体内容区域 */}
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={4} sx={{ height: '100%', minHeight: 400, alignItems: 'stretch', justifyContent: 'stretch' }}>
        {/* 左侧区域：内容健康 */}
        <Stack flex={1} sx={{ height: '100%', py: 2 }}>
          <Paper sx={{ 
            flex: 1, 
            p: 4, 
            minHeight: 400, 
            display: 'flex', 
            flexDirection: 'column', 
            justifyContent: 'flex-start', 
            alignItems: 'stretch', 
            height: '100%' 
          }}>
            <Typography variant="h6" sx={{ 
              background: '#FFD600',
              px: 2, 
              py: 1,
              mb: 3, 
              fontSize: 20,
              fontWeight: 'bold',
              alignSelf: 'flex-start',
              mt: 0,
              borderRadius: 1,
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              color: '#333'
            }}>
              Content health
            </Typography>
            
            {/* 文件上传区域 */}
            <Box sx={{ mb: 3 }}>
              <Button 
                variant="contained" 
                component="label" 
                disabled={uploading} 
                sx={{ 
                  py: 1.5, 
                  px: 2, 
                  fontSize: 14,
                  mb: 2
                }}
              >
                {uploading ? "Uploading..." : "Upload File"}
                <input
                  type="file"
                  hidden
                  accept="application/pdf"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                />
              </Button>
              
              <Typography variant="body2" sx={{ 
                fontSize: 12, 
                color: 'text.secondary',
                fontStyle: 'italic',
                mb: 2
              }}>
                This file will be used to generate RAG index so that AI bot can use it as knowledge base to answer staff's question.
              </Typography>
        
              {uploadMsg && (
                <Typography variant="body2" color={uploadMsg.startsWith("Upload successful:") ? "success.main" : "error"} sx={{ fontSize: 14 }}>
                  {uploadMsg}
                </Typography>
              )}
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            {/* 文件管理区域 */}
            <Box sx={{ flex: 1, overflow: 'hidden' }}>
              <FileManagement />
            </Box>
          </Paper>
        </Stack>
        
        {/* 右侧区域：用户活跃度 + 未答疑问 */}
        <Stack flex={1} sx={{ height: '100%', py: 2 }}>
          {/* 用户活跃度 */}
          <Paper sx={{ 
            p: 4, 
            mb: 3, 
            minHeight: 180, 
            display: 'flex', 
            flexDirection: 'column', 
            justifyContent: 'flex-start', 
            height: '30%' 
          }}>
            <Typography variant="h6" sx={{ 
              background: '#FFD600',
              px: 2, 
              py: 1,
              mb: 2, 
              fontSize: 20,
              fontWeight: 'bold',
              alignSelf: 'flex-start',
              mt: 0,
              borderRadius: 1,
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              color: '#333'
            }}>
              User engagement
            </Typography>
            
            <Box sx={{ 
              flex: 1,
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              background: '#f5f5f5', 
              borderRadius: 1 
            }}>
              <Typography variant="caption" sx={{ fontSize: 16 }}>eg. active user over 7 days</Typography>
            </Box>
          </Paper>
          
          {/* 未答疑问 */}
          <Paper sx={{ 
            flex: 1, 
            p: 4, 
            minHeight: 200, 
            display: 'flex', 
            flexDirection: 'column', 
            justifyContent: 'flex-start', 
            alignItems: 'stretch', 
            height: '70%' 
          }}>
            <Typography variant="h6" sx={{ 
              background: '#FFD600',
              px: 2, 
              py: 1,
              mb: 3, 
              fontSize: 20,
              fontWeight: 'bold',
              alignSelf: 'flex-start',
              mt: 0,
              borderRadius: 1,
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              color: '#333'
            }}>
              Unanswered queries
            </Typography>
            
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
    </Box>
  );
}

export default AdminLanding; 