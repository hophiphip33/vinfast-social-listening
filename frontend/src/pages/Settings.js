/**
 * Settings Page
 * Configuration and system management interface
 */

import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Alert,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText
} from '@mui/material';
import {
  Save,
  RestoreFromTrash,
  Download,
  Upload,
  Security,
  DataUsage,
  Schedule
} from '@mui/icons-material';

// Hooks and services
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getSystemStatus, resetAllData } from '../services/api';
import toast from 'react-hot-toast';

const Settings = () => {
  const [settings, setSettings] = useState({
    // Collection settings
    maxPostsPerBatch: 100,
    crawlDelay: 5,
    autoCollection: false,
    collectionSchedule: 'daily',
    
    // Processing settings
    autoSentimentAnalysis: true,
    modelName: 'vinai/phobert-base',
    maxSequenceLength: 256,
    
    // Database settings
    dataRetentionDays: 365,
    autoBackup: false,
    
    // Notification settings
    emailNotifications: false,
    slackNotifications: false
  });

  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null });
  const queryClient = useQueryClient();

  // Get system status
  const { data: systemStatus } = useQuery({
    queryKey: ['system-status'],
    queryFn: getSystemStatus,
  });

  // Reset data mutation
  const resetDataMutation = useMutation({
    mutationFn: resetAllData,
    onSuccess: (data) => {
      toast.success(data.message || 'Đã xóa tất cả dữ liệu');
      queryClient.invalidateQueries();
      setConfirmDialog({ open: false, action: null });
    },
    onError: (error) => {
      toast.error(error.message || 'Lỗi khi xóa dữ liệu');
    }
  });

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleSaveSettings = () => {
    // In a real app, this would save to backend
    toast.success('Cài đặt đã được lưu');
  };

  const handleConfirmAction = (action) => {
    if (action === 'reset') {
      resetDataMutation.mutate();
    }
    // Add other actions as needed
  };

  const confirmActions = {
    reset: {
      title: 'Xác nhận xóa dữ liệu',
      message: 'Bạn có chắc chắn muốn xóa tất cả dữ liệu đã thu thập? Hành động này không thể hoàn tác.',
      color: 'error'
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Cài đặt hệ thống
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Cấu hình và quản lý hệ thống Social Listening
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
            <strong>Trạng thái hệ thống:</strong> {' '}
            Database: {systemStatus.data.database} • {' '}
            Model: {systemStatus.data.sentiment_model} • {' '}
            API: v{systemStatus.data.api_version}
          </Typography>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Collection Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={3}>
                Cài đặt thu thập dữ liệu
              </Typography>
              
              <Box mb={3}>
                <TextField
                  fullWidth
                  label="Số bài viết tối đa mỗi lần"
                  type="number"
                  value={settings.maxPostsPerBatch}
                  onChange={(e) => handleSettingChange('maxPostsPerBatch', parseInt(e.target.value))}
                  margin="normal"
                />
                
                <TextField
                  fullWidth
                  label="Độ trễ giữa các request (giây)"
                  type="number"
                  value={settings.crawlDelay}
                  onChange={(e) => handleSettingChange('crawlDelay', parseInt(e.target.value))}
                  margin="normal"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoCollection}
                      onChange={(e) => handleSettingChange('autoCollection', e.target.checked)}
                    />
                  }
                  label="Thu thập tự động"
                  sx={{ mt: 2 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Processing Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={3}>
                Cài đặt xử lý dữ liệu
              </Typography>
              
              <Box mb={3}>
                <TextField
                  fullWidth
                  label="Tên model sentiment"
                  value={settings.modelName}
                  onChange={(e) => handleSettingChange('modelName', e.target.value)}
                  margin="normal"
                />
                
                <TextField
                  fullWidth
                  label="Độ dài chuỗi tối đa"
                  type="number"
                  value={settings.maxSequenceLength}
                  onChange={(e) => handleSettingChange('maxSequenceLength', parseInt(e.target.value))}
                  margin="normal"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.autoSentimentAnalysis}
                      onChange={(e) => handleSettingChange('autoSentimentAnalysis', e.target.checked)}
                    />
                  }
                  label="Phân tích tình cảm tự động"
                  sx={{ mt: 2 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Data Management */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} mb={3}>
                Quản lý dữ liệu
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Thời gian lưu trữ (ngày)"
                    type="number"
                    value={settings.dataRetentionDays}
                    onChange={(e) => handleSettingChange('dataRetentionDays', parseInt(e.target.value))}
                    helperText="Dữ liệu cũ hơn sẽ được tự động xóa"
                  />
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={settings.autoBackup}
                        onChange={(e) => handleSettingChange('autoBackup', e.target.checked)}
                      />
                    }
                    label="Sao lưu tự động"
                  />
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Box display="flex" gap={1}>
                    <Button
                      variant="outlined"
                      startIcon={<Download />}
                      size="small"
                    >
                      Tải xuống
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<Upload />}
                      size="small"
                    >
                      Tải lên
                    </Button>
                  </Box>
                </Grid>
              </Grid>
              
              <Divider sx={{ my: 3 }} />
              
              {/* Dangerous Actions */}
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="body2">
                  <strong>Cảnh báo:</strong> Các hành động bên dưới có thể ảnh hưởng đến dữ liệu hệ thống.
                </Typography>
              </Alert>
              
              <Button
                variant="outlined"
                color="error"
                startIcon={<RestoreFromTrash />}
                onClick={() => setConfirmDialog({ open: true, action: 'reset' })}
                disabled={resetDataMutation.isLoading}
              >
                {resetDataMutation.isLoading ? 'Đang xóa...' : 'Xóa tất cả dữ liệu'}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Save Settings */}
        <Grid item xs={12}>
          <Box display="flex" justifyContent="flex-end" gap={2}>
            <Button
              variant="outlined"
              onClick={() => {
                // Reset to default settings
                toast.info('Đã khôi phục cài đặt mặc định');
              }}
            >
              Khôi phục mặc định
            </Button>
            <Button
              variant="contained"
              startIcon={<Save />}
              onClick={handleSaveSettings}
            >
              Lưu cài đặt
            </Button>
          </Box>
        </Grid>
      </Grid>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, action: null })}
      >
        {confirmDialog.action && confirmActions[confirmDialog.action] && (
          <>
            <DialogTitle sx={{ color: confirmActions[confirmDialog.action].color + '.main' }}>
              {confirmActions[confirmDialog.action].title}
            </DialogTitle>
            <DialogContent>
              <DialogContentText className="vietnamese-text">
                {confirmActions[confirmDialog.action].message}
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button 
                onClick={() => setConfirmDialog({ open: false, action: null })}
                color="inherit"
              >
                Hủy
              </Button>
              <Button 
                onClick={() => handleConfirmAction(confirmDialog.action)}
                color={confirmActions[confirmDialog.action].color}
                variant="contained"
                disabled={resetDataMutation.isLoading}
              >
                {resetDataMutation.isLoading ? 'Đang thực hiện...' : 'Xác nhận'}
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default Settings;
