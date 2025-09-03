/**
 * Sentiment Distribution Chart Component
 * Displays sentiment analysis results as a pie chart
 */

import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  Title
} from 'chart.js';
import { Box, Typography, Grid } from '@mui/material';
import { getSentimentColor, getSentimentLabel, formatNumber } from '../../services/api';

ChartJS.register(ArcElement, Tooltip, Legend, Title);

const SentimentChart = ({ data }) => {
  if (!data || data.total === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={300}>
        <Typography color="text.secondary">Chưa có dữ liệu tình cảm</Typography>
      </Box>
    );
  }

  // Prepare chart data
  const chartData = {
    labels: ['Tích cực', 'Tiêu cực', 'Trung tính'],
    datasets: [
      {
        data: [data.positive, data.negative, data.neutral],
        backgroundColor: [
          getSentimentColor('positive'),
          getSentimentColor('negative'),
          getSentimentColor('neutral')
        ],
        borderColor: ['#fff', '#fff', '#fff'],
        borderWidth: 3,
        hoverOffset: 10
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          font: {
            size: 14,
            family: 'Inter, sans-serif'
          },
          usePointStyle: true,
          pointStyle: 'circle'
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed;
            const percentage = ((value / data.total) * 100).toFixed(1);
            return `${label}: ${formatNumber(value)} (${percentage}%)`;
          }
        }
      }
    },
    cutout: '60%'
  };

  return (
    <Box>
      {/* Chart */}
      <Box className="chart-container" mb={2}>
        <Doughnut data={chartData} options={chartOptions} />
        
        {/* Center text */}
        <Box
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center'
          }}
        >
          <Typography variant="h5" fontWeight={700}>
            {formatNumber(data.total)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Tổng bài viết
          </Typography>
        </Box>
      </Box>

      {/* Statistics */}
      <Grid container spacing={2}>
        <Grid item xs={4}>
          <Box textAlign="center">
            <Typography 
              variant="h6" 
              fontWeight={600}
              sx={{ color: getSentimentColor('positive') }}
            >
              {data.positive_percentage.toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Tích cực
            </Typography>
          </Box>
        </Grid>
        
        <Grid item xs={4}>
          <Box textAlign="center">
            <Typography 
              variant="h6" 
              fontWeight={600}
              sx={{ color: getSentimentColor('negative') }}
            >
              {data.negative_percentage.toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Tiêu cực
            </Typography>
          </Box>
        </Grid>
        
        <Grid item xs={4}>
          <Box textAlign="center">
            <Typography 
              variant="h6" 
              fontWeight={600}
              sx={{ color: getSentimentColor('neutral') }}
            >
              {data.neutral_percentage.toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Trung tính
            </Typography>
          </Box>
        </Grid>
      </Grid>

      {/* Average sentiment score */}
      <Box mt={2} p={2} bgcolor="grey.50" borderRadius={1}>
        <Typography variant="body2" color="text.secondary" textAlign="center">
          <strong>Điểm tình cảm trung bình:</strong> {' '}
          <span style={{ 
            color: data.avg_sentiment_score > 0 ? getSentimentColor('positive') : 
                   data.avg_sentiment_score < 0 ? getSentimentColor('negative') : 
                   getSentimentColor('neutral'),
            fontWeight: 600
          }}>
            {data.avg_sentiment_score.toFixed(3)}
          </span>
          {' '}(thang điểm -1.0 đến 1.0)
        </Typography>
      </Box>
    </Box>
  );
};

export default SentimentChart;
