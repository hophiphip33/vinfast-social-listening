/**
 * Main App component for VinFast Social Listening Dashboard
 */

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';

// Components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import DataCollection from './pages/DataCollection';
import PostsExplorer from './pages/PostsExplorer';
import Settings from './pages/Settings';

// Hooks and utilities
import { useLocalStorage } from './hooks/useLocalStorage';

function App() {
  const [sidebarOpen, setSidebarOpen] = useLocalStorage('sidebarOpen', true);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <Sidebar 
        open={sidebarOpen} 
        onToggle={toggleSidebar}
      />
      
      {/* Main content area */}
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          display: 'flex', 
          flexDirection: 'column',
          marginLeft: sidebarOpen ? '280px' : '80px',
          transition: 'margin-left 0.3s ease',
          minHeight: '100vh'
        }}
      >
        {/* Top navigation */}
        <Navbar 
          onMenuClick={toggleSidebar}
          sidebarOpen={sidebarOpen}
        />
        
        {/* Page content */}
        <Box sx={{ flex: 1, padding: 0, backgroundColor: '#f5f5f5' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/collection" element={<DataCollection />} />
            <Route path="/posts" element={<PostsExplorer />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Box>
      </Box>
    </Box>
  );
}

export default App;
