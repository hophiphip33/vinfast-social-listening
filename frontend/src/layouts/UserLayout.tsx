// Layout cho phía User - Sidebar + Content Area
import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  LayoutDashboard, Radio, Sparkles, Settings, 
  LogOut, Menu, X, Radar, ChevronRight 
} from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

// Menu items
const menuItems = [
  { path: '/user', icon: LayoutDashboard, label: 'Tổng quan', end: true },
  { path: '/user/live-feed', icon: Radio, label: 'Live Feed' },
  { path: '/user/analysis', icon: Sparkles, label: 'Phân tích nhanh' },
  { path: '/user/settings', icon: Settings, label: 'Cài đặt' },
];

const UserLayout = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const userEmail = localStorage.getItem('user_email') || 'user@vinfast.vn';
  const username = localStorage.getItem('username') || 'Veda User';

  // Đăng xuất
  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_role');
    toast.success('Đã đăng xuất!');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 h-14 bg-card border-b border-border px-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radar className="h-6 w-6 text-primary" />
          <span className="font-bold">Social Listening</span>
        </div>
        <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)}>
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </header>

      {/* Sidebar */}
      <aside className={cn(
        "fixed top-0 left-0 z-40 h-screen bg-card border-r border-border transition-all duration-300",
        sidebarOpen ? "w-64" : "w-0 lg:w-20",
        "lg:block",
        !sidebarOpen && "hidden lg:block"
      )}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-20 lg:h-20 flex items-center gap-3 px-4 border-b border-border">
            {/* Ảnh Logo */}
            <div className="h-20 w-20 flex items-center justify-center shrink-0">
               <img src="/logo2.png" alt="Veda Logo" className="w-full h-full object-contain" />
            </div>
            {sidebarOpen && (
              <div className="animate-fade-in">
                <p className="font-bold text-sm">{username}</p>
                <p className="text-xs text-muted-foreground">Hệ thống Social Listening</p>
              </div>
            )}
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 py-4">
            <nav className="space-y-1 px-2">
              {menuItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.end}
                  className={({ isActive }) => cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors",
                    isActive 
                      ? "bg-primary text-primary-foreground" 
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                  )}
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  {sidebarOpen && <span className="font-medium">{item.label}</span>}
                </NavLink>
              ))}
            </nav>
          </ScrollArea>

          {/* Footer */}
          <div className="p-4 border-t border-border">
            {sidebarOpen ? (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-secondary/50">
                  <p className="text-xs text-muted-foreground">Đăng nhập với</p>
                  <p className="text-sm font-medium truncate">{userEmail}</p>
                </div>
                <Button 
                  variant="ghost" 
                  className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive"
                  onClick={handleLogout}
                >
                  <LogOut className="h-4 w-4" />
                  Đăng xuất
                </Button>
              </div>
            ) : (
              <Button 
                variant="ghost" 
                size="icon" 
                className="w-full text-muted-foreground hover:text-destructive"
                onClick={handleLogout}
              >
                <LogOut className="h-5 w-5" />
              </Button>
            )}
          </div>
        </div>
      </aside>

      {/* Toggle Sidebar Button (Desktop) */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className={cn(
          "hidden lg:flex fixed z-50 top-6 items-center justify-center w-6 h-6 rounded-full bg-card border border-border shadow-sm transition-all",
          sidebarOpen ? "left-[248px]" : "left-[68px]"
        )}
      >
        <ChevronRight className={cn("h-4 w-4 transition-transform", sidebarOpen && "rotate-180")} />
      </button>

      {/* Main Content */}
      <main className={cn(
        "min-h-screen pt-14 lg:pt-0 transition-all duration-300",
        sidebarOpen ? "lg:pl-64" : "lg:pl-20"
      )}>
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default UserLayout;
