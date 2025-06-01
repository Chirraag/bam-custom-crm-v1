import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Typography,
  Divider,
} from '@mui/material';
import { Client } from '../types/client';

interface ClientDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (client: Partial<Client>) => void;
  client?: Client;
  mode: 'create' | 'edit';
}

const ClientDialog = ({ open, onClose, onSave, client, mode }: ClientDialogProps) => {
  const [formData, setFormData] = useState<Partial<Client>>({});

  useEffect(() => {
    if (client && mode === 'edit') {
      setFormData(client);
    } else {
      setFormData({});
    }
  }, [client, mode]);

  const handleChange = (field: keyof Client) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleSubmit = () => {
    onSave(formData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {mode === 'create' ? 'Add New Client' : 'Edit Client'}
      </DialogTitle>
      <DialogContent dividers>
        <Grid container spacing={3}>
          {/* Personal Information */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" fontWeight={500} gutterBottom>
              Personal Information
            </Typography>
          </Grid>
          <Grid item xs={12} sm={2}>
            <TextField
              select
              fullWidth
              label="Prefix"
              value={formData.name_prefix || ''}
              onChange={handleChange('name_prefix')}
            >
              <MenuItem value="Mr.">Mr.</MenuItem>
              <MenuItem value="Mrs.">Mrs.</MenuItem>
              <MenuItem value="Ms.">Ms.</MenuItem>
              <MenuItem value="Dr.">Dr.</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              required
              fullWidth
              label="First Name"
              value={formData.first_name || ''}
              onChange={handleChange('first_name')}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="Middle Name"
              value={formData.middle_name || ''}
              onChange={handleChange('middle_name')}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              required
              fullWidth
              label="Last Name"
              value={formData.last_name || ''}
              onChange={handleChange('last_name')}
            />
          </Grid>

          {/* Contact Information */}
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight={500} gutterBottom>
              Contact Information
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              required
              fullWidth
              label="Primary Email"
              type="email"
              value={formData.primary_email || ''}
              onChange={handleChange('primary_email')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Alternate Email"
              type="email"
              value={formData.alternate_email || ''}
              onChange={handleChange('alternate_email')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              required
              fullWidth
              label="Primary Phone"
              value={formData.primary_phone || ''}
              onChange={handleChange('primary_phone')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Mobile Phone"
              value={formData.mobile_phone || ''}
              onChange={handleChange('mobile_phone')}
            />
          </Grid>

          {/* Address */}
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight={500} gutterBottom>
              Address
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Address Line 1"
              value={formData.address_line1 || ''}
              onChange={handleChange('address_line1')}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Address Line 2"
              value={formData.address_line2 || ''}
              onChange={handleChange('address_line2')}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="City"
              value={formData.city || ''}
              onChange={handleChange('city')}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="State"
              value={formData.state || ''}
              onChange={handleChange('state')}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="ZIP Code"
              value={formData.zip_code || ''}
              onChange={handleChange('zip_code')}
            />
          </Grid>

          {/* Case Information */}
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" fontWeight={500} gutterBottom>
              Case Information
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              select
              fullWidth
              label="Case Type"
              value={formData.case_type || ''}
              onChange={handleChange('case_type')}
            >
              <MenuItem value="Corporate">Corporate</MenuItem>
              <MenuItem value="Criminal">Criminal</MenuItem>
              <MenuItem value="Family">Family</MenuItem>
              <MenuItem value="Immigration">Immigration</MenuItem>
              <MenuItem value="Real Estate">Real Estate</MenuItem>
              <MenuItem value="Tax">Tax</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              select
              fullWidth
              label="Case Status"
              value={formData.case_status || ''}
              onChange={handleChange('case_status')}
            >
              <MenuItem value="Active">Active</MenuItem>
              <MenuItem value="Pending">Pending</MenuItem>
              <MenuItem value="Closed">Closed</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Case Date"
              type="date"
              value={formData.case_date || ''}
              onChange={handleChange('case_date')}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Date of Injury"
              type="date"
              value={formData.date_of_injury || ''}
              onChange={handleChange('date_of_injury')}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={handleSubmit}>
          {mode === 'create' ? 'Create Client' : 'Save Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ClientDialog;