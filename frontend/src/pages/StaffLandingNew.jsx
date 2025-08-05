import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Box, 
  Typography, 
  TextField, 
  IconButton, 
  Paper,
  Avatar,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Checkbox,
  FormControlLabel,
  Snackbar
} from "@mui/material";
import { 
  Send as SendIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon
} from "@mui/icons-material";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function StaffLandingNew() {
  const navigate = useNavigate();
  const GREETING_MESSAGE = "Hi! I'm HDingo's AI chat bot, how can I help you?";
  
  // sessionId 由后端生成
  const [sessionId, setSessionId] = useState(null);
  const [sessionTitle, setSessionTitle] = useState("New Chat");
  
  // 成功提示状态
  const [showSuccessPopup, setShowSuccessPopup] = useState(false);
  
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: GREETING_MESSAGE,
      sender: "ai",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading] = useState(false);
  
  // 模式管理
  const MODES = [
    { value: "general", label: "General" },
    { value: "rag", label: "RAG" },
    { value: "checklist", label: "Checklist" }
  ];
  const [mode, setMode] = useState("general");
  const currentMode = MODES.find(m => m.value === mode);
  

  
  // 历史会话管理
  const [historySessions, setHistorySessions] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [editingHistoryId, setEditingHistoryId] = useState(null);
  const [editingHistoryTitle, setEditingHistoryTitle] = useState("");
  
  // 删除确认弹窗
  const [openDeleteConfirm, setOpenDeleteConfirm] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  
  // 用户信息
  const [profile, setProfile] = useState(null);
  
  // Checklist状态管理
  const [checklistStates, setChecklistStates] = useState({});

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 检查是否需要显示成功提示
  useEffect(() => {
    const shouldShowHumanHelpSuccess = localStorage.getItem('showHumanHelpSuccess');
    
    console.log('Checking success popups:', { shouldShowHumanHelpSuccess });
    
    if (shouldShowHumanHelpSuccess === 'true') {
      console.log('Showing human help success popup');
      setShowSuccessPopup(true);
      localStorage.removeItem('showHumanHelpSuccess');
    }
  }, []);

  // 获取用户信息
  const fetchProfile = async () => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const response = await fetch('http://localhost:8000/api/profile', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setProfile(data.profile);
      }
    } catch (error) {
      console.error('Failed to fetch profile:', error);
    }
  };

  // 自动加载历史会话和用户信息
  useEffect(() => {
    fetchHistorySessions();
    fetchProfile();
    // 只在组件挂载时执行一次，不需要依赖
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 只有已登录用户才显示
  if (!localStorage.getItem("role")) {
    return null;
  }

  // 处理发送消息 - 复刻原有AIchat逻辑
  const handleSendMessage = async () => {
    if (inputMessage.trim()) {  // 如果输入消息不为空
      // 如果没有sessionId，先创建一个新的session
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        const user_id = localStorage.getItem('user_id');
        if (!user_id) {
          alert('User not logged in.');
          return;
        }
        try {
          const resp = await fetch('/api/start_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id, title: 'New Chat' })
          });
          const data = await resp.json();
          if (data.session_id) {
            currentSessionId = data.session_id;
            setSessionId(data.session_id);
          } else {
            alert('Failed to create chat session.');
            return;
          }
        } catch {
          alert('Failed to create chat session.');
          return;
        }
      }

      // 构建新消息, 这里是 user 发送的消息
      const newMessage = {
        id: messages.length + 1,
        text: inputMessage,
        sender: "user",
        timestamp: new Date(),
      };
      // 保存到历史信息 messages 中
      setMessages([...messages, newMessage]);
      setInputMessage("");  // 清空输入框

      // 如果是新会话第一次发消息，自动用用户输入更新 title
      console.log('Debug - sessionTitle:', sessionTitle, 'messages.length:', messages.length, 'inputMessage:', inputMessage);
      // 检查是否是新会话的第一次消息（只有一条AI问候语）
      if (messages.length === 1 && sessionTitle !== inputMessage) {
        setSessionTitle(inputMessage);
        // 异步更新后端 title
        if (currentSessionId) {
          fetch("/api/update_session_title", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: currentSessionId, title: inputMessage })
          }).then(async resp => {
            const data = await resp.json();
            if (!data.success) {
              alert(data.error || "Failed to update title");
            } else {
              // 更新 historySessions 里的 title
              setHistorySessions(prev => prev.map(s => s.session_id === currentSessionId ? { ...s, title: inputMessage } : s));
            }
          });
        }
      }

      // 根据模式选择不同的后端 API
      let useMock = true;

      let apiUrl = "/api/aichat/general";
      if (useMock) {
        apiUrl = "/api/aichat/mock/general";
      }
      
      if (mode === "rag") {
        if (useMock) {
          apiUrl = "/api/aichat/mock/rag";
        } else {
          apiUrl = "/api/aichat/rag";
        }
      } else if (mode === "checklist") {
        if (useMock) {
          apiUrl = "/api/aichat/mock/checklist";
        } else {
          apiUrl = "/api/aichat/checklist";
        }
      }

      // 确保sessionId存在
      if (!currentSessionId) {
        const errorResponse = {
          id: messages.length + 2,
          text: "Error: Session not created. Please try again.",
          sender: "ai",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorResponse]);
        return;
      }

      // 真实请求后端 AI
      try {
        const resp = await fetch(apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: inputMessage,
            session_id: currentSessionId,
          }),
        });
        const data = await resp.json();
        
        // 检查API响应状态
        if (!resp.ok) {
          throw new Error(`API Error: ${resp.status} - ${data.error || 'Unknown error'}`);
        }
        
        let aiText = data.answer || (data.error ? `error: ${data.error}` : "AI not responding");
        let aiReference = undefined;
        let needHuman = data.need_human || false;
        let aiChecklist = undefined;
        
        // checklist 模式特殊处理
        if (mode === "checklist" && data.checklist) {
          aiChecklist = data.checklist;
        }
        // rag 和 checklist 模式都处理 reference 字段
        if ((mode === "rag" || mode === "checklist") && data.reference && Object.keys(data.reference).length > 0) {
          aiReference = data.reference;
        }
        
        const aiResponse = {
          id: data.message_id || messages.length + 2, // 使用API返回的消息ID，如果没有则使用前端生成的ID
          text: aiText,
          sender: "ai",
          timestamp: new Date(),
          reference: aiReference,
          checklist: aiChecklist,
          needHuman: needHuman
        };
        setMessages((prev) => [...prev, aiResponse]);
      } catch (error) {
        console.error('API Error:', error);
        const aiResponse = {
          id: messages.length + 2,
          text: "error: network or server error",
          sender: "ai",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, aiResponse]);
      }
    }
  };

  // 处理回车键
  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };



  // 拉取历史会话
  const fetchHistorySessions = async () => {
    setLoadingHistory(true);
    const user_id = localStorage.getItem('user_id');
    if (!user_id) return;
    try {
      const resp = await fetch(`/api/get_sessions/${user_id}`);
      const data = await resp.json();
      const sessions = Array.isArray(data) ? data : [];
      setHistorySessions(sessions);
      
      // 如果有历史会话，自动选择最新的一个
      if (sessions.length > 0) {
        const latestSession = sessions[0]; // 假设按时间倒序排列
        handleSelectHistorySession(latestSession.session_id);
      }
    } catch (error) {
      console.error('Failed to fetch history sessions:', error);
    }
    setLoadingHistory(false);
  };

  // 切换到历史会话
  const handleSelectHistorySession = async (session_id) => {
    setSessionId(session_id);
    // 拉取该会话的所有消息
    try {
      const resp = await fetch(`/api/get_messages/${session_id}`);
      
      // 检查响应状态
      if (!resp.ok) {
        console.error(`API Error: ${resp.status} - ${resp.statusText}`);
        // 如果API失败，设置默认状态
        setMessages([
          {
            id: 1,
            text: GREETING_MESSAGE,
            sender: "ai",
            timestamp: new Date(),
          },
        ]);
        // 查找 title
        const found = historySessions.find(s => s.session_id === session_id);
        setSessionTitle(found ? (found.title || session_id) : session_id);
        return;
      }
      
      const msgs = await resp.json();
      
      // 检查 msgs 是否为数组
      if (!Array.isArray(msgs)) {
        console.error('API returned non-array data:', msgs);
        // 如果返回的不是数组，设置默认状态
        setMessages([
          {
            id: 1,
            text: GREETING_MESSAGE,
            sender: "ai",
            timestamp: new Date(),
          },
        ]);
        // 查找 title
        const found = historySessions.find(s => s.session_id === session_id);
        setSessionTitle(found ? (found.title || session_id) : session_id);
        return;
      }
      
      // 转换为前端消息格式，并在最前面加问候语
      const convertedMessages = [
        {
          id: 0,
          text: GREETING_MESSAGE,
          sender: "ai",
          timestamp: new Date(),
        },
        ...msgs.map((m) => {
          // 解析 reference 字段（JSON字符串转对象）
          let reference = null;
          if (m.reference) {
            try {
              reference = JSON.parse(m.reference);
            } catch (e) {
              console.warn('Failed to parse reference:', m.reference, e);
              reference = null;
            }
          }
          
          // 解析 checklist 字段（JSON字符串转对象）
          let checklist = null;
          if (m.checklist) {
            try {
              checklist = JSON.parse(m.checklist);
            } catch (e) {
              console.warn('Failed to parse checklist:', m.checklist, e);
              checklist = null;
            }
          }
          
          return {
            id: m.message_id,  // 使用数据库中的实际消息ID
            text: m.content,
            sender: m.role,
            timestamp: new Date(m.timestamp),
            reference: reference,  // 解析后的reference对象
            checklist: checklist,  // 解析后的checklist对象
            needHuman: m.need_human || false  // 添加needHuman字段
          };
        })
      ];
      
      setMessages(convertedMessages);
      
      // 初始化checkbox状态，反映数据库中的实际状态
      const newChecklistStates = {};
      convertedMessages.forEach((message, messageIndex) => {
        if (message.checklist && Array.isArray(message.checklist)) {
          message.checklist.forEach((item, itemIndex) => {
            const checkboxKey = `${session_id}-${messageIndex}-${itemIndex}`;
            newChecklistStates[checkboxKey] = item.done || false;
          });
        }
      });
      setChecklistStates(newChecklistStates);
      // 查找 title
      const found = historySessions.find(s => s.session_id === session_id);
      setSessionTitle(found ? (found.title || session_id) : session_id);
    } catch (error) {
      console.error('Failed to load session messages:', error);
      // 设置默认状态而不是显示错误
      setMessages([
        {
          id: 1,
          text: GREETING_MESSAGE,
          sender: "ai",
          timestamp: new Date(),
        },
      ]);
      // 查找 title
      const found = historySessions.find(s => s.session_id === session_id);
      setSessionTitle(found ? (found.title || session_id) : session_id);
    }
  };

  // 人工帮助
  const handleHumanHelp = () => {
    // 打开人工帮助页面，传递当前的 sessionId
    navigate('/human-help', { 
      state: { session_id: sessionId },
      replace: true 
    });
  };

  // 处理checklist状态变化
  const handleChecklistChange = async (messageId, itemIndex, checked) => {
    // 使用会话ID和消息在会话中的位置来生成稳定的key
    const messageIndex = messages.findIndex(m => m.id === messageId);
    const checkboxKey = `${sessionId}-${messageIndex}-${itemIndex}`;
    
    // 更新本地状态
    setChecklistStates(prev => ({
      ...prev,
      [checkboxKey]: checked
    }));
    
    // 调用API更新数据库
    try {
      const response = await fetch(`/api/message/${messageId}/update-checklist-item`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          item_index: itemIndex,
          checked: checked
        })
      });
      
      const data = await response.json();
      if (!data.success) {
        console.error('Failed to update checklist item:', data.error);
        // 如果API调用失败，回滚本地状态
        setChecklistStates(prev => ({
          ...prev,
          [checkboxKey]: !checked
        }));
      } else {
        // API调用成功，更新本地消息中的checklist状态
        setMessages(prev => prev.map(message => {
          if (message.id === messageId && message.checklist) {
            const updatedChecklist = [...message.checklist];
            if (updatedChecklist[itemIndex]) {
              updatedChecklist[itemIndex] = {
                ...updatedChecklist[itemIndex],
                done: checked
              };
            }
            return {
              ...message,
              checklist: updatedChecklist
            };
          }
          return message;
        }));
      }
    } catch (error) {
      console.error('Error updating checklist item:', error);
      // 如果API调用失败，回滚本地状态
      setChecklistStates(prev => ({
        ...prev,
        [checkboxKey]: !checked
      }));
    }
  };

  // 显示删除确认弹窗
  const handleShowDeleteConfirm = (session_id) => {
    setSessionToDelete(session_id);
    setOpenDeleteConfirm(true);
  };

  // 执行删除会话
  const handleConfirmDelete = async () => {
    if (!sessionToDelete) return;
    
    try {
      const resp = await fetch("/api/delete_session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionToDelete })
      });
      const data = await resp.json();
      if (data.success) {
        // 如果当前会话被删，需要切换到其他会话或新建
        if (sessionId === sessionToDelete) {
          // 获取删除后的会话列表
          const updatedSessions = historySessions.filter(s => s.session_id !== sessionToDelete);
          setHistorySessions(updatedSessions);
          
          if (updatedSessions.length > 0) {
            // 如果有其他会话，自动切换到最新的
            const latestSession = updatedSessions[0];
            handleSelectHistorySession(latestSession.session_id);
          } else {
            // 如果没有会话了，自动新建一个
            const user_id = localStorage.getItem('user_id');
            if (user_id) {
              const resp = await fetch('/api/start_session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id, title: 'New Chat' })
              });
              const newData = await resp.json();
              if (newData.session_id) {
                setSessionId(newData.session_id);
                setSessionTitle('New Chat');
                setMessages([
                  {
                    id: 1,
                    text: GREETING_MESSAGE,
                    sender: "ai",
                    timestamp: new Date(),
                  },
                ]);
                // 刷新历史会话列表以包含新创建的会话
                fetchHistorySessions();
              } else {
                alert('Failed to create new chat.');
                setSessionId(null);
                setSessionTitle('New Chat');
                setMessages([
                  {
                    id: 1,
                    text: GREETING_MESSAGE,
                    sender: "ai",
                    timestamp: new Date(),
                  },
                ]);
              }
            } else {
              setSessionId(null);
              setSessionTitle('New Chat');
              setMessages([
                {
                  id: 1,
                  text: GREETING_MESSAGE,
                  sender: "ai",
                  timestamp: new Date(),
                },
              ]);
            }
          }
        } else {
          // 如果删除的不是当前会话，只需要更新列表
          setHistorySessions(prev => prev.filter(s => s.session_id !== sessionToDelete));
        }
      } else {
        alert(data.error || "Failed to delete session");
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      alert('Failed to delete session.');
    }
    
    setOpenDeleteConfirm(false);
    setSessionToDelete(null);
  };

  // 新建对话
  const handleNewConversation = async () => {
    const user_id = localStorage.getItem('user_id');
    if (!user_id) {
      alert('User not logged in.');
      return;
    }
    try {
      const resp = await fetch('/api/start_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id, title: 'New Chat' })
      });
      const data = await resp.json();
      if (data.session_id) {
        setSessionId(data.session_id);
        setSessionTitle('New Chat');
        setMessages([
          {
            id: 1,
            text: GREETING_MESSAGE,
            sender: "ai",
            timestamp: new Date(),
          }
        ]);
        
        // 刷新历史会话列表
        fetchHistorySessions();
      } else {
        alert('Failed to create new chat.');
      }
    } catch {
      alert('Failed to create new chat.');
    }
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)', bgcolor: '#ffffff', mt: '64px' }}>
      {/* 左侧边栏 */}
      <Box sx={{ 
        width: 260, 
        bgcolor: '#f7f7f8', 
        borderRight: '1px solid #e0e0e0',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* 新建对话按钮 */}
        <Box sx={{ p: 2, borderBottom: '1px solid #eee', flexShrink: 0 }}>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={handleNewConversation}
            fullWidth
            sx={{ 
              textTransform: 'none',
              borderColor: '#d1d5db',
              color: '#374151',
              '&:hover': {
                borderColor: '#FFD600',
                color: '#000'
              }
            }}
          >
            New Chat
          </Button>
        </Box>

        {/* 对话历史 */}
        <List sx={{ flex: 1, overflow: 'auto', overflowX: 'hidden' }}>
          {loadingHistory ? (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Loading...
              </Typography>
            </Box>
          ) : historySessions.length === 0 ? (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                No history found
              </Typography>
            </Box>
          ) : (
            historySessions.map((session, index) => (
              <React.Fragment key={session.session_id}>
                <ListItem
                  selected={sessionId === session.session_id}
                  onClick={() => handleSelectHistorySession(session.session_id)}
                  sx={{
                    borderRadius: 1,
                    mx: 1,
                    mb: 0.5,
                    cursor: 'pointer',
                    pr: 1,
                    '&.Mui-selected': {
                      bgcolor: '#FFF9C4',
                      border: '1px solid #FFD600',
                      '&:hover': { bgcolor: '#FFF9C4' }
                    }
                  }}
                secondaryAction={
                  <Box sx={{ display: 'flex', gap: 0.5, ml: 1, minWidth: 'fit-content' }}>
                    <IconButton 
                      size="small"
                      onClick={e => { 
                        e.stopPropagation(); 
                        setEditingHistoryId(session.session_id); 
                        setEditingHistoryTitle(session.title || ""); 
                      }}
                      sx={{ p: 0.5 }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton 
                      size="small"
                      onClick={e => { 
                        e.stopPropagation(); 
                        handleShowDeleteConfirm(session.session_id); 
                      }}
                      sx={{ p: 0.5 }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                }
              >
                <ListItemText 
                  primary={
                    editingHistoryId === session.session_id ? (
                      <TextField
                        value={editingHistoryTitle}
                        onChange={e => setEditingHistoryTitle(e.target.value)}
                        size="small"
                        variant="standard"
                        sx={{ fontSize: '0.875rem' }}
                        inputProps={{ maxLength: 50 }}
                        autoFocus
                        onBlur={async () => {
                          const newTitle = editingHistoryTitle.trim() || "Untitled Session";
                          if (newTitle !== session.title) {
                            const resp = await fetch("/api/update_session_title", {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ session_id: session.session_id, title: newTitle })
                            });
                            const data = await resp.json();
                            if (data.success) {
                              setHistorySessions(prev => prev.map(item => item.session_id === session.session_id ? { ...item, title: newTitle } : item));
                              if (sessionId === session.session_id) setSessionTitle(newTitle);
                            } else {
                              alert(data.error || "Failed to update title");
                            }
                          }
                          setEditingHistoryId(null);
                          setEditingHistoryTitle("");
                        }}
                        onKeyDown={async e => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            e.target.blur();
                          }
                          if (e.key === 'Escape') {
                            setEditingHistoryId(null);
                            setEditingHistoryTitle("");
                          }
                        }}
                      />
                    ) : (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography
                          variant="body2"
                          sx={{
                            fontSize: '0.875rem',
                            color: sessionId === session.session_id ? '#111827' : '#6b7280',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            fontWeight: sessionId === session.session_id ? 600 : 400
                          }}
                        >
                          {session.title || session.session_id}
                        </Typography>
                        {sessionId === session.session_id && (
                          <Chip 
                            label="Current" 
                            size="small" 
                            sx={{ 
                              height: 18, 
                              fontSize: '0.7rem',
                              bgcolor: '#FFD600',
                              color: 'black',
                              fontWeight: 'bold',
                              boxShadow: 1
                            }} 
                          />
                        )}
                      </Box>
                    )
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary" sx={{ pr: 8, display: 'block' }}>
                      {session.created_at}
                    </Typography>
                  }
                />
              </ListItem>
              {index < historySessions.length - 1 && (
                <Divider sx={{ mx: 2, my: 0.5 }} />
              )}
              </React.Fragment>
            ))
          )}
        </List>
      </Box>

      {/* 主聊天区域 */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* 标题栏 - 参考AIchat风格 */}
        <Box
          sx={{
            background: "#FFD600",
            color: "black",
            fontWeight: "bold",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            py: 1,
            px: 2,
            borderBottom: '1px solid #e0e0e0',
          }}
        >
          <Typography variant="h6">
            AI Chat - {currentMode?.label || "General"}
          </Typography>
        </Box>
        

        
        {/* 消息列表 */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {messages.map((message) => (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                mb: 4,
                justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start'
              }}
            >
              <Box sx={{ 
                maxWidth: '80%',
                display: 'flex',
                gap: 2,
                alignItems: 'flex-start'
              }}>
                {message.sender === 'ai' && (
                  <Avatar sx={{ width: 32, height: 32, bgcolor: '#10a37f' }}>
                    AI
                  </Avatar>
                )}
                
                <Paper
                  sx={{
                    p: 2,
                    bgcolor: message.sender === 'user' ? '#007aff' : '#f7f7f8',
                    color: message.sender === 'user' ? 'white' : 'inherit',
                    borderRadius: 2,
                    position: 'relative'
                  }}
                >

                  
                  <Box>
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code: ({ inline, className, children, ...props }) => {
                          return !inline ? (
                            <Box
                              component="pre"
                              sx={{
                                bgcolor: '#1e1e1e',
                                color: '#d4d4d4',
                                p: 2,
                                borderRadius: 1,
                                overflow: 'auto',
                                fontSize: '0.875rem',
                                my: 1
                              }}
                            >
                              <code className={className} {...props}>
                                {children}
                              </code>
                            </Box>
                          ) : (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        },
                        p: ({ children, ...props }) => {
                          // 检查是否包含pre标签，如果包含则直接返回children
                          const hasPre = React.Children.toArray(children).some(
                            child => React.isValidElement(child) && child.type === 'pre'
                          );
                          if (hasPre) {
                            return <>{children}</>;
                          }
                          return <p {...props}>{children}</p>;
                        }
                      }}
                    >
                      {message.text}
                    </ReactMarkdown>
                  </Box>
                  
                  {/* 显示checklist（Checklist模式） */}
                  {message.sender === "ai" && message.checklist && Array.isArray(message.checklist) && message.checklist.length > 0 && (
                    <Box sx={{ mt: 2, p: 2, bgcolor: '#f0f8ff', borderRadius: 1, border: '1px solid #cce7ff' }}>
                      <Typography variant="caption" sx={{ color: 'grey.700', fontWeight: 600, display: 'block', mb: 1 }}>
                        Checklist:
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {message.checklist.map((item, index) => {
                          const checkboxKey = `${message.id}-${index}`;
                          const isChecked = checklistStates[checkboxKey] !== undefined 
                            ? checklistStates[checkboxKey] 
                            : item.done || false;
                          
                          return (
                            <FormControlLabel
                              key={index}
                              control={
                                <Checkbox
                                  checked={isChecked}
                                  onChange={(e) => handleChecklistChange(message.id, index, e.target.checked)}
                                  sx={{
                                    color: '#1976d2',
                                    '&.Mui-checked': {
                                      color: '#1976d2',
                                    },
                                  }}
                                />
                              }
                              label={
                                <Typography 
                                  variant="body2" 
                                  sx={{ 
                                    textDecoration: isChecked ? 'line-through' : 'none',
                                    color: isChecked ? 'grey.500' : 'inherit',
                                    fontSize: '0.875rem'
                                  }}
                                >
                                  {item.item}
                                </Typography>
                              }
                              sx={{
                                margin: 0,
                                '& .MuiFormControlLabel-label': {
                                  flex: 1,
                                }
                              }}
                            />
                          );
                        })}
                      </Box>
                    </Box>
                  )}
                  
                  {/* 显示reference（RAG模式） */}
                  {message.sender === "ai" && message.reference && Object.keys(message.reference).length > 0 && !message.needHuman && (
                    <Box sx={{ mt: 2, p: 2, bgcolor: '#f8f9fa', borderRadius: 1, border: '1px solid #e9ecef' }}>
                      <Typography variant="caption" sx={{ color: 'grey.700', fontWeight: 600, display: 'block', mb: 1 }}>
                        Related Documents:
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        {Object.entries(message.reference).map(([title, url]) => (
                          <Box key={title} sx={{ 
                            display: 'flex', 
                            alignItems: 'center',
                            p: 1,
                            bgcolor: 'white',
                            borderRadius: 1,
                            border: '1px solid #dee2e6',
                            '&:hover': { bgcolor: '#f8f9fa' }
                          }}>
                            <Typography variant="body2" sx={{ 
                              color: '#1976d2', 
                              fontWeight: 500,
                              cursor: 'pointer',
                              textDecoration: 'underline',
                              '&:hover': { color: '#1565c0' }
                            }} onClick={() => window.open(url, '_blank')}>
                              {title}
                            </Typography>
                          </Box>
                        ))}
                      </Box>
                    </Box>
                  )}
                  
                  {/* 需要人工帮助时显示帮助按钮 */}
                  {message.sender === "ai" && message.needHuman && (
                    <Box sx={{ mt: 1, p: 1 }}>
                      <Button
                        variant="contained"
                        size="small"
                        onClick={() => handleHumanHelp()}
                        sx={{ 
                          bgcolor: '#FFD600', 
                          color: 'black',
                          '&:hover': { bgcolor: '#FFE44D' }
                        }}
                      >
                        Ask for Human Help
                      </Button>
                    </Box>
                  )}
                </Paper>

                {message.sender === 'user' && (
                  <Avatar sx={{ 
                    width: 32, 
                    height: 32, 
                    bgcolor: '#FFD600',
                    color: '#222',
                    fontSize: 14
                  }}>
                    {profile ? profile.firstName[0] : "U"}
                  </Avatar>
                )}
              </Box>
            </Box>
          ))}
          
          {isLoading && (
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
              <Avatar sx={{ width: 32, height: 32, bgcolor: '#10a37f' }}>
                AI
              </Avatar>
              <Paper sx={{ p: 2, bgcolor: '#f7f7f8', borderRadius: 2 }}>
                <Typography variant="body2" sx={{ color: '#6b7280' }}>
                  AI is thinking...
                </Typography>
              </Paper>
            </Box>
          )}
          
          <div ref={messagesEndRef} />
        </Box>

        {/* 输入区域 */}
        <Box sx={{ p: 2, borderTop: '1px solid #e0e0e0', bgcolor: '#fff' }}>
          <Box sx={{ 
            display: 'flex', 
            gap: 1, 
            alignItems: 'flex-end',
            maxWidth: '90%',
            mx: 'auto'
          }}>
            <TextField
              ref={inputRef}
              multiline
              maxRows={4}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              variant="outlined"
              fullWidth
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  bgcolor: '#f9fafb',
                  borderColor: '#e0e0e0',
                  '&:hover': {
                    bgcolor: '#f3f4f6',
                    borderColor: '#FFD600'
                  },
                  '&.Mui-focused': {
                    bgcolor: 'white',
                    borderColor: '#FFD600'
                  }
                }
              }}
            />
            <IconButton
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              sx={{
                bgcolor: '#FFD600',
                color: 'black',
                fontWeight: 'bold',
                '&:hover': {
                  bgcolor: '#FFE44D'
                },
                '&:disabled': {
                  bgcolor: '#d1d5db',
                  color: '#9ca3af'
                }
              }}
            >
              <SendIcon />
            </IconButton>
          </Box>
          
          {/* 模式选择 - 参考ChatGPT布局 */}
          <Box sx={{ 
            mt: 2, 
            display: 'flex', 
            justifyContent: 'center', 
            gap: 1,
            flexWrap: 'wrap'
          }}>
            {MODES.map(m => (
              <Chip
                key={m.value}
                label={m.label}
                onClick={() => setMode(m.value)}
                variant={mode === m.value ? "filled" : "outlined"}
                sx={{
                  cursor: 'pointer',
                  bgcolor: mode === m.value ? '#FFD600' : 'transparent',
                  color: mode === m.value ? 'black' : '#666',
                  borderColor: mode === m.value ? '#FFD600' : '#ddd',
                  fontWeight: mode === m.value ? 'bold' : 'normal',
                  '&:hover': {
                    bgcolor: mode === m.value ? '#FFE44D' : '#f5f5f5'
                  }
                }}
              />
            ))}
          </Box>
        </Box>
      </Box>

      {/* 删除确认弹窗 */}
      <Dialog open={openDeleteConfirm} onClose={() => setOpenDeleteConfirm(false)}>
        <DialogTitle>Delete Chat Session?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            You are about to delete this chat session. This action cannot be undone. Continue?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDeleteConfirm(false)}>Cancel</Button>
          <Button
            onClick={handleConfirmDelete}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* 成功提示 Snackbar */}
      <Snackbar
        open={showSuccessPopup}
        autoHideDuration={5000}
        onClose={() => setShowSuccessPopup(false)}
        message="Your human help request has been submitted successfully! We'll get back to you soon."
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        sx={{
          zIndex: 9999,
          '& .MuiSnackbarContent-root': {
            backgroundColor: '#4caf50',
            color: 'white',
            fontWeight: 'bold',
            fontSize: '1rem',
            padding: '12px 24px'
          }
        }}
      />
    </Box>
  );
}

export default StaffLandingNew; 