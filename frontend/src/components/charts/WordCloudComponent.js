/**
 * Word Cloud Component
 * Displays trending keywords in a visually appealing word cloud
 */

import React from 'react';
import ReactWordcloud from 'react-wordcloud';
import { Box, Typography, CircularProgress } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { fetchWordCloudData, getSentimentColor } from '../../services/api';

const WordCloudComponent = ({ days = 7 }) => {
  const { 
    data: wordCloudData, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: ['wordcloud', days],
    queryFn: () => fetchWordCloudData(days),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={300}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !wordCloudData?.data || wordCloudData.data.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height={300}>
        <Typography color="text.secondary">
          {error ? 'Lỗi tải từ khóa' : 'Chưa có dữ liệu từ khóa'}
        </Typography>
      </Box>
    );
  }

  const words = wordCloudData.data.map(item => ({
    text: item.text,
    value: item.value,
    color: getSentimentColor(item.sentiment)
  }));

  const options = {
    fontFamily: 'Inter, sans-serif',
    fontSizes: [14, 60],
    fontWeight: 'bold',
    padding: 3,
    rotations: 2,
    rotationAngles: [-90, 0],
    scale: 'sqrt',
    spiral: 'archimedean',
    transitionDuration: 1000,
    enableTooltip: true,
    deterministic: false,
    tooltipOptions: {
      formatter: function(word) {
        return `${word.text}: ${word.value} lần xuất hiện`;
      }
    }
  };

  const callbacks = {
    onWordClick: (word) => {
      console.log(`Clicked word: ${word.text}`);
      // Could implement search functionality here
    },
    onWordMouseOver: (word) => {
      // Could implement hover effects here
    }
  };

  return (
    <Box>
      <div className="wordcloud-container">
        <ReactWordcloud
          words={words}
          options={options}
          callbacks={callbacks}
        />
      </div>
      
      {/* Legend */}
      <Box mt={2} display="flex" justifyContent="center" gap={2}>
        <Box display="flex" alignItems="center" gap={0.5}>
          <Box 
            width={12} 
            height={12} 
            borderRadius="50%" 
            bgcolor={getSentimentColor('positive')}
          />
          <Typography variant="caption">Tích cực</Typography>
        </Box>
        
        <Box display="flex" alignItems="center" gap={0.5}>
          <Box 
            width={12} 
            height={12} 
            borderRadius="50%" 
            bgcolor={getSentimentColor('negative')}
          />
          <Typography variant="caption">Tiêu cực</Typography>
        </Box>
        
        <Box display="flex" alignItems="center" gap={0.5}>
          <Box 
            width={12} 
            height={12} 
            borderRadius="50%" 
            bgcolor={getSentimentColor('neutral')}
          />
          <Typography variant="caption">Trung tính</Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default WordCloudComponent;
