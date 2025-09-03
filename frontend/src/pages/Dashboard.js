/**
 * Main Dashboard Page - Overview of VinFast Social Listening
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
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  RemoveRedEye,
  ThumbUp,
  Comment,
  Share,
  Assessment,
  CloudDownload
} from '@mui/icons-material';

// Hooks and utilities
import { useQuery } from '@tanstack/react-query';
import { 
  fetchDashboardStats, 
  fetchAnalyticsOverview, 
  startFullCollection,
  formatNumber,
  getSentimentColor,
  getSentimentLabel
} from '../services/api';
import toast from 'react-hot-toast';

// Components
import StatCard from '../components/StatCard';
import SentimentChart from '../components/charts/SentimentChart';
import TrendChart from '../components/charts/TrendChart';
import PlatformBreakdown from '../components/charts/PlatformBreakdown';
import WordCloudComponent from '../components/charts/WordCloudComponent';
import RecentPosts from '../components/RecentPosts';
import KeyInsights from '../components/KeyInsights';

const Dashboard = () => {
  const [timeRange, setTimeRange] = useState(7);
  
  // Fetch dashboard data
  const { 
    data: dashboardData, 
    isLoading: dashboardLoading, 
    error: dashboardError 
  } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 60000, // Refresh every minute
  });

  const {
    data: analyticsData,
    isLoading: analyticsLoading,
    error: analyticsError
  } = useQuery({
    queryKey: ['analytics-overview', timeRange],
    queryFn: () => fetchAnalyticsOverview(timeRange),
    enabled: timeRange > 0,
  });

  // Handle data collection
  const handleStartCollection = async () => {
    try {
      const result = await startFullCollection();
      toast.success(result.message || 'Đã bắt đầu thu thập dữ liệu');
    } catch (error) {
      toast.error(error.message || 'Lỗi khi bắt đầu thu thập dữ liệu');
    }
  };

  // Extract data for display
  const realTimeData = dashboardData?.data?.real_time;
  const weeklyOverview = dashboardData?.data?.weekly_overview;
  const analyticsReport = analyticsData?.data;

  if (dashboardLoading && analyticsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (dashboardError || analyticsError) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Lỗi khi tải dữ liệu dashboard: {dashboardError?.message || analyticsError?.message}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ padding: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight={700} color="text.primary">
            Dashboard VinFast Social Listening
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={1}>
            Theo dõi và phân tích tình cảm về VinFast trên mạng xã hội
          </Typography>
        </Box>
        
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Thời gian</InputLabel>
            <Select
              value={timeRange}
              label="Thời gian"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value={1}>24 giờ</MenuItem>
              <MenuItem value={7}>7 ngày</MenuItem>
              <MenuItem value={30}>30 ngày</MenuItem>
              <MenuItem value={90}>3 tháng</MenuItem>
            </Select>
          </FormControl>
          
          <Button
            variant="contained"
            startIcon={<CloudDownload />}
            onClick={handleStartCollection}
            className="collect-button"
          >
            Thu thập dữ liệu
          </Button>
        </Box>
      </Box>

      {/* Real-time Status */}
      {realTimeData && (
        <Alert 
          severity={realTimeData.status === 'active' ? 'success' : 'info'} 
          sx={{ mb: 3 }}
        >
          <Typography variant="body2">
            <strong>Trạng thái:</strong> {realTimeData.status === 'active' ? 'Đang hoạt động' : 'Không hoạt động'} • 
            <strong> 24h gần nhất:</strong> {formatNumber(realTimeData.last_24h?.total_posts || 0)} bài viết
          </Typography>
        </Alert>
      )}

      {/* Key Statistics Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Tổng bài viết"
            value={analyticsReport?.basic_statistics?.total_posts || 0}
            icon={<Assessment />}
            color="#1976d2"
            subtitle={`Trong ${timeRange} ngày qua`}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Tương tác"
            value={analyticsReport?.basic_statistics?.total_engagement || 0}
            icon={<ThumbUp />}
            color="#4caf50"
            subtitle="Likes, shares, comments"
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Tình cảm tích cực"
            value={`${analyticsReport?.sentiment_analysis?.positive_percentage || 0}%`}
            icon={<TrendingUp />}
            color="#4caf50"
            subtitle={`${analyticsReport?.sentiment_analysis?.positive || 0} bài viết`}
          />
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Tình cảm tiêu cực"
            value={`${analyticsReport?.sentiment_analysis?.negative_percentage || 0}%`}
            icon={<TrendingDown />}
            color="#f44336"
            subtitle={`${analyticsReport?.sentiment_analysis?.negative || 0} bài viết`}
          />
        </Grid>
      </Grid>

      {/* Main Charts */}
      <Grid container spacing={3} mb={3}>
        {/* Sentiment Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={2}>
                Phân bố tình cảm
              </Typography>
              {analyticsReport?.sentiment_analysis ? (
                <SentimentChart data={analyticsReport.sentiment_analysis} />
              ) : (
                <Box display="flex" justifyContent="center" py={4}>
                  <Typography color="text.secondary">Không có dữ liệu</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Platform Breakdown */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={2}>
                Phân tích theo nền tảng
              </Typography>
              {analyticsReport?.platform_breakdown ? (
                <PlatformBreakdown data={analyticsReport.platform_breakdown} />
              ) : (
                <Box display="flex" justifyContent="center" py={4}>
                  <Typography color="text.secondary">Không có dữ liệu</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Trend Analysis and Word Cloud */}
      <Grid container spacing={3} mb={3}>
        {/* Sentiment Trends */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={2}>
                Xu hướng tình cảm theo thời gian
              </Typography>
              <TrendChart timeRange={timeRange} />
            </CardContent>
          </Card>
        </Grid>
        
        {/* Word Cloud */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={2}>
                Từ khóa nổi bật
              </Typography>
              <WordCloudComponent days={timeRange} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Bottom Section */}
      <Grid container spacing={3}>
        {/* Key Insights */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={2}>
                Nhận xét chính
              </Typography>
              <KeyInsights insights={analyticsReport?.key_insights || []} />
            </CardContent>
          </Card>
        </Grid>
        
        {/* Recent Posts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={2}>
                Bài viết gần đây
              </Typography>
              <RecentPosts limit={5} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Vietnamese Summary */}
      {analyticsReport?.vietnamese_summary && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" fontWeight={600} mb={2}>
              Tóm tắt phân tích
            </Typography>
            <Box 
              className="vietnamese-text"
              sx={{ 
                backgroundColor: '#f8f9fa',
                padding: 3,
                borderRadius: 2,
                border: '1px solid #e9ecef'
              }}
            >
              <Typography 
                variant="body1" 
                sx={{ whiteSpace: 'pre-line', lineHeight: 1.7 }}
              >
                {analyticsReport.vietnamese_summary}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Dashboard;
