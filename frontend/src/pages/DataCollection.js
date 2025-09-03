/**
 * Data Collection Management Page
 * Interface for managing and monitoring data collection processes
 */

import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  CloudDownload,
  PlayArrow,
  Stop,
  Refresh,
  Facebook,
  VideoLibrary,
  Newspaper,
  Settings,
  Analytics,
  CheckCircle,
  Error as ErrorIcon,
  Warning
} from '@mui/icons-material';

// Hooks and services
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  startNewsCollection,
  startFacebookCollection,
  startTikTokCollection,
  startFullCollection,
  startSentimentProcessing,
  getSystemStatus
} from '../services/api';
import toast from 'react-hot-toast';

const DataCollection = () => {
  const [selectedSource, setSelectedSource] = useState(null);
  const [configDialog, setConfigDialog] = useState(false);
  const queryClient = useQueryClient();

  // Get system status
  const { 
    data: systemStatus, 
    isLoading: statusLoading 
  } = useQuery({
    queryKey: ['system-status'],
    queryFn: getSystemStatus,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Collection mutations
  const newsCollectionMutation = useMutation({
    mutationFn: startNewsCollection,
    onSuccess: (data) => {
      toast.success(data.message || 'Bắt đầu thu thập tin tức');
      queryClient.invalidateQueries(['system-status']);
    },
    onError: (error) => {
      toast.error(error.message || 'Lỗi thu thập tin tức');
    }
  });

  const facebookCollectionMutation = useMutation({
    mutationFn: startFacebookCollection,
    onSuccess: (data) => {
      toast.success(data.message || 'Bắt đầu thu thập Facebook');
      queryClient.invalidateQueries(['system-status']);
    },
    onError: (error) => {
      toast.error(error.message || 'Lỗi thu thập Facebook');
    }
  });

  const tiktokCollectionMutation = useMutation({
    mutationFn: startTikTokCollection,
    onSuccess: (data) => {
      toast.success(data.message || 'Bắt đầu thu thập TikTok');
      queryClient.invalidateQueries(['system-status']);
    },
    onError: (error) => {
      toast.error(error.message || 'Lỗi thu thập TikTok');
    }
  });

  const fullCollectionMutation = useMutation({
    mutationFn: startFullCollection,
    onSuccess: (data) => {
      toast.success(data.message || 'Bắt đầu thu thập tất cả');
      queryClient.invalidateQueries(['system-status']);
    },
    onError: (error) => {
      toast.error(error.message || 'Lỗi thu thập dữ liệu');
    }
  });

  const sentimentProcessingMutation = useMutation({
    mutationFn: startSentimentProcessing,
    onSuccess: (data) => {
      toast.success(data.message || 'Bắt đầu xử lý tình cảm');
      queryClient.invalidateQueries(['system-status']);
    },
    onError: (error) => {
      toast.error(error.message || 'Lỗi xử lý tình cảm');
    }
  });

  // Data sources configuration
  const dataSources = [
    {
      id: 'news',
      name: 'Tin tức trực tuyến',
      description: 'Thu thập từ các trang báo Việt Nam',
      icon: <Newspaper />,
      color: '#ff6b35',
      sources: ['VnExpress', 'Tuổi Trẻ', 'Thanh Niên', 'VietNamNet'],
      status: 'ready',
      mutation: newsCollectionMutation
    },
    {
      id: 'facebook',
      name: 'Facebook',
      description: 'Bài viết và bình luận công khai',
      icon: <Facebook />,
      color: '#1877f2',
      sources: ['VinFast', 'VinGroup', 'Cộng đồng xe hơi'],
      status: 'ready',
      mutation: facebookCollectionMutation
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      description: 'Video và hashtag công khai',
      icon: <VideoLibrary />,
      color: '#000000',
      sources: ['#vinfast', '#vf8', '#vf9', '#xevinfast'],
      status: 'ready',
      mutation: tiktokCollectionMutation
    }
  ];

  const getStatusChip = (source) => {
    const isLoading = source.mutation.isLoading;
    
    if (isLoading) {
      return <Chip label="Đang chạy..." color="warning" size="small" />;
    }
    
    return <Chip label="Sẵn sàng" color="success" size="small" />;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <CircularProgress size={20} />;
      case 'completed':
        return <CheckCircle color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <CheckCircle color="success" />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Thu thập dữ liệu
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Quản lý và theo dõi quá trình thu thập dữ liệu từ các nền tảng mạng xã hội
        </Typography>
      </Box>

      {/* System Status */}
      {systemStatus?.data && (
        <Alert 
          severity={
            systemStatus.data.database === 'connected' && 
            systemStatus.data.sentiment_model === 'loaded' 
              ? 'success' : 'warning'
          } 
          sx={{ mb: 3 }}
        >
          <Typography variant="body2">
            <strong>Database:</strong> {systemStatus.data.database === 'connected' ? 'Đã kết nối' : 'Chưa kết nối'} • 
            <strong> Model:</strong> {systemStatus.data.sentiment_model === 'loaded' ? 'Đã tải' : 'Chưa tải'} • 
            <strong> API:</strong> v{systemStatus.data.api_version}
          </Typography>
        </Alert>
      )}

      {/* Quick Actions */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} mb={2}>
            Hành động nhanh
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                size="large"
                startIcon={<CloudDownload />}
                onClick={() => fullCollectionMutation.mutate()}
                disabled={fullCollectionMutation.isLoading}
                sx={{ py: 1.5 }}
              >
                {fullCollectionMutation.isLoading ? 'Đang thu thập...' : 'Thu thập tất cả'}
              </Button>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                size="large"
                startIcon={<Analytics />}
                onClick={() => sentimentProcessingMutation.mutate()}
                disabled={sentimentProcessingMutation.isLoading}
                sx={{ py: 1.5 }}
              >
                {sentimentProcessingMutation.isLoading ? 'Đang xử lý...' : 'Xử lý tình cảm'}
              </Button>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                size="large"
                startIcon={<Refresh />}
                onClick={() => queryClient.invalidateQueries()}
                sx={{ py: 1.5 }}
              >
                Làm mới
              </Button>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="outlined"
                size="large"
                startIcon={<Settings />}
                onClick={() => setConfigDialog(true)}
                sx={{ py: 1.5 }}
              >
                Cấu hình
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Data Sources */}
      <Typography variant="h5" fontWeight={600} mb={3}>
        Nguồn dữ liệu
      </Typography>

      <Grid container spacing={3}>
        {dataSources.map((source) => (
          <Grid item xs={12} md={4} key={source.id}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                {/* Header */}
                <Box display="flex" alignItems="center" mb={2}>
                  <Box sx={{ color: source.color, mr: 1.5 }}>
                    {source.icon}
                  </Box>
                  <Typography variant="h6" fontWeight={600}>
                    {source.name}
                  </Typography>
                  <Box ml="auto">
                    {getStatusChip(source)}
                  </Box>
                </Box>

                {/* Description */}
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {source.description}
                </Typography>

                {/* Sources list */}
                <Box mb={3}>
                  <Typography variant="caption" color="text.secondary" fontWeight={500}>
                    NGUỒN:
                  </Typography>
                  <Box mt={1} display="flex" flexWrap="wrap" gap={1}>
                    {source.sources.map((sourceName, idx) => (
                      <Chip
                        key={idx}
                        label={sourceName}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '11px' }}
                      />
                    ))}
                  </Box>
                </Box>

                {/* Action button */}
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={source.mutation.isLoading ? <CircularProgress size={16} /> : <PlayArrow />}
                  onClick={() => source.mutation.mutate()}
                  disabled={source.mutation.isLoading}
                  sx={{ 
                    backgroundColor: source.color,
                    '&:hover': {
                      backgroundColor: source.color + 'dd'
                    }
                  }}
                >
                  {source.mutation.isLoading ? 'Đang thu thập...' : 'Bắt đầu thu thập'}
                </Button>

                {/* Progress bar */}
                {source.mutation.isLoading && (
                  <Box mt={2}>
                    <LinearProgress />
                    <Typography variant="caption" color="text.secondary" textAlign="center" display="block" mt={1}>
                      Đang thu thập dữ liệu...
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Collection History */}
      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" fontWeight={600} mb={3}>
            Lịch sử thu thập
          </Typography>
          
          <List>
            {/* Mock collection history */}
            {[
              {
                id: 1,
                source: 'Tất cả',
                status: 'completed',
                timestamp: new Date(),
                collected: 45,
                processed: 42
              },
              {
                id: 2,
                source: 'Facebook',
                status: 'running',
                timestamp: new Date(Date.now() - 30 * 60 * 1000),
                collected: 23,
                processed: 0
              },
              {
                id: 3,
                source: 'Tin tức',
                status: 'completed',
                timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
                collected: 12,
                processed: 12
              }
            ].map((item) => (
              <ListItem
                key={item.id}
                sx={{
                  border: '1px solid #e0e0e0',
                  borderRadius: 2,
                  mb: 1,
                  backgroundColor: '#fff'
                }}
              >
                <ListItemIcon>
                  {getStatusIcon(item.status)}
                </ListItemIcon>
                
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle2" fontWeight={500}>
                        {item.source}
                      </Typography>
                      <Chip
                        label={item.status === 'completed' ? 'Hoàn thành' : 'Đang chạy'}
                        size="small"
                        color={item.status === 'completed' ? 'success' : 'warning'}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {item.timestamp.toLocaleString('vi-VN')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Thu thập: {item.collected} • Xử lý: {item.processed}
                      </Typography>
                    </Box>
                  }
                />
                
                <ListItemSecondaryAction>
                  <IconButton size="small">
                    <Settings />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </CardContent>
      </Card>

      {/* Configuration Dialog */}
      <Dialog open={configDialog} onClose={() => setConfigDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Cấu hình thu thập dữ liệu</DialogTitle>
        <DialogContent>
          <Box py={2}>
            <TextField
              fullWidth
              label="Số bài viết tối đa mỗi lần"
              type="number"
              defaultValue={100}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Độ trễ giữa các request (giây)"
              type="number"
              defaultValue={5}
              margin="normal"
            />
            <TextField
              fullWidth
              label="Từ khóa bổ sung"
              placeholder="vinfast, xe điện, ô tô"
              margin="normal"
              multiline
              rows={3}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Hủy</Button>
          <Button variant="contained" onClick={() => setConfigDialog(false)}>
            Lưu cấu hình
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataCollection;
