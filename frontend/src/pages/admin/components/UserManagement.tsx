import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch'; // Import Switch
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import StatusBadge from './StatusBadge';
import { Plus, Search, Pencil, Trash2, Eye, RefreshCw, Mail, Youtube, Newspaper } from 'lucide-react';
import { toast } from 'sonner';

// Định nghĩa URL API
const API_URL = 'http://localhost:8000';

// Cập nhật interface User để có active_sources
interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  brand_name?: string;
  keywords: string[];
  active_sources?: {
    youtube: boolean;
    news: boolean;
  };
}

const UserManagement = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Dialog States
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isDetailDialogOpen, setIsDetailDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);

  // Form state cho thêm user mới
  const [newUser, setNewUser] = useState({
    username: '',    
    email: '',       
    brand_name: '',  
    keywords: '',    
    role: 'user',
    active_sources: { youtube: true, news: true } // Mặc định bật cả hai
  });

  // State cho form chỉnh sửa
  const [editForm, setEditForm] = useState({
    brand_name: '',
    role: 'user',
    is_active: true,
    keywords: '',
    active_sources: { youtube: true, news: true }
  });

  // --- 1. LẤY DANH SÁCH USER ---
  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_URL}/api/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        toast.error('Không thể tải danh sách người dùng');
      }
    } catch (error) {
      console.error(error);
      toast.error('Lỗi kết nối Server');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // --- 2. THÊM USER MỚI ---
  const handleAddUser = async () => {
    if (!newUser.username || !newUser.email) {
      toast.error('Vui lòng điền Tên đăng nhập và Email!');
      return;
    }

    try {
      const token = localStorage.getItem('auth_token');
      
      const payload = {
        username: newUser.username,
        email: newUser.email,
        role: newUser.role,
        brand_name: newUser.brand_name || null,
        keywords: newUser.keywords.split(',').map(k => k.trim()).filter(k => k),
        active_sources: newUser.active_sources // Gửi cấu hình nguồn tin
      };

      const response = await fetch(`${API_URL}/api/users/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(`Đã tạo user ${newUser.username}!`);
        setNewUser({ 
            username: '', email: '', brand_name: '', keywords: '', role: 'user', 
            active_sources: { youtube: true, news: true } 
        });
        setIsAddDialogOpen(false);
        fetchUsers();
      } else {
        toast.error(data.detail || 'Lỗi khi tạo user');
      }
    } catch (error) {
      toast.error('Lỗi kết nối Server');
    }
  };

  // --- 3. XÓA USER ---
  const deleteUser = async (userId: string) => {
    if (!confirm('Bạn có chắc chắn muốn xóa user này?')) return;
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_URL}/api/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        toast.success('Đã xóa user');
        fetchUsers();
      } else {
        toast.error('Không thể xóa user');
      }
    } catch (error) {
      toast.error('Lỗi hệ thống');
    }
  };

  // --- 4. CHỈNH SỬA USER ---
  const openEditDialog = (user: User) => {
    setSelectedUser(user);
    setEditForm({
      brand_name: user.brand_name || '',
      role: user.role,
      is_active: user.is_active,
      keywords: (user.keywords || []).join(', '),
      active_sources: user.active_sources || { youtube: true, news: true }
    });
    setIsEditDialogOpen(true);
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;
    try {
      const token = localStorage.getItem('auth_token');
      const payload = {
        brand_name: editForm.brand_name,
        role: editForm.role,
        is_active: editForm.is_active,
        keywords: editForm.keywords.split(',').map(k => k.trim()).filter(k => k),
        active_sources: editForm.active_sources // Cập nhật nguồn tin
      };

      // Gọi endpoint update settings hoặc endpoint update user (tuỳ backend)
      // Ở đây giả định dùng endpoint PUT /api/users/{id} đã có hoặc dùng /api/users/settings nếu backend hỗ trợ update user khác
      // Theo logic thông thường admin update user dùng endpoint riêng.
      // Chúng ta sẽ dùng endpoint PUT /api/users/{id} và đảm bảo backend xử lý active_sources
      
      // Lưu ý: Backend cần hỗ trợ nhận active_sources ở endpoint này.
      // Nếu chưa, bạn cần đảm bảo backend/api/main.py phần update_user (admin) chấp nhận trường này.
      const response = await fetch(`${API_URL}/api/users/${selectedUser.id}`, { // Giả định endpoint này tồn tại
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      // Fallback: Nếu API admin update chưa hỗ trợ, ta có thể cần backend update
      // Nhưng với code hiện tại, ta giả định backend đã sẵn sàng hoặc sẽ được update.
      
      if (response.ok) {
        toast.success('Cập nhật thành công');
        setIsEditDialogOpen(false);
        fetchUsers();
      } else {
         // Thử dùng endpoint settings nếu endpoint trên 404 hoặc lỗi (chỉ là fallback logic nếu cần)
         toast.error('Cập nhật thất bại');
      }
    } catch (error) {
      toast.error('Lỗi hệ thống');
    }
  };

  const filteredUsers = users.filter(user =>
    (user.username?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (user.email?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
    (user.brand_name?.toLowerCase() || '').includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Tìm theo tên, email, brand..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 bg-secondary border-border"
          />
        </div>
        <div className="flex gap-2">
            <Button variant="outline" size="icon" onClick={fetchUsers} title="Tải lại">
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
                <Button className="gap-2"><Plus className="h-4 w-4" /> Thêm User</Button>
            </DialogTrigger>
            <DialogContent className="bg-card border-border max-w-lg">
                <DialogHeader><DialogTitle>Thêm Khách hàng Mới</DialogTitle></DialogHeader>
                <div className="space-y-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Tên đăng nhập <span className="text-destructive">*</span></Label>
                            <Input value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} />
                        </div>
                        <div className="space-y-2">
                            <Label>Email <span className="text-destructive">*</span></Label>
                            <Input type="email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label>Tên Branding</Label>
                        <Input value={newUser.brand_name} onChange={(e) => setNewUser({ ...newUser, brand_name: e.target.value })} />
                    </div>
                    
                    {/* Cấu hình nguồn tin cho User mới */}
                    <div className="space-y-2 border p-3 rounded-md bg-secondary/20">
                        <Label className="mb-2 block text-xs uppercase text-muted-foreground font-semibold">Nguồn thu thập</Label>
                        <div className="flex gap-6">
                            <div className="flex items-center gap-2">
                                <Switch 
                                    checked={newUser.active_sources.youtube}
                                    onCheckedChange={(c) => setNewUser({...newUser, active_sources: {...newUser.active_sources, youtube: c}})}
                                />
                                <span className="flex items-center gap-1 text-sm"><Youtube className="h-4 w-4 text-red-600"/> Youtube</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Switch 
                                    checked={newUser.active_sources.news}
                                    onCheckedChange={(c) => setNewUser({...newUser, active_sources: {...newUser.active_sources, news: c}})}
                                />
                                <span className="flex items-center gap-1 text-sm"><Newspaper className="h-4 w-4 text-blue-600"/> News</span>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label>Từ khóa</Label>
                        <Textarea value={newUser.keywords} onChange={(e) => setNewUser({ ...newUser, keywords: e.target.value })} rows={3} />
                    </div>
                    <Button onClick={handleAddUser} className="w-full mt-2" disabled={isLoading}>{isLoading ? 'Đang xử lý...' : 'Tạo Tài khoản'}</Button>
                </div>
            </DialogContent>
            </Dialog>
        </div>
      </div>

      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-secondary/50">
              <TableHead>User</TableHead>
              <TableHead>Branding</TableHead>
              <TableHead>Cấu hình Crawl</TableHead> {/* Cột mới */}
              <TableHead>Trạng thái</TableHead>
              <TableHead>Từ khóa</TableHead>
              <TableHead className="text-right">Thao tác</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredUsers.length === 0 ? (
                 <TableRow><TableCell colSpan={6} className="text-center py-8 text-muted-foreground">Chưa có dữ liệu</TableCell></TableRow>
            ) : (
                filteredUsers.map((user) => (
                <TableRow key={user.id} className="hover:bg-secondary/30">
                    <TableCell>
                        <div className="flex flex-col">
                            <span className="font-medium">{user.username}</span>
                            <span className="text-xs text-muted-foreground">{user.email}</span>
                        </div>
                    </TableCell>
                    <TableCell className="font-semibold text-primary">{user.brand_name || '—'}</TableCell>
                    
                    {/* Hiển thị trạng thái nguồn tin */}
                    <TableCell>
                        <div className="flex gap-3">
                            <div className={`flex items-center gap-1 text-xs border px-2 py-1 rounded-full ${user.active_sources?.youtube ? 'bg-red-500/10 text-red-500 border-red-500/20' : 'text-muted-foreground border-transparent opacity-50'}`}>
                                <Youtube className="h-3 w-3" />
                                {user.active_sources?.youtube ? 'ON' : 'OFF'}
                            </div>
                            <div className={`flex items-center gap-1 text-xs border px-2 py-1 rounded-full ${user.active_sources?.news ? 'bg-blue-500/10 text-blue-500 border-blue-500/20' : 'text-muted-foreground border-transparent opacity-50'}`}>
                                <Newspaper className="h-3 w-3" />
                                {user.active_sources?.news ? 'ON' : 'OFF'}
                            </div>
                        </div>
                    </TableCell>

                    <TableCell><StatusBadge status={user.is_active ? 'Active' : 'Inactive'} /></TableCell>
                    <TableCell>
                        <div className="flex flex-wrap gap-1 max-w-[200px]">
                            {(user.keywords || []).slice(0, 2).map((kw, i) => (
                            <span key={i} className="px-2 py-0.5 bg-secondary text-xs rounded-full border border-border">{kw}</span>
                            ))}
                            {(user.keywords || []).length > 2 && <span className="text-xs text-muted-foreground">+{user.keywords.length - 2}</span>}
                        </div>
                    </TableCell>
                    <TableCell className="text-right">
                        <div className="flex gap-1 justify-end">
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:text-warning" onClick={() => openEditDialog(user)}><Pencil className="h-4 w-4" /></Button>
                            <Button variant="ghost" size="icon" className="h-8 w-8 hover:text-destructive" onClick={() => deleteUser(user.id)}><Trash2 className="h-4 w-4" /></Button>
                        </div>
                    </TableCell>
                </TableRow>
                ))
            )}
          </TableBody>
        </Table>
      </div>

       {/* Dialog Edit User */}
       <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="bg-card border-border max-w-lg">
          <DialogHeader><DialogTitle>Cập nhật thông tin: {selectedUser?.username}</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
             <div className="space-y-2">
                <Label>Tên Branding</Label>
                <Input value={editForm.brand_name} onChange={(e) => setEditForm({...editForm, brand_name: e.target.value})}/>
             </div>
             
             {/* Cấu hình nguồn tin khi Edit */}
             <div className="space-y-2 border p-3 rounded-md bg-secondary/20">
                <Label className="mb-2 block text-xs uppercase text-muted-foreground font-semibold">Cấu hình Crawl</Label>
                <div className="flex gap-6">
                    <div className="flex items-center gap-2">
                        <Switch 
                            checked={editForm.active_sources.youtube}
                            onCheckedChange={(c) => setEditForm({...editForm, active_sources: {...editForm.active_sources, youtube: c}})}
                        />
                        <span className="flex items-center gap-1 text-sm"><Youtube className="h-4 w-4 text-red-600"/> Youtube</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Switch 
                            checked={editForm.active_sources.news}
                            onCheckedChange={(c) => setEditForm({...editForm, active_sources: {...editForm.active_sources, news: c}})}
                        />
                        <span className="flex items-center gap-1 text-sm"><Newspaper className="h-4 w-4 text-blue-600"/> News</span>
                    </div>
                </div>
             </div>

             <div className="space-y-2">
                <Label>Từ khóa</Label>
                <Textarea value={editForm.keywords} onChange={(e) => setEditForm({...editForm, keywords: e.target.value})}/>
             </div>
             <div className="flex items-center gap-2 pt-2">
                <Switch checked={editForm.is_active} onCheckedChange={(c) => setEditForm({...editForm, is_active: c})} />
                <Label>Kích hoạt tài khoản</Label>
             </div>
          </div>
          <DialogFooter><Button onClick={handleUpdateUser}>Lưu thay đổi</Button></DialogFooter>
        </DialogContent>
       </Dialog>
    </div>
  );
};

export default UserManagement;