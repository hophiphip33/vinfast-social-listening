// ===== MOCK DATA - DỮ LIỆU GIẢ LẬP CHO ADMIN DASHBOARD =====
// File này chứa tất cả dữ liệu mẫu để chạy giao diện ngay lập tức

// ----- TYPES -----
export interface User {
  id: string;
  name: string;
  email: string;
  plan: 'Free' | 'Premium' | 'Enterprise';
  status: 'Active' | 'Banned' | 'Inactive';
  keywords: string[];
  createdAt: string;
}

export interface Post {
  id: string;
  title: string;
  platform: 'Facebook' | 'Twitter' | 'TikTok' | 'YouTube' | 'News';
  sentiment: 'Positive' | 'Negative' | 'Neutral';
  score: number;
  isSpam: boolean;
  createdAt: string;
}

export interface AuditLog {
  id: string;
  action: string;
  actor: string;
  timestamp: string;
  details: string;
}

export interface SystemMetrics {
  cpuUsage: number;
  ramUsage: number;
  dbSize: string;
  activeConnections: number;
}

// ----- MOCK USERS - DANH SÁCH NGƯỜI DÙNG MẪU -----
export const mockUsers: User[] = [
  {
    id: 'USR001',
    name: 'Nguyễn Văn An',
    email: 'an.nguyen@vinfast.vn',
    plan: 'Premium',
    status: 'Active',
    keywords: ['VinFast', 'VF8', 'VF9', 'xe điện'],
    createdAt: '2024-01-15',
  },
  {
    id: 'USR002',
    name: 'Trần Thị Bình',
    email: 'binh.tran@fpt.com.vn',
    plan: 'Free',
    status: 'Active',
    keywords: ['FPT Software', 'công nghệ', 'AI'],
    createdAt: '2024-02-20',
  },
  {
    id: 'USR003',
    name: 'Lê Minh Châu',
    email: 'chau.le@viettel.com.vn',
    plan: 'Premium',
    status: 'Active',
    keywords: ['Viettel', '5G', 'viễn thông'],
    createdAt: '2024-03-10',
  },
  {
    id: 'USR004',
    name: 'Phạm Đức Dũng',
    email: 'dung.pham@gmail.com',
    plan: 'Free',
    status: 'Banned',
    keywords: ['startup', 'khởi nghiệp'],
    createdAt: '2024-01-05',
  },
  {
    id: 'USR005',
    name: 'Hoàng Thu Hà',
    email: 'ha.hoang@samsung.com',
    plan: 'Premium',
    status: 'Active',
    keywords: ['Samsung', 'Galaxy', 'điện thoại'],
    createdAt: '2024-04-01',
  },
];

// ----- MOCK POSTS - BÀI VIẾT ĐÃ THU THẬP -----
export const mockPosts: Post[] = [
  {
    id: 'POST001',
    title: 'VinFast VF8 đạt doanh số kỷ lục tháng 12',
    platform: 'Facebook',
    sentiment: 'Positive',
    score: 0.92,
    isSpam: false,
    createdAt: '2024-12-28 14:30',
  },
  {
    id: 'POST002',
    title: 'Người dùng phàn nàn về pin VF9 yếu khi trời lạnh',
    platform: 'Twitter',
    sentiment: 'Negative',
    score: 0.78,
    isSpam: false,
    createdAt: '2024-12-28 12:15',
  },
  {
    id: 'POST003',
    title: 'So sánh chi tiết VF8 vs Tesla Model Y 2024',
    platform: 'YouTube',
    sentiment: 'Neutral',
    score: 0.65,
    isSpam: false,
    createdAt: '2024-12-27 18:45',
  },
  {
    id: 'POST004',
    title: 'CLICK NGAY - Mua xe điện giá rẻ nhất!!!',
    platform: 'TikTok',
    sentiment: 'Positive',
    score: 0.45,
    isSpam: true,
    createdAt: '2024-12-27 09:20',
  },
  {
    id: 'POST005',
    title: 'FPT Software ký hợp đồng 100 triệu USD với đối tác Nhật',
    platform: 'News',
    sentiment: 'Positive',
    score: 0.88,
    isSpam: false,
    createdAt: '2024-12-26 16:00',
  },
  {
    id: 'POST006',
    title: 'Viettel triển khai mạng 5G phủ sóng toàn quốc',
    platform: 'News',
    sentiment: 'Positive',
    score: 0.91,
    isSpam: false,
    createdAt: '2024-12-26 10:30',
  },
  {
    id: 'POST007',
    title: 'Người dùng tố FPT Shop bán hàng kém chất lượng',
    platform: 'Facebook',
    sentiment: 'Negative',
    score: 0.82,
    isSpam: false,
    createdAt: '2024-12-25 20:15',
  },
];

// ----- MOCK AUDIT LOGS - NHẬT KÝ HOẠT ĐỘNG -----
export const mockAuditLogs: AuditLog[] = [
  {
    id: 'LOG001',
    action: 'CREATE_USER',
    actor: 'Admin',
    timestamp: '2024-12-28 15:30:00',
    details: 'Đã thêm user mới: Hoàng Thu Hà',
  },
  {
    id: 'LOG002',
    action: 'CRAWL_COMPLETE',
    actor: 'System',
    timestamp: '2024-12-28 14:00:00',
    details: 'Hệ thống đã cào 523 bài viết từ Facebook',
  },
  {
    id: 'LOG003',
    action: 'BAN_USER',
    actor: 'Admin',
    timestamp: '2024-12-28 11:45:00',
    details: 'Đã khóa tài khoản: Phạm Đức Dũng (vi phạm ToS)',
  },
  {
    id: 'LOG004',
    action: 'UPDATE_KEYWORD',
    actor: 'Admin',
    timestamp: '2024-12-28 10:20:00',
    details: 'Đã thêm từ khóa global: "xe điện 2025"',
  },
  {
    id: 'LOG005',
    action: 'DELETE_SPAM',
    actor: 'Admin',
    timestamp: '2024-12-27 16:30:00',
    details: 'Đã xóa 15 bài viết spam',
  },
  {
    id: 'LOG006',
    action: 'CRAWL_COMPLETE',
    actor: 'System',
    timestamp: '2024-12-27 12:00:00',
    details: 'Hệ thống đã cào 892 bài viết từ Twitter',
  },
  {
    id: 'LOG007',
    action: 'API_KEY_UPDATE',
    actor: 'Admin',
    timestamp: '2024-12-27 09:15:00',
    details: 'Đã cập nhật Gemini API Key',
  },
];

// ----- MOCK GLOBAL KEYWORDS - TỪ KHÓA HỆ THỐNG -----
export const mockGlobalKeywords: string[] = [
  'VinFast',
  'FPT',
  'Viettel',
  'Samsung Vietnam',
  'xe điện',
  'công nghệ AI',
  'startup Việt Nam',
  'thương mại điện tử',
];

// ----- HÀM GIẢ LẬP LẤY SYSTEM METRICS -----
export const getSystemMetrics = (): SystemMetrics => {
  return {
    cpuUsage: Math.floor(Math.random() * 30) + 35, // 35-65%
    ramUsage: Math.floor(Math.random() * 20) + 50, // 50-70%
    dbSize: '2.4 GB',
    activeConnections: Math.floor(Math.random() * 10) + 5,
  };
};

// ----- HÀM TẠO ID MỚI -----
export const generateId = (prefix: string): string => {
  const num = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  return `${prefix}${num}`;
};
