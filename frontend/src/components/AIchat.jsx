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
} from "@mui/material";
import {
  Close as CloseIcon,
  Send as SendIcon,
  Minimize as MinimizeIcon,
} from "@mui/icons-material";

const AIchat = () => {
  const [isOpen, setIsOpen] = useState(false);
  // 用于保存所有历史消息
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hi! I'm HDingo's AI chat bot, how can I help you?",
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
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

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

      try {
        const resp = await fetch(apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          // 目前发送给后端的还是只有 user 的输入, 没有历史信息
          body: JSON.stringify({ question: inputMessage }),
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

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* 悬浮聊天按钮 */}
      <Fab
        color="primary"
        aria-label="AI Chat"
        onClick={toggleChat}
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
            width: "400px",
            height: "60vh",
            maxHeight: "60vh",
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
            <IconButton onClick={toggleChat} size="small">
              <MinimizeIcon />
            </IconButton>
          </Box>
          {/* 模式切换按钮组 */}
          <Box sx={{ px: 2, py: 1, borderBottom: '1px solid #eee', background: '#fff', display: 'flex', gap: 2 }}>
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
    </>
  );
};

export default AIchat;
