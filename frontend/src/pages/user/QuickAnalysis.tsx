import { useState } from 'react';
import { useMutation } from '@tanstack/react-query'; // Import React Query
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Search, Loader2, ThumbsUp, ThumbsDown, FileText, Tag, Sparkles, BarChart3, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = 'http://localhost:8000';

// Interface cho kết quả từ Backend
interface BackendResponse {
  sentiment: string;     // POSITIVE, NEGATIVE, NEUTRAL
  sentiment_score: number;
  marketing_score: number;
  content_snippet: string;
  has_keyword: boolean;
  matched_keyword: string;
  platform: string;
  saved: boolean;
  title: string;
}

// Interface cho hiển thị (giữ nguyên cấu trúc cũ hoặc mở rộng nhẹ)
interface AnalysisResult {
  sentiment: 'Positive' | 'Negative' | 'Neutral';
  confidence: number;
  summary: string;
  keywords: string[]; // Sẽ chứa matched_keyword và platform
  source: string;
  marketing_score: number; // Thêm hiển thị điểm MKT
  saved: boolean;         // Thêm trạng thái lưu
}

const QuickAnalysis = () => {
  const [url, setUrl] = useState('');
  
  // Dùng mutation để gọi API
  const analyzeMutation = useMutation({
    mutationFn: async (inputUrl: string) => {
      const token = localStorage.getItem('auth_token');
      if (!token) throw new Error("Vui lòng đăng nhập lại");

      const res = await fetch(`${API_URL}/api/analyze-url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ url: inputUrl }) // Gửi URL lên
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Phân tích thất bại');
      }
      return await res.json() as BackendResponse;
    },
    onSuccess: (data) => {
        if (data.saved) {
            toast.success(`Đã lưu! Khớp từ khóa: ${data.matched_keyword}`);
        } else {
            toast.warning('Đã phân tích nhưng KHÔNG lưu (Không khớp từ khóa)');
        }
    },
    onError: (error: Error) => {
        toast.error(error.message);
    }
  });

  const isLoading = analyzeMutation.isPending;

  // Chuyển đổi dữ liệu Backend -> Frontend Format để giữ nguyên giao diện cũ
  const result: AnalysisResult | null = analyzeMutation.data ? {
    sentiment: analyzeMutation.data.sentiment === 'POSITIVE' ? 'Positive' : 
               analyzeMutation.data.sentiment === 'NEGATIVE' ? 'Negative' : 'Neutral',
    confidence: Math.abs(analyzeMutation.data.sentiment_score), // Lấy trị tuyệt đối làm độ tin cậy giả định
    summary: analyzeMutation.data.content_snippet,
    keywords: [
        analyzeMutation.data.platform, 
        ...(analyzeMutation.data.matched_keyword ? [analyzeMutation.data.matched_keyword] : [])
    ],
    source: analyzeMutation.data.platform === 'youtube' ? 'YouTube' : 'News',
    marketing_score: analyzeMutation.data.marketing_score,
    saved: analyzeMutation.data.saved
  } : null;

  const handleAnalyze = () => {
    if (!url.trim()) return toast.error('Vui lòng nhập URL bài viết!');
    
    // Validate cơ bản
    const isYoutube = url.includes('youtube.com') || url.includes('youtu.be');
    const isWeb = url.startsWith('http');
    const isSocial = url.includes('facebook.com') || url.includes('tiktok.com');

    if (isYoutube || (isWeb && !isSocial)) {
        analyzeMutation.mutate(url);
    } else {
        toast.error('Chỉ hỗ trợ YouTube hoặc Link báo chí (Không hỗ trợ Facebook/TikTok)');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          Phân tích nhanh
        </h1>
        <p className="text-muted-foreground">Dán URL bài viết để phân tích sentiment ngay lập tức</p>
      </div>

      {/* Input Section */}
      <Card className="gradient-card border-border">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                placeholder="Dán URL bài viết hoặc video (YouTube, Báo chí...)"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
                className="pl-10 bg-secondary border-border h-12 text-base"
              />
            </div>
            <Button 
              onClick={handleAnalyze} 
              disabled={isLoading}
              className="h-12 px-8 gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Đang phân tích...
                </>
              ) : (
                <>
                  <Sparkles className="h-5 w-5" />
                  Phân tích ngay
                </>
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-3 flex items-center gap-1">
             <AlertTriangle className="h-3 w-3" />
             Hệ thống sẽ tự động lưu nếu nội dung khớp với từ khóa trong Cấu hình của bạn.
          </p>
        </CardContent>
      </Card>

      {/* Loading State - Giữ nguyên */}
      {isLoading && (
        <Card className="gradient-card border-border">
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center gap-4">
              <div className="relative">
                <div className="w-16 h-16 border-4 border-primary/20 rounded-full" />
                <div className="absolute top-0 left-0 w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin" />
              </div>
              <div className="text-center">
                <p className="font-medium">Đang đọc nội dung & Phân tích AI...</p>
                <p className="text-sm text-muted-foreground">Đang lấy transcript và chấm điểm Marketing</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Result Section - Giữ nguyên cấu trúc nhưng binding data thật */}
      {result && !isLoading && (
        <div className="space-y-4">
          {/* Thông báo trạng thái lưu */}
          {result.saved ? (
             <div className="flex items-center gap-2 p-3 bg-green-50 text-green-700 rounded-lg border border-green-200 text-sm">
                <CheckCircle2 className="h-4 w-4" />
                Đã lưu vào hệ thống vì khớp từ khóa theo dõi.
             </div>
          ) : (
             <div className="flex items-center gap-2 p-3 bg-yellow-50 text-yellow-700 rounded-lg border border-yellow-200 text-sm">
                <AlertTriangle className="h-4 w-4" />
                Kết quả này KHÔNG được lưu (Không khớp từ khóa).
             </div>
          )}

          <Card className="gradient-card border-border overflow-hidden">
            <div className={`h-1 ${result.sentiment === 'Positive' ? 'bg-green-500' : result.sentiment === 'Negative' ? 'bg-red-500' : 'bg-gray-400'}`} />
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">Kết quả phân tích</CardTitle>
                <Badge variant="outline" className="text-muted-foreground capitalize">
                  Nguồn: {result.source}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Sentiment & Marketing Score */}
              <div className="flex items-center gap-4 p-4 rounded-xl bg-secondary/50">
                <div className={`p-4 rounded-xl ${
                  result.sentiment === 'Positive' 
                    ? 'bg-green-100 text-green-700' 
                    : result.sentiment === 'Negative'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-200 text-gray-700'
                }`}>
                  {result.sentiment === 'Positive' ? <ThumbsUp className="h-8 w-8" /> : 
                   result.sentiment === 'Negative' ? <ThumbsDown className="h-8 w-8" /> : <div className="h-8 w-8 font-bold text-2xl flex items-center justify-center">-</div>}
                </div>
                
                <div className="flex-1 grid grid-cols-2 gap-4">
                    <div>
                        <p className="text-2xl font-bold">
                            {result.sentiment === 'Positive' ? 'Tích cực' : result.sentiment === 'Negative' ? 'Tiêu cực' : 'Trung lập'}
                        </p>
                        <p className="text-muted-foreground text-sm">
                            Độ tin cậy AI: <span className="font-mono text-primary">{(result.confidence * 100).toFixed(0)}%</span>
                        </p>
                    </div>
                    <div className="border-l pl-4">
                         <div className="flex items-center gap-2 mb-1">
                             <BarChart3 className="h-4 w-4 text-muted-foreground" />
                             <span className="text-sm font-medium text-muted-foreground">Điểm Marketing</span>
                         </div>
                         <p className="text-2xl font-bold text-primary">{result.marketing_score}/10</p>
                    </div>
                </div>
              </div>

              {/* Summary */}
              <div className="space-y-2">
                <h4 className="font-medium flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  Tóm tắt nội dung
                </h4>
                <p className="text-muted-foreground leading-relaxed p-4 bg-secondary/30 rounded-lg text-sm">
                  {result.summary}
                </p>
              </div>

              {/* Keywords / Tags */}
              <div className="space-y-2">
                <h4 className="font-medium flex items-center gap-2">
                  <Tag className="h-4 w-4 text-primary" />
                  Thông tin trích xuất
                </h4>
                <div className="flex flex-wrap gap-2">
                  {result.keywords.map((keyword, i) => (
                    <Badge 
                      key={i} 
                      variant="outline" 
                      className="bg-primary/10 text-primary border-primary/30 px-3 py-1 capitalize"
                    >
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State - Giữ nguyên */}
      {!result && !isLoading && (
        <Card className="gradient-card border-border border-dashed">
          <CardContent className="py-16">
            <div className="flex flex-col items-center justify-center text-center gap-3">
              <div className="p-4 rounded-2xl bg-secondary">
                <Search className="h-8 w-8 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium">Chưa có kết quả</p>
                <p className="text-sm text-muted-foreground">Dán URL bài viết và nhấn "Phân tích ngay"</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default QuickAnalysis;