import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  IconButton,
  Divider,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Email as EmailIcon,
  Send as SendIcon,
  Inbox as InboxIcon,
  Outbox as OutboxIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { api } from '../utils/api';
import { Client } from '../types/client';

interface Email {
  id: string;
  gmail_message_id: string;
  direction: 'inbound' | 'outbound';
  subject: string;
  body_text: string;
  body_html: string;
  from_email: string;
  to_email: string;
  sent_at: string;
  read_status: boolean;
}

interface EmailStats {
  total_emails: number;
  inbound_emails: number;
  outbound_emails: number;
  unread_emails: number;
}

interface EmailInterfaceProps {
  client: Client;
}

const EmailInterface: React.FC<EmailInterfaceProps> = ({ client }) => {
  const [emails, setEmails] = useState<Email[]>([]);
  const [stats, setStats] = useState<EmailStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [composeOpen, setComposeOpen] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [emailDetailOpen, setEmailDetailOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Compose email form
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (client.id) {
      fetchEmails();
      fetchStats();
    }
  }, [client.id]);

  const fetchEmails = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/emails/client/${client.id}`);
      setEmails(response.emails || []);
    } catch (error) {
      console.error('Error fetching emails:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get(`/api/emails/client/${client.id}/stats`);
      setStats(response);
    } catch (error) {
      console.error('Error fetching email stats:', error);
    }
  };

  const handleSendEmail = async () => {
    if (!emailSubject.trim() || !emailBody.trim()) {
      alert('Please fill in both subject and message');
      return;
    }

    try {
      setSending(true);
      await api.post('/api/emails/send', {
        to_email: client.primary_email,
        subject: emailSubject,
        body: emailBody,
        client_id: client.id
      });

      setEmailSubject('');
      setEmailBody('');
      setComposeOpen(false);
      await fetchEmails(); // Refresh email list
      await fetchStats(); // Refresh stats
      alert('Email sent successfully!');
    } catch (error) {
      console.error('Error sending email:', error);
      alert('Failed to send email. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const handleEmailClick = async (email: Email) => {
    setSelectedEmail(email);
    setEmailDetailOpen(true);

    // Mark as read if it's an inbound unread email
    if (email.direction === 'inbound' && !email.read_status) {
      try {
        await api.patch(`/api/emails/mark-read/${email.id}`);
        // Update local state
        setEmails(prevEmails =>
          prevEmails.map(e =>
            e.id === email.id ? { ...e, read_status: true } : e
          )
        );
        await fetchStats(); // Refresh stats
      } catch (error) {
        console.error('Error marking email as read:', error);
      }
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      // Trigger email sync
      await api.post('/api/emails/sync');
      await fetchEmails();
      await fetchStats();
    } catch (error) {
      console.error('Error refreshing emails:', error);
      alert('Failed to refresh emails. Please try again.');
    } finally {
      setRefreshing(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getEmailPreview = (bodyText: string, maxLength: number = 100) => {
    if (!bodyText) return 'No content';
    return bodyText.length > maxLength 
      ? bodyText.substring(0, maxLength) + '...'
      : bodyText;
  };

  const getDirectionIcon = (direction: string) => {
    return direction === 'inbound' ? <InboxIcon /> : <OutboxIcon />;
  };

  const getDirectionColor = (direction: string) => {
    return direction === 'inbound' ? 'success' : 'primary';
  };

  if (!client.primary_email) {
    return (
      <Card>
        <CardContent>
          <Alert severity="warning">
            No primary email address set for this client. Please add an email address to enable email communication.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      {/* Email Stats */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" component="h3">
              Email Communication with {client.first_name} {client.last_name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <IconButton onClick={handleRefresh} disabled={refreshing}>
                <RefreshIcon />
              </IconButton>
              <Button
                variant="contained"
                startIcon={<SendIcon />}
                onClick={() => setComposeOpen(true)}
                disabled={!client.primary_email}
              >
                Send Email
              </Button>
            </Box>
          </Box>

          <Typography variant="body2" color="text.secondary" gutterBottom>
            {client.primary_email}
          </Typography>

          {stats && (
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Chip label={`Total: ${stats.total_emails}`} variant="outlined" />
              <Chip 
                label={`Inbound: ${stats.inbound_emails}`} 
                color="success" 
                variant="outlined" 
              />
              <Chip 
                label={`Outbound: ${stats.outbound_emails}`} 
                color="primary" 
                variant="outlined" 
              />
              {stats.unread_emails > 0 && (
                <Chip 
                  label={`Unread: ${stats.unread_emails}`} 
                  color="error" 
                  variant="outlined" 
                />
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Email List */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Email History
          </Typography>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : emails.length === 0 ? (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No email history found for this client.
            </Typography>
          ) : (
            <List>
              {emails.map((email, index) => (
                <React.Fragment key={email.id}>
                  <ListItem
                    button
                    onClick={() => handleEmailClick(email)}
                    sx={{
                      borderRadius: 1,
                      mb: 1,
                      backgroundColor: !email.read_status && email.direction === 'inbound' 
                        ? 'action.hover' 
                        : 'transparent'
                    }}
                  >
                    <ListItemIcon>
                      <Chip
                        icon={getDirectionIcon(email.direction)}
                        label={email.direction === 'inbound' ? 'Received' : 'Sent'}
                        color={getDirectionColor(email.direction) as any}
                        size="small"
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography 
                            variant="subtitle2" 
                            sx={{ 
                              fontWeight: !email.read_status && email.direction === 'inbound' ? 600 : 400 
                            }}
                          >
                            {email.subject || 'No Subject'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(email.sent_at)}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {email.direction === 'inbound' ? 'From' : 'To'}: {
                              email.direction === 'inbound' ? email.from_email : email.to_email
                            }
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {getEmailPreview(email.body_text)}
                          </Typography>
                        </Box>
                      }
                    />
                    {!email.read_status && email.direction === 'inbound' && (
                      <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: 'primary.main', ml: 1 }} />
                    )}
                  </ListItem>
                  {index < emails.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Compose Email Dialog */}
      <Dialog 
        open={composeOpen} 
        onClose={() => setComposeOpen(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            Compose Email to {client.first_name} {client.last_name}
            <IconButton onClick={() => setComposeOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            To: {client.primary_email}
          </Typography>
          
          <TextField
            autoFocus
            margin="dense"
            label="Subject"
            fullWidth
            variant="outlined"
            value={emailSubject}
            onChange={(e) => setEmailSubject(e.target.value)}
            sx={{ mb: 2 }}
          />
          
          <TextField
            margin="dense"
            label="Message"
            fullWidth
            multiline
            rows={8}
            variant="outlined"
            value={emailBody}
            onChange={(e) => setEmailBody(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setComposeOpen(false)} disabled={sending}>
            Cancel
          </Button>
          <Button 
            onClick={handleSendEmail} 
            variant="contained" 
            disabled={sending}
            startIcon={sending ? <CircularProgress size={20} /> : <SendIcon />}
          >
            {sending ? 'Sending...' : 'Send Email'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Email Detail Dialog */}
      <Dialog
        open={emailDetailOpen}
        onClose={() => setEmailDetailOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedEmail && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                {selectedEmail.subject || 'No Subject'}
                <IconButton onClick={() => setEmailDetailOpen(false)}>
                  <CloseIcon />
                </IconButton>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2"><strong>From:</strong> {selectedEmail.from_email}</Typography>
                <Typography variant="body2"><strong>To:</strong> {selectedEmail.to_email}</Typography>
                <Typography variant="body2"><strong>Date:</strong> {formatDate(selectedEmail.sent_at)}</Typography>
                <Chip
                  icon={getDirectionIcon(selectedEmail.direction)}
                  label={selectedEmail.direction === 'inbound' ? 'Received' : 'Sent'}
                  color={getDirectionColor(selectedEmail.direction) as any}
                  size="small"
                  sx={{ mt: 1 }}
                />
              </Box>
              <Divider sx={{ my: 2 }} />
              <Box>
                {selectedEmail.body_html ? (
                  <div dangerouslySetInnerHTML={{ __html: selectedEmail.body_html }} />
                ) : (
                  <Typography component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                    {selectedEmail.body_text}
                  </Typography>
                )}
              </Box>
            </DialogContent>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default EmailInterface;