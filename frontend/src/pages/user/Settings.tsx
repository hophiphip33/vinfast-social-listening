import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch'; // Đảm bảo đã import Switch
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { Save, Loader2, User, Shield, Lock, KeyRound, Youtube, Newspaper, AlertCircle } from 'lucide-react';

const API_URL = 'http://localhost:8000';

const Settings = () => {
  const queryClient = useQueryClient();
  
  // 1. State form cấu hình (Bổ sung active_sources)
  const [formData, setFormData] = useState({
    brand_name: '',
    keywords: '',
    email: '',
    active_sources: { youtube: true, news: true } // Mặc định bật hết
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  // 2. LẤY DỮ LIỆU USER TỪ API
  const { data: userProfile, isLoading, isError, error } = useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const token = localStorage.getItem('auth_token');
      if (!token) throw new Error("Chưa đăng nhập");

      const res = await fetch(`${API_URL}/api/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error('Không thể tải thông tin user');
      return await res.json();
    }
  });

  useEffect(() => {
    if (userProfile) {
      setFormData({
        brand_name: userProfile.brand_name || '',
        keywords: userProfile.keywords || '',
        email: userProfile.email || '',
        // Lấy config từ API, nếu thiếu thì mặc định True
        active_sources: userProfile.active_sources || { youtube: true, news: true }
      });
    }
  }, [userProfile]);

  // 3. API CẬP NHẬT CẤU HÌNH (Sửa lỗi 422 bằng cách gửi đủ active_sources)
  const updateSettingsMutation = useMutation({
    mutationFn: async (data: any) => {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API_URL}/api/users/settings`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Cập nhật thất bại');
      }
      return await res.json();
    },
    onSuccess: () => {
      toast.success('Đã lưu cấu hình thành công!');
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
    },
    onError: (err: Error) => toast.error(`Lỗi: ${err.message}`)
  });

  const handleSaveSettings = () => {
    // Gửi đầy đủ 3 trường mà Backend yêu cầu
    updateSettingsMutation.mutate({
      brand_name: formData.brand_name,
      keywords: formData.keywords,
      active_sources: formData.active_sources 
    });
  };

  // 4. API ĐỔI MẬT KHẨU
  const changePasswordMutation = useMutation({
    mutationFn: async () => {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API_URL}/api/users/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          current_password: passwordData.currentPassword,
          new_password: passwordData.newPassword
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Đổi mật khẩu thất bại');
      }
      return await res.json();
    },
    onSuccess: () => {
      toast.success('Đổi mật khẩu thành công!');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    },
    onError: (err: Error) => toast.error(err.message)
  });

  const handleChangePassword = () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      return toast.error("Mật khẩu mới không khớp");
    }
    if (passwordData.newPassword.length < 6) {
      return toast.error("Mật khẩu mới phải có ít nhất 6 ký tự");
    }
    changePasswordMutation.mutate();
  };

  if (isLoading) return <div className="p-8 text-center flex justify-center items-center gap-2"><Loader2 className="animate-spin"/> Đang tải...</div>;
  
  if (isError) return (
    <div className="p-8 text-center text-red-500">
        <AlertCircle className="h-10 w-10 mx-auto mb-2"/>
        <p>Lỗi tải dữ liệu: {error instanceof Error ? error.message : 'Unknown error'}</p>
        <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>Thử lại</Button>
    </div>
  );

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto p-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Cài đặt hệ thống</h1>
        <p className="text-muted-foreground mt-2">Quản lý từ khóa và nguồn dữ liệu.</p>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          <TabsTrigger value="general">Cấu hình chung</TabsTrigger>
          <TabsTrigger value="security">Bảo mật</TabsTrigger>
        </TabsList>

        {/* TAB CẤU HÌNH CHUNG */}
        <TabsContent value="general" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Cấu hình Theo dõi</CardTitle>
              <CardDescription>Chọn nguồn dữ liệu và từ khóa để hệ thống thu thập.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              {/* PHẦN SWITCH NGUỒN TIN (QUAN TRỌNG) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-4 rounded-lg border bg-secondary/20">
                    <div className="flex items-center gap-3">
                        <Youtube className="h-5 w-5 text-red-600" />
                        <span className="font-medium">YouTube</span>
                    </div>
                    <Switch 
                        checked={formData.active_sources?.youtube ?? true}
                        onCheckedChange={(c) => setFormData({
                            ...formData, 
                            active_sources: { ...formData.active_sources, youtube: c }
                        })}
                    />
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg border bg-secondary/20">
                    <div className="flex items-center gap-3">
                        <Newspaper className="h-5 w-5 text-blue-600" />
                        <span className="font-medium">Báo chí (News)</span>
                    </div>
                    <Switch 
                        checked={formData.active_sources?.news ?? true}
                        onCheckedChange={(c) => setFormData({
                            ...formData, 
                            active_sources: { ...formData.active_sources, news: c }
                        })}
                    />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Tên Thương hiệu</Label>
                <div className="relative">
                  <Shield className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input 
                    className="pl-9"
                    value={formData.brand_name}
                    onChange={(e) => setFormData({...formData, brand_name: e.target.value})}
                    placeholder="Ví dụ: VinFast"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Từ khóa liên quan</Label>
                <Textarea 
                  className="min-h-[100px]"
                  value={formData.keywords}
                  onChange={(e) => setFormData({...formData, keywords: e.target.value})}
                  placeholder="ngăn cách bằng dấu phẩy: vf8, xe điện, pin..."
                />
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleSaveSettings} disabled={updateSettingsMutation.isPending}>
                  {updateSettingsMutation.isPending ? <Loader2 className="animate-spin mr-2"/> : <Save className="mr-2"/>}
                  Lưu cấu hình
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB BẢO MẬT */}
        <TabsContent value="security" className="space-y-4 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Thông tin & Bảo mật</CardTitle>
              <CardDescription>Quản lý mật khẩu đăng nhập.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Email đăng nhập</Label>
                <div className="relative">
                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input value={formData.email} disabled className="pl-9 bg-muted/50" />
                </div>
              </div>

              <div className="border-t pt-4">
                <h3 className="text-sm font-medium mb-4 flex items-center gap-2">
                    <Lock className="h-4 w-4" /> Đổi mật khẩu
                </h3>
                <div className="grid gap-4 max-w-md">
                    <div className="space-y-2">
                        <Label>Mật khẩu hiện tại</Label>
                        <div className="relative">
                            <KeyRound className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                            <Input 
                                type="password" 
                                className="pl-9"
                                value={passwordData.currentPassword}
                                onChange={(e) => setPasswordData({...passwordData, currentPassword: e.target.value})}
                            />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label>Mật khẩu mới</Label>
                        <Input 
                            type="password"
                            value={passwordData.newPassword}
                            onChange={(e) => setPasswordData({...passwordData, newPassword: e.target.value})}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label>Xác nhận mật khẩu mới</Label>
                        <Input 
                            type="password"
                            value={passwordData.confirmPassword}
                            onChange={(e) => setPasswordData({...passwordData, confirmPassword: e.target.value})}
                        />
                    </div>
                    <Button onClick={handleChangePassword} disabled={changePasswordMutation.isPending} className="mt-2">
                         {changePasswordMutation.isPending ? 'Đang xử lý...' : 'Cập nhật mật khẩu'}
                    </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Settings;