import { useState, useEffect } from 'react';
import { 
  Box,
  Typography,
  Button,
  IconButton,
  Paper,
  Grid,
  Divider,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tooltip,
  useTheme
} from '@mui/material';
import {
  ChevronLeft,
  ChevronRight,
  Add as AddIcon,
  AccessTime,
  LocationOn,
  People,
  MoreVert
} from '@mui/icons-material';
import Layout from '../components/Layout';
import { format, addMonths, subMonths, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, parseISO } from 'date-fns';

const Calendar = () => {
  const theme = useTheme();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [events, setEvents] = useState([
    {
      id: 1,
      title: 'Client Consultation',
      startTime: '10:00 AM',
      endTime: '11:00 AM',
      location: 'Conference Room A',
      attendees: ['Robert Johnson', 'Sarah Davis'],
      color: theme.palette.primary.main
    },
    {
      id: 2,
      title: 'Document Review Deadline',
      startTime: '12:00 PM',
      location: '',
      attendees: [],
      color: theme.palette.error.main
    },
    {
      id: 3,
      title: 'Team Strategy Meeting',
      startTime: '2:00 PM',
      endTime: '3:30 PM',
      location: "Partner's Room",
      attendees: ['Legal Team', 'Associates'],
      color: theme.palette.success.main
    }
  ]);

  const handlePrevMonth = () => {
    setCurrentDate(subMonths(currentDate, 1));
  };

  const handleNextMonth = () => {
    setCurrentDate(addMonths(currentDate, 1));
  };

  const handleToday = () => {
    setCurrentDate(new Date());
    setSelectedDate(new Date());
  };

  const renderCalendar = () => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const monthDays = eachDayOfInterval({ start: monthStart, end: monthEnd });
    
    const monthName = format(currentDate, 'MMMM yyyy');
    const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    
    return (
      <Box>
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mb: 3,
          px: 2
        }}>
          <Typography variant="h5" component="h2" fontWeight="500">
            {monthName}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Button 
              variant="outlined" 
              size="small"
              onClick={handleToday}
              sx={{ borderRadius: '20px' }}
            >
              Today
            </Button>
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <IconButton 
                size="small" 
                onClick={handlePrevMonth}
                sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: '8px' }}
              >
                <ChevronLeft />
              </IconButton>
              <IconButton 
                size="small" 
                onClick={handleNextMonth}
                sx={{ border: `1px solid ${theme.palette.divider}`, borderRadius: '8px' }}
              >
                <ChevronRight />
              </IconButton>
            </Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              sx={{ 
                bgcolor: '#F97316',
                '&:hover': {
                  bgcolor: '#EA580C'
                },
                borderRadius: '20px',
                ml: 1
              }}
            >
              Event
            </Button>
          </Box>
        </Box>
        
        <Grid container spacing={0}>
          {daysOfWeek.map(day => (
            <Grid item xs key={day} sx={{ borderBottom: `1px solid ${theme.palette.divider}`, borderRight: `1px solid ${theme.palette.divider}` }}>
              <Typography 
                variant="subtitle2" 
                align="center" 
                sx={{ py: 1, color: 'text.secondary', fontWeight: 500 }}
              >
                {day}
              </Typography>
            </Grid>
          ))}
          
          {monthDays.map((day, index) => {
            const dayEvents = events.filter(event => 
              isSameDay(parseISO(event.startTime), day)
            );
            
            return (
              <Grid 
                item 
                xs 
                key={day.toISOString()}
                sx={{ 
                  height: 120,
                  p: 1,
                  borderBottom: `1px solid ${theme.palette.divider}`,
                  borderRight: `1px solid ${theme.palette.divider}`,
                  bgcolor: isSameDay(day, selectedDate) ? 'action.selected' : 'background.paper',
                  cursor: 'pointer',
                  '&:hover': {
                    bgcolor: 'action.hover'
                  }
                }}
                onClick={() => setSelectedDate(day)}
              >
                <Typography 
                  variant="body2"
                  sx={{ 
                    fontWeight: isSameDay(day, new Date()) ? 700 : 400,
                    color: !isSameMonth(day, currentDate) ? 'text.disabled' : 'text.primary',
                  }}
                >
                  {format(day, 'd')}
                </Typography>
                
                {dayEvents.map(event => (
                  <Box
                    key={event.id}
                    sx={{
                      mt: 0.5,
                      p: 0.5,
                      borderRadius: '4px',
                      bgcolor: event.color,
                      color: 'white',
                      fontSize: '0.75rem',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}
                  >
                    {event.title}
                  </Box>
                ))}
              </Grid>
            );
          })}
        </Grid>
      </Box>
    );
  };

  return (
    <Layout>
      <Grid container spacing={3}>
        <Grid item xs={12} md={9}>
          <Card elevation={0} sx={{ borderRadius: 2, border: `1px solid ${theme.palette.divider}` }}>
            {renderCalendar()}
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card elevation={0} sx={{ borderRadius: 2, border: `1px solid ${theme.palette.divider}` }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                {format(selectedDate, 'EEEE, MMMM d, yyyy')}
              </Typography>
              
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="subtitle1" color="text.secondary" fontWeight={500}>
                  SCHEDULE
                </Typography>
                <Button
                  startIcon={<AddIcon />}
                  sx={{ color: '#F97316' }}
                >
                  Add Event
                </Button>
              </Box>
              
              <List>
                {events.map(event => (
                  <ListItem
                    key={event.id}
                    sx={{
                      borderLeft: `4px solid ${event.color}`,
                      bgcolor: `${event.color}10`,
                      borderRadius: 1,
                      mb: 1,
                      py: 2
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="subtitle2" fontWeight={500}>
                            {event.title}
                          </Typography>
                          <IconButton size="small">
                            <MoreVert fontSize="small" />
                          </IconButton>
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 1 }}>
                          {event.startTime && (
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                              <AccessTime fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                              <Typography variant="body2" color="text.secondary">
                                {event.startTime}{event.endTime && ` - ${event.endTime}`}
                              </Typography>
                            </Box>
                          )}
                          
                          {event.location && (
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                              <LocationOn fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                              <Typography variant="body2" color="text.secondary">
                                {event.location}
                              </Typography>
                            </Box>
                          )}
                          
                          {event.attendees && event.attendees.length > 0 && (
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <People fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                              <Typography variant="body2" color="text.secondary">
                                {event.attendees.join(', ')}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Layout>
  );
};

export default Calendar;