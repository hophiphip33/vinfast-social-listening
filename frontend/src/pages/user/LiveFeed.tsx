import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter 
} from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { 
  Youtube, Newspaper, RefreshCw, AlertCircle, Clock, 
  ExternalLink, BarChart3, Bot, ChevronRight, Search, 
  ChevronLeft, ChevronsLeft, ChevronsRight, Download // [THÊM] Import Download
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';
import { vi } from 'date-fns/locale';
import { useToast } from '@/components/ui/use-toast'; // [THÊM] Import useToast

// --- CẤU HÌNH API ---
const API_URL = 'http://localhost:8000';
const ITEMS_PER_PAGE = 20; // Số bài mỗi trang

interface PostData {
  id: string;
  title: string;
  content: string;
  platform: string;
  sentiment: string;
  sentiment_score?: number;
  marketing_score?: number;
  published_at: string;
  source_name?: string;
  url?: string;
}

const platformIcons: Record<string, any> = {
  youtube: Youtube,
  news: Newspaper,
};

const sentimentStyles: Record<string, string> = {
  POSITIVE: 'bg-green-100 text-green-700 border-green-200',
  NEGATIVE: 'bg-red-100 text-red-700 border-red-200',
  NEUTRAL: 'bg-gray-100 text-gray-700 border-gray-200',
};

const LiveFeed = () => {
  const { toast } = useToast(); // [THÊM] Khởi tạo toast

  // State bộ lọc
  const [platformFilter, setPlatformFilter] = useState<string>('all');
  const [sentimentFilter, setSentimentFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>(''); 
  
  // State phân trang & Modal
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [selectedPost, setSelectedPost] = useState<PostData | null>(null);

  // Reset về trang 1 mỗi khi thay đổi bộ lọc hoặc tìm kiếm
  useEffect(() => {
    setCurrentPage(1);
  }, [platformFilter, sentimentFilter, searchQuery]);

  // --- GỌI API ---
  const { data: posts, isLoading, isError, refetch } = useQuery({
    queryKey: ['live-feed-posts'],
    queryFn: async () => {
      const token = localStorage.getItem('auth_token'); // Lưu ý: Kiểm tra lại key token của bạn là 'auth_token' hay 'token'
      if (!token) throw new Error("Chưa đăng nhập");

      // Lưu ý: Nếu key token trong localStorage là "token" (như ở file Login.tsx thường dùng), hãy sửa lại dòng trên.
      // Ví dụ: const token = localStorage.getItem('token'); 

      const res = await fetch(`${API_URL}/api/dashboard/data`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) throw new Error('Lỗi tải dữ liệu');
      const rawData = await res.json();
      
      // Map data để lấy đúng url
      const mapData = (items: any[]) => items.map(item => ({
        ...item,
        url: item.source_url || item.url 
      }));

      const merged: PostData[] = [...mapData(rawData.news || []), ...mapData(rawData.youtube || [])];
      return merged.sort((a, b) => 
        new Date(b.published_at).getTime() - new Date(a.published_at).getTime()
      );
    },
    refetchInterval: 30000,
  });

  // --- [THÊM] HÀM XỬ LÝ EXPORT ---
  const handleExport = async () => {
    try {
      const token = localStorage.getItem('auth_token') || localStorage.getItem('token'); // Lấy token an toàn hơn
      
      // Tạo query string dựa trên state hiện tại
      const queryParams = new URLSearchParams({
        platform: platformFilter,
        sentiment: sentimentFilter,
        search: searchQuery
      });

      const response = await fetch(`${API_URL}/api/posts/export?${queryParams}`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // Tạo blob từ response để tải file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Veda_Report_${new Date().toISOString().slice(0,10)}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        toast({
          title: "Thành công",
          description: "Đã xuất báo cáo thành công!",
        });
      } else {
        throw new Error("Lỗi khi xuất file");
      }
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Lỗi",
        description: "Không thể xuất báo cáo. Vui lòng thử lại.",
      });
    }
  };

  // --- XỬ LÝ LỌC & TÌM KIẾM (Client-side cho hiển thị) ---
  const filteredPosts = posts?.filter(post => {
    const postPlatform = post.platform.toLowerCase();
    const filterPlatform = platformFilter.toLowerCase();
    const matchPlatform = filterPlatform === 'all' || postPlatform === filterPlatform;

    // Check Sentiment
    let matchSentiment = true;
    if (sentimentFilter !== 'all') {
        const postSentiment = post.sentiment ? post.sentiment.toUpperCase() : 'NEUTRAL';
        matchSentiment = postSentiment === sentimentFilter.toUpperCase();
    }

    // Check Tìm kiếm (Tiêu đề hoặc Nội dung)
    const query = searchQuery.toLowerCase();
    const matchSearch = post.title.toLowerCase().includes(query) || 
                        post.content.toLowerCase().includes(query);

    return matchPlatform && matchSentiment && matchSearch;
  }) || [];

  // --- XỬ LÝ PHÂN TRANG ---
  const totalItems = filteredPosts.length;
  const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentPosts = filteredPosts.slice(startIndex, endIndex);

  // Helpers
  const formatTime = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true, locale: vi });
    } catch { return dateString; }
  };

  const handleOpenLink = (e: React.MouseEvent, url?: string) => {
    e.stopPropagation();
    if (url) window.open(url, '_blank');
  };

  const renderDetailModal = () => {
    if (!selectedPost) return null;
    const PlatformIcon = platformIcons[selectedPost.platform.toLowerCase()] || Newspaper;
    const sentimentKey = selectedPost.sentiment ? selectedPost.sentiment.toUpperCase() : 'NEUTRAL';
    const sentimentClass = sentimentStyles[sentimentKey] || sentimentStyles.NEUTRAL;
    const sentimentLabel = sentimentKey === 'POSITIVE' ? 'Tích cực' : sentimentKey === 'NEGATIVE' ? 'Tiêu cực' : 'Trung lập';

    return (
      <Dialog open={!!selectedPost} onOpenChange={(open) => !open && setSelectedPost(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
              <PlatformIcon className="h-4 w-4" />
              <span className="capitalize">{selectedPost.platform}</span>
              <span>•</span>
              <span>{formatTime(selectedPost.published_at)}</span>
            </div>
            <DialogTitle className="text-xl leading-relaxed">{selectedPost.title}</DialogTitle>
          </DialogHeader>
          <div className="space-y-6 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-secondary/30 space-y-2 border">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Bot className="h-4 w-4" /> Đánh giá AI
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className={`${sentimentClass} text-base px-3 py-1`}>{sentimentLabel}</Badge>
                  {selectedPost.sentiment_score !== undefined && (
                    <span className="text-sm font-mono text-muted-foreground">({selectedPost.sentiment_score.toFixed(3)})</span>
                  )}
                </div>
              </div>
              <div className="p-4 rounded-xl bg-secondary/30 space-y-2 border">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <BarChart3 className="h-4 w-4" /> Điểm Marketing
                </div>
                <div className="text-2xl font-bold font-mono text-primary">
                  {selectedPost.marketing_score ? selectedPost.marketing_score.toFixed(1) : 'N/A'}
                  <span className="text-sm text-muted-foreground font-normal ml-1">/ 10</span>
                </div>
              </div>
            </div>
            <Separator />
            <div className="space-y-3">
              <h4 className="font-semibold flex items-center gap-2"><Bot className="h-4 w-4 text-blue-500" /> Nội dung phân tích & Tóm tắt:</h4>
              <div className="bg-muted/50 p-4 rounded-lg text-sm leading-7 text-foreground/90 whitespace-pre-wrap">
                {selectedPost.content}
              </div>
            </div>
          </div>
          <DialogFooter className="sm:justify-between gap-2">
            <Button variant="outline" onClick={() => setSelectedPost(null)}>Đóng</Button>
            {selectedPost.url && (
              <Button onClick={() => window.open(selectedPost.url, '_blank')} className="gap-2">
                Xem bài viết gốc <ExternalLink className="h-4 w-4" />
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  };

  return (
    <div className="space-y-6 animate-fade-in p-2 h-[calc(100vh-80px)] flex flex-col">
      {/* HEADER */}
      <div className="flex flex-col gap-4 shrink-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-3">
              Live Feed
              <Badge className="bg-green-100 text-green-700 border-green-200 animate-pulse">
                <span className="mr-1 text-[10px]">●</span> Live Updates
              </Badge>
            </h1>
            <p className="text-muted-foreground text-sm mt-1">Dữ liệu thời gian thực từ các nguồn đã đăng ký</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={() => refetch()} title="Làm mới">
               <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* TOOLBAR: SEARCH & FILTERS & EXPORT */}
        <div className="flex flex-col sm:flex-row gap-3 items-center bg-card p-3 rounded-lg border shadow-sm">
            {/* Search Input */}
            <div className="relative w-full sm:flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input 
                    placeholder="Tìm kiếm theo tiêu đề hoặc nội dung..." 
                    className="pl-9 bg-background"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-2 w-full sm:w-auto items-center">
                <Select value={platformFilter} onValueChange={setPlatformFilter}>
                    <SelectTrigger className="w-full sm:w-[130px] bg-background"><SelectValue placeholder="Nguồn" /></SelectTrigger>
                    <SelectContent>
                    <SelectItem value="all">Tất cả nguồn</SelectItem>
                    <SelectItem value="youtube">YouTube</SelectItem>
                    <SelectItem value="news">Báo chí</SelectItem>
                    </SelectContent>
                </Select>

                <Select value={sentimentFilter} onValueChange={setSentimentFilter}>
                    <SelectTrigger className="w-full sm:w-[130px] bg-background"><SelectValue placeholder="Sắc thái" /></SelectTrigger>
                    <SelectContent>
                    <SelectItem value="all">Tất cả sắc thái</SelectItem>
                    <SelectItem value="positive">Tích cực</SelectItem>
                    <SelectItem value="negative">Tiêu cực</SelectItem>
                    <SelectItem value="neutral">Trung lập</SelectItem>
                    </SelectContent>
                </Select>

                {/* [THÊM] Nút Xuất Báo Cáo */}
                <Button 
                    variant="outline" 
                    onClick={handleExport}
                    className="flex items-center gap-2 border-green-600 text-green-700 hover:bg-green-50 w-full sm:w-auto"
                >
                    <Download className="h-4 w-4" />
                    <span className="hidden sm:inline">Xuất CSV</span>
                    <span className="sm:hidden">Xuất</span>
                </Button>
            </div>
        </div>
      </div>

      {/* CONTENT LIST */}
      <ScrollArea className="flex-1 pr-4 -mr-4">
        <div className="space-y-4 pr-4 pb-4">
          {isLoading ? (
            // Skeleton Loading
            [1, 2, 3].map((i) => (
              <div key={i} className="flex flex-col space-y-3 p-4 border rounded-xl"><Skeleton className="h-20 w-full" /></div>
            ))
          ) : isError ? (
            <Card className="border-destructive/50 bg-destructive/10 text-center p-8">
               <div className="flex flex-col items-center gap-2">
                  <AlertCircle className="h-8 w-8 text-destructive" /><p>Lỗi tải dữ liệu</p>
                  <Button variant="outline" onClick={() => refetch()}>Thử lại</Button>
               </div>
            </Card>
          ) : filteredPosts.length === 0 ? (
            <Card className="border-dashed p-12 text-center bg-muted/30">
              <div className="flex flex-col items-center gap-2">
                  <Search className="h-10 w-10 text-muted-foreground/50" />
                  <p className="text-muted-foreground font-medium">Không tìm thấy bài viết nào phù hợp.</p>
                  <p className="text-xs text-muted-foreground">Thử thay đổi từ khóa hoặc bộ lọc của bạn.</p>
              </div>
            </Card>
          ) : (
            currentPosts.map((post) => {
              const PlatformIcon = platformIcons[post.platform.toLowerCase()] || Newspaper;
              const sentimentKey = post.sentiment ? post.sentiment.toUpperCase() : 'NEUTRAL';
              const sentimentClass = sentimentStyles[sentimentKey] || sentimentStyles.NEUTRAL;
              const sentimentLabel = sentimentKey === 'POSITIVE' ? 'Tích cực' : sentimentKey === 'NEGATIVE' ? 'Tiêu cực' : 'Trung lập';

              return (
                <Card key={post.id} onClick={() => setSelectedPost(post)} className="group border-border/60 hover:border-primary/50 transition-all hover:shadow-md cursor-pointer active:scale-[0.99] relative overflow-hidden">
                  <CardHeader className="pb-3 pt-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className={`p-2 rounded-lg ${post.platform === 'youtube' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>
                          <PlatformIcon className="h-4 w-4" />
                        </div>
                        <div className="flex flex-col">
                          <span className="font-semibold text-sm capitalize">{post.platform}</span>
                          <span className="text-[10px] text-muted-foreground">{post.source_name || post.platform}</span>
                        </div>
                      </div>
                      <span className="flex items-center gap-1 text-xs text-muted-foreground"><Clock className="h-3 w-3" /> {formatTime(post.published_at)}</span>
                    </div>
                  </CardHeader>
                  <CardContent className="pb-4 space-y-3">
                    <div className="block group-hover:text-primary transition-colors"><h3 className="font-semibold leading-tight text-base line-clamp-1">{post.title}</h3></div>
                    <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">{post.content}</p>
                    <div className="flex items-center justify-between pt-3 border-t border-border/50">
                      <Badge variant="outline" className={`${sentimentClass} border`}>{sentimentLabel}</Badge>
                      <div className="flex items-center gap-2">
                          {post.url && (
                            <Button variant="ghost" size="sm" className="h-7 px-2 text-xs text-muted-foreground hover:text-primary hover:bg-primary/10 gap-1" onClick={(e) => handleOpenLink(e, post.url)}>
                              <ExternalLink className="h-3 w-3" /> Mở Link
                            </Button>
                          )}
                          <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })
          )}
        </div>
      </ScrollArea>

      {/* PAGINATION CONTROLS */}
      {totalItems > 0 && (
          <div className="flex items-center justify-between border-t pt-4 shrink-0 bg-background/95 backdrop-blur py-2">
              <div className="text-sm text-muted-foreground">
                  Hiển thị <span className="font-medium text-foreground">{startIndex + 1}</span> - <span className="font-medium text-foreground">{Math.min(endIndex, totalItems)}</span> trên <span className="font-medium text-foreground">{totalItems}</span> bài viết
              </div>
              <div className="flex items-center gap-2">
                  <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setCurrentPage(1)} disabled={currentPage === 1}>
                      <ChevronsLeft className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>
                      <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <div className="text-sm font-medium px-2">
                      Trang {currentPage} / {totalPages}
                  </div>
                  <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>
                      <ChevronRight className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages}>
                      <ChevronsRight className="h-4 w-4" />
                  </Button>
              </div>
          </div>
      )}

      {renderDetailModal()}
    </div>
  );
};

export default LiveFeed;