import { useState, useEffect } from 'react';
import { getSystemMetrics, SystemMetrics } from '@/lib/mockData'; // Vẫn giữ metrics giả lập nếu chưa có backend metrics
import MetricCard from '@/components/shared/MetricCard';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Cpu, HardDrive, Database, Activity, Clock, 
  User, Settings, AlertCircle, Trash, ShieldAlert, LogIn, CheckCircle2 
} from 'lucide-react';
import { toast } from 'sonner';

// URL API
const API_URL = 'http://localhost:8000';

// Interface cho Log (khớp với Backend)
interface LogEntry {
  id: string;
  level: string;
  actor: string;
  action: string;
  details: string;
  created_at: string;
}

const SystemHealth = () => {
  const [metrics, setMetrics] = useState<SystemMetrics>(getSystemMetrics());
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filterType, setFilterType] = useState<'ALL' | 'SYSTEM' | 'USER'>('ALL');

  // Cập nhật metrics giả lập (CPU/RAM)
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(getSystemMetrics());
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Hàm gọi API lấy Log thật
  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(`${API_URL}/api/logs?limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setLogs(data);
      }
    } catch (error) {
      console.error("Lỗi tải logs:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Tải logs khi component mount và set interval tải lại mỗi 10s
  useEffect(() => {
    fetchLogs();
    const logInterval = setInterval(fetchLogs, 10000); // Live update logs
    return () => clearInterval(logInterval);
  }, []);

  // Helper chọn Icon
  const getActionIcon = (action: string) => {
    const map: Record<string, any> = {
      'LOGIN': <LogIn className="h-4 w-4 text-blue-500" />,
      'CREATE_USER': <User className="h-4 w-4 text-green-500" />,
      'ERROR': <AlertCircle className="h-4 w-4 text-red-500" />,
      'CRAWL': <Activity className="h-4 w-4 text-orange-500" />,
      'SUCCESS': <CheckCircle2 className="h-4 w-4 text-green-500" />
    };
    return map[action] || <Activity className="h-4 w-4 text-gray-500" />;
  };

  // Logic lọc dữ liệu theo Tabs
  const filteredLogs = logs.filter(log => {
    if (filterType === 'ALL') return true;
    // SYSTEM logs: Actor là "SYSTEM" hoặc "System"
    if (filterType === 'SYSTEM') return log.actor.toUpperCase() === 'SYSTEM';
    // USER logs: Actor KHÔNG phải là "SYSTEM"
    if (filterType === 'USER') return log.actor.toUpperCase() !== 'SYSTEM';
    return true;
  });

  // Format thời gian
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('vi-VN', {
      hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit'
    });
  };

  // Component bảng Log con
  const LogTable = ({ data }: { data: LogEntry[] }) => (
    <div className="rounded-lg border border-border overflow-hidden max-h-[500px] overflow-y-auto">
      <Table>
        <TableHeader className="sticky top-0 bg-secondary z-10">
          <TableRow>
            <TableHead className="w-12 text-center">#</TableHead>
            <TableHead>Hành động</TableHead>
            <TableHead>Người thực hiện</TableHead>
            <TableHead>Chi tiết</TableHead>
            <TableHead className="text-right">Thời gian</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length > 0 ? (
            data.map((log) => (
              <TableRow key={log.id} className="hover:bg-secondary/30">
                <TableCell className="text-center">{getActionIcon(log.action)}</TableCell>
                <TableCell>
                  <span className={`text-xs font-bold px-2 py-1 rounded border ${
                    log.level === 'ERROR' ? 'bg-red-500/10 text-red-500 border-red-500/20' : 
                    log.level === 'WARNING' ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20' : 
                    'bg-secondary text-foreground border-border'
                  }`}>
                    {log.action}
                  </span>
                </TableCell>
                <TableCell>
                  {log.actor.toUpperCase() === 'SYSTEM' ? (
                    <span className="font-mono text-xs text-primary font-bold">SYSTEM</span>
                  ) : (
                    <span className="text-sm font-medium">{log.actor}</span>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground text-sm truncate max-w-[300px]" title={log.details}>
                  {log.details}
                </TableCell>
                <TableCell className="text-right text-xs text-muted-foreground font-mono">
                  {formatDate(log.created_at)}
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                {isLoading ? 'Đang tải dữ liệu...' : 'Chưa có nhật ký nào'}
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  );

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Metrics Cards (Giữ nguyên phần hiển thị chỉ số) */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="CPU Usage"
          value={`${metrics.cpuUsage}%`}
          icon={<Cpu className="h-5 w-5" />}
          color={metrics.cpuUsage > 70 ? 'destructive' : 'success'}
          trend="stable"
          trendValue="Ổn định"
        />
        <MetricCard
          title="RAM Usage"
          value={`${metrics.ramUsage}%`}
          icon={<HardDrive className="h-5 w-5" />}
          color="warning"
          trend="up"
          trendValue="+2% usage"
        />
         <MetricCard
          title="DB Size"
          value={metrics.dbSize}
          icon={<Database className="h-5 w-5" />}
          color="primary"
          trend="up"
          trendValue="+50MB"
        />
         <MetricCard
          title="Connections"
          value={metrics.activeConnections}
          icon={<Activity className="h-5 w-5" />}
          color="success"
          trend="stable"
          trendValue="Normal"
        />
      </div>

      {/* Audit Logs Tabs */}
      <Card className="gradient-card border-border">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Clock className="h-5 w-5 text-primary" />
              </div>
              <div>
                <CardTitle>Nhật ký Hoạt động (Audit Logs)</CardTitle>
                <p className="text-sm text-muted-foreground">
                  Theo dõi hoạt động hệ thống và người dùng theo thời gian thực
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${isLoading ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`} />
                <span className="text-xs text-muted-foreground">{isLoading ? 'Syncing...' : 'Live'}</span>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <Tabs defaultValue="ALL" className="w-full" onValueChange={(val) => setFilterType(val as any)}>
            <div className="flex justify-between items-center mb-4">
              <TabsList className="bg-secondary p-1">
                <TabsTrigger value="ALL" className="px-4">Tất cả</TabsTrigger>
                <TabsTrigger value="SYSTEM" className="gap-2 px-4">
                  <Activity className="h-3 w-3" /> Hệ thống
                </TabsTrigger>
                <TabsTrigger value="USER" className="gap-2 px-4">
                  <User className="h-3 w-3" /> Người dùng
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Nội dung các Tab sử dụng chung component LogTable với dữ liệu đã lọc */}
            <TabsContent value="ALL" className="mt-0 focus-visible:ring-0">
              <LogTable data={filteredLogs} />
            </TabsContent>
            
            <TabsContent value="SYSTEM" className="mt-0 focus-visible:ring-0">
              <LogTable data={filteredLogs} />
            </TabsContent>
            
            <TabsContent value="USER" className="mt-0 focus-visible:ring-0">
              <LogTable data={filteredLogs} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default SystemHealth;