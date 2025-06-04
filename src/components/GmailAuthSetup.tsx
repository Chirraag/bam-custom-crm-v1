import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Stepper,
  Step,
  StepLabel,
  Alert,
  CircularProgress,
  Link
} from '@mui/material';
import { Email as EmailIcon } from '@mui/icons-material';
import { api } from '../utils/api';

interface GmailAuthSetupProps {
  open: boolean;
  onClose: () => void;
  onComplete: () => void;
}

const GmailAuthSetup: React.FC<GmailAuthSetupProps> = ({ open, onClose, onComplete }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [authUrl, setAuthUrl] = useState('');
  const [authCode, setAuthCode] = useState('');
  const [error, setError] = useState('');

  const steps = [
    'Setup Gmail Credentials',
    'Authorize Access',
    'Complete Setup'
  ];

  // Sample credentials structure
  const sampleCredentials = {
    "web": {
      "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
      "client_secret": "YOUR_CLIENT_SECRET",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
    }
  };

  const [credentials, setCredentials] = useState(JSON.stringify(sampleCredentials, null, 2));

  const handleNext = async () => {
    setError('');
    setLoading(true);

    try {
      if (activeStep === 0) {
        // Parse and validate credentials
        const credentialsJson = JSON.parse(credentials);
        
        // Setup Gmail auth and get auth URL
        const response = await api.post('/api/emails/setup-gmail-auth', {
          credentials: credentialsJson
        });
        
        setAuthUrl(response.auth_url);
        setActiveStep(1);
      } else if (activeStep === 1) {
        if (!authCode.trim()) {
          setError('Please enter the authorization code');
          return;
        }

        // Complete Gmail authentication
        await api.post('/api/emails/complete-gmail-auth', {
          auth_code: authCode
        });
        
        setActiveStep(2);
      } else if (activeStep === 2) {
        // Setup complete
        onComplete();
        onClose();
        handleReset();
      }
    } catch (error: any) {
      console.error('Gmail auth error:', error);
      setError(error.response?.data?.detail || 'An error occurred during setup');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setActiveStep(activeStep - 1);
    setError('');
  };

  const handleReset = () => {
    setActiveStep(0);
    setAuthUrl('');
    setAuthCode('');
    setError('');
    setCredentials(JSON.stringify(sampleCredentials, null, 2));
  };

  const handleClose = () => {
    onClose();
    handleReset();
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Gmail API Credentials Setup
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              To enable email integration, you need to set up Gmail API credentials from Google Cloud Console.
            </Typography>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Instructions:</strong>
                <br />1. Go to Google Cloud Console
                <br />2. Create a project or select existing one
                <br />3. Enable Gmail API
                <br />4. Create OAuth 2.0 credentials (Desktop Application)
                <br />5. Download the credentials JSON and paste it below
              </Typography>
            </Alert>

            <TextField
              fullWidth
              multiline
              rows={12}
              label="Gmail API Credentials (JSON)"
              value={credentials}
              onChange={(e) => setCredentials(e.target.value)}
              variant="outlined"
              sx={{ fontFamily: 'monospace' }}
            />
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Authorize Gmail Access
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Click the link below to authorize access to your Gmail account, then paste the authorization code here.
            </Typography>

            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Important:</strong> Make sure you're signed into the Gmail account you want to use for sending emails.
              </Typography>
            </Alert>

            <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Authorization URL:
              </Typography>
              <Link 
                href={authUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                sx={{ wordBreak: 'break-all' }}
              >
                {authUrl}
              </Link>
            </Box>

            <TextField
              fullWidth
              label="Authorization Code"
              value={authCode}
              onChange={(e) => setAuthCode(e.target.value)}
              variant="outlined"
              placeholder="Paste the authorization code here"
            />
          </Box>
        );

      case 2:
        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <EmailIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Gmail Integration Complete!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Your Gmail account has been successfully connected. You can now send and receive emails through the CRM.
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Gmail Integration Setup
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <Stepper activeStep={activeStep}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {renderStepContent()}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>
          Cancel
        </Button>
        
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={loading}>
            Back
          </Button>
        )}
        
        <Button
          variant="contained"
          onClick={handleNext}
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Processing...' : activeStep === steps.length - 1 ? 'Finish' : 'Next'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default GmailAuthSetup;