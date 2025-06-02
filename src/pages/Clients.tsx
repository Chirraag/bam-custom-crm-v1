import { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Card, 
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  Avatar,
  Menu,
  MenuItem,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import Layout from '../components/Layout';
import { Client } from '../types/client';
import ClientDialog from '../components/ClientDialog';
import ClientDetailsDialog from '../components/ClientDetailsDialog';
import { api } from '../utils/api';
import { useAuth } from '../context/AuthContext';

const Clients = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await api.get('/api/clients');
      setClients(response);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching clients:', error);
      setLoading(false);
    }
  };

  const handleCreateClient = () => {
    setDialogMode('create');
    setSelectedClient(null);
    setDialogOpen(true);
  };

  const handleSaveClient = async (clientData: Partial<Client>) => {
    try {
      if (dialogMode === 'create') {
        const clientWithCreator = {
          ...clientData,
          created_by: user?.id
        };
        await api.post('/api/clients', clientWithCreator);
        console.log('Client created successfully');
      } else {
        await api.put(`/api/clients/${selectedClient?.id}`, clientData);
        console.log('Client updated successfully');
      }
      await fetchClients();
      setDialogOpen(false);
    } catch (error) {
      console.error('Error saving client:', error);
      alert('Failed to save client. Please try again.');
    }
  };

  const handleDeleteConfirm = async () => {
    if (selectedClient) {
      try {
        await api.delete(`/api/clients/${selectedClient.id}`);
        setDeleteDialogOpen(false);
        setSelectedClient(null);
        await fetchClients(); // Refresh the client list after successful deletion
      } catch (error) {
        console.error('Error deleting client:', error);
        // Since 204 is a success status, we still want to refresh and close
        setDeleteDialogOpen(false);
        setSelectedClient(null);
        await fetchClients();
      }
    }
  };

  const handleOpenMenu = (event: React.MouseEvent<HTMLElement>, client: Client) => {
    setAnchorEl(event.currentTarget);
    setSelectedClient(client);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
  };

  const handleViewClient = () => {
    handleCloseMenu();
    setDetailsDialogOpen(true);
  };

  const handleEditClient = () => {
    setDialogMode('edit');
    setDialogOpen(true);
    handleCloseMenu();
  };

  const handleDeleteClient = () => {
    handleCloseMenu();
    setDeleteDialogOpen(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Active':
        return {
          bg: '#E8F5E9',
          text: '#2E7D32'
        };
      case 'Pending':
        return {
          bg: '#FFF3E0',
          text: '#E65100'
        };
      case 'Closed':
        return {
          bg: '#FFEBEE',
          text: '#C62828'
        };
      default:
        return {
          bg: '#E8F5E9',
          text: '#2E7D32'
        };
    }
  };

  const filteredClients = clients.filter(client => 
    client.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.primary_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.primary_phone?.includes(searchTerm) ||
    client.case_type?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Layout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="500" sx={{ mb: 1 }}>
          Clients
        </Typography>
        <Typography color="text.secondary">
          Manage your client information and cases
        </Typography>
      </Box>

      <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid rgba(0, 0, 0, 0.12)' }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <TextField
              placeholder="Search clients..."
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              sx={{ width: 300 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                ),
              }}
            />
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateClient}
              sx={{ textTransform: 'none' }}
            >
              Add New Client
            </Button>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer component={Paper} elevation={0}>
              <Table sx={{ minWidth: 650 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Primary Email</TableCell>
                    <TableCell>Primary Phone</TableCell>
                    <TableCell>Case Type</TableCell>
                    <TableCell>Case Status</TableCell>
                    <TableCell>Created At</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredClients.map((client) => (
                    <TableRow
                      key={client.id}
                      sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                    >
                      <TableCell component="th" scope="row">
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar sx={{ bgcolor: 'primary.main', width: 36, height: 36, mr: 2 }}>
                            {client.first_name?.charAt(0)}
                          </Avatar>
                          {`${client.first_name} ${client.last_name}`}
                        </Box>
                      </TableCell>
                      <TableCell>{client.primary_email}</TableCell>
                      <TableCell>{client.primary_phone}</TableCell>
                      <TableCell>{client.case_type}</TableCell>
                      <TableCell>
                        <Chip
                          label={client.case_status}
                          size="small"
                          sx={{
                            bgcolor: getStatusColor(client.case_status || '').bg,
                            color: getStatusColor(client.case_status || '').text,
                            fontWeight: 500,
                            border: 'none',
                            '& .MuiChip-label': {
                              px: 2,
                            },
                          }}
                        />
                      </TableCell>
                      <TableCell>{new Date(client.created_at).toLocaleDateString()}</TableCell>
                      <TableCell align="right">
                        <IconButton
                          aria-label="more"
                          onClick={(event) => handleOpenMenu(event, client)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={handleViewClient}>
          <ListItemIcon>
            <VisibilityIcon fontSize="small" />
          </ListItemIcon>
          View Details
        </MenuItem>
        <MenuItem onClick={handleEditClient}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          Edit
        </MenuItem>
        <MenuItem onClick={handleDeleteClient} sx={{ color: 'error.main' }}>
          <ListItemIcon sx={{ color: 'error.main' }}>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          Delete
        </MenuItem>
      </Menu>

      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Client</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete {selectedClient?.first_name} {selectedClient?.last_name}? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error">Delete</Button>
        </DialogActions>
      </Dialog>
      
      <ClientDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={handleSaveClient}
        client={selectedClient}
        mode={dialogMode}
      />

      <ClientDetailsDialog
        open={detailsDialogOpen}
        onClose={() => setDetailsDialogOpen(false)}
        client={selectedClient}
      />
    </Layout>
  );
};

export default Clients;