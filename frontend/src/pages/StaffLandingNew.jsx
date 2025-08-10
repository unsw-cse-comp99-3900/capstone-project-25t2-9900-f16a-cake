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
  
  const [sessionId, setSessionId] = useState(null);
  const [sessionTitle, setSessionTitle] = useState("New Chat");
  
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
  
  const MODES = [
    { value: "general", label: "General" },
    { value: "rag", label: "RAG" },
    { value: "checklist", label: "Checklist" }
  ];
  const [mode, setMode] = useState("general");
  const currentMode = MODES.find(m => m.value === mode);
  
  const [historySessions, setHistorySessions] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [editingHistoryId, setEditingHistoryId] = useState(null);
  const [editingHistoryTitle, setEditingHistoryTitle] = useState("");
  
  const [openDeleteConfirm, setOpenDeleteConfirm] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  
  const [profile, setProfile] = useState(null);
  
  const [checklistStates, setChecklistStates] = useState({});

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
  
  useEffect(() => {
    fetchHistorySessions();
    fetchProfile();
    // 只在组件挂载时执行一次，不需要依赖
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!localStorage.getItem("role")) {
    return null;
  }

  const handleSendMessage = async () => {
    if (inputMessage.trim()) {
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

      const newMessage = {
        id: messages.length + 1,
        text: inputMessage,
        sender: "user",
        timestamp: new Date(),
      };
      setMessages([...messages, newMessage]);
      setInputMessage("");

      console.log('Debug - sessionTitle:', sessionTitle, 'messages.length:', messages.length, 'inputMessage:', inputMessage);

      if (messages.length === 1 && sessionTitle !== inputMessage) {
        setSessionTitle(inputMessage);

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

              setHistorySessions(prev => prev.map(s => s.session_id === currentSessionId ? { ...s, title: inputMessage } : s));
            }
          });
        }
      }

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
        
        if (!resp.ok) {
          throw new Error(`API Error: ${resp.status} - ${data.error || 'Unknown error'}`);
        }
        
        let aiText = data.answer || (data.error ? `error: ${data.error}` : "AI not responding");
        let aiReference = undefined;
        let needHuman = data.need_human || false;
        let aiChecklist = undefined;
        
        if (mode === "checklist" && data.checklist) {
          aiChecklist = data.checklist;
        }

        if ((mode === "rag" || mode === "checklist") && data.reference && Object.keys(data.reference).length > 0) {
          aiReference = data.reference;
        }
        
        const aiResponse = {
          id: data.message_id || messages.length + 2,
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

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const fetchHistorySessions = async () => {
    setLoadingHistory(true);
    const user_id = localStorage.getItem('user_id');
    if (!user_id) return;
    try {
      const resp = await fetch(`/api/get_sessions/${user_id}`);
      const data = await resp.json();
      const sessions = Array.isArray(data) ? data : [];
      setHistorySessions(sessions);
      
      if (sessions.length > 0) {
        const latestSession = sessions[0]; // 假设按时间倒序排列
        handleSelectHistorySession(latestSession.session_id);
      }
    } catch (error) {
      console.error('Failed to fetch history sessions:', error);
    }
    setLoadingHistory(false);
  };

  const handleSelectHistorySession = async (session_id) => {
    setSessionId(session_id);
    try {
      const resp = await fetch(`/api/get_messages/${session_id}`);
      
      if (!resp.ok) {
        console.error(`API Error: ${resp.status} - ${resp.statusText}`);
        setMessages([
          {
            id: 1,
            text: GREETING_MESSAGE,
            sender: "ai",
            timestamp: new Date(),
          },
        ]);
        const found = historySessions.find(s => s.session_id === session_id);
        setSessionTitle(found ? (found.title || session_id) : session_id);
        return;
      }
      
      const msgs = await resp.json();
      if (!Array.isArray(msgs)) {
        console.error('API returned non-array data:', msgs);
        setMessages([
          {
            id: 1,
            text: GREETING_MESSAGE,
            sender: "ai",
            timestamp: new Date(),
          },
        ]);
        const found = historySessions.find(s => s.session_id === session_id);
        setSessionTitle(found ? (found.title || session_id) : session_id);
        return;
      }
      
      const convertedMessages = [
        {
          id: 0,
          text: GREETING_MESSAGE,
          sender: "ai",
          timestamp: new Date(),
        },
        ...msgs.map((m) => {
          let reference = null;
          if (m.reference) {
            try {
              reference = JSON.parse(m.reference);
            } catch (e) {
              console.warn('Failed to parse reference:', m.reference, e);
              reference = null;
            }
          }
          
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
            id: m.message_id,
            text: m.content,
            sender: m.role,
            timestamp: new Date(m.timestamp),
            reference: reference, 
            checklist: checklist,
            needHuman: m.need_human || false
          };
        })
      ];
      
      setMessages(convertedMessages);
      
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
      const found = historySessions.find(s => s.session_id === session_id);
      setSessionTitle(found ? (found.title || session_id) : session_id);
    } catch (error) {
      console.error('Failed to load session messages:', error);
      setMessages([
        {
          id: 1,
          text: GREETING_MESSAGE,
          sender: "ai",
          timestamp: new Date(),
        },
      ]);
      const found = historySessions.find(s => s.session_id === session_id);
      setSessionTitle(found ? (found.title || session_id) : session_id);
    }
  };

  const handleHumanHelp = () => {
    navigate('/human-help', { 
      state: { session_id: sessionId }
    });
  };

  const handleChecklistChange = async (messageId, itemIndex, checked) => {
    const messageIndex = messages.findIndex(m => m.id === messageId);
    const checkboxKey = `${sessionId}-${messageIndex}-${itemIndex}`;
    
    setChecklistStates(prev => ({
      ...prev,
      [checkboxKey]: checked
    }));
    
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
        setChecklistStates(prev => ({
          ...prev,
          [checkboxKey]: !checked
        }));
      } else {
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
      setChecklistStates(prev => ({
        ...prev,
        [checkboxKey]: !checked
      }));
    }
  };

  const handleShowDeleteConfirm = (session_id) => {
    setSessionToDelete(session_id);
    setOpenDeleteConfirm(true);
  };

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
        if (sessionId === sessionToDelete) {
          const updatedSessions = historySessions.filter(s => s.session_id !== sessionToDelete);
          setHistorySessions(updatedSessions);
          
          if (updatedSessions.length > 0) {
            const latestSession = updatedSessions[0];
            handleSelectHistorySession(latestSession.session_id);
          } else {
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
      <Box sx={{ 
        width: 260, 
        bgcolor: '#f7f7f8', 
        borderRight: '1px solid #e0e0e0',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
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

      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
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


    </Box>
  );
}

export default StaffLandingNew; 