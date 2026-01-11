import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Save, RefreshCw, Plus, Trash2, Server, Key, Shield } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = 'http://localhost:8000';

const SystemConfig = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [config, setConfig] = useState({
    crawl_delay_news: 15,
    crawl_delay_social: 30,
    max_posts_batch: 50,
    active_sources: { youtube: true, news: true, facebook: false }, // Vẫn giữ state để không lỗi, nhưng không hiển thị UI chỉnh sửa global
    api_keys: [],
    blacklist_keywords: [],
  });
  
  const [blacklistStr, setBlacklistStr] = useState('');

  const fetchConfig = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/system/config`);
      const data = await res.json();
      setConfig(data);
      setBlacklistStr(data.blacklist_keywords?.join(', ') || '');
    } catch (error) {
      toast.error('Lỗi tải cấu hình hệ thống');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const payload = {
        ...config,
        blacklist_keywords: blacklistStr.split(',').map(k => k.trim()).filter(k => k)
      };

      const res = await fetch(`${API_URL}/api/system/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        toast.success('Đã lưu cấu hình thành công!');
        fetchConfig();
      } else {
        toast.error('Lưu thất bại');
      }
    } catch (error) {
      toast.error('Lỗi kết nối Server');
    } finally {
      setIsLoading(false);
    }
  };

  const addApiKey = () => {
    const newKey = prompt("Nhập API Key mới:");
    if (newKey) {
        setConfig(prev => ({...prev, api_keys: [...prev.api_keys, newKey]}));
    }
  };
  
  const removeApiKey = (index: number) => {
      const newKeys = [...config.api_keys];
      newKeys.splice(index, 1);
      setConfig(prev => ({...prev, api_keys: newKeys}));
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={fetchConfig} disabled={isLoading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} /> 
          {isLoading ? 'Đang tải...' : 'Tải lại'}
        </Button>
        <Button onClick={handleSave} disabled={isLoading}>
          <Save className="mr-2 h-4 w-4" /> Lưu thay đổi
        </Button>
      </div>

      <Tabs defaultValue="crawler" className="w-full">
        <TabsList className="grid w-full grid-cols-3 lg:w-[400px]">
          <TabsTrigger value="crawler">Thu thập</TabsTrigger>
          <TabsTrigger value="ai">AI & API</TabsTrigger>
          <TabsTrigger value="security">Bộ lọc & Bảo mật</TabsTrigger>
        </TabsList>

        {/* TAB 1: CRAWLER - Đã bỏ phần chọn Nguồn dữ liệu global */}
        <TabsContent value="crawler" className="mt-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Server className="h-5 w-5 text-primary"/> Cấu hình Crawler</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>News Crawl Delay (Giờ)</Label>
                  <Input 
                    type="number" 
                    value={config.crawl_delay_news}
                    onChange={(e) => setConfig({...config, crawl_delay_news: parseInt(e.target.value) || 0})}
                  />
                  <p className="text-xs text-muted-foreground">Thời gian chờ giữa các lần quét tin tức.</p>
                </div>
                <div className="space-y-2">
                  <Label>Social Crawl Delay (Giờ)</Label>
                  <Input 
                    type="number" 
                    value={config.crawl_delay_social}
                    onChange={(e) => setConfig({...config, crawl_delay_social: parseInt(e.target.value) || 0})}
                  />
                  <p className="text-xs text-muted-foreground">Thời gian chờ giữa các lần quét Youtube/Social.</p>
                </div>
              </div>
              
              <div className="p-4 border border-l-4 border-l-primary/50 rounded bg-secondary/10 text-sm text-muted-foreground">
                 <p className="font-semibold text-foreground mb-1">Lưu ý:</p>
                 Cấu hình bật/tắt nguồn tin (Youtube/News) hiện được quản lý riêng cho từng khách hàng tại menu <b>Quản lý User</b>.
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* TAB 2: AI KEYS */}
        <TabsContent value="ai" className="mt-4">
            <Card>
                <CardHeader><CardTitle className="flex gap-2"><Key className="h-5 w-5 text-warning"/> API Keys</CardTitle></CardHeader>
                <CardContent className="space-y-4">
                    {(config.api_keys || []).map((key, idx) => (
                        <div key={idx} className="flex gap-2">
                            <Input value={key} readOnly className="font-mono text-xs bg-muted"/>
                            <Button variant="ghost" size="icon" onClick={() => removeApiKey(idx)}><Trash2 className="h-4 w-4 text-destructive"/></Button>
                        </div>
                    ))}
                    <Button variant="outline" className="w-full border-dashed" onClick={addApiKey}><Plus className="h-4 w-4 mr-2"/> Thêm Key mới</Button>
                </CardContent>
            </Card>
        </TabsContent>

        {/* TAB 3: BLACKLIST */}
        <TabsContent value="security" className="mt-4">
            <Card>
                <CardHeader><CardTitle className="flex gap-2"><Shield className="h-5 w-5 text-destructive"/> Bộ lọc rác</CardTitle></CardHeader>
                <CardContent>
                    <div className="space-y-2">
                        <Label>Từ khóa chặn (cách nhau bởi dấu phẩy)</Label>
                        <textarea 
                            className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                            value={blacklistStr}
                            onChange={(e) => setBlacklistStr(e.target.value)}
                            placeholder="xổ số, cờ bạc,..."
                        />
                    </div>
                </CardContent>
            </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SystemConfig;