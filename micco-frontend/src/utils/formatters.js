// src/utils/formatters.js

export function formatBytes(bytes) {
    if (!bytes && bytes !== 0) return '—';
    if (typeof bytes === 'string') return bytes;
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

export function timeAgo(dateStr) {
    if (!dateStr) return '—';
    const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
    if (diff < 60) return 'vừa xong';
    if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`;
    if (diff < 86400 * 7) return `${Math.floor(diff / 86400)} ngày trước`;
    return formatDate(dateStr);
}

export function getExt(name = '') {
    return name.includes('.') ? name.split('.').pop().toUpperCase() : 'FILE';
}

export function getInitials(name = '') {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
}

const avatarColors = [
    'bg-blue-500', 'bg-green-500', 'bg-purple-500',
    'bg-orange-500', 'bg-teal-500', 'bg-pink-500', 'bg-red-500',
];
export function avatarColor(name = '') {
    let hash = 0;
    for (const c of name) hash += c.charCodeAt(0);
    return avatarColors[hash % avatarColors.length];
}

const categoryLabels = {
    'Tài liệu': 'Tài liệu', 'Hợp đồng': 'Hợp đồng', 'Báo cáo': 'Báo cáo',
    'Biên bản': 'Biên bản', 'Quy trình': 'Quy trình', 'Khác': 'Khác',
    Report: 'Báo cáo', Spreadsheet: 'Bảng tính',
    'Technical Document': 'Tài liệu kỹ thuật', Media: 'Đa phương tiện', Archive: 'Lưu trữ',
};

export const categoryColors = {
    'Báo cáo': 'bg-blue-50 text-blue-700 dark:bg-blue-500/20 dark:text-blue-300',
    'Bảng tính': 'bg-green-50 text-green-700 dark:bg-green-500/20 dark:text-green-300',
    'Tài liệu kỹ thuật': 'bg-violet-50 text-violet-700 dark:bg-violet-500/20 dark:text-violet-300',
    'Đa phương tiện': 'bg-pink-50 text-pink-700 dark:bg-pink-500/20 dark:text-pink-300',
    'Lưu trữ': 'bg-yellow-50 text-yellow-700 dark:bg-yellow-500/20 dark:text-yellow-300',
    'Tài liệu': 'bg-sky-50 text-sky-700 dark:bg-sky-500/20 dark:text-sky-300',
    'Hợp đồng': 'bg-purple-50 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300',
    'Biên bản': 'bg-teal-50 text-teal-700 dark:bg-teal-500/20 dark:text-teal-300',
    'Quy trình': 'bg-orange-50 text-orange-700 dark:bg-orange-500/20 dark:text-orange-300',
    'Khác': 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
};

export function getCategoryLabel(cat) {
    return categoryLabels[cat] || cat || 'Khác';
}
