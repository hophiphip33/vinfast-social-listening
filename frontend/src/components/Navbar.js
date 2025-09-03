/**
 * Top Navigation Bar Component
 */

import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Chip,
  Tooltip
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications,
  Settings,
  Refresh
} from '@mui/icons-material';

// Hooks
import { useQuery } from '@tanstack/react-query';
import { fetchRealTimeMetrics } from '../services/api';

const Navbar = ({ onMenuClick, sidebarOpen }) => {
  // Get real-time metrics for status display
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['real-time-metrics'],
    queryFn: fetchRealTimeMetrics,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const renderStatusChip = () => {
    if (isLoading) {
      return <Chip label="Đang tải..." size="small" color="default" />;
    }
    
    if (metrics?.data?.status === 'active') {
      return (
        <Chip 
          label={`${metrics.data.last_24h?.total_posts || 0} bài viết (24h)`}
          size="small" 
          color="success"
          sx={{ fontWeight: 500 }}
        />
      );
    }
    
    return <Chip label="Không hoạt động" size="small" color="error" />;
  };

  return (
    <AppBar 
      position="static" 
      elevation={1}
      sx={{ 
        backgroundColor: '#fff', 
        borderBottom: '1px solid #e0e0e0',
        color: '#333'
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between', minHeight: '70px' }}>
        {/* Left section */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {!sidebarOpen && (
            <IconButton
              edge="start"
              color="inherit"
              onClick={onMenuClick}
              sx={{ marginRight: 1 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          
          <Typography 
            variant="h6" 
            component="div"
            sx={{ 
              fontWeight: 600,
              background: 'linear-gradient(45deg, #1976d2, #1565c0)',
              backgroundClip: 'text',
              textFillColor: 'transparent',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}
          >
            VinFast Social Listening
          </Typography>
        </Box>
        
        {/* Center section - Status */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {renderStatusChip()}
        </Box>
        
        {/* Right section - Actions */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Làm mới dữ liệu">
            <IconButton color="inherit" size="small">
              <Refresh />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Thông báo">
            <IconButton color="inherit" size="small">
              <Notifications />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Cài đặt">
            <IconButton color="inherit" size="small">
              <Settings />
            </IconButton>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
