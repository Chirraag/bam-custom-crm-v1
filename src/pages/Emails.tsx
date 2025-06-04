import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Button,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton
} from '@mui/material';
import {
  Email as EmailIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  Sync as SyncIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import Layout from '../components/Layout';
import GmailAuthSetup from '../components/GmailAuthSetup';
import { api } from '../utils/api';

interface SyncStatus {
  last_sync: {
    last_sync_at: string;
    sync_errors?: any;
  } | null;
}

const Emails: React.FC = () => {
  const [authSetupOpen, setAuthSetupOpen] = useState(false);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [authConfigured, setAuthConfigured] = useState(false);

  useEffect(() => {
    fetchSyncStatus();
  }, []);

  const fetchSyncStatus = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/emails/sync-status');
      setSyncStatus(response);
      
      // Check if auth is configured by seeing if we have sync status
      setAuthConfigured(!!response.last_sync);
    } catch (error) {
      console.error('Error fetching sync status:', error);
      setAuthConfigured(false);
    } finally {
      setLoading(false);
    }
  };

  const handleManualSync = async () => {
    setSyncing(true);
    try {
      await api.post('/api/emails/sync');
      await fetchSyncStatus();
      alert('Email sync completed successfully!');
    } catch (error) {
      console.error('Error during manual sync:', error);
      alert('Email sync failed. Please check your Gmail connection.');
    } finally {
      setSyncing(false);
    }
  };

  const handleAuthSetupComplete = () => {
    setAuthConfigured(true);
    fetchSyncStatus();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Layout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="500" sx={{ mb: 1 }}>
          Email Management
        </Typography>
        <Typography color="text.secondary">
          Configure and monitor email integration with Gmail
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Gmail Integration Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  Gmail Integration
                </Typography>
                <IconButton onClick={() => setAuthSetupOpen(true)}>
                  <SettingsIcon />
                </IconButton>
              </Box>

              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <Box>
                  {authConfigured ? (
                    <Alert severity="success" sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <CheckCircleIcon sx={{ mr: 1 }} />
                        Gmail integration is configured and active
                      </Box>
                    </Alert>
                  ) : (
                    <Alert severity="warning" sx={{ mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <ErrorIcon sx={{ mr: 1 }} />
                        Gmail integration not configured
                      </Box>
                    </Alert>
                  )}

                  <Button
                    variant="contained"
                    startIcon={<SettingsIcon />}
                    onClick={() => setAuthSetupOpen(true)}
                    sx={{ mb: 2 }}
                  >
                    {authConfigured ? 'Reconfigure Gmail' : 'Setup Gmail Integration'}
                  </Button>

                  {authConfigured && (
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Features enabled:
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>
                            <EmailIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary="Send emails to clients" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <SyncIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary="Automatic email synchronization" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            <CheckCircleIcon fontSize="small" />
                          </ListItemIcon>
                          <ListItemText primary="Email history tracking" />
                        </ListItem>
                      </List>
                    </Box>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sync Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  Sync Status
                </Typography>
                <IconButton onClick={handleManualSync} disabled={syncing || !authConfigured}>
                  <RefreshIcon />
                </IconButton>
              </Box>

              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                  <CircularProgress />
                </Box>
              ) : syncStatus?.last_sync ? (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Chip
                      icon={<CheckCircleIcon />}
                      label="Active"
                      color="success"
                      size="small"
                    />
                  </Box>

                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Last Sync:
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formatDate(syncStatus.last_sync.last_sync_at)}
                  </Typography>

                  <Button
                    variant="outlined"
                    startIcon={syncing ? <CircularProgress size={20} /> : <RefreshIcon />}
                    onClick={handleManualSync}
                    disabled={syncing || !authConfigured}
                    sx={{ mt: 2 }}
                  >
                    {syncing ? 'Syncing...' : 'Manual Sync'}
                  </Button>

                  {syncStatus.last_sync.sync_errors && (
                    <Alert severity="error" sx={{ mt: 2 }}>
                      <Typography variant="body2">
                        Last sync had errors. Check logs for details.
                      </Typography>
                    </Alert>
                  )}
                </Box>
              ) : (
                <Alert severity="info">
                  <Typography variant="body2">
                    {authConfigured 
                      ? 'No sync history available yet. Sync will start automatically.'
                      : 'Configure Gmail integration to enable email synchronization.'
                    }
                  </Typography>
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Email System Information */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" component="h2" gutterBottom>
                How Email Integration Works
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Inbound Emails
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    The system automatically monitors your Gmail account and detects emails from clients. 
                    When an email is received from a client's primary email address, it's automatically 
                    linked to their profile and stored in the CRM.
                  </Typography>

                  <Typography variant="subtitle1" gutterBottom>
                    Outbound Emails
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    You can send emails directly to clients from their profile page. All sent emails 
                    are automatically tracked and stored in the client's communication history.
                  </Typography>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Synchronization
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Email synchronization runs automatically every 10 minutes. You can also trigger 
                    a manual sync at any time. Only emails related to clients in your CRM are processed.
                  </Typography>

                  <Typography variant="subtitle1" gutterBottom>
                    Privacy & Security
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Your Gmail credentials are securely stored and encrypted. The system only accesses 
                    emails necessary for client communication and does not store personal emails.
                  </Typography>
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              <Alert severity="info">
                <Typography variant="body2">
                  <strong>Note:</strong> Make sure your clients use their primary email address 
                  when communicating with you. Emails from different addresses won't be automatically 
                  linked to client profiles.
                </Typography>
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <GmailAuthSetup
        open={authSetupOpen}
        onClose={() => setAuthSetupOpen(false)}
        onComplete={handleAuthSetupComplete}
      />
    </Layout>
  );
};

export default Emails;