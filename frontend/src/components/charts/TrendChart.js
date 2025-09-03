/**
 * Sentiment Trends Chart Component
 * Displays sentiment trends over time using line charts
 */

import React from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Box, Typography, CircularProgress } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { fetchSentimentTrends, getSentimentColor } from '../../services/api';
import { format } from 'date-fns';
import { vi } from 'date-fns/locale';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const TrendChart = ({ timeRange = 7 }) => {
  const { 
    data: trendsData, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: ['sentiment-trends', timeRange],
    queryFn: () => fetchSentimentTrends(timeRange, timeRange <= 7 ? 'daily' : 'weekly'),
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={300}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !trendsData?.data || trendsData.data.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={300}>
        <Typography color="text.secondary">
          {error ? 'Lỗi tải dữ liệu xu hướng' : 'Chưa có dữ liệu xu hướng'}
        </Typography>
      </Box>
    );
  }

  const trends = trendsData.data;

  // Prepare chart data
  const labels = trends.map(trend => 
    format(new Date(trend.date), 'dd/MM', { locale: vi })
  );

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Tích cực',
        data: trends.map(trend => trend.positive_count),
        borderColor: getSentimentColor('positive'),
        backgroundColor: getSentimentColor('positive') + '20',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6
      },
      {
        label: 'Tiêu cực',
        data: trends.map(trend => trend.negative_count),
        borderColor: getSentimentColor('negative'),
        backgroundColor: getSentimentColor('negative') + '20',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6
      },
      {
        label: 'Trung tính',
        data: trends.map(trend => trend.neutral_count),
        borderColor: getSentimentColor('neutral'),
        backgroundColor: getSentimentColor('neutral') + '20',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6
      }
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      title: {
        display: false
      },
      legend: {
        position: 'top',
        align: 'end',
        labels: {
          padding: 20,
          font: {
            size: 12,
            family: 'Inter, sans-serif'
          },
          usePointStyle: true,
          pointStyle: 'circle'
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          title: function(context) {
            const dataIndex = context[0].dataIndex;
            const date = new Date(trends[dataIndex].date);
            return format(date, 'dd MMMM yyyy', { locale: vi });
          },
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y} bài viết`;
          }
        }
      }
    },
    scales: {
      x: {
        grid: {
          display: false
        },
        ticks: {
          font: {
            size: 11
          }
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: '#f0f0f0'
        },
        ticks: {
          font: {
            size: 11
          },
          callback: function(value) {
            return Number.isInteger(value) ? value : '';
          }
        }
      }
    },
    elements: {
      line: {
        borderWidth: 2
      },
      point: {
        borderWidth: 2,
        hoverBorderWidth: 3
      }
    }
  };

  return (
    <Box>
      <Box className="chart-container">
        <Line data={chartData} options={chartOptions} />
      </Box>
      
      {/* Summary stats */}
      <Box mt={2} display="flex" justifyContent="space-around" textAlign="center">
        <Box>
          <Typography variant="body2" color="text.secondary">
            Tổng bài viết
          </Typography>
          <Typography variant="h6" fontWeight={600}>
            {trends.reduce((sum, trend) => sum + trend.total_posts, 0)}
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="body2" color="text.secondary">
            Điểm TB
          </Typography>
          <Typography 
            variant="h6" 
            fontWeight={600}
            sx={{
              color: trends.length > 0 && 
                (trends.reduce((sum, trend) => sum + trend.avg_sentiment_score, 0) / trends.length) > 0
                ? getSentimentColor('positive')
                : getSentimentColor('negative')
            }}
          >
            {trends.length > 0 
              ? (trends.reduce((sum, trend) => sum + trend.avg_sentiment_score, 0) / trends.length).toFixed(2)
              : '0.00'
            }
          </Typography>
        </Box>
        
        <Box>
          <Typography variant="body2" color="text.secondary">
            Xu hướng
          </Typography>
          <Typography variant="h6" fontWeight={600}>
            {trends.length >= 2 && 
             trends[trends.length - 1].avg_sentiment_score > trends[trends.length - 2].avg_sentiment_score 
             ? '📈' : trends.length >= 2 ? '📉' : '➡️'
            }
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default TrendChart;
