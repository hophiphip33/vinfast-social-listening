import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input'; // Cần import Input
import { 
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow 
} from '@/components/ui/table';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '@/components/ui/select';
import StatusBadge from './StatusBadge';
import { toast } from 'sonner';
import { Loader2, Search } from 'lucide-react';

const API_URL = 'http://localhost:8000';

const DataModeration = () => {
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // State bộ lọc
  const [filterPlatform, setFilterPlatform] = useState('all');
  const [filterSentiment, setFilterSentiment] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Hàm gọi API lấy dữ liệu
  const fetchPosts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      // Tạo URL params
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

  // Gọi lại API mỗi khi filter hoặc page thay đổi
  useEffect(() => {
    fetchPosts();
  }, [page, filterPlatform, filterSentiment]); // Thêm searchTerm vào đây nếu muốn search realtime, hoặc để riêng nút Search

  // Hàm cập nhật Sentiment
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
        // Cập nhật giao diện ngay lập tức
        setPosts(posts.map(p => p.id === postId ? { ...p, sentiment: newSentiment } : p));
      }
    } catch (error) {
      toast.error("Lỗi kết nối");
    }
  };

  return (
    <div className="space-y-6">
      {/* --- THANH CÔNG CỤ (Search & Filter) --- */}
      <div className="flex flex-wrap gap-4 justify-between">
        <div className="flex gap-2 w-full md:w-auto">
          <Input 
            placeholder="Tìm kiếm nội dung..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchPosts()} // Enter để tìm
            className="w-[200px]"
          />
          <Button variant="outline" onClick={fetchPosts}><Search className="w-4 h-4" /></Button>
        </div>

        <div className="flex gap-2">
           <Select value={filterPlatform} onValueChange={(v) => {setFilterPlatform(v); setPage(1);}}>
             <SelectTrigger className="w-[130px]"><SelectValue placeholder="Platform" /></SelectTrigger>
             <SelectContent>
               <SelectItem value="all">All Platform</SelectItem>
               <SelectItem value="facebook">Facebook</SelectItem>
               <SelectItem value="youtube">YouTube</SelectItem>
               <SelectItem value="news">News</SelectItem>
             </SelectContent>
           </Select>
           {/* Thêm Select Sentiment tương tự */}
        </div>
      </div>

      {/* --- BẢNG DỮ LIỆU --- */}
      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tiêu đề / Nội dung</TableHead>
              <TableHead>Nguồn</TableHead>
              <TableHead>Cảm xúc (AI)</TableHead>
              <TableHead>Link</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={4} className="text-center h-24"><Loader2 className="animate-spin mx-auto"/></TableCell></TableRow>
            ) : posts.map((post) => (
              <TableRow key={post.id}>
                <TableCell className="max-w-[400px]">
                  <div className="font-medium truncate">{post.title || "No Title"}</div>
                  <div className="text-xs text-muted-foreground truncate">{post.content}</div>
                </TableCell>
                <TableCell className="capitalize">{post.platform}</TableCell>
                <TableCell>
                  <Select 
                    value={post.sentiment || "Neutral"} 
                    onValueChange={(val) => changeSentiment(post.id, val)}
                  >
                    <SelectTrigger className="h-8 w-[110px] border-none shadow-none">
                      <StatusBadge status={post.sentiment} />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Positive">Positive</SelectItem>
                      <SelectItem value="Negative">Negative</SelectItem>
                      <SelectItem value="Neutral">Neutral</SelectItem>
                    </SelectContent>
                  </Select>
                </TableCell>
                <TableCell>
                  {post.source_url && (
                    <a href={post.source_url} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline text-sm">
                      Xem gốc
                    </a>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* --- PHÂN TRANG --- */}
      <div className="flex justify-end gap-2">
        <Button 
          variant="outline" 
          disabled={page <= 1} 
          onClick={() => setPage(p => p - 1)}
        >Trước</Button>
        <span className="py-2 px-2 text-sm">Trang {page} / {totalPages}</span>
        <Button 
          variant="outline" 
          disabled={page >= totalPages} 
          onClick={() => setPage(p => p + 1)}
        >Sau</Button>
      </div>
    </div>
  );
};

export default DataModeration;