import React, { useState, useRef, useEffect } from "react";
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
} from "@mui/material";
import {
  Close as CloseIcon,
  Send as SendIcon,
  Minimize as MinimizeIcon,
} from "@mui/icons-material";
// <<-- 步骤 1: 引入 Auth 模块，请确保路径正确 -->>
import { Auth } from "../utils/Auth"; 

const GREETING_MESSAGE = "Hi! I'm HDingo's AI chat bot, how can I help you?";

const AIchat = () => {
  // sessionId 由后端生成
  const [sessionId, setSessionId] = useState(null);

  const [isOpen, setIsOpen] = useState(false);
  const [openConfirm, setOpenConfirm] = useState(false);
  const [openHistory, setOpenHistory] = useState(false);
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

      // 根据模式选择不同的后端 API
      let apiUrl = "/api/aichat/general";
      if (mode === "rag") apiUrl = "/api/aichat/rag";
      else if (mode === "checklist") apiUrl = "/api/aichat/checklist";

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
          reference: aiReference
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
          body: JSON.stringify({ user_id, title: 'Default Chat' })
        });
        const data = await resp.json();
        if (data.session_id) setSessionId(data.session_id);
        else alert('Failed to create chat session.');
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
  };

  return (
    <>
      {/* 悬浮聊天按钮 */}
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
                    <Typography variant="body2">{message.text}</Typography>
                    {/* rag 模式下显示 reference, 如果是 AI 发的, 并且有 reference 字段, 显示 reference */}
                    {message.sender === "ai" && message.reference && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" sx={{ color: 'grey.700', fontWeight: 500 }}>Sources:</Typography>
                        {Object.entries(message.reference).map(([title, url]) => (
                          <Box key={title} sx={{ fontSize: 12, color: 'grey.700', wordBreak: 'break-all' }}>
                            <a href={url} target="_blank" rel="noopener noreferrer">{title}</a>
                          </Box>
                        ))}
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
      <Dialog open={openHistory} onClose={() => setOpenHistory(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Chat History</DialogTitle>
        <DialogContent dividers>
          {loadingHistory ? (
            <Typography>Loading...</Typography>
          ) : historySessions.length === 0 ? (
            <Typography>No history found.</Typography>
          ) : (
            <MUIList>
              {historySessions.map(s => (
                <MUIListItem button key={s.session_id} onClick={() => handleSelectHistorySession(s.session_id)}>
                  <MUIListItemText primary={s.title || s.session_id} secondary={s.created_at} />
                </MUIListItem>
              ))}
            </MUIList>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenHistory(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default AIchat;
