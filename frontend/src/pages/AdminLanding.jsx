import React from "react";
import { Box, Button, Typography, Paper, Divider, TextField, Checkbox, FormControlLabel } from "@mui/material";
import { Auth } from "../utils/Auth";

function AdminLanding() {
  return (
    <Box sx={{ minHeight: "100vh", background: "#f7f7fa", p: 3, pt: 10 }}>
      {/* 顶部导航栏 */}
      {/* <Divider sx={{ mb: 2 }} /> */}
      {/* 主体内容区域 */}
      <Box sx={{ display: "flex", gap: 2 }}>
        {/* 左侧区域 */}
        <Box sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
          {/* 上传文件 */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Button variant="contained" component="label" fullWidth>
              Upload file to knowledge base
              <input type="file" hidden />
            </Button>
          </Paper>
          {/* 用户活跃度 */}
          <Paper sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" sx={{ background: '#FFD600', px: 1, mb: 1 }}>User engagement</Typography>
            {/* 简单折线图占位 */}
            <Box sx={{ height: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5', borderRadius: 1 }}>
              <Typography variant="caption">eg. active user over 7 days</Typography>
            </Box>
          </Paper>
          {/* 内容健康 */}
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" sx={{ background: '#FFD600', px: 1, mb: 1 }}>Content health</Typography>
            <Button variant="outlined" color="error" fullWidth>file delete</Button>
          </Paper>
        </Box>
        {/* 右侧区域：未答疑问 */}
        <Box sx={{ flex: 1 }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="subtitle1" sx={{ background: '#FFD600', px: 1, mb: 2 }}>Unanswered queries</Typography>
            {/* 示例未答疑问列表 */}
            {[1,2,3,4].map(i => (
              <Box key={i} sx={{ display: 'flex', alignItems: 'center', mb: 2, border: '1px solid #eee', borderRadius: 1, p: 1 }}>
                <Typography sx={{ flex: 1 }}>{`querie ${i}`}</Typography>
                <FormControlLabel control={<Checkbox />} label="Checkbox" />
              </Box>
            ))}
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}

export default AdminLanding; 