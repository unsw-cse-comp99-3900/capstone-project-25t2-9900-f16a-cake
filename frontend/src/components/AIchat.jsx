import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  Paper,
  Typography,
  TextField,
  IconButton,
  Fab,
  List,
  ListItem,
  ListItemText,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  List as MUIList,
  ListItem as MUIListItem,
  ListItemText as MUIListItemText,
  Stack,
} from "@mui/material";
import {
  Send as SendIcon,
  Minimize as MinimizeIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";
// <<-- 步骤 1: 引入 Auth 模块，请确保路径正确 -->>
import { Auth } from "../utils/Auth";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; 

const GREETING_MESSAGE = "Hi! I'm HDingo's AI chat bot, how can I help you?";

const AIchat = ({ showFab = true }) => {
  const navigate = useNavigate();
  // sessionId 由后端生成
  const [sessionId, setSessionId] = useState(null);
  const [sessionTitle, setSessionTitle] = useState("New Chat");

  const [isOpen, setIsOpen] = useState(false);
  const [openConfirm, setOpenConfirm] = useState(false);
  const [openHistory, setOpenHistory] = useState(false);
  const [openDeleteConfirm, setOpenDeleteConfirm] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [historySessions, setHistorySessions] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  // 用于保存所有历史消息
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: GREETING_MESSAGE,
      sender: "ai",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const MODES = [
    { value: "general", label: "General" },
    { value: "rag", label: "RAG" },
    { value: "checklist", label: "Checklist" }
  ];
  const [mode, setMode] = useState("general");
  const currentMode = MODES.find(m => m.value === mode); // 当前模式, 有上面一行决定, 现在是 general
  const otherModes = MODES.filter(m => m.value !== mode); // 其他模式, 现在是 rag 和 general

  const [editingTitle, setEditingTitle] = useState(false);
  const [titleInput, setTitleInput] = useState("");

  const [editingHistoryId, setEditingHistoryId] = useState(null);
  const [editingHistoryTitle, setEditingHistoryTitle] = useState("");

  // 自动滚动到底部
  const messagesEndRef = useRef(null);
  useEffect(() => {
    if (isOpen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [isOpen, messages]);



  // 只有已登录用户才显示
  if (!localStorage.getItem("role")) {
    return null;
  }

  const handleSendMessage = async () => {
    if (inputMessage.trim()) {  // 如果输入消息不为空
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
      if (sessionTitle === "New Chat" && messages.length === 1) {
        setSessionTitle(inputMessage);
        // 异步更新后端 title
        if (sessionId) {
          fetch("/api/update_session_title", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId, title: inputMessage })
          }).then(async resp => {
            const data = await resp.json();
            if (!data.success) {
              alert(data.error || "Failed to update title");
            } else {
              // 更新 historySessions 里的 title
              setHistorySessions(prev => prev.map(s => s.session_id === sessionId ? { ...s, title: inputMessage } : s));
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

      // ==========vvvv 这一部分感觉没必要, 因为没有登录的用户在前端无法访问到 vvvv==========
      // <<-- 步骤 2: 从 Auth 模块获取 user_id -->>
      const userId = Auth.getUserId();

      // 如果获取不到 userId，说明用户未正确登录，中断操作
      if (!userId) {
        const errorResponse = {
          id: messages.length + 2,
          text: "Error: User not found. Please log in again.",
          sender: "ai",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorResponse]);
        return;
      }
      // ==========^^^^ 这一部分感觉没必要, 因为没有登录的用户在前端无法访问到 ^^^^==========

      // 真实请求后端 AI
      try {
        const resp = await fetch(apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: inputMessage,
            session_id: sessionId,
          }),
        });
        const data = await resp.json();
        let aiText = data.answer || (data.error ? `error: ${data.error}` : "AI not responding");
        let aiReference = undefined;
        let needHuman = data.need_human || false;
        
        // checklist 模式特殊处理
        if (mode === "checklist" && data.checklist) {
          aiText += "\n " + data.checklist.map((item, idx) => `${idx + 1}. ${item.item}`).join("\n");
        }
        // rag 模式特殊处理，保存 reference 字段
        if (mode === "rag" && data.reference && Object.keys(data.reference).length > 0) {
          aiReference = data.reference;
        }
        
        const aiResponse = {
          id: messages.length + 2,
          text: aiText,
          sender: "ai",
          timestamp: new Date(),
          reference: aiReference,
          needHuman: needHuman
        };
        setMessages((prev) => [...prev, aiResponse]);
      } catch {
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

  const handleKeyPress = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  // 只有首次且 sessionId 为空时才新建 session
  const handleOpenChat = async () => {
    if (!isOpen) {
      if (!sessionId) {
        const user_id = localStorage.getItem('user_id');
        if (!user_id) {
          alert('User not logged in.');
          return;
        }
        const resp = await fetch('/api/start_session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id, title: 'New Chat' })
        });
        const data = await resp.json();
        if (data.session_id) {
          setSessionId(data.session_id);
          setSessionTitle('New Chat');
        } else alert('Failed to create chat session.');
      }
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  };

  // 新建会话
  const handleNewChat = async () => {
    const user_id = localStorage.getItem('user_id');
    if (!user_id) {
      alert('User not logged in.');
      return;
    }
    const resp = await fetch('/api/start_session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id, title: 'New Chat' })
    });
    const data = await resp.json();
    if (data.session_id) {
      setSessionId(data.session_id);
      setSessionTitle('New Chat');
      setEditingTitle(false);
      setTitleInput("");
      setMessages([
        {
          id: 1,
          text: GREETING_MESSAGE,
          sender: "ai",
          timestamp: new Date(),
        }
      ]);
    } else {
      alert('Failed to create new chat.');
    }
  };

  // 拉取历史会话
  const fetchHistorySessions = async () => {
    setLoadingHistory(true);
    const user_id = localStorage.getItem('user_id');
    if (!user_id) return;
    const resp = await fetch(`/api/get_sessions/${user_id}`);
    const data = await resp.json();
    setHistorySessions(Array.isArray(data) ? data : []);
    setLoadingHistory(false);
  };

  // 查看历史会话时拉取
  const handleOpenHistory = async () => {
    await fetchHistorySessions();
    setOpenHistory(true);
  };

  // 切换到历史会话
  const handleSelectHistorySession = async (session_id) => {
    setOpenHistory(false);
    setSessionId(session_id);
    // 拉取该会话的所有消息
    const resp = await fetch(`/api/get_messages/${session_id}`);
    const msgs = await resp.json();
    // 转换为前端消息格式，并在最前面加问候语
    setMessages([
      {
        id: 0,
        text: GREETING_MESSAGE,
        sender: "ai",
        timestamp: new Date(),
      },
      ...msgs.map((m, idx) => ({
        id: idx + 1,
        text: m.content,
        sender: m.role,
        timestamp: new Date(m.timestamp),
      }))
    ]);
    // 查找 title
    const found = historySessions.find(s => s.session_id === session_id);
    setSessionTitle(found ? (found.title || session_id) : session_id);
    setEditingTitle(false);
    setTitleInput("");
  };

  const handleEditTitle = () => {
    setTitleInput(sessionTitle);
    setEditingTitle(true);
  };

  const handleCancelEditTitle = () => {
    setEditingTitle(false);
    setTitleInput("");
  };

  const handleSaveTitle = async () => {
    if (!sessionId) return;
    const newTitle = titleInput.trim() || "Untitled Session";
    // 假设有后端接口 /api/update_session_title
    const resp = await fetch("/api/update_session_title", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, title: newTitle })
    });
    const data = await resp.json();
    if (data.success) {
      setSessionTitle(newTitle);
      setEditingTitle(false);
      setTitleInput("");
      // 更新 historySessions 里的 title
      setHistorySessions(prev => prev.map(s => s.session_id === sessionId ? { ...s, title: newTitle } : s));
    } else {
      alert(data.error || "Failed to update title");
    }
  };

  const handleHumanHelp = () => {
    // 打开人工帮助页面
    navigate('/human-help');
  };

  // 显示删除确认弹窗
  const handleShowDeleteConfirm = (session_id) => {
    setSessionToDelete(session_id);
    setOpenDeleteConfirm(true);
  };

  // 执行删除会话
  const handleConfirmDelete = async () => {
    if (!sessionToDelete) return;
    
    // 先删除后端数据库里的 session
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
          // 如果有其他会话，自动切换到最新的，但不关闭历史会话弹窗
          const latestSession = updatedSessions[0];
          // 直接设置会话ID和加载消息，而不调用handleSelectHistorySession
          setSessionId(latestSession.session_id);
          setSessionTitle(latestSession.title || latestSession.session_id);
          
          // 加载该会话的消息
          const resp = await fetch(`/api/get_messages/${latestSession.session_id}`);
          const msgs = await resp.json();
          setMessages([
            {
              id: 0,
              text: GREETING_MESSAGE,
              sender: "ai",
              timestamp: new Date(),
            },
            ...msgs.map((m, idx) => ({
              id: idx + 1,
              text: m.content,
              sender: m.role,
              timestamp: new Date(m.timestamp),
            }))
          ]);
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
    
    setOpenDeleteConfirm(false);
    setSessionToDelete(null);
  };

  return (
    <>
      {/* 悬浮聊天按钮 - 只在showFab为true时显示 */}
      {showFab && (
        <Fab
          color="primary"
          aria-label="AI Chat"
          onClick={handleOpenChat}
          sx={{
            position: "fixed",
            bottom: 16,
            right: 16,
            width: 80,
            height: 64,
            background: "#FFD600",
            color: "black",
            fontWeight: "bold",
            fontSize: 12,
            boxShadow: 3,
            borderRadius: "32px",
            "&:hover": {
              background: "#FFE44D",
            },
          }}
        >
          AI CHAT
        </Fab>
      )}

      {/* 聊天对话框 */}
      {isOpen && (
        <Box
          sx={{
            position: "fixed",
            bottom: 80,
            right: 16,
            width: "500px",
            height: "75vh",
            maxHeight: "75vh",
            backgroundColor: "white",
            borderRadius: 2,
            boxShadow: 3,
            zIndex: 1300,
            display: "flex",
            flexDirection: "column",
            border: "1px solid #e0e0e0",
          }}
        >
          {/* 标题栏 */}
          <Box
            sx={{
              background: "#FFD600",
              color: "black",
              fontWeight: "bold",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              py: 1,
              px: 2,
              borderTopLeftRadius: 8,
              borderTopRightRadius: 8,
            }}
          >
            <Typography variant="h6">
              AI Chat - {currentMode.label} {/* 用来展示当前 ai 对话模式 */}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={handleOpenHistory}
                sx={{ minWidth: 80 }}
              >
                View History
              </Button>
              <IconButton onClick={handleOpenChat} size="small">
                <MinimizeIcon />
              </IconButton>
            </Box>
          </Box>
          {/* 模式切换按钮组和 Save Chat 按钮同一行 */}
          <Box sx={{ px: 2, py: 1, borderBottom: '1px solid #eee', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2 }}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              {otherModes.map(m => (
                <Button
                  key={m.value}
                  variant="outlined"
                  size="small"
                  onClick={() => setMode(m.value)}
                  sx={{ minWidth: 100 }}
                >
                  {m.label}
                </Button>
              ))}
            </Box>
            <Button
              variant="contained"
              size="small"
              sx={{ background: '#1976d2', color: 'white', fontWeight: 600, minWidth: 80, boxShadow: 1, '&:hover': { background: '#1565c0' } }}
              onClick={() => setOpenConfirm(true)}
            >
              New Chat
            </Button>
          </Box>
          {/* 会话标题展示 */}
          <Box sx={{ px: 2, py: 0.5, background: '#fff', borderBottom: '1px solid #eee', display: 'flex', alignItems: 'center', gap: 1 }}>
            {editingTitle ? (
              <TextField
                value={titleInput}
                onChange={e => setTitleInput(e.target.value)}
                size="small"
                variant="standard"
                sx={{ minWidth: 120, fontSize: 16 }}
                inputProps={{ maxLength: 50 }}
                autoFocus
                onBlur={handleSaveTitle}
                onKeyDown={e => {
                  if (e.key === 'Enter') handleSaveTitle();
                  if (e.key === 'Escape') handleCancelEditTitle();
                }}
              />
            ) : (
              <>
                <Typography variant="subtitle2" sx={{ color: 'grey.700', fontWeight: 500, mr: 1 }}>
                  {sessionTitle}
                </Typography>
                <IconButton size="small" onClick={handleEditTitle} sx={{ color: 'grey.700' }}><EditIcon fontSize="small" /></IconButton>
              </>
            )}
          </Box>

          {/* 消息列表 */}
          <Box
            sx={{
              flex: 1,
              overflowY: "auto",
              p: 2,
              backgroundColor: "#f5f5f5",
            }}
          >
            <List sx={{ p: 0 }}>
              {messages.map((message) => (
                <ListItem
                  key={message.id}
                  sx={{
                    display: "flex",
                    justifyContent:
                      message.sender === "user" ? "flex-end" : "flex-start",
                    px: 0,
                  }}
                >
                  <Paper
                    sx={{
                      p: 1.5,
                      maxWidth: "70%",
                      backgroundColor:
                        message.sender === "user" ? "#1976d2" : "white",
                      color: message.sender === "user" ? "white" : "black",
                      borderRadius: 2,
                      boxShadow: 1,
                    }}
                  >
                    {/* 使用ReactMarkdown渲染AI消息，用户消息保持纯文本 */}
                    {message.sender === "ai" ? (
                      <Box sx={{ 
                        '& h1, & h2, & h3, & h4, & h5, & h6': { 
                          color: 'inherit',
                          margin: '8px 0 4px 0',
                          fontWeight: 600
                        },
                        '& h1': { fontSize: '1.5em' },
                        '& h2': { fontSize: '1.3em' },
                        '& h3': { fontSize: '1.1em' },
                        '& p': { margin: '4px 0' },
                        '& ul, & ol': { margin: '4px 0', paddingLeft: '20px' },
                        '& li': { margin: '2px 0' },
                        '& code': { 
                          backgroundColor: 'rgba(0,0,0,0.1)', 
                          padding: '2px 4px', 
                          borderRadius: '3px',
                          fontSize: '0.9em'
                        },
                        '& pre': { 
                          backgroundColor: 'rgba(0,0,0,0.05)', 
                          padding: '8px', 
                          borderRadius: '4px',
                          overflow: 'auto',
                          margin: '8px 0'
                        },
                        '& blockquote': { 
                          borderLeft: '3px solid #ccc', 
                          paddingLeft: '10px', 
                          margin: '8px 0',
                          fontStyle: 'italic'
                        },
                        '& table': { 
                          borderCollapse: 'collapse', 
                          width: '100%',
                          margin: '8px 0'
                        },
                        '& th, & td': { 
                          border: '1px solid #ddd', 
                          padding: '4px 8px',
                          fontSize: '0.9em'
                        },
                        '& th': { 
                          backgroundColor: 'rgba(0,0,0,0.05)',
                          fontWeight: 600
                        },
                        '& a': { 
                          color: message.sender === "user" ? 'white' : '#1976d2',
                          textDecoration: 'underline'
                        },
                        '& img': { 
                          maxWidth: '100%', 
                          height: 'auto',
                          borderRadius: '4px'
                        }
                      }}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.text}
                        </ReactMarkdown>
                      </Box>
                    ) : (
                      <Typography variant="body2">{message.text}</Typography>
                    )}
                    {/* rag 模式下显示 reference, 如果是 AI 发的, 并且有 reference 字段, 显示 reference */}
                    {message.sender === "ai" && message.reference && Object.keys(message.reference).length > 0 && !message.needHuman && (
                      <Box sx={{ mt: 2, p: 2, bgcolor: '#f8f9fa', borderRadius: 1, border: '1px solid #e9ecef' }}>
                        <Typography variant="caption" sx={{ color: 'grey.700', fontWeight: 600, display: 'block', mb: 1 }}>
                          Related Documents:
                        </Typography>
                        <Stack spacing={1}>
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
                        </Stack>
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
                    <Typography
                      variant="caption"
                      sx={{
                        display: "block",
                        mt: 0.5,
                        opacity: 0.7,
                        fontSize: "0.7rem",
                      }}
                    >
                      {message.timestamp.toLocaleTimeString()}
                    </Typography>
                  </Paper>
                </ListItem>
              ))}
              {/* 滚动锚点 */}
              <div ref={messagesEndRef} />
            </List>
          </Box>

          <Divider />

          {/* 输入区域 */}
          <Box
            sx={{
              p: 2,
              backgroundColor: "white",
              borderBottomLeftRadius: 8,
              borderBottomRightRadius: 8,
            }}
          >
            <Box sx={{ display: "flex", gap: 1 }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Input your message..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                size="small"
                sx={{
                  "& .MuiOutlinedInput-root": {
                    borderRadius: 2,
                  },
                }}
              />
              <IconButton
                onClick={handleSendMessage}
                disabled={!inputMessage.trim()}
                sx={{
                  backgroundColor: "#FFD600",
                  color: "black",
                  "&:hover": {
                    backgroundColor: "#FFE44D",
                  },
                  "&:disabled": {
                    backgroundColor: "#e0e0e0",
                    color: "#9e9e9e",
                  },
                }}
              >
                <SendIcon />
              </IconButton>
            </Box>
          </Box>
        </Box>
      )}

      {/* New Chat 确认弹窗 */}
      <Dialog open={openConfirm} onClose={() => setOpenConfirm(false)}>
        <DialogTitle>Start New Chat?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            You are about to leave the current conversation, but you can return to it from View History. Continue?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenConfirm(false)}>Cancel</Button>
          <Button
            onClick={async () => {
              setOpenConfirm(false);
              await handleNewChat();
            }}
            color="primary"
            variant="contained"
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>

      {/* 历史会话弹窗 */}
      <Dialog 
        open={openHistory} 
        onClose={() => setOpenHistory(false)} 
        maxWidth="xs" 
        fullWidth
        keepMounted={false}
        disableEscapeKeyDown={false}
        disableBackdropClick={false}
      >
        <DialogTitle>Chat History</DialogTitle>
        <DialogContent dividers>
          {loadingHistory ? (
            <Typography>Loading...</Typography>
          ) : historySessions.length === 0 ? (
            <Typography>No history found.</Typography>
          ) : (
            <MUIList>
              {(() => {
                const current = historySessions.find(s => s.session_id === sessionId);
                const others = historySessions.filter(s => s.session_id !== sessionId);
                const ordered = current ? [current, ...others] : others;
                return ordered.map(s => (
                  <MUIListItem
                    button
                    key={s.session_id}
                    onClick={() => handleSelectHistorySession(s.session_id)}
                    selected={sessionId === s.session_id}
                    secondaryAction={
                      <>
                        <IconButton edge="end" aria-label="edit" onClick={e => { e.stopPropagation(); setEditingHistoryId(s.session_id); setEditingHistoryTitle(s.title || ""); }}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton edge="end" aria-label="delete" onClick={e => { e.stopPropagation(); handleShowDeleteConfirm(s.session_id); }}>
                          <DeleteIcon />
                        </IconButton>
                      </>
                    }
                    sx={sessionId === s.session_id ? { background: '#FFF9C4' } : {}}
                  >
                    <MUIListItemText
                      primary={
                        editingHistoryId === s.session_id ? (
                          <TextField
                            value={editingHistoryTitle}
                            onChange={e => setEditingHistoryTitle(e.target.value)}
                            size="small"
                            variant="standard"
                            sx={{ minWidth: 80, fontSize: 15 }}
                            inputProps={{ maxLength: 50 }}
                            autoFocus
                            onBlur={async () => {
                              const newTitle = editingHistoryTitle.trim() || "Untitled Session";
                              if (newTitle !== s.title) {
                                const resp = await fetch("/api/update_session_title", {
                                  method: "POST",
                                  headers: { "Content-Type": "application/json" },
                                  body: JSON.stringify({ session_id: s.session_id, title: newTitle })
                                });
                                const data = await resp.json();
                                if (data.success) {
                                  setHistorySessions(prev => prev.map(item => item.session_id === s.session_id ? { ...item, title: newTitle } : item));
                                  if (sessionId === s.session_id) setSessionTitle(newTitle);
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
                          <span style={sessionId === s.session_id ? { fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 } : {}}>
                            {s.title || s.session_id}
                            {sessionId === s.session_id && (
                              <span style={{ color: '#1976d2', fontSize: 12, fontWeight: 500, marginLeft: 6 }}>
                                Current Session
                              </span>
                            )}
                          </span>
                        )
                      }
                      secondary={s.created_at}
                    />
                  </MUIListItem>
                ));
              })()}
            </MUIList>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenHistory(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* 删除确认弹窗 */}
      <Dialog 
        open={openDeleteConfirm} 
        onClose={() => setOpenDeleteConfirm(false)}
        disableEscapeKeyDown={false}
        disableBackdropClick={false}
        keepMounted={false}
      >
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
    </>
  );
};

export default AIchat;
