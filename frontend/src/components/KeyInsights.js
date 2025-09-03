/**
 * Key Insights Component
 * Displays AI-generated insights about VinFast sentiment analysis
 */

import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Alert
} from '@mui/material';
import {
  Lightbulb,
  TrendingUp,
  TrendingDown,
  Info,
  Warning,
  CheckCircle
} from '@mui/icons-material';

const KeyInsights = ({ insights = [] }) => {
  if (!insights || insights.length === 0) {
    return (
      <Box className="empty-state" sx={{ py: 3 }}>
        <Typography variant="body2" color="text.secondary">
          Chưa có đủ dữ liệu để tạo nhận xét
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" mt={1}>
          Thu thập thêm dữ liệu để nhận được phân tích chi tiết
        </Typography>
      </Box>
    );
  }

  // Categorize insights by type
  const categorizeInsight = (insight) => {
    const text = insight.toLowerCase();
    
    if (text.includes('tích cực') || text.includes('tăng') || text.includes('cao')) {
      return { type: 'positive', icon: <TrendingUp />, color: 'success' };
    } else if (text.includes('tiêu cực') || text.includes('giảm') || text.includes('thấp')) {
      return { type: 'negative', icon: <TrendingDown />, color: 'error' };
    } else if (text.includes('cân bằng') || text.includes('ổn định')) {
      return { type: 'neutral', icon: <CheckCircle />, color: 'info' };
    } else if (text.includes('cần chú ý') || text.includes('cảnh báo')) {
      return { type: 'warning', icon: <Warning />, color: 'warning' };
    } else {
      return { type: 'info', icon: <Lightbulb />, color: 'primary' };
    }
  };

  return (
    <Box>
      <List sx={{ p: 0 }}>
        {insights.map((insight, index) => {
          const category = categorizeInsight(insight);
          
          return (
            <ListItem
              key={index}
              sx={{
                border: '1px solid #e0e0e0',
                borderRadius: 2,
                mb: 1.5,
                backgroundColor: '#fff',
                transition: 'all 0.2s ease',
                '&:hover': {
                  backgroundColor: '#f8f9fa',
                  transform: 'translateX(4px)'
                }
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <Box 
                  sx={{ 
                    color: category.color + '.main',
                    display: 'flex',
                    alignItems: 'center'
                  }}
                >
                  {category.icon}
                </Box>
              </ListItemIcon>
              
              <ListItemText
                primary={
                  <Typography 
                    variant="body2" 
                    className="vietnamese-text"
                    sx={{ 
                      lineHeight: 1.6,
                      fontWeight: 500
                    }}
                  >
                    {insight}
                  </Typography>
                }
              />
              
              {/* Insight category chip */}
              <Chip
                size="small"
                variant="outlined"
                sx={{
                  borderColor: category.color + '.main',
                  color: category.color + '.main',
                  fontSize: '10px',
                  height: 24
                }}
              />
            </ListItem>
          );
        })}
      </List>

      {/* Insights summary */}
      <Alert 
        severity="info" 
        sx={{ mt: 2, fontSize: '13px' }}
        icon={<Info />}
      >
        <Typography variant="body2" className="vietnamese-text">
          <strong>Ghi chú:</strong> Các nhận xét này được tạo tự động dựa trên phân tích dữ liệu 
          mạng xã hội và có thể không phản ánh đầy đủ thực tế. Hãy kết hợp với phân tích thủ công 
          để có cái nhìn toàn diện hơn.
        </Typography>
      </Alert>
    </Box>
  );
};

export default KeyInsights;
