/**
 * Platform Breakdown Chart Component
 * Shows analytics breakdown by social media platform
 */

import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Box, Typography, Grid, Chip } from '@mui/material';
import { 
  Facebook, 
  VideoLibrary, 
  Newspaper 
} from '@mui/icons-material';
import { getPlatformLabel, formatNumber } from '../../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const PlatformBreakdown = ({ data }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={300}>
        <Typography color="text.secondary">Chưa có dữ liệu nền tảng</Typography>
      </Box>
    );
  }

  // Platform colors
  const platformColors = {
    facebook: '#1877f2',
    tiktok: '#000000',
    news: '#ff6b35',
    default: '#757575'
  };

  // Platform icons
  const platformIcons = {
    facebook: <Facebook fontSize="small" />,
    tiktok: <VideoLibrary fontSize="small" />,
    news: <Newspaper fontSize="small" />
  };

  const platforms = Object.keys(data);
  const postCounts = platforms.map(platform => data[platform]?.post_count || 0);
  const engagementCounts = platforms.map(platform => data[platform]?.total_engagement || 0);

  // Prepare chart data
  const chartData = {
    labels: platforms.map(p => getPlatformLabel(p)),
    datasets: [
      {
        label: 'Số bài viết',
        data: postCounts,
        backgroundColor: platforms.map(p => platformColors[p] || platformColors.default),
        borderRadius: 4,
        borderSkipped: false,
      }
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          title: function(context) {
            const platform = platforms[context[0].dataIndex];
            return getPlatformLabel(platform);
          },
          label: function(context) {
            const platform = platforms[context.dataIndex];
            const platformData = data[platform];
            return [
              `Bài viết: ${formatNumber(platformData.post_count)}`,
              `Tương tác: ${formatNumber(platformData.total_engagement)}`,
              `TB tương tác: ${platformData.avg_engagement.toFixed(1)}`
            ];
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
            return Number.isInteger(value) ? formatNumber(value) : '';
          }
        }
      }
    }
  };

  return (
    <Box>
      {/* Chart */}
      <Box className="chart-container" mb={3}>
        <Bar data={chartData} options={chartOptions} />
      </Box>

      {/* Platform Details */}
      <Grid container spacing={2}>
        {platforms.map((platform) => {
          const platformData = data[platform];
          const icon = platformIcons[platform];
          const color = platformColors[platform] || platformColors.default;
          
          return (
            <Grid item xs={12} key={platform}>
              <Box 
                display="flex" 
                alignItems="center" 
                justifyContent="space-between"
                p={2}
                borderRadius={1}
                bgcolor="grey.50"
              >
                <Box display="flex" alignItems="center" gap={1}>
                  <Box sx={{ color: color }}>
                    {icon}
                  </Box>
                  <Typography variant="body2" fontWeight={500}>
                    {getPlatformLabel(platform)}
                  </Typography>
                </Box>
                
                <Box display="flex" gap={2} alignItems="center">
                  <Chip 
                    label={`${formatNumber(platformData.post_count)} bài`}
                    size="small"
                    sx={{ backgroundColor: color + '20', color: color }}
                  />
                  <Chip 
                    label={`${formatNumber(platformData.total_engagement)} tương tác`}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </Box>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default PlatformBreakdown;
