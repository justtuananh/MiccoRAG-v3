import {
    FileText, FileSpreadsheet, FileImage, File, FileArchive
} from 'lucide-react';

export const documents = [
    { id: 1, name: 'Q4 Financial Report 2025.pdf', type: 'PDF', size: '2.4 MB', owner: 'Alex Johnson', date: '2026-02-20', tags: ['Finance', 'Reports'], status: 'Active' },
    { id: 2, name: 'Employee Handbook v3.docx', type: 'DOCX', size: '1.8 MB', owner: 'Sarah Chen', date: '2026-02-19', tags: ['HR', 'Policy'], status: 'Active' },
    { id: 3, name: 'Product Roadmap 2026.pptx', type: 'PPTX', size: '5.2 MB', owner: 'Mike Rivera', date: '2026-02-18', tags: ['Product', 'Strategy'], status: 'Active' },
    { id: 4, name: 'Vendor Contract - CloudServ.pdf', type: 'PDF', size: '890 KB', owner: 'Alex Johnson', date: '2026-02-17', tags: ['Legal', 'Contracts'], status: 'Active' },
    { id: 5, name: 'Marketing Budget Q1.xlsx', type: 'XLSX', size: '1.2 MB', owner: 'Lisa Park', date: '2026-02-16', tags: ['Marketing', 'Finance'], status: 'Active' },
    { id: 6, name: 'API Documentation v2.md', type: 'MD', size: '340 KB', owner: 'Dev Team', date: '2026-02-15', tags: ['Engineering', 'Docs'], status: 'Active' },
    { id: 7, name: 'Customer Survey Results.xlsx', type: 'XLSX', size: '3.1 MB', owner: 'Lisa Park', date: '2026-02-14', tags: ['Research', 'Data'], status: 'Archived' },
    { id: 8, name: 'Brand Guidelines 2026.pdf', type: 'PDF', size: '12.5 MB', owner: 'Sarah Chen', date: '2026-02-13', tags: ['Design', 'Branding'], status: 'Active' },
    { id: 9, name: 'Security Audit Report.pdf', type: 'PDF', size: '4.7 MB', owner: 'IT Team', date: '2026-02-12', tags: ['Security', 'Compliance'], status: 'Active' },
    { id: 10, name: 'Meeting Notes - Board.docx', type: 'DOCX', size: '520 KB', owner: 'Alex Johnson', date: '2026-02-11', tags: ['Management', 'Notes'], status: 'Active' },
    { id: 11, name: 'Project Timeline.xlsx', type: 'XLSX', size: '780 KB', owner: 'Mike Rivera', date: '2026-02-10', tags: ['Project', 'Planning'], status: 'Active' },
    { id: 12, name: 'NDA - Partner Corp.pdf', type: 'PDF', size: '210 KB', owner: 'Legal', date: '2026-02-09', tags: ['Legal', 'NDA'], status: 'Active' },
    { id: 13, name: 'Training Materials.zip', type: 'ZIP', size: '45.3 MB', owner: 'HR Team', date: '2026-02-08', tags: ['HR', 'Training'], status: 'Active' },
    { id: 14, name: 'System Architecture.png', type: 'PNG', size: '2.1 MB', owner: 'Dev Team', date: '2026-02-07', tags: ['Engineering', 'Architecture'], status: 'Active' },
    { id: 15, name: 'Quarterly OKRs.docx', type: 'DOCX', size: '430 KB', owner: 'Alex Johnson', date: '2026-02-06', tags: ['Strategy', 'OKR'], status: 'Active' },
];

export const dashboardStats = {
    totalFiles: 1247,
    storageUsed: '34.8 GB',
    recentUploads: 23,
    teamMembers: 48,
};

export const uploadsOverTime = [
    { month: 'Sep', uploads: 45 },
    { month: 'Oct', uploads: 62 },
    { month: 'Nov', uploads: 58 },
    { month: 'Dec', uploads: 71 },
    { month: 'Jan', uploads: 89 },
    { month: 'Feb', uploads: 23 },
];

export const storageByType = [
    { type: 'PDF', size: 12.4, fill: '#1E3A8A' },
    { type: 'DOCX', size: 8.2, fill: '#4F46E5' },
    { type: 'XLSX', size: 5.1, fill: '#10B981' },
    { type: 'Images', size: 4.8, fill: '#F59E0B' },
    { type: 'Khác', size: 4.3, fill: '#6B7280' },
];

export const testimonials = [
    {
        name: 'Jennifer Walsh',
        role: 'Phó giám đốc vận hành',
        company: 'TechForward Inc.',
        quote: 'Micco AI đã thay đổi hoàn toàn cách chúng tôi quản lý tài liệu tuân thủ. Trợ lý AI tìm câu trả lời chỉ trong vài giây, thay vì hàng giờ tìm thủ công.',
        rating: 5,
    },
    {
        name: 'David Kim',
        role: 'Trưởng phòng pháp lý',
        company: 'Meridian Partners',
        quote: 'Tính năng tìm kiếm thông minh thật sự ấn tượng. Đội pháp lý của chúng tôi có thể đối chiếu hợp đồng và tìm điều khoản liên quan ngay lập tức trên hàng nghìn tài liệu.',
        rating: 5,
    },
    {
        name: 'Rachel Torres',
        role: 'Giám đốc công nghệ',
        company: 'ScaleUp Solutions',
        quote: 'Chúng tôi đã đánh giá 12 nền tảng quản lý tài liệu. Micco AI là lựa chọn vượt trội — bảo mật cấp doanh nghiệp nhưng vẫn đủ đơn giản để cả đội sử dụng hằng ngày.',
        rating: 5,
    },
];

export const chatMessages = [
    {
        id: 1,
        role: 'ai',
        content: 'Xin chào! Tôi là Trợ lý Tài liệu AI của bạn. Tôi có thể giúp bạn tìm thông tin, tóm tắt tài liệu hoặc trả lời câu hỏi dựa trên các tệp bạn đã tải lên. Tôi có thể giúp gì cho bạn hôm nay?',
        sources: [],
    },
];

export const examplePrompts = [
    'Tóm tắt hợp đồng này.',
    'Điều khoản thanh toán trong thỏa thuận là gì?',
    'Liệt kê các rủi ro chính được nêu trong báo cáo.',
    'So sánh hai tài liệu này.',
    'Số liệu doanh thu theo quý là bao nhiêu?',
    'Tìm tất cả nội dung đề cập đến yêu cầu tuân thủ.',
];

export const fileTypeIcons = {
    PDF: FileText,
    DOCX: FileText,
    XLSX: FileSpreadsheet,
    PPTX: FileText,
    PNG: FileImage,
    JPG: FileImage,
    MD: File,
    ZIP: FileArchive,
};

export const fileTypeColors = {
    PDF: 'text-red-500',
    DOCX: 'text-blue-500',
    XLSX: 'text-green-500',
    PPTX: 'text-orange-500',
    PNG: 'text-purple-500',
    JPG: 'text-purple-500',
    MD: 'text-gray-500',
    ZIP: 'text-yellow-600',
};

export const navItems = [
    { label: 'Tổng quan', path: '/dashboard', icon: 'LayoutDashboard' },
    { label: 'Tài liệu của tôi', path: '/documents', icon: 'FolderOpen' },
    { label: 'Tải lên', path: '/documents', icon: 'Upload' },
    { label: 'Trợ lý trò chuyện', path: '/chat', icon: 'MessageSquare' },
    { label: 'Nhóm', path: '/dashboard', icon: 'Users' },
    { label: 'Cài đặt', path: '/dashboard', icon: 'Settings' },
];
