import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Lock, Mail, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

// Import logo trực tiếp
import logoVeda from '@/assets/logo2.png'; 

const API_URL = 'http://127.0.0.1:8000';

const Login = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // --- STATE CHO PHẦN QUÊN MẬT KHẨU ---
  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [isResetting, setIsResetting] = useState(false);
  const [resetError, setResetError] = useState('');

  // Xử lý đăng nhập
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const response = await fetch(`${API_URL}/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        // Lưu thông tin Token và Role
        localStorage.setItem('auth_token', data.access_token);
        localStorage.setItem('user_role', data.role || 'user');
        localStorage.setItem('user_email', email);

        // --- [SỬA ĐỔI QUAN TRỌNG] ---
        // Ưu tiên lấy username từ Backend trả về (data.username)
        // Nếu Backend không trả về username thì mới dùng fallback là email cắt ra
        const finalUsername = data.username || email.split('@')[0];
        localStorage.setItem('username', finalUsername);
        // ----------------------------

        toast.success(`Xin chào, ${finalUsername}!`);
        
        if (data.role === 'admin') {
          navigate('/admin', { replace: true });
        } else {
          navigate('/user', { replace: true });
        }
      } else {
        toast.error(data.detail || 'Đăng nhập thất bại.');
      }
    } catch (error) {
      console.error("Login error:", error);
      toast.error('Lỗi kết nối Server Backend');
    } finally {
      setIsLoading(false);
    }
  };

  // --- XỬ LÝ QUÊN MẬT KHẨU ---
  const handleForgotPassword = async () => {
    setResetError(''); 

    if (!resetEmail) {
      setResetError("Vui lòng nhập email.");
      return;
    }

    setIsResetting(true);

    try {
      const res = await fetch(`${API_URL}/api/auth/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: resetEmail })
      });

      if (res.ok) {
        toast.success("Mật khẩu mới đã được gửi vào email của bạn!");
        setIsForgotPasswordOpen(false); 
        setResetEmail(""); 
      } else {
        if (res.status === 404) {
          setResetError("Email này không tồn tại trong hệ thống.");
        } else {
          const data = await res.json();
          setResetError(data.detail || "Có lỗi xảy ra, vui lòng thử lại.");
        }
      }
    } catch (error) {
      setResetError("Lỗi kết nối Server.");
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:20px_20px]" />
      <div className="absolute h-full w-full bg-background [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)]" />
      
      <Card className="w-full max-w-md relative z-10 border-border/50 bg-card/50 backdrop-blur-xl animate-fade-in shadow-2xl">
        <CardHeader className="space-y-1 text-center pt-4">
          
          {/* Logo */}
          <div className="flex justify-center mb-1">
            <div className="h-40 w-40 flex items-center justify-center">
              <img 
                src="/logo2.png" 
                alt="Veda Logo" 
                className="w-full h-full object-contain drop-shadow-md" 
              />
            </div>
          </div>

          
          <CardDescription className="text-base">
            Hệ thống Social Listening thông minh
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleLogin}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input 
                  id="email" 
                  placeholder="user@example.com" 
                  type="email" 
                  className="pl-9"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">Mật khẩu</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input 
                  id="password" 
                  type="password" 
                  className="pl-9"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>

              {/* Nút Quên mật khẩu */}
              <div className="flex justify-end pt-1">
                <Dialog open={isForgotPasswordOpen} onOpenChange={setIsForgotPasswordOpen}>
                  <DialogTrigger asChild>
                    <span 
                      className="text-xs text-primary cursor-pointer hover:underline font-medium transition-colors"
                      onClick={() => {
                        setResetEmail(email);
                        setResetError('');
                      }}
                    >
                      Quên mật khẩu?
                    </span>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-[425px]">
                    <DialogHeader>
                      <DialogTitle>Quên mật khẩu</DialogTitle>
                      <DialogDescription>
                        Nhập email đã đăng ký để nhận mật khẩu mới.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="grid gap-4 py-4">
                      <div className="space-y-2">
                        <Label htmlFor="reset-email">Email</Label>
                        <Input
                          id="reset-email"
                          placeholder="name@example.com"
                          value={resetEmail}
                          onChange={(e) => {
                            setResetEmail(e.target.value);
                            setResetError('');
                          }}
                          className={resetError ? "border-destructive focus-visible:ring-destructive" : ""}
                        />
                      </div>
                      
                      {resetError && (
                        <div className="text-center">
                          <p className="text-xs text-destructive font-medium animate-in fade-in slide-in-from-top-1">
                            {resetError}
                          </p>
                        </div>
                      )}
                      
                    </div>
                    <DialogFooter>
                      <Button onClick={handleForgotPassword} disabled={isResetting}>
                        {isResetting ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Đang gửi...
                          </>
                        ) : (
                          "Gửi yêu cầu"
                        )}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
              
            </div>
          </CardContent>
          <CardFooter>
            <Button className="w-full" type="submit" disabled={isLoading}>
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Đang xử lý...
                </div>
              ) : 'Đăng nhập'}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
};

export default Login;