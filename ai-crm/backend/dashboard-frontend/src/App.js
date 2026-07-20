import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Dashboard from './components/Dashboard';
import EmployeePortal from './components/EmployeePortal';
import AttendanceSystem from './components/AttendanceSystem';
import Navigation from './components/Navigation';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1f77b4',
    },
    secondary: {
      main: '#ff9800',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/employee" element={<EmployeePortal />} />
          <Route path="/attendance" element={<AttendanceSystem />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
