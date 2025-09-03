/**
 * Detailed Analytics Page
 * Comprehensive analytics and insights for VinFast social listening data
 */

import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert
} from '@mui/material';
import {
  TrendingUp,
  Download,
  FilterList,
  Assessment,
  Timeline
} from '@mui/icons-material';

// Hooks and services
import { useQuery } from '@tanstack/react-query';
import { 
  fetchAnalyticsOverview,
  fetchKeywordAnalysis,
  exportReport,
  formatNumber,
  getSentimentColor,
  getSentimentLabel
} from '../services/api';

// Components
import SentimentChart from '../components/charts/SentimentChart';
import TrendChart from '../components/charts/TrendChart';
import WordCloudComponent from '../components/charts/WordCloudComponent';

const Analytics = () => {
  const [timeRange, setTimeRange] = useState(30);
  const [activeTab, setActiveTab] = useState(0);
  const [exportFormat, setExportFormat] = useState('json');

  // Fetch analytics data
  const { 
    data: analyticsData, 
    isLoading: analyticsLoading 
  } = useQuery({
    queryKey: ['detailed-analytics', timeRange],
    queryFn: () => fetchAnalyticsOverview(timeRange),
  });

  const { 
    data: keywordsData, 
    isLoading: keywordsLoading 
  } = useQuery({
    queryKey: ['detailed-keywords', timeRange],
    queryFn: () => fetchKeywordAnalysis(timeRange, 100),
  });

  const handleExport = async () => {
    try {
      const result = await exportReport(timeRange, exportFormat);
      toast.success('Báo cáo đã được tải xuống');
    } catch (error) {
      toast.error('Lỗi xuất báo cáo: ' + error.message);
    }
  };

  const analytics = analyticsData?.data;
  const keywords = keywordsData?.data || [];

  // Tab content
  const tabContent = [
    {
      label: 'Tổng quan',
      content: (
        <Grid container spacing={3}>
          {/* Sentiment Analysis */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} mb={2}>
                  Phân tích tình cảm chi tiết
                </Typography>
                {analytics?.sentiment_analysis ? (
                  <SentimentChart data={analytics.sentiment_analysis} />
                ) : (
                  <Typography color="text.secondary">Đang tải...</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
          
          {/* Trends */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} mb={2}>
                  Xu hướng thời gian
                </Typography>
                <TrendChart timeRange={timeRange} />
              </CardContent>
            </Card>
          </Grid>
          
          {/* Vietnamese Summary */}
          {analytics?.vietnamese_summary && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight={600} mb={2}>
                    Tóm tắt phân tích
                  </Typography>
                  <Box 
                    className="vietnamese-text"
                    sx={{ 
                      backgroundColor: '#f8f9fa',
                      p: 3,
                      borderRadius: 2,
                      border: '1px solid #e9ecef'
                    }}
                  >
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-line', lineHeight: 1.7 }}>
                      {analytics.vietnamese_summary}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )
    },
    {
      label: 'Từ khóa',
      content: (
        <Grid container spacing={3}>
          {/* Word Cloud */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} mb={2}>
                  Word Cloud từ khóa
                </Typography>
                <WordCloudComponent days={timeRange} />
              </CardContent>
            </Card>
          </Grid>
          
          {/* Keywords Table */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} mb={2}>
                  Top từ khóa
                </Typography>
                
                {keywordsLoading ? (
                  <Typography>Đang tải...</Typography>
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Từ khóa</TableCell>
                          <TableCell align="right">Số lần</TableCell>
                          <TableCell align="center">Tình cảm</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {keywords.slice(0, 15).map((keyword, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              <Typography variant="body2" fontWeight={500}>
                                {keyword.keyword}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography variant="body2">
                                {formatNumber(keyword.count)}
                              </Typography>
                            </TableCell>
                            <TableCell align="center">
                              <Chip
                                label={getSentimentLabel(keyword.sentiment_category)}
                                size="small"
                                sx={{
                                  backgroundColor: getSentimentColor(keyword.sentiment_category) + '20',
                                  color: getSentimentColor(keyword.sentiment_category),
                                  fontSize: '11px'
                                }}
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )
    },
    {
      label: 'Báo cáo',
      content: (
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={600} mb={3}>
              Xuất báo cáo
            </Typography>
            
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Thời gian</InputLabel>
                  <Select
                    value={timeRange}
                    label="Thời gian"
                    onChange={(e) => setTimeRange(e.target.value)}
                  >
                    <MenuItem value={7}>7 ngày</MenuItem>
                    <MenuItem value={30}>30 ngày</MenuItem>
                    <MenuItem value={90}>3 tháng</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Định dạng</InputLabel>
                  <Select
                    value={exportFormat}
                    label="Định dạng"
                    onChange={(e) => setExportFormat(e.target.value)}
                  >
                    <MenuItem value="json">JSON</MenuItem>
                    <MenuItem value="csv">CSV</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<Download />}
                  onClick={handleExport}
                  size="large"
                >
                  Tải xuống báo cáo
                </Button>
              </Grid>
            </Grid>
            
            {/* Report preview */}
            {analytics && (
              <Box mt={4} p={3} bgcolor="grey.50" borderRadius={2}>
                <Typography variant="subtitle1" fontWeight={600} mb={2}>
                  Xem trước báo cáo
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Tổng bài viết</Typography>
                    <Typography variant="h6" fontWeight={600}>
                      {formatNumber(analytics.basic_statistics?.total_posts || 0)}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Tổng tương tác</Typography>
                    <Typography variant="h6" fontWeight={600}>
                      {formatNumber(analytics.basic_statistics?.total_engagement || 0)}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Tích cực</Typography>
                    <Typography 
                      variant="h6" 
                      fontWeight={600}
                      sx={{ color: getSentimentColor('positive') }}
                    >
                      {analytics.sentiment_analysis?.positive_percentage?.toFixed(1) || 0}%
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={6} md={3}>
                    <Typography variant="body2" color="text.secondary">Tiêu cực</Typography>
                    <Typography 
                      variant="h6" 
                      fontWeight={600}
                      sx={{ color: getSentimentColor('negative') }}
                    >
                      {analytics.sentiment_analysis?.negative_percentage?.toFixed(1) || 0}%
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            )}
          </CardContent>
        </Card>
      )
    }
  ];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Phân tích chi tiết
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Báo cáo và phân tích chuyên sâu về VinFast
          </Typography>
        </Box>
        
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Khoảng thời gian</InputLabel>
            <Select
              value={timeRange}
              label="Khoảng thời gian"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value={7}>7 ngày</MenuItem>
              <MenuItem value={30}>30 ngày</MenuItem>
              <MenuItem value={90}>3 tháng</MenuItem>
              <MenuItem value={365}>1 năm</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {/* Tabs Navigation */}
      <Card sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(e, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: '1px solid #e0e0e0' }}
        >
          {tabContent.map((tab, index) => (
            <Tab key={index} label={tab.label} />
          ))}
        </Tabs>
      </Card>

      {/* Tab Content */}
      <Box>
        {tabContent[activeTab]?.content}
      </Box>
    </Box>
  );
};

export default Analytics;
