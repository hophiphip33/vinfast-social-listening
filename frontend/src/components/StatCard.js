/**
 * Statistics Card Component
 * Displays key metrics with icons and styling
 */

import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  useTheme
} from '@mui/material';

const StatCard = ({ title, value, icon, color, subtitle, trend }) => {
  const theme = useTheme();

  return (
    <Card 
      className="interactive-card"
      sx={{ 
        height: '100%',
        background: `linear-gradient(135deg, ${color}10, ${color}05)`,
        border: `1px solid ${color}20`
      }}
    >
      <CardContent sx={{ position: 'relative', pb: 2 }}>
        {/* Icon */}
        <Box
          sx={{
            position: 'absolute',
            top: 16,
            right: 16,
            color: color,
            opacity: 0.8,
            fontSize: 24
          }}
        >
          {icon}
        </Box>
        
        {/* Title */}
        <Typography 
          variant="body2" 
          color="text.secondary" 
          fontWeight={500}
          sx={{ mb: 1 }}
        >
          {title}
        </Typography>
        
        {/* Main value */}
        <Typography 
          variant="h4" 
          fontWeight={700}
          sx={{ 
            color: color,
            mb: 0.5,
            fontFamily: '"Inter", sans-serif'
          }}
        >
          {typeof value === 'number' ? formatNumber(value) : value}
        </Typography>
        
        {/* Subtitle */}
        {subtitle && (
          <Typography 
            variant="caption" 
            color="text.secondary"
            sx={{ display: 'block', mt: 1 }}
          >
            {subtitle}
          </Typography>
        )}
        
        {/* Trend indicator */}
        {trend && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
            <Typography 
              variant="caption" 
              sx={{ 
                color: trend > 0 ? theme.palette.success.main : theme.palette.error.main,
                fontWeight: 500
              }}
            >
              {trend > 0 ? '+' : ''}{trend}% so với trước
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default StatCard;
