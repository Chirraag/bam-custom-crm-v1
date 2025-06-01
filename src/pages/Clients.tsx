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
import { api } from '../utils/api';

const Clients = () => {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

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
        await api.get('/');
      } else {
        await api.put(`/api/clients/${selectedClient?.id}`, clientData);
      }
      fetchClients();
      setDialogOpen(false);
    } catch (error) {
      console.error('Error saving client:', error);
    }
  };

  const handleDeleteConfirm = async () => {
    if (selectedClient) {
      try {
        await api.delete(`/api/clients/${selectedClient.id}`);
        fetchClients();
        setDeleteDialogOpen(false);
        setSelectedClient(null);
      } catch (error) {
        console.error('Error deleting client:', error);
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
    // Navigate to client details page
    console.log('View client:', selectedClient);
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
                            bgcolor: 
                              client.case_status === 'Active' ? 'success.light' : 
                              client.case_status === 'Pending' ? 'warning.light' : 
                              'error.light',
                            color: 
                              client.case_status === 'Active' ? 'success.dark' : 
                              client.case_status === 'Pending' ? 'warning.dark' : 
                              'error.dark',
                            fontWeight: 500,
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
    </Layout>
  );
};

export default Clients;