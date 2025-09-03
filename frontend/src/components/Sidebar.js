/**
 * Sidebar Navigation Component
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Typography,
  Box,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Dashboard,
  Analytics,
  CloudDownload,
  Forum,
  Settings,
  TrendingUp,
  Assessment,
  DataUsage,
  MenuOpen
} from '@mui/icons-material';

const Sidebar = ({ open, onToggle }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Navigation items
  const navigationItems = [
    {
      text: 'Tổng quan',
      icon: <Dashboard />,
      path: '/',
      description: 'Dashboard tổng quan'
    },
    {
      text: 'Phân tích',
      icon: <Analytics />,
      path: '/analytics',
      description: 'Phân tích chi tiết'
    },
    {
      text: 'Thu thập dữ liệu',
      icon: <CloudDownload />,
      path: '/collection',
      description: 'Quản lý thu thập dữ liệu'
    },
    {
      text: 'Khám phá bài viết',
      icon: <Forum />,
      path: '/posts',
      description: 'Duyệt qua các bài viết'
    }
  ];

  const utilityItems = [
    {
      text: 'Cài đặt',
      icon: <Settings />,
      path: '/settings',
      description: 'Cấu hình hệ thống'
    }
  ];

  const handleNavigation = (path) => {
    navigate(path);
  };

  const isActivePath = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const renderNavItem = (item, isActive) => (
    <ListItem key={item.path} disablePadding>
      <Tooltip title={open ? '' : item.text} placement="right">
        <ListItemButton
          onClick={() => handleNavigation(item.path)}
          selected={isActive}
          sx={{
            borderRadius: 2,
            margin: '4px 8px',
            minHeight: 48,
            backgroundColor: isActive ? 'primary.main' : 'transparent',
            color: isActive ? 'white' : 'text.primary',
            '&:hover': {
              backgroundColor: isActive ? 'primary.dark' : 'action.hover',
            },
            '&.Mui-selected': {
              backgroundColor: 'primary.main',
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
            },
          }}
        >
          <ListItemIcon
            sx={{
              minWidth: open ? 40 : 0,
              color: isActive ? 'white' : 'text.primary',
              justifyContent: 'center'
            }}
          >
            {item.icon}
          </ListItemIcon>
          
          {open && (
            <ListItemText
              primary={item.text}
              secondary={item.description}
              primaryTypographyProps={{
                fontSize: '14px',
                fontWeight: isActive ? 600 : 500,
              }}
              secondaryTypographyProps={{
                fontSize: '12px',
                color: isActive ? 'rgba(255,255,255,0.7)' : 'text.secondary',
              }}
            />
          )}
        </ListItemButton>
      </Tooltip>
    </ListItem>
  );

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: open ? 280 : 80,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: open ? 280 : 80,
          boxSizing: 'border-box',
          borderRight: '1px solid #e0e0e0',
          backgroundColor: '#fff',
          transition: 'width 0.3s ease',
          overflowX: 'hidden'
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: open ? 'space-between' : 'center',
          padding: '16px',
          minHeight: '70px',
          borderBottom: '1px solid #e0e0e0'
        }}
      >
        {open && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUp sx={{ color: 'primary.main', fontSize: 28 }} />
            <Typography variant="h6" sx={{ fontWeight: 700, fontSize: '16px' }}>
              VinFast Insights
            </Typography>
          </Box>
        )}
        
        <IconButton onClick={onToggle} size="small">
          <MenuOpen sx={{ 
            transform: open ? 'rotate(0deg)' : 'rotate(180deg)',
            transition: 'transform 0.3s ease'
          }} />
        </IconButton>
      </Box>

      {/* Navigation items */}
      <Box sx={{ flexGrow: 1, paddingTop: 2 }}>
        <List>
          {navigationItems.map((item) =>
            renderNavItem(item, isActivePath(item.path))
          )}
        </List>
        
        <Divider sx={{ margin: '16px 8px' }} />
        
        <List>
          {utilityItems.map((item) =>
            renderNavItem(item, isActivePath(item.path))
          )}
        </List>
      </Box>

      {/* Footer info */}
      {open && (
        <Box sx={{ padding: 2, borderTop: '1px solid #e0e0e0' }}>
          <Typography variant="caption" color="text.secondary" align="center">
            Graduation Project 2024
          </Typography>
          <Typography variant="caption" color="text.secondary" align="center" display="block">
            Vietnamese Social Listening
          </Typography>
        </Box>
      )}
    </Drawer>
  );
};

export default Sidebar;
