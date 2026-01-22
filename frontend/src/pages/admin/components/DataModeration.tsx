import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from '@/components/ui/table';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter 
} from '@/components/ui/dialog';
import StatusBadge from './StatusBadge';
import { toast } from 'sonner';
import { Loader2, Search, Eye, Trash2, ExternalLink, BarChart3, MessageCircle, ThumbsUp, AlertTriangle } from 'lucide-react';

const API_URL = 'http://localhost:8000';

interface Post {
  id: string;
  title: string;
  platform: string;
  sentiment: 'Positive' | 'Negative' | 'Neutral';
  sentiment_score: number;
  marketing_score: number;
  source_url: string;
  content: string;
  full_text?: string;
  published_at: string;
  views_count: number;
  likes_count: number;
  comments_count: number;
}

const DataModeration = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(false);
  
  // State bộ lọc
  const [filterPlatform, setFilterPlatform] = useState('all');
  const [filterSentiment, setFilterSentiment] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // State cho Modal chi tiết
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  // --- 1. Gọi API lấy dữ liệu ---
  const fetchPosts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        platform: filterPlatform,
        sentiment: filterSentiment,
      });
      if (searchTerm) params.append('search', searchTerm);

      const res = await fetch(`${API_URL}/api/posts/moderation?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      
      setPosts(data.data);
      setTotalPages(data.total_pages);
    } catch (error) {
      toast.error("Lỗi tải dữ liệu");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, [page, filterPlatform, filterSentiment]);

  // --- 2. Cập nhật Sentiment (Inline) ---
  const changeSentiment = async (postId: string, newSentiment: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API_URL}/api/posts/${postId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ sentiment: newSentiment })
      });

      if (res.ok) {
        toast.success("Đã cập nhật sentiment");
        setPosts(posts.map(p => p.id === postId ? { ...p, sentiment: newSentiment as any } : p));
      }
    } catch (error) {
      toast.error("Lỗi kết nối");
    }
  };

  // --- 3. Xóa bài viết ---
  const handleDelete = async (postId: string) => {
    if (!confirm('Hành động này không thể hoàn tác. Bạn chắc chắn muốn xóa?')) return;

    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`${API_URL}/api/posts/${postId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        toast.success('Đã xóa bài viết');
        setIsDetailOpen(false);
        fetchPosts(); // Load lại danh sách
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Xóa thất bại');
      }
    } catch (error) {
      toast.error('Lỗi hệ thống');
    }
  };

  const handleViewDetail = (post: Post) => {
    setSelectedPost(post);
    setIsDetailOpen(true);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* --- THANH CÔNG CỤ --- */}
      <div className="flex flex-wrap gap-4 justify-between bg-card p-4 rounded-lg border shadow-sm">
        <div className="flex gap-2 w-full md:w-auto flex-1">
          <Input 
            placeholder="Tìm kiếm nội dung..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchPosts()}
            className="max-w-[300px]"
          />
          <Button variant="secondary" onClick={fetchPosts}><Search className="w-4 h-4" /></Button>
        </div>

        <div className="flex gap-2">
           <Select value={filterPlatform} onValueChange={(v) => {setFilterPlatform(v); setPage(1);}}>
             <SelectTrigger className="w-[140px]"><SelectValue placeholder="Platform" /></SelectTrigger>
             <SelectContent>
               <SelectItem value="all">Tất cả Nguồn</SelectItem>
               <SelectItem value="youtube">YouTube</SelectItem>
               <SelectItem value="news">Báo chí</SelectItem>
             </SelectContent>
           </Select>
           
           <Select value={filterSentiment} onValueChange={(v) => {setFilterSentiment(v); setPage(1);}}>
             <SelectTrigger className="w-[140px]"><SelectValue placeholder="Cảm xúc" /></SelectTrigger>
             <SelectContent>
               <SelectItem value="all">Tất cả Cảm xúc</SelectItem>
               <SelectItem value="POSITIVE">Tích cực</SelectItem>
               <SelectItem value="NEGATIVE">Tiêu cực</SelectItem>
               <SelectItem value="NEUTRAL">Trung tính</SelectItem>
             </SelectContent>
           </Select>
        </div>
      </div>

      {/* --- BẢNG DỮ LIỆU --- */}
      <div className="border rounded-md bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[400px]">Tiêu đề / Nội dung</TableHead>
              <TableHead>Nguồn</TableHead>
              <TableHead>Cảm xúc (AI)</TableHead>
              <TableHead>Link Gốc</TableHead>
              <TableHead className="text-right">Thao tác</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={5} className="text-center h-24"><Loader2 className="animate-spin mx-auto"/></TableCell></TableRow>
            ) : posts.length === 0 ? (
                <TableRow><TableCell colSpan={5} className="text-center h-24 text-muted-foreground">Không có dữ liệu</TableCell></TableRow>
            ) : (
                posts.map((post) => (
              <TableRow key={post.id} className="hover:bg-muted/50">
                <TableCell className="max-w-[400px]">
                  <div className="font-medium truncate" title={post.title}>{post.title || "No Title"}</div>
                  <div className="text-xs text-muted-foreground truncate" title={post.content}>{post.content}</div>
                </TableCell>
                <TableCell>
                    <span className="capitalize px-2 py-1 bg-secondary rounded text-xs font-medium">
                        {post.platform}
                    </span>
                </TableCell>
                <TableCell>
                  <Select 
                    value={post.sentiment || "Neutral"} 
                    onValueChange={(val) => changeSentiment(post.id, val)}
                  >
                    <SelectTrigger className="h-8 w-[110px] border-none shadow-none bg-transparent p-0">
                      <StatusBadge status={post.sentiment} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="POSITIVE">Positive</SelectItem>
                      <SelectItem value="NEGATIVE">Negative</SelectItem>
                      <SelectItem value="NEUTRAL">Neutral</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  {post.source_url && (
                    <a href={post.source_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-blue-500 hover:underline text-xs">
                      Xem <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </TableCell>
                <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-blue-500" onClick={() => handleViewDetail(post)}>
                            <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500" onClick={() => handleDelete(post.id)}>
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                </TableCell>
              </TableRow>
            )))}
          </TableBody>
        </Table>
      </div>

      {/* --- PHÂN TRANG --- */}
      <div className="flex justify-end gap-2 items-center">
        <Button 
          variant="outline" 
          size="sm"
          disabled={page <= 1} 
          onClick={() => setPage(p => p - 1)}
        >Trước</Button>
        <span className="text-xs font-medium text-muted-foreground">Trang {page} / {totalPages}</span>
        <Button 
          variant="outline" 
          size="sm"
          disabled={page >= totalPages} 
          onClick={() => setPage(p => p + 1)}
        >Sau</Button>
      </div>

      {/* --- DIALOG CHI TIẾT (Đã tích hợp vào giao diện của bạn) --- */}
      <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="pr-8 line-clamp-2 leading-normal">{selectedPost?.title}</DialogTitle>
          </DialogHeader>
          
          {selectedPost && (
            <div className="flex-1 overflow-y-auto pr-2 space-y-6 py-2">
              {/* Stats Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-secondary/10 p-3 rounded-lg border">
                  <div>
                    <div className="text-[10px] uppercase text-muted-foreground font-bold">Sentiment</div>
                    <div className={`text-sm font-bold ${selectedPost.sentiment_score > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {selectedPost.sentiment_score?.toFixed(3)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-muted-foreground font-bold">Marketing Score</div>
                    <div className="text-sm font-bold text-primary flex items-center gap-1">
                        <BarChart3 className="h-3 w-3" /> {selectedPost.marketing_score}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-muted-foreground font-bold">Tương tác</div>
                    <div className="text-sm font-medium">
                       {(selectedPost.likes_count || 0) + (selectedPost.comments_count || 0)}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase text-muted-foreground font-bold">Ngày đăng</div>
                    <div className="text-sm font-medium">
                        {new Date(selectedPost.published_at).toLocaleDateString('vi-VN')}
                    </div>
                  </div>
              </div>

              {/* Nội dung */}
              <div className="space-y-2">
                <h4 className="text-sm font-semibold flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-orange-500" /> Tóm tắt nội dung
                </h4>
                <div className="bg-muted/50 p-4 rounded-md text-sm leading-relaxed border">
                    {selectedPost.content || "Chưa có nội dung tóm tắt"}
                </div>
              </div>

              {/* Engagement Detail */}
              <div className="flex gap-4 text-xs text-muted-foreground border-t pt-4">
                 <span className="flex items-center gap-1"><Eye className="h-3 w-3"/> {selectedPost.views_count} Views</span>
                 <span className="flex items-center gap-1"><ThumbsUp className="h-3 w-3"/> {selectedPost.likes_count} Likes</span>
                 <span className="flex items-center gap-1"><MessageCircle className="h-3 w-3"/> {selectedPost.comments_count} Comments</span>
              </div>
            </div>
          )}

          <DialogFooter className="gap-2 sm:gap-0 border-t pt-4 mt-2">
             {selectedPost?.source_url && (
                <Button variant="outline" asChild size="sm">
                    <a href={selectedPost.source_url} target="_blank" rel="noreferrer">
                        <ExternalLink className="mr-2 h-3 w-3"/> Link gốc
                    </a>
                </Button>
             )}
             <Button 
                variant="destructive" 
                size="sm"
                onClick={() => selectedPost && handleDelete(selectedPost.id)}
             >
                <Trash2 className="mr-2 h-3 w-3"/> Xóa bài viết
             </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DataModeration;