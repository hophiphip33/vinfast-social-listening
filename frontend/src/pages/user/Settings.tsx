import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  Save, Loader2, User, Shield, Lock, KeyRound, 
  Youtube, Newspaper, AlertCircle, RefreshCcw, Clock, CheckCircle2 
} from 'lucide-react';

// Sử dụng biến môi trường nếu có, không thì fallback về localhost
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Cấu hình thời gian chờ: 1 giờ = 3600 giây
const COOLDOWN_TIME = 3600; 
const STORAGE_KEY = 'last_collect_timestamp';

const Settings = () => {
  const queryClient = useQueryClient();
  
  // --- STATE CHO NÚT THU THẬP ---
  const [isCollecting, setIsCollecting] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  // --- STATE FORM CẤU HÌNH ---
  const [formData, setFormData] = useState({
    brand_name: '',
    keywords: '',
    email: '',
    active_sources: { youtube: true, news: true }
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  // --- LOGIC ĐẾM NGƯỢC (CLIENT-SIDE) ---
  useEffect(() => {
    const lastRun = localStorage.getItem(STORAGE_KEY);
    if (lastRun) {
      const lastTime = parseInt(lastRun, 10);
      const now = Date.now();
      const diffSeconds = Math.floor((now - lastTime) / 1000);
      
      if (diffSeconds < COOLDOWN_TIME) {
        setCooldown(COOLDOWN_TIME - diffSeconds);
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown((prev) => {
          if (prev <= 1) {
             localStorage.removeItem(STORAGE_KEY);
             return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h} giờ ${m} phút`;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  // --- API LẤY USER ---
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
        active_sources: userProfile.active_sources || { youtube: true, news: true }
      });
    }
  }, [userProfile]);

  // --- API KÍCH HOẠT THU THẬP ---
  const handleTriggerCollect = async () => {
    if (cooldown > 0) return;
    setIsCollecting(true);
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API_URL}/api/collect/me`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        toast.success("Đã kích hoạt quét dữ liệu!", {
          description: "Hệ thống đang chạy ngầm, vui lòng đợi kết quả."
        });
        const now = Date.now();
        localStorage.setItem(STORAGE_KEY, now.toString());
        setCooldown(COOLDOWN_TIME); 
      } else {
        const err = await res.json();
        if (res.status === 429) {
            toast.warning("Thao tác quá nhanh", { description: err.detail });
        } else {
            toast.error("Lỗi", { description: err.detail });
        }
      }
    } catch (e) {
      toast.error("Lỗi kết nối Server");
    } finally {
      setIsCollecting(false);
    }
  };

  // --- API CẬP NHẬT CẤU HÌNH ---
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
    updateSettingsMutation.mutate({
      brand_name: formData.brand_name,
      keywords: formData.keywords,
      active_sources: formData.active_sources 
    });
  };

  // --- API ĐỔI MẬT KHẨU ---
  const changePasswordMutation = useMutation({
    mutationFn: async () => {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API_URL}/api/change-password`, {
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
          
          {/* --- CARD 1: CẬP NHẬT DỮ LIỆU (Đã đồng bộ giao diện) --- */}
          <Card>
            <CardHeader className="pb-3">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            <RefreshCcw className="h-5 w-5" /> Cập nhật dữ liệu
                        </CardTitle>
                        <CardDescription>
                            Kích hoạt robot quét dữ liệu thủ công (Giới hạn 1 lần/giờ).
                        </CardDescription>
                    </div>
                    
                    {/* Nút bấm đặt bên phải cho gọn */}
                    <Button 
                        onClick={handleTriggerCollect} 
                        disabled={isCollecting || cooldown > 0}
                        variant={cooldown > 0 ? "outline" : "default"} // Đổi style nút khi chờ
                        className={cooldown > 0 ? "border-dashed" : ""}
                    >
                        {isCollecting ? (
                            <><Loader2 className="mr-2 h-4 w-4 animate-spin"/> Đang xử lý...</>
                        ) : cooldown > 0 ? (
                            <><Clock className="mr-2 h-4 w-4 text-orange-500"/> Chờ {formatTime(cooldown)}</>
                        ) : (
                            <><RefreshCcw className="mr-2 h-4 w-4"/> Quét ngay</>
                        )}
                    </Button>
                </div>
            </CardHeader>
          </Card>

          {/* --- CARD 2: CẤU HÌNH THEO DÕI --- */}
          <Card>
            <CardHeader>
              <CardTitle>Cấu hình Theo dõi</CardTitle>
              <CardDescription>Chọn nguồn dữ liệu và từ khóa để hệ thống thu thập.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-4 rounded-lg border bg-secondary/10 hover:bg-secondary/20 transition-colors">
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
                <div className="flex items-center justify-between p-4 rounded-lg border bg-secondary/10 hover:bg-secondary/20 transition-colors">
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
                  className="min-h-[100px] font-mono text-sm"
                  value={formData.keywords}
                  onChange={(e) => setFormData({...formData, keywords: e.target.value})}
                  placeholder="ngăn cách bằng dấu phẩy: vf8, xe điện, pin..."
                />
              </div>

              <div className="flex justify-end pt-2">
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
                         {changePasswordMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin"/> : null} 
                         Cập nhật mật khẩu
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