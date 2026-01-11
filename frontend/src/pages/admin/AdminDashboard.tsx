import { useSearchParams } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import UserManagement from './components/UserManagement';
import SystemConfig from './components/SystemConfig';
import DataModeration from './components/DataModeration';
import SystemHealth from './components/SystemHealth';
import { Users, Settings, FileSearch, Activity } from 'lucide-react';

const AdminDashboard = () => {
  // Kết nối Tabs với URL
  const [searchParams, setSearchParams] = useSearchParams();
  const currentTab = searchParams.get('tab') || 'users';

  // Hàm cập nhật URL khi bấm tab
  const handleTabChange = (value: string) => {
    setSearchParams({ tab: value });
  };

  return (
    <Tabs value={currentTab} onValueChange={handleTabChange} className="space-y-6">
      {/* Ẩn TabsList trên Desktop nếu muốn Sidebar làm menu chính, 
          hoặc giữ lại để có menu ngang phụ trợ */}
      <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-flex bg-secondary/50 p-1">
        <TabsTrigger value="users" className="gap-2">
          <Users className="h-4 w-4" /> <span className="hidden sm:inline">Khách hàng</span>
        </TabsTrigger>
        <TabsTrigger value="config" className="gap-2">
          <Settings className="h-4 w-4" /> <span className="hidden sm:inline">Cấu hình</span>
        </TabsTrigger>
        <TabsTrigger value="moderation" className="gap-2">
          <FileSearch className="h-4 w-4" /> <span className="hidden sm:inline">Kiểm duyệt</span>
        </TabsTrigger>
        <TabsTrigger value="health" className="gap-2">
          <Activity className="h-4 w-4" /> <span className="hidden sm:inline">Giám sát</span>
        </TabsTrigger>
      </TabsList>

      <TabsContent value="users" className="mt-6">
        <div className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold">Quản lý Khách hàng & Từ khóa</h2>
            <p className="text-muted-foreground">Quản lý tài khoản người dùng và từ khóa theo dõi.</p>
          </div>
          <UserManagement />
        </div>
      </TabsContent>

      <TabsContent value="config" className="mt-6">
        <div className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold">Cấu hình Hệ thống</h2>
            <p className="text-muted-foreground">Quản lý từ khóa global và API key.</p>
          </div>
          <SystemConfig />
        </div>
      </TabsContent>

      <TabsContent value="moderation" className="mt-6">
        <div className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold">Kiểm duyệt Dữ liệu</h2>
            <p className="text-muted-foreground">Đánh dấu spam và huấn luyện lại AI.</p>
          </div>
          <DataModeration />
        </div>
      </TabsContent>

      <TabsContent value="health" className="mt-6">
        <div className="space-y-4">
          <div>
            <h2 className="text-2xl font-semibold">Nhật ký & Giám sát</h2>
            <p className="text-muted-foreground">Theo dõi sức khỏe hệ thống.</p>
          </div>
          <SystemHealth />
        </div>
      </TabsContent>
    </Tabs>
  );
};

export default AdminDashboard;