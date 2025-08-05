import React, { useState, useEffect, useRef } from "react";
import { Box, Button, Typography, Paper, Divider, TextField, Checkbox, FormControlLabel, Stack } from "@mui/material";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Auth } from "../utils/Auth";
import FileManagement from "../components/FileManagement";
import UploadDialog from "../components/UploadDialog";

function AdminLanding() {
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");
  const [userEngagementData, setUserEngagementData] = useState([]);
  const [loading, setLoading] = useState(true);
  const fileManagementRef = useRef();

  // 新增：未完成工单
  const [tickets, setTickets] = useState([]);
  const [ticketsLoading, setTicketsLoading] = useState(true);
  const [ticketsError, setTicketsError] = useState("");

  // 获取用户活跃度数据
  useEffect(() => {
    const fetchUserEngagement = async () => {
      try {
        const response = await fetch('/api/user-engagement');
        const result = await response.json();
        if (result.success) {
          setUserEngagementData(result.data);
        }
      } catch (error) {
        console.error('Failed to fetch user engagement data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUserEngagement();
  }, []);

  // 获取未完成工单
  useEffect(() => {
    const fetchTickets = async () => {
      setTicketsLoading(true);
      setTicketsError("");
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/get_tickets?all=false', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        if (data.success) {
          setTickets(data.tickets || []);
        } else {
          setTicketsError(data.message || 'Failed to fetch tickets');
        }
      } catch {
        setTicketsError('Network error');
      } finally {
        setTicketsLoading(false);
      }
    };
    fetchTickets();
  }, []);

  const handleUploadSuccess = (data) => {
    setUploadMsg("Upload successful: " + data.title);
    // 刷新文件列表
    if (fileManagementRef.current) {
      fileManagementRef.current.refreshPdfs();
    }
  };

  const handleOpenUploadDialog = () => {
    setUploadDialogOpen(true);
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
              mb: 3, 
              fontSize: 20,
              fontWeight: 'bold',
              color: '#333',
              borderBottom: '2px solid #FFD600',
              pb: 1
            }}>
              Content health
            </Typography>
            
            {/* 文件上传区域 */}
            <Box sx={{ mb: 3 }}>
              <Button 
                variant="contained" 
                onClick={handleOpenUploadDialog}
                sx={{ 
                  py: 1.5, 
                  px: 2, 
                  fontSize: 14,
                  mb: 2
                }}
              >
                Upload File
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
              <FileManagement ref={fileManagementRef} />
            </Box>
          </Paper>
        </Stack>
        
        {/* 右侧区域：用户活跃度 + 未答疑问 */}
        <Stack flex={1} sx={{ height: '100%', py: 2 }}>
          {/* 用户活跃度 */}
          <Paper sx={{ 
            p: 4, 
            mb: 3, 
            minHeight: 250, 
            display: 'flex', 
            flexDirection: 'column', 
            justifyContent: 'flex-start', 
            height: '45%' 
          }}>
            <Typography variant="h6" sx={{ 
              mb: 2, 
              fontSize: 20,
              fontWeight: 'bold',
              color: '#333',
              borderBottom: '2px solid #FFD600',
              pb: 1
            }}>
              User engagement
            </Typography>
            
            <Box sx={{ 
              flex: 1,
              display: 'flex', 
              flexDirection: 'column',
              background: '#f5f5f5', 
              borderRadius: 1,
              minHeight: 180,
              overflow: 'hidden'
            }}>
              {loading ? (
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  flex: 1
                }}>
                  <Typography variant="body2" sx={{ fontSize: 16 }}>Loading...</Typography>
                </Box>
              ) : userEngagementData.length > 0 ? (
                <>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      textAlign: 'center', 
                      py: 1, 
                      fontWeight: 'bold',
                      color: '#333'
                    }}
                  >
                    Daily Active Users (Last 7 Days)
                  </Typography>
                  <Box sx={{ flex: 1, px: 2, pb: 2, minHeight: 0 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={userEngagementData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="date" 
                          tick={{ fontSize: 12 }}
                          angle={-45}
                          textAnchor="end"
                          height={60}
                        />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip 
                          formatter={(value) => [value, 'active users']}
                          labelFormatter={(label) => `date: ${label}`}
                        />
                        <Line 
                          type="monotone" 
                          dataKey="active_users" 
                          stroke="#FFD600" 
                          strokeWidth={2}
                          dot={{ fill: '#FFD600', strokeWidth: 2, r: 4 }}
                          activeDot={{ r: 6, stroke: '#FFD600', strokeWidth: 2, fill: '#fff' }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </>
              ) : (
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  flex: 1
                }}>
                  <Typography variant="body2" sx={{ fontSize: 16 }}>No data</Typography>
                </Box>
              )}
            </Box>
          </Paper>
          
          {/* 未答疑问 */}
          <Paper sx={{ 
            flex: 1, 
            p: 4, 
            minHeight: 150, 
            display: 'flex', 
            flexDirection: 'column', 
            justifyContent: 'flex-start', 
            alignItems: 'stretch', 
            height: '55%' 
          }}>
            <Typography variant="h6" sx={{ 
              mb: 3, 
              fontSize: 20,
              fontWeight: 'bold',
              color: '#333',
              borderBottom: '2px solid #FFD600',
              pb: 1
            }}>
              Unanswered queries
            </Typography>
            <Stack spacing={2} sx={{ flex: 1, overflow: 'auto' }}>
              {ticketsLoading ? (
                <Typography>Loading...</Typography>
              ) : ticketsError ? (
                <Typography color="error">{ticketsError}</Typography>
              ) : tickets.length === 0 ? (
                <Typography>No unanswered queries.</Typography>
              ) : (
                tickets.map(ticket => (
                  <Box key={ticket.ticket_id} sx={{ display: 'flex', alignItems: 'flex-start', border: '1px solid #eee', borderRadius: 1, p: 1.5, background: '#fff' }}>
                    <Box sx={{ flex: 1 }}>
                      <Typography sx={{ fontWeight: 'bold', fontSize: 15, mb: 0.5 }}>
                        {ticket.first_name} {ticket.last_name}
                      </Typography>
                      <Typography sx={{ fontSize: 13, color: '#666', mb: 0.5 }}>
                        {ticket.department} | {ticket.role}
                      </Typography>
                      <Typography sx={{ fontSize: 14, color: '#222', mb: 0.5 }}>
                        {ticket.content.length > 50 ? `${ticket.content.substring(0, 50)}...` : ticket.content}
                      </Typography>
                      <Typography sx={{ fontSize: 12, color: '#999' }}>
                        {ticket.request_time ? new Date(ticket.request_time).toLocaleString() : ''}
                      </Typography>
                    </Box>
                  </Box>
                ))
              )}
            </Stack>
          </Paper>
        </Stack>
      </Stack>
      
      {/* Upload Dialog */}
      <UploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onUpload={handleUploadSuccess}
      />
    </Box>
  );
}

export default AdminLanding; 