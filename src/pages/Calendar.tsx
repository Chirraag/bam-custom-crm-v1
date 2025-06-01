import { useState } from 'react';
import { 
  Typography, 
  Box, 
  Card, 
  Grid,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  IconButton
} from '@mui/material';
import {
  Add as AddIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  Today as TodayIcon
} from '@mui/icons-material';
import Layout from '../components/Layout';

const Calendar = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [dialogOpen, setDialogOpen] = useState(false);

  const daysInMonth = (year: number, month: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const firstDayOfMonth = (year: number, month: number) => {
    return new Date(year, month, 1).getDay();
  };

  const handlePrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const renderCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const days = daysInMonth(year, month);
    const firstDay = firstDayOfMonth(year, month);
    
    const monthName = currentDate.toLocaleString('default', { month: 'long' });
    
    const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    
    // Create calendar grid
    const calendarDays = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      calendarDays.push(<Grid item xs={1.7} key={`empty-${i}`}></Grid>);
    }
    
    // Add cells for days of the month
    for (let day = 1; day <= days; day++) {
      const date = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayAppointments = appointments.filter(a => a.date === date);
      
      const isToday = 
        day === new Date().getDate() && 
        month === new Date().getMonth() && 
        year === new Date().getFullYear();
      
      calendarDays.push(
        <Grid item xs={1.7} key={day}>
          <Paper 
            elevation={0} 
            sx={{ 
              p: 1, 
              height: 120, 
              border: '1px solid rgba(0, 0, 0, 0.12)',
              borderRadius: 1,
              position: 'relative',
              bgcolor: isToday ? 'primary.light' : 'background.paper',
              opacity: isToday ? 0.9 : 1,
            }}
          >
            <Typography 
              variant="body2" 
              sx={{ 
                fontWeight: isToday ? 700 : 400,
                color: isToday ? 'white' : 'text.primary',
                mb: 1 
              }}
            >
              {day}
            </Typography>
            
            {dayAppointments.slice(0, 2).map((appointment, index) => (
              <Box 
                key={appointment.id}
                sx={{ 
                  p: 0.5, 
                  mb: 0.5, 
                  borderRadius: 0.5, 
                  fontSize: '0.75rem',
                  backgroundColor: 
                    appointment.type === 'Consultation' ? 'primary.light' : 
                    appointment.type === 'Review' ? 'secondary.light' : 
                    appointment.type === 'Document' ? 'info.light' : 
                    appointment.type === 'Court' ? 'error.light' : 
                    'success.light',
                  color: 'white',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}
              >
                {appointment.time} - {appointment.title}
              </Box>
            ))}
            
            {dayAppointments.length > 2 && (
              <Typography variant="caption" sx={{ color: isToday ? 'white' : 'text.secondary' }}>
                +{dayAppointments.length - 2} more
              </Typography>
            )}
          </Paper>
        </Grid>
      );
    }
    
    return (
      <Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" component="h2" fontWeight="500">
            {monthName} {year}
          </Typography>
          <Box>
            <IconButton onClick={handlePrevMonth}>
              <ChevronLeftIcon />
            </IconButton>
            <Button 
              variant="outlined" 
              size="small" 
              startIcon={<TodayIcon />} 
              onClick={handleToday}
              sx={{ mx: 1, textTransform: 'none' }}
            >
              Today
            </Button>
            <IconButton onClick={handleNextMonth}>
              <ChevronRightIcon />
            </IconButton>
          </Box>
        </Box>
        
        <Grid container spacing={1} sx={{ mb: 2 }}>
          {daysOfWeek.map(day => (
            <Grid item xs={1.7} key={day}>
              <Typography 
                variant="body2" 
                align="center" 
                sx={{ fontWeight: 500, color: 'text.secondary', mb: 1 }}
              >
                {day}
              </Typography>
            </Grid>
          ))}
        </Grid>
        
        <Grid container spacing={1}>
          {calendarDays}
        </Grid>
      </Box>
    );
  };

  return (
    <Layout>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" fontWeight="500" sx={{ mb: 1 }}>
          Calendar
        </Typography>
        <Typography color="text.secondary">
          Manage your appointments and schedule
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 3 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
          sx={{ textTransform: 'none' }}
        >
          New Appointment
        </Button>
      </Box>

      <Card elevation={0} sx={{ borderRadius: 2, border: '1px solid rgba(0, 0, 0, 0.12)', p: 3 }}>
        {renderCalendar()}
      </Card>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Appointment</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              label="Title"
              fullWidth
              margin="normal"
            />
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Date"
                  type="date"
                  fullWidth
                  margin="normal"
                  InputLabelProps={{
                    shrink: true,
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Time"
                  type="time"
                  fullWidth
                  margin="normal"
                  InputLabelProps={{
                    shrink: true,
                  }}
                />
              </Grid>
            </Grid>
            <FormControl fullWidth margin="normal">
              <InputLabel>Client</InputLabel>
              <Select label="Client">
                <MenuItem value="John Smith">John Smith</MenuItem>
                <MenuItem value="Emma Johnson">Emma Johnson</MenuItem>
                <MenuItem value="Michael Brown">Michael Brown</MenuItem>
                <MenuItem value="Sarah Wilson">Sarah Wilson</MenuItem>
                <MenuItem value="David Lee">David Lee</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel>Appointment Type</InputLabel>
              <Select label="Appointment Type">
                <MenuItem value="Consultation">Consultation</MenuItem>
                <MenuItem value="Review">Case Review</MenuItem>
                <MenuItem value="Document">Document Signing</MenuItem>
                <MenuItem value="Court">Court Hearing</MenuItem>
                <MenuItem value="Meeting">Client Meeting</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Notes"
              fullWidth
              margin="normal"
              multiline
              rows={3}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => setDialogOpen(false)}>Save</Button>
        </DialogActions>
      </Dialog>
    </Layout>
  );
};

export default Calendar;