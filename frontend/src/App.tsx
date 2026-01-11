import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";

// Layouts
import AdminLayout from "./layouts/AdminLayout";
import UserLayout from "./layouts/UserLayout";

// Pages
import AdminDashboard from "./pages/admin/AdminDashboard";
import UserDashboard from "./pages/user/UserDashboard";
import LiveFeed from "./pages/user/LiveFeed";
import QuickAnalysis from "./pages/user/QuickAnalysis";
import Settings from "./pages/user/Settings";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

// --- 1. Điều hướng thông minh ---
const SmartRedirect = () => {
  const token = localStorage.getItem('auth_token');
  const role = localStorage.getItem('user_role');
  
  if (!token) return <Navigate to="/login" replace />;
  if (role === 'admin') return <Navigate to="/admin" replace />;
  return <Navigate to="/user" replace />;
};

// --- 2. Bảo vệ Route Admin ---
const AdminRouteWrapper = () => {
  const role = localStorage.getItem('user_role'); 
  if (role !== 'admin') return <Navigate to="/" replace />;
  return <Outlet />;
};

// --- 3. Bảo vệ Route User ---
const UserRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('auth_token');
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          {/* Mặc định vào SmartRedirect để phân loại user/admin */}
          <Route path="/" element={<SmartRedirect />} />
          <Route path="/login" element={<Login />} />
          
          {/* Admin Routes */}
          <Route element={<AdminRouteWrapper />}>
            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<AdminDashboard />} />
            </Route>
          </Route>
          
          {/* User Routes */}
          <Route path="/user" element={<UserRoute><UserLayout /></UserRoute>}>
            <Route index element={<UserDashboard />} />
            <Route path="live-feed" element={<LiveFeed />} />
            <Route path="analysis" element={<QuickAnalysis />} />
            <Route path="settings" element={<Settings />} />
          </Route>
          
          {/* Bắt lỗi 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;