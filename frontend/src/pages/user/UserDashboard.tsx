import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button'; // [MỚI] Thêm Button
import { 
  FileText, ThumbsUp, ThumbsDown, Heart, Clock, TrendingUp, 
  Youtube, Newspaper, Globe, Loader2, AlertCircle, Download // [MỚI] Thêm icon Download
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  AreaChart, Area
} from 'recharts';
import { toast } from 'sonner';

const API_URL = 'http://localhost:8000';

// --- INTERFACES ---
interface Post {
  id: string;
  title: string;
  source_name?: string;
  platform: string;
  published_at: string;
  sentiment?: string; // POSITIVE, NEGATIVE, NEUTRAL
  views_count?: number;
  likes_count?: number;
  comments_count?: number;
  source_url?: string;
}

interface DashboardStats {
  totalPosts: number;
  positivePercent: number;
  negativePercent: number;
  totalEngagement: number;
}

// --- HELPER COMPONENTS ---

const MetricCard = ({ title, value, icon: Icon, color, subtext }: {
  title: string;
  value: string | number;
  icon: any;
  color: string;
  subtext?: string;
}) => (
  <Card className="gradient-card border-border">
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="text-3xl font-bold">{value}</p>
          {subtext && <p className="text-xs text-muted-foreground">{subtext}</p>}
        </div>
        <div className={`p-3 rounded-xl ${color}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </CardContent>
  </Card>
);

const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return percent > 0 ? (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" className="text-xs font-bold">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  ) : null;
};

// --- MAIN COMPONENT ---

const UserDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [allPosts, setAllPosts] = useState<Post[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalPosts: 0, positivePercent: 0, negativePercent: 0, totalEngagement: 0
  });
  
  // State cho biểu đồ
  const [chartData, setChartData] = useState<any[]>([]);
  const [sentimentSource, setSentimentSource] = useState<'all' | 'news' | 'youtube'>('all');
  const [sentimentChartData, setSentimentChartData] = useState<any[]>([]);
  const [sourceDistribution, setSourceDistribution] = useState<any[]>([]);

  // --- [MỚI] HÀM XỬ LÝ EXPORT ---
  const handleExport = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) {
        toast.error("Vui lòng đăng nhập để thực hiện chức năng này");
        return;
      }

      // Thông báo đang xử lý
      const toastId = toast.loading("Đang chuẩn bị file báo cáo...");

      // Gọi API Export
      const queryParams = new URLSearchParams({
        platform: "all",
        sentiment: "all",
        search: ""
      });

      const res = await fetch(`${API_URL}/api/posts/export?${queryParams}`, {
        method: "GET",
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) throw new Error('Lỗi khi xuất file');

      // Tải file về
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Veda_Dashboard_Report_${new Date().toISOString().slice(0,10)}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      
      // Thông báo thành công
      toast.dismiss(toastId);
      toast.success("Đã xuất báo cáo CSV thành công!");

    } catch (error) {
      console.error(error);
      toast.dismiss();
      toast.error("Không thể xuất báo cáo. Vui lòng thử lại.");
    }
  };

  // --- 1. FETCH DATA TỪ API ---
  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      if (!token) return;

      const res = await fetch(`${API_URL}/api/dashboard/data`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error('Failed to fetch data');
      
      const data = await res.json();
      // Gom data từ news và youtube thành 1 mảng chung để dễ xử lý
      const combinedPosts: Post[] = [...(data.news || []), ...(data.youtube || [])];
      
      // Sắp xếp theo thời gian mới nhất
      combinedPosts.sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime());

      setAllPosts(combinedPosts);
      processData(combinedPosts);
      
    } catch (error) {
      console.error(error);
      toast.error("Không thể tải dữ liệu dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // --- 2. XỬ LÝ DỮ LIỆU (TÍNH TOÁN STATS & CHARTS) ---
  const processData = (posts: Post[]) => {
    if (posts.length === 0) return;

    // A. Tính Stats cơ bản
    const total = posts.length;
    const positive = posts.filter(p => p.sentiment === 'POSITIVE').length;
    const negative = posts.filter(p => p.sentiment === 'NEGATIVE').length;
    
    // Tính tổng tương tác (View + Like + Comment)
    const engagement = posts.reduce((sum, p) => sum + (p.views_count||0) + (p.likes_count||0) + (p.comments_count||0), 0);

    setStats({
      totalPosts: total,
      positivePercent: total > 0 ? Math.round((positive / total) * 100) : 0,
      negativePercent: total > 0 ? Math.round((negative / total) * 100) : 0,
      totalEngagement: engagement
    });

    // B. Xử lý Biểu đồ cột (Sentiment theo ngày - 7 ngày gần nhất)
    const last7Days = [...Array(7)].map((_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - i));
      return d.toISOString().split('T')[0]; // YYYY-MM-DD
    });

    const dailyData = last7Days.map(dateStr => {
      const dayPosts = posts.filter(p => p.published_at.startsWith(dateStr));
      return {
        day: dateStr.split('-').slice(1).join('/'), // MM/DD
        positive: dayPosts.filter(p => p.sentiment === 'POSITIVE').length,
        negative: dayPosts.filter(p => p.sentiment === 'NEGATIVE').length,
        neutral: dayPosts.filter(p => !['POSITIVE', 'NEGATIVE'].includes(p.sentiment || '')).length,
      };
    });
    setChartData(dailyData);

    // C. Xử lý Phân bố nguồn
    const sources = {
      YouTube: posts.filter(p => p.platform === 'youtube').length,
      News: posts.filter(p => p.platform === 'news').length,
    };
    setSourceDistribution([
      { name: 'YouTube', value: sources.YouTube, color: '#FF0000' },
      { name: 'News', value: sources.News, color: '#3B82F6' },
    ]);
  };

  // Tính lại biểu đồ tròn khi đổi Filter (All/News/YouTube)
  useEffect(() => {
    let filtered = allPosts;
    if (sentimentSource !== 'all') {
      filtered = allPosts.filter(p => p.platform === sentimentSource);
    }

    const pos = filtered.filter(p => p.sentiment === 'POSITIVE').length;
    const neg = filtered.filter(p => p.sentiment === 'NEGATIVE').length;
    const neu = filtered.length - pos - neg;

    setSentimentChartData([
      { name: 'Tích cực', value: pos, color: 'hsl(var(--success))' },
      { name: 'Tiêu cực', value: neg, color: 'hsl(var(--destructive))' },
      { name: 'Trung lập', value: neu, color: 'hsl(var(--muted-foreground))' },
    ]);
  }, [sentimentSource, allPosts]);


  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center flex-col gap-4">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="text-muted-foreground">Đang phân tích dữ liệu...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Tổng quan</h1>
          <p className="text-muted-foreground">Thống kê dữ liệu Social Listening của bạn</p>
        </div>
        
        {/* [MỚI] Khu vực Action Buttons */}
        <div className="flex items-center gap-3">
            <div className="text-xs text-muted-foreground bg-secondary px-3 py-1.5 rounded-full hidden sm:block">
                Cập nhật: {new Date().toLocaleTimeString()}
            </div>
            
            <Button onClick={handleExport} variant="outline" className="gap-2 border-green-600 text-green-700 hover:bg-green-50">
                <Download className="h-4 w-4" />
                <span className="hidden sm:inline">Xuất Báo cáo</span>
                <span className="sm:hidden">CSV</span>
            </Button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Tổng bài viết"
          value={stats.totalPosts}
          icon={FileText}
          color="bg-primary/10 text-primary"
        />
        <MetricCard
          title="Tỉ lệ Tích cực"
          value={`${stats.positivePercent}%`}
          icon={ThumbsUp}
          color="bg-success/10 text-success"
        />
        <MetricCard
          title="Tỉ lệ Tiêu cực"
          value={`${stats.negativePercent}%`}
          icon={ThumbsDown}
          color="bg-destructive/10 text-destructive"
        />
        <MetricCard
          title="Tổng tương tác"
          value={(stats.totalEngagement > 1000 ? (stats.totalEngagement/1000).toFixed(1) + 'K' : stats.totalEngagement)}
          icon={Heart}
          color="bg-warning/10 text-warning"
          subtext="Views, Likes, Comments"
        />
      </div>

      {/* Row 2: Biểu đồ tròn + Xu hướng */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Biểu đồ tròn Sentiment */}
        <Card className="gradient-card border-border">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Phân tích Cảm xúc</CardTitle>
              <Tabs value={sentimentSource} onValueChange={(v) => setSentimentSource(v as any)}>
                <TabsList className="h-8 bg-secondary">
                  <TabsTrigger value="all" className="text-xs h-7">All</TabsTrigger>
                  <TabsTrigger value="news" className="text-xs h-7">News</TabsTrigger>
                  <TabsTrigger value="youtube" className="text-xs h-7">YouTube</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              {allPosts.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={sentimentChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={renderCustomLabel}
                      outerRadius={100}
                      innerRadius={40}
                      dataKey="value"
                    >
                      {sentimentChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground">Chưa có dữ liệu</div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Biểu đồ cột theo ngày */}
        <Card className="gradient-card border-border">
          <CardHeader>
            <CardTitle className="text-lg">Xu hướng 7 ngày qua</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip cursor={{fill: 'transparent'}} />
                  <Legend />
                  <Bar dataKey="positive" name="Tích cực" stackId="a" fill="hsl(var(--success))" />
                  <Bar dataKey="neutral" name="Trung lập" stackId="a" fill="hsl(var(--muted-foreground))" />
                  <Bar dataKey="negative" name="Tiêu cực" stackId="a" fill="hsl(var(--destructive))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 3: Tin mới nhất & Phân bố nguồn */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Tin mới nhất */}
        <Card className="gradient-card border-border lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Nội dung mới nhất
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[300px] px-6">
              <div className="space-y-3 pb-4">
                {allPosts.length === 0 ? (
                  <div className="text-center py-10 text-muted-foreground">
                    <AlertCircle className="mx-auto h-8 w-8 mb-2 opacity-50"/>
                    Chưa có bài viết nào được thu thập
                  </div>
                ) : (
                  allPosts.slice(0, 10).map((post) => (
                    <div 
                      key={post.id} 
                      className="group p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors cursor-pointer border border-transparent hover:border-border"
                      onClick={() => post.source_url && window.open(post.source_url, '_blank')}
                    >
                      <h4 className="font-medium text-sm line-clamp-2 group-hover:text-primary transition-colors">
                        {post.title || "Bài viết không có tiêu đề"}
                      </h4>
                      <div className="flex items-center justify-between mt-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
                            post.platform === 'youtube' ? 'bg-red-500/10 text-red-500 border-red-500/20' : 
                            'bg-blue-500/10 text-blue-500 border-blue-500/20'
                          }`}>
                            {post.platform.toUpperCase()}
                          </span>
                          <span className="text-xs text-muted-foreground">{post.source_name}</span>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(post.published_at).toLocaleDateString('vi-VN')}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Phân bố nguồn */}
        <Card className="gradient-card border-border">
          <CardHeader>
            <CardTitle className="text-lg">Nguồn dữ liệu</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[220px]">
               <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={sourceDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {sourceDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend verticalAlign="bottom" />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="text-center text-sm text-muted-foreground mt-2">
              Dựa trên {stats.totalPosts} bài viết
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default UserDashboard;