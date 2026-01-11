import { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { 
  Activity, LogOut, KeyRound 
} from 'lucide-react';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';

const API_URL = 'http://localhost:8000';

const AdminLayout = () => {
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || 'Admin';
  
  const [isChangePassOpen, setIsChangePassOpen] = useState(false);
  const [passForm, setPassForm] = useState({ old_password: '', new_password: '', confirm_password: '' });
  const [isLoading, setIsLoading] = useState(false);

  // Xử lý đăng xuất
  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('username');
    localStorage.removeItem('user_email');
    toast.info('Đã đăng xuất thành công');
    navigate('/login');
  };

  // Xử lý đổi mật khẩu
  const handleChangePassword = async () => {
    if (!passForm.old_password || !passForm.new_password) return toast.error('Nhập thiếu thông tin');
    if (passForm.new_password !== passForm.confirm_password) return toast.error('Mật khẩu mới không khớp');
    
    setIsLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API_URL}/api/change-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ old_password: passForm.old_password, new_password: passForm.new_password })
      });
      if (res.ok) {
        toast.success('Đổi mật khẩu thành công!');
        setIsChangePassOpen(false);
        setPassForm({ old_password: '', new_password: '', confirm_password: '' });
      } else {
        const d = await res.json();
        toast.error(d.detail || 'Lỗi đổi mật khẩu');
      }
    } catch { toast.error('Lỗi kết nối Server'); } 
    finally { setIsLoading(false); }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* HEADER */}
      <header className="border-b border-border bg-background/95 backdrop-blur sticky top-0 z-50">
        <div className="flex h-50 items-center px-6 justify-between">
          <div className="flex items-center gap-2 font-bold text-xl text-primary">
            <div className="h-20 w-20 flex items-center justify-center">
                <img 
                    src="/logo2.png" 
                    alt="Veda Admin" 
                    className="w-full h-full object-contain" 
                />
             </div>
            <span>Hệ thống Admin</span>
          </div>
          
          <div className="flex items-center gap-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="h-8 w-8 rounded-full p-0 bg-secondary">
                  {username.charAt(0).toUpperCase()}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuLabel>Tài khoản</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => setIsChangePassOpen(true)} className="cursor-pointer">
                    <KeyRound className="mr-2 h-4 w-4"/> Đổi mật khẩu
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleLogout} className="text-destructive cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4"/> Đăng xuất
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* BODY: CHỈ CÒN CONTENT CHÍNH */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <main className="flex-1 overflow-y-auto p-6 bg-secondary/10">
          <Outlet />
        </main>
      </div>

      {/* MODAL ĐỔI MẬT KHẨU */}
      <Dialog open={isChangePassOpen} onOpenChange={setIsChangePassOpen}>
        <DialogContent>
            <DialogHeader><DialogTitle>Đổi mật khẩu</DialogTitle></DialogHeader>
            <div className="space-y-4 py-4">
                <div className="space-y-2"><Label>Mật khẩu cũ</Label><Input type="password" value={passForm.old_password} onChange={e=>setPassForm({...passForm, old_password: e.target.value})}/></div>
                <div className="space-y-2"><Label>Mật khẩu mới</Label><Input type="password" value={passForm.new_password} onChange={e=>setPassForm({...passForm, new_password: e.target.value})}/></div>
                <div className="space-y-2"><Label>Nhập lại mới</Label><Input type="password" value={passForm.confirm_password} onChange={e=>setPassForm({...passForm, confirm_password: e.target.value})}/></div>
            </div>
            <DialogFooter>
                <Button variant="outline" onClick={()=>setIsChangePassOpen(false)}>Hủy</Button>
                <Button onClick={handleChangePassword} disabled={isLoading}>Lưu</Button>
            </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminLayout;