/**
 * Recent Posts Component
 * Displays a list of recent social media posts about VinFast
 */

import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Button
} from '@mui/material';
import {
  Facebook,
  VideoLibrary,
  Newspaper,
  ThumbUp,
  Comment,
  Share,
  MoreVert,
  OpenInNew
} from '@mui/icons-material';

// Hooks and services
import { useQuery } from '@tanstack/react-query';
import { 
  fetchPosts, 
  getSentimentColor, 
  getSentimentLabel, 
  getPlatformLabel,
  formatDate 
} from '../services/api';

const RecentPosts = ({ limit = 10, platform = null, sentiment = null }) => {
  const { 
    data: postsData, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: ['recent-posts', limit, platform, sentiment],
    queryFn: () => fetchPosts({ 
      platform, 
      sentiment, 
      days: 7, 
      limit 
    }),
    refetchInterval: 2 * 60 * 1000, // Refresh every 2 minutes
  });

  // Platform icon mapping
  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'facebook':
        return <Facebook sx={{ fontSize: 20, color: '#1877f2' }} />;
      case 'tiktok':
        return <VideoLibrary sx={{ fontSize: 20, color: '#000000' }} />;
      case 'news':
        return <Newspaper sx={{ fontSize: 20, color: '#ff6b35' }} />;
      default:
        return <Newspaper sx={{ fontSize: 20, color: '#757575' }} />;
    }
  };

  // Truncate text for display
  const truncateText = (text, maxLength = 120) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" py={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box textAlign="center" py={4}>
        <Typography color="error">
          Lỗi tải bài viết: {error.message}
        </Typography>
      </Box>
    );
  }

  const posts = postsData?.data || [];

  if (posts.length === 0) {
    return (
      <Box className="empty-state">
        <Typography variant="h6" color="text.secondary" gutterBottom>
          📝
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Chưa có bài viết nào được thu thập
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" mt={1}>
          Hãy bắt đầu thu thập dữ liệu để xem nội dung
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <List sx={{ maxHeight: 400, overflowY: 'auto' }}>
        {posts.map((post, index) => (
          <ListItem
            key={post.id || index}
            alignItems="flex-start"
            sx={{ 
              border: '1px solid #e0e0e0',
              borderRadius: 2,
              mb: 1,
              backgroundColor: '#fff',
              '&:hover': {
                backgroundColor: '#f8f9fa',
                borderColor: '#1976d2'
              },
              transition: 'all 0.2s ease'
            }}
          >
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: 'transparent' }}>
                {getPlatformIcon(post.platform)}
              </Avatar>
            </ListItemAvatar>
            
            <ListItemText
              primary={
                <Box>
                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                    <Typography variant="body2" fontWeight={500}>
                      {getPlatformLabel(post.platform)}
                    </Typography>
                    
                    {post.sentiment && (
                      <Chip
                        label={getSentimentLabel(post.sentiment)}
                        size="small"
                        sx={{
                          backgroundColor: getSentimentColor(post.sentiment) + '20',
                          color: getSentimentColor(post.sentiment),
                          fontWeight: 500,
                          fontSize: '11px'
                        }}
                      />
                    )}
                    
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(post.published_at)}
                    </Typography>
                  </Box>
                  
                  {post.title && (
                    <Typography 
                      variant="subtitle2" 
                      fontWeight={600}
                      sx={{ mb: 0.5 }}
                    >
                      {truncateText(post.title, 80)}
                    </Typography>
                  )}
                </Box>
              }
              secondary={
                <Box>
                  <Typography 
                    variant="body2" 
                    color="text.primary"
                    className="vietnamese-text"
                    sx={{ mb: 1.5, lineHeight: 1.5 }}
                  >
                    {truncateText(post.content, 150)}
                  </Typography>
                  
                  {/* Engagement metrics */}
                  <Box display="flex" alignItems="center" gap={2}>
                    {post.likes_count > 0 && (
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <ThumbUp sx={{ fontSize: 14, color: '#757575' }} />
                        <Typography variant="caption" color="text.secondary">
                          {formatNumber(post.likes_count)}
                        </Typography>
                      </Box>
                    )}
                    
                    {post.comments_count > 0 && (
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Comment sx={{ fontSize: 14, color: '#757575' }} />
                        <Typography variant="caption" color="text.secondary">
                          {formatNumber(post.comments_count)}
                        </Typography>
                      </Box>
                    )}
                    
                    {post.shares_count > 0 && (
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Share sx={{ fontSize: 14, color: '#757575' }} />
                        <Typography variant="caption" color="text.secondary">
                          {formatNumber(post.shares_count)}
                        </Typography>
                      </Box>
                    )}
                    
                    {/* Keywords */}
                    {post.keywords && post.keywords.length > 0 && (
                      <Box display="flex" alignItems="center" gap={0.5} ml="auto">
                        {post.keywords.slice(0, 3).map((keyword, idx) => (
                          <Chip
                            key={idx}
                            label={keyword}
                            size="small"
                            variant="outlined"
                            sx={{ 
                              fontSize: '10px',
                              height: 20,
                              '& .MuiChip-label': { px: 1 }
                            }}
                          />
                        ))}
                        {post.keywords.length > 3 && (
                          <Typography variant="caption" color="text.secondary">
                            +{post.keywords.length - 3}
                          </Typography>
                        )}
                      </Box>
                    )}
                  </Box>
                </Box>
              }
            />
            
            {/* Action buttons */}
            <Box display="flex" flexDirection="column" gap={1}>
              {post.source_url && (
                <Tooltip title="Xem bài viết gốc">
                  <IconButton 
                    size="small"
                    onClick={() => window.open(post.source_url, '_blank')}
                  >
                    <OpenInNew fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
              
              <Tooltip title="Xem thêm">
                <IconButton size="small">
                  <MoreVert fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          </ListItem>
        ))}
      </List>

      {/* Show more button */}
      {posts.length >= limit && (
        <Box textAlign="center" mt={2}>
          <Button 
            variant="outlined" 
            size="small"
            onClick={() => {
              // Navigate to posts explorer page
              window.location.href = '/posts';
            }}
          >
            Xem thêm bài viết
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default RecentPosts;
