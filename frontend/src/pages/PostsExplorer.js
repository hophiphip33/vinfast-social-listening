/**
 * Posts Explorer Page
 * Browse, search, and filter social media posts about VinFast
 */

import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Pagination,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Button,
  InputAdornment,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  Search,
  FilterList,
  Facebook,
  VideoLibrary,
  Newspaper,
  ThumbUp,
  Comment,
  Share,
  OpenInNew,
  Visibility
} from '@mui/icons-material';

// Hooks and services
import { useQuery } from '@tanstack/react-query';
import { 
  fetchPosts,
  searchPosts,
  getPlatformLabel,
  getSentimentColor,
  getSentimentLabel,
  formatDate,
  formatNumber
} from '../services/api';

const PostsExplorer = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [platformFilter, setPlatformFilter] = useState('');
  const [sentimentFilter, setSentimentFilter] = useState('');
  const [timeRangeFilter, setTimeRangeFilter] = useState(7);
  const [page, setPage] = useState(1);
  const [selectedPost, setSelectedPost] = useState(null);
  const [postDetailDialog, setPostDetailDialog] = useState(false);
  
  const postsPerPage = 20;

  // Fetch posts with filters
  const { 
    data: postsData, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: ['posts-explorer', platformFilter, sentimentFilter, timeRangeFilter, page],
    queryFn: () => fetchPosts({
      platform: platformFilter || undefined,
      sentiment: sentimentFilter || undefined,
      days: timeRangeFilter,
      limit: postsPerPage,
      offset: (page - 1) * postsPerPage
    }),
  });

  // Search posts
  const { 
    data: searchResults 
  } = useQuery({
    queryKey: ['search-posts', searchQuery, platformFilter, sentimentFilter],
    queryFn: () => searchPosts(searchQuery, {
      platform: platformFilter || undefined,
      sentiment: sentimentFilter || undefined,
      limit: 50
    }),
    enabled: searchQuery.length > 2,
  });

  const handlePostClick = (post) => {
    setSelectedPost(post);
    setPostDetailDialog(true);
  };

  const getPlatformIcon = (platform) => {
    switch (platform) {
      case 'facebook':
        return <Facebook sx={{ color: '#1877f2' }} />;
      case 'tiktok':
        return <VideoLibrary sx={{ color: '#000000' }} />;
      case 'news':
        return <Newspaper sx={{ color: '#ff6b35' }} />;
      default:
        return <Newspaper sx={{ color: '#757575' }} />;
    }
  };

  const displayPosts = searchQuery.length > 2 ? searchResults?.data || [] : postsData?.data || [];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Khám phá bài viết
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Tìm kiếm và phân tích các bài viết về VinFast
        </Typography>
      </Box>

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            {/* Search */}
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Tìm kiếm trong bài viết..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search color="action" />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>
            
            {/* Platform Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Nền tảng</InputLabel>
                <Select
                  value={platformFilter}
                  label="Nền tảng"
                  onChange={(e) => setPlatformFilter(e.target.value)}
                >
                  <MenuItem value="">Tất cả</MenuItem>
                  <MenuItem value="facebook">Facebook</MenuItem>
                  <MenuItem value="tiktok">TikTok</MenuItem>
                  <MenuItem value="news">Tin tức</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {/* Sentiment Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Tình cảm</InputLabel>
                <Select
                  value={sentimentFilter}
                  label="Tình cảm"
                  onChange={(e) => setSentimentFilter(e.target.value)}
                >
                  <MenuItem value="">Tất cả</MenuItem>
                  <MenuItem value="positive">Tích cực</MenuItem>
                  <MenuItem value="negative">Tiêu cực</MenuItem>
                  <MenuItem value="neutral">Trung tính</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {/* Time Range Filter */}
            <Grid item xs={12} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Thời gian</InputLabel>
                <Select
                  value={timeRangeFilter}
                  label="Thời gian"
                  onChange={(e) => setTimeRangeFilter(e.target.value)}
                >
                  <MenuItem value={1}>24 giờ</MenuItem>
                  <MenuItem value={7}>7 ngày</MenuItem>
                  <MenuItem value={30}>30 ngày</MenuItem>
                  <MenuItem value={90}>3 tháng</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {/* Clear Filters */}
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<FilterList />}
                onClick={() => {
                  setSearchQuery('');
                  setPlatformFilter('');
                  setSentimentFilter('');
                  setTimeRangeFilter(7);
                  setPage(1);
                }}
              >
                Xóa bộ lọc
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" fontWeight={600}>
              Kết quả tìm kiếm
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {formatNumber(displayPosts.length)} bài viết
            </Typography>
          </Box>

          {isLoading ? (
            <Box display="flex" justifyContent="center" py={6}>
              <CircularProgress />
            </Box>
          ) : displayPosts.length === 0 ? (
            <Box className="empty-state" py={6}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                🔍
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Không tìm thấy bài viết nào
              </Typography>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Hãy thử điều chỉnh bộ lọc hoặc từ khóa tìm kiếm
              </Typography>
            </Box>
          ) : (
            <>
              <List>
                {displayPosts.map((post, index) => (
                  <ListItem
                    key={post.id || index}
                    alignItems="flex-start"
                    sx={{
                      border: '1px solid #e0e0e0',
                      borderRadius: 2,
                      mb: 2,
                      backgroundColor: '#fff',
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: '#f8f9fa',
                        borderColor: '#1976d2'
                      },
                      transition: 'all 0.2s ease'
                    }}
                    onClick={() => handlePostClick(post)}
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
                            
                            {post.source_name && (
                              <Typography variant="caption" color="text.secondary">
                                • {post.source_name}
                              </Typography>
                            )}
                            
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
                            
                            <Typography variant="caption" color="text.secondary" ml="auto">
                              {formatDate(post.published_at)}
                            </Typography>
                          </Box>
                          
                          {post.title && (
                            <Typography 
                              variant="subtitle1" 
                              fontWeight={600}
                              sx={{ mb: 1, lineHeight: 1.4 }}
                            >
                              {post.title}
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
                            sx={{ mb: 2, lineHeight: 1.5 }}
                          >
                            {post.content.length > 200 
                              ? post.content.substring(0, 200) + '...' 
                              : post.content
                            }
                          </Typography>
                          
                          {/* Keywords */}
                          {post.keywords && post.keywords.length > 0 && (
                            <Box display="flex" flexWrap="wrap" gap={0.5} mb={1}>
                              {post.keywords.slice(0, 5).map((keyword, idx) => (
                                <Chip
                                  key={idx}
                                  label={keyword}
                                  size="small"
                                  variant="outlined"
                                  sx={{ 
                                    fontSize: '10px',
                                    height: 20
                                  }}
                                />
                              ))}
                            </Box>
                          )}
                          
                          {/* Engagement metrics */}
                          <Box display="flex" alignItems="center" gap={3}>
                            <Box display="flex" alignItems="center" gap={0.5}>
                              <ThumbUp sx={{ fontSize: 16, color: '#757575' }} />
                              <Typography variant="caption">
                                {formatNumber(post.likes_count)}
                              </Typography>
                            </Box>
                            
                            <Box display="flex" alignItems="center" gap={0.5}>
                              <Comment sx={{ fontSize: 16, color: '#757575' }} />
                              <Typography variant="caption">
                                {formatNumber(post.comments_count)}
                              </Typography>
                            </Box>
                            
                            <Box display="flex" alignItems="center" gap={0.5}>
                              <Share sx={{ fontSize: 16, color: '#757575' }} />
                              <Typography variant="caption">
                                {formatNumber(post.shares_count)}
                              </Typography>
                            </Box>
                            
                            {post.source_url && (
                              <IconButton 
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  window.open(post.source_url, '_blank');
                                }}
                                sx={{ ml: 'auto' }}
                              >
                                <OpenInNew fontSize="small" />
                              </IconButton>
                            )}
                          </Box>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>

              {/* Pagination */}
              <Box display="flex" justifyContent="center" mt={3}>
                <Pagination
                  count={Math.ceil((postsData?.total || 0) / postsPerPage)}
                  page={page}
                  onChange={(e, newPage) => setPage(newPage)}
                  color="primary"
                />
              </Box>
            </>
          )}
        </CardContent>
      </Card>

      {/* Post Detail Dialog */}
      <Dialog 
        open={postDetailDialog} 
        onClose={() => setPostDetailDialog(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedPost && (
          <>
            <DialogTitle>
              <Box display="flex" alignItems="center" gap={2}>
                {getPlatformIcon(selectedPost.platform)}
                <Typography variant="h6" fontWeight={600}>
                  {getPlatformLabel(selectedPost.platform)}
                </Typography>
                {selectedPost.sentiment && (
                  <Chip
                    label={getSentimentLabel(selectedPost.sentiment)}
                    sx={{
                      backgroundColor: getSentimentColor(selectedPost.sentiment) + '20',
                      color: getSentimentColor(selectedPost.sentiment),
                    }}
                  />
                )}
              </Box>
            </DialogTitle>
            
            <DialogContent>
              <Box>
                {selectedPost.title && (
                  <Typography variant="h6" fontWeight={600} mb={2}>
                    {selectedPost.title}
                  </Typography>
                )}
                
                <Typography 
                  variant="body1" 
                  className="vietnamese-text"
                  sx={{ mb: 3, lineHeight: 1.7 }}
                >
                  {selectedPost.content}
                </Typography>
                
                {/* Metadata */}
                <Grid container spacing={2} mb={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Tác giả: {selectedPost.author || 'Không rõ'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Thời gian: {formatDate(selectedPost.published_at)}
                    </Typography>
                  </Grid>
                </Grid>
                
                {/* Sentiment Analysis */}
                {selectedPost.sentiment && (
                  <Box mb={2} p={2} bgcolor="grey.50" borderRadius={1}>
                    <Typography variant="subtitle2" fontWeight={600} mb={1}>
                      Phân tích tình cảm
                    </Typography>
                    <Box display="flex" gap={2} alignItems="center">
                      <Chip
                        label={getSentimentLabel(selectedPost.sentiment)}
                        sx={{
                          backgroundColor: getSentimentColor(selectedPost.sentiment) + '20',
                          color: getSentimentColor(selectedPost.sentiment),
                        }}
                      />
                      <Typography variant="body2">
                        Điểm: {selectedPost.sentiment_score?.toFixed(3) || 'N/A'}
                      </Typography>
                      <Typography variant="body2">
                        Độ tin cậy: {selectedPost.confidence_score?.toFixed(3) || 'N/A'}
                      </Typography>
                    </Box>
                  </Box>
                )}
                
                {/* Keywords */}
                {selectedPost.keywords && selectedPost.keywords.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="subtitle2" fontWeight={600} mb={1}>
                      Từ khóa
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      {selectedPost.keywords.map((keyword, idx) => (
                        <Chip
                          key={idx}
                          label={keyword}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </Box>
                )}
                
                {/* Engagement */}
                <Box>
                  <Typography variant="subtitle2" fontWeight={600} mb={1}>
                    Tương tác
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={3}>
                      <Box textAlign="center">
                        <ThumbUp sx={{ color: '#757575', mb: 0.5 }} />
                        <Typography variant="h6" fontWeight={600}>
                          {formatNumber(selectedPost.likes_count)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Likes
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={3}>
                      <Box textAlign="center">
                        <Comment sx={{ color: '#757575', mb: 0.5 }} />
                        <Typography variant="h6" fontWeight={600}>
                          {formatNumber(selectedPost.comments_count)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Comments
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={3}>
                      <Box textAlign="center">
                        <Share sx={{ color: '#757575', mb: 0.5 }} />
                        <Typography variant="h6" fontWeight={600}>
                          {formatNumber(selectedPost.shares_count)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Shares
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={3}>
                      <Box textAlign="center">
                        <Visibility sx={{ color: '#757575', mb: 0.5 }} />
                        <Typography variant="h6" fontWeight={600}>
                          {formatNumber(selectedPost.views_count)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Views
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              </Box>
            </DialogContent>
            
            <DialogActions>
              {selectedPost.source_url && (
                <Button
                  startIcon={<OpenInNew />}
                  onClick={() => window.open(selectedPost.source_url, '_blank')}
                >
                  Xem bài gốc
                </Button>
              )}
              <Button onClick={() => setPostDetailDialog(false)}>
                Đóng
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default PostsExplorer;
