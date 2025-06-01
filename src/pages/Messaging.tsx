import { useState } from 'react';
import { 
  Typography, 
  Box, 
  Grid, 
  Paper, 
  List, 
  ListItem, 
  ListItemAvatar, 
  ListItemText, 
  Avatar, 
  TextField, 
  IconButton, 
  Divider,
  InputAdornment,
  Badge,
  useTheme
} from '@mui/material';
import {
  Search as SearchIcon,
  Send as SendIcon,
  AttachFile as AttachFileIcon
} from '@mui/icons-material';
import Layout from '../components/Layout';

interface Message {
  id: number;
  senderId: number;
  text: string;
  timestamp: string;
}

interface Contact {
  id: number;
  name: string;
  lastMessage: string;
  timestamp: string;
  unread: number;
  online: boolean;
}

const Messaging = () => {
  const theme = useTheme();
  const [contacts] = useState<Contact[]>([]);
  
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [newMessage, setNewMessage] = useState('');
  
  const [messages, setMessages] = useState<Message[]>([]);

  const handleContactSelect = (contact: Contact) => {
    // Mark messages as read when selecting a contact
    const updatedContacts = contacts.map(c => 
      c.id === contact.id ? { ...c, unread: 0 } : c
    );
    setContacts(updatedContacts);
    setSelectedContact(contact);
  };

  const handleSendMessage = () => {
    if (newMessage.trim() && selectedContact) {
      const newMsg: Message = {
        id: messages.length + 1,
        senderId: 0, // 0 represents the current user
        text: newMessage,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages([...messages, newMsg]);
      
      // Update the last message in contacts
      const updatedContacts = contacts.map(c => 
        c.id === selectedContact.id 
          ? { ...c, lastMessage: newMessage, timestamp: 'Just now' } 
          : c
      );
      setContacts(updatedContacts);
      setNewMessage('');
    }
  };

  const filteredContacts = contacts.filter(contact => 
    contact.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Layout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="500" sx={{ mb: 1 }}>
          Messaging
        </Typography>
        <Typography color="text.secondary">
          Communicate with your clients securely
        </Typography>
      </Box>

      <Grid container spacing={2} sx={{ height: 'calc(100vh - 180px)' }}>
        <Grid item xs={12} md={4} lg={3}>
          <Paper 
            elevation={0} 
            sx={{ 
              height: '100%', 
              borderRadius: 2, 
              border: '1px solid rgba(0, 0, 0, 0.12)',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <Box sx={{ p: 2 }}>
              <TextField
                placeholder="Search contacts..."
                variant="outlined"
                size="small"
                fullWidth
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
            <Divider />
            <List sx={{ flex: 1, overflow: 'auto', p: 0 }}>
              {filteredContacts.map((contact) => (
                <ListItem 
                  key={contact.id}
                  button
                  selected={selectedContact?.id === contact.id}
                  onClick={() => handleContactSelect(contact)}
                  sx={{ 
                    px: 2,
                    py: 1.5,
                    borderBottom: `1px solid ${theme.palette.divider}`,
                    '&.Mui-selected': {
                      backgroundColor: 'rgba(25, 118, 210, 0.08)',
                    },
                  }}
                >
                  <ListItemAvatar>
                    <Badge
                      overlap="circular"
                      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                      variant="dot"
                      sx={{
                        '& .MuiBadge-badge': {
                          backgroundColor: contact.online ? 'success.main' : 'transparent',
                          boxShadow: `0 0 0 2px ${theme.palette.background.paper}`,
                        },
                      }}
                    >
                      <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                        {contact.name.charAt(0)}
                      </Avatar>
                    </Badge>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: contact.unread > 0 ? 600 : 400 }}>
                          {contact.name}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {contact.timestamp}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: contact.unread > 0 ? 'text.primary' : 'text.secondary',
                            fontWeight: contact.unread > 0 ? 500 : 400,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            maxWidth: '180px'
                          }}
                        >
                          {contact.lastMessage}
                        </Typography>
                        {contact.unread > 0 && (
                          <Badge 
                            badgeContent={contact.unread} 
                            color="primary"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
        <Grid item xs={12} md={8} lg={9}>
          <Paper 
            elevation={0} 
            sx={{ 
              height: '100%', 
              borderRadius: 2, 
              border: '1px solid rgba(0, 0, 0, 0.12)',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            {selectedContact ? (
              <>
                <Box sx={{ 
                  p: 2, 
                  borderBottom: `1px solid ${theme.palette.divider}`,
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  <Badge
                    overlap="circular"
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    variant="dot"
                    sx={{
                      mr: 2,
                      '& .MuiBadge-badge': {
                        backgroundColor: selectedContact.online ? 'success.main' : 'transparent',
                        boxShadow: `0 0 0 2px ${theme.palette.background.paper}`,
                      },
                    }}
                  >
                    <Avatar sx={{ bgcolor: theme.palette.primary.main }}>
                      {selectedContact.name.charAt(0)}
                    </Avatar>
                  </Badge>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                      {selectedContact.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {selectedContact.online ? 'Online' : 'Offline'}
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ 
                  flex: 1, 
                  p: 2,
                  overflow: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1.5
                }}>
                  {messages.map((message) => (
                    <Box
                      key={message.id}
                      sx={{
                        display: 'flex',
                        justifyContent: message.senderId === 0 ? 'flex-end' : 'flex-start',
                      }}
                    >
                      {message.senderId !== 0 && (
                        <Avatar 
                          sx={{ 
                            width: 36, 
                            height: 36, 
                            mr: 1,
                            bgcolor: theme.palette.primary.main
                          }}
                        >
                          {selectedContact.name.charAt(0)}
                        </Avatar>
                      )}
                      <Box>
                        <Box
                          sx={{
                            bgcolor: message.senderId === 0 ? 'primary.main' : 'grey.100',
                            color: message.senderId === 0 ? 'white' : 'text.primary',
                            p: 1.5,
                            borderRadius: 2,
                            maxWidth: '70%',
                            borderTopRightRadius: message.senderId === 0 ? 0 : 2,
                            borderTopLeftRadius: message.senderId !== 0 ? 0 : 2,
                          }}
                        >
                          <Typography variant="body1">
                            {message.text}
                          </Typography>
                        </Box>
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            display: 'block', 
                            mt: 0.5, 
                            color: 'text.secondary',
                            textAlign: message.senderId === 0 ? 'right' : 'left'
                          }}
                        >
                          {message.timestamp}
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
                <Box sx={{ 
                  p: 2, 
                  borderTop: `1px solid ${theme.palette.divider}`,
                  display: 'flex',
                  alignItems: 'center'
                }}>
                  <IconButton sx={{ mr: 1 }}>
                    <AttachFileIcon />
                  </IconButton>
                  <TextField
                    placeholder="Type a message..."
                    variant="outlined"
                    fullWidth
                    size="small"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleSendMessage();
                      }
                    }}
                  />
                  <IconButton 
                    sx={{ ml: 1 }} 
                    color="primary"
                    onClick={handleSendMessage}
                    disabled={!newMessage.trim()}
                  >
                    <SendIcon />
                  </IconButton>
                </Box>
              </>
            ) : (
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                height: '100%',
                flexDirection: 'column',
                p: 3,
              }}>
                <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                  Select a contact to start messaging
                </Typography>
                <Typography variant="body2" color="text.secondary" align="center">
                  Choose a client from the list to view your conversation history and send messages.
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Layout>
  );
};

export default Messaging;