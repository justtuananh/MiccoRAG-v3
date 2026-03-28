import { useState, useEffect } from 'react';
import { X, Save, Tag, Loader2, Lock, Globe } from 'lucide-react';
import WysiwygEditor from './WysiwygEditor';

const CATEGORIES = [
    'Chung',
    'Quy trình',
    'Hướng dẫn',
    'Tiêu chuẩn',
    'Quy định',
    'Kinh nghiệm',
    'Vật tư',
    'Nhà cung cấp',
    'An toàn',
    'Kỹ thuật',
];

export default function KnowledgeForm({ entry, onSave, onClose, saving = false }) {
    const [title, setTitle] = useState('');
    const [category, setCategory] = useState('Chung');
    const [status, setStatus] = useState('Active');
    const [visibility, setVisibility] = useState('internal');
    const [tags, setTags] = useState([]);
    const [tagInput, setTagInput] = useState('');
    const [contentHtml, setContentHtml] = useState('');
    const [contentText, setContentText] = useState('');

    useEffect(() => {
        if (entry) {
            setTitle(entry.title || '');
            setCategory(entry.category || 'Chung');
            setStatus(entry.status || 'Active');
            setVisibility(entry.visibility || 'internal');
            setTags(entry.tags || []);
            setContentHtml(entry.content_html || '');
            setContentText(entry.content_text || '');
        } else {
            setVisibility('internal');
        }
    }, [entry]);

    const handleEditorChange = ({ html, text }) => {
        setContentHtml(html);
        setContentText(text);
    };

    const handleAddTag = (e) => {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            const newTag = tagInput.replace(/,+$/, '').trim();
            if (newTag && !tags.includes(newTag)) {
                setTags([...tags, newTag]);
            }
            setTagInput('');
        }
    };

    const handleRemoveTag = (tag) => {
        setTags(tags.filter((t) => t !== tag));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!title.trim() || !contentText.trim()) return;
        onSave({
            title: title.trim(),
            content_html: contentHtml,
            content_text: contentText,
            category,
            tags,
            visibility,
            status,
        });
    };

    return (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 backdrop-blur-sm overflow-y-auto py-8">
            <div className="w-full max-w-4xl bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-800 mx-4">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {entry ? 'Chỉnh sửa tri thức' : 'Thêm tri thức mới'}
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {/* Title */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                            Tiêu đề <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Nhập tiêu đề tri thức..."
                            className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all"
                            required
                        />
                    </div>

                    {/* Category & Status row */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                                Danh mục
                            </label>
                            <select
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all"
                            >
                                {CATEGORIES.map((c) => (
                                    <option key={c} value={c}>{c}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                                Trạng thái
                            </label>
                            <select
                                value={status}
                                onChange={(e) => setStatus(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all"
                            >
                                <option value="Active">Hoạt động</option>
                                <option value="Draft">Bản nháp</option>
                                <option value="Archived">Lưu trữ</option>
                            </select>
                        </div>
                    </div>

                    {/* Visibility toggle */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                            Chế độ hiển thị
                        </label>
                        <div className="flex gap-3">
                            <button
                                type="button"
                                onClick={() => setVisibility('internal')}
                                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border-2 text-sm font-medium transition-all ${
                                    visibility === 'internal'
                                        ? 'border-primary-600 bg-primary-600/5 text-primary-700 dark:text-primary-400 dark:border-primary-500 dark:bg-primary-500/10'
                                        : 'border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                                }`}
                            >
                                <Lock className="w-4 h-4" />
                                Nội bộ
                            </button>
                            <button
                                type="button"
                                onClick={() => setVisibility('public')}
                                className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border-2 text-sm font-medium transition-all ${
                                    visibility === 'public'
                                        ? 'border-emerald-600 bg-emerald-600/5 text-emerald-700 dark:text-emerald-400 dark:border-emerald-500 dark:bg-emerald-500/10'
                                        : 'border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                                }`}
                            >
                                <Globe className="w-4 h-4" />
                                Công khai
                            </button>
                        </div>
                        <p className="text-xs text-gray-400 mt-1.5">
                            {visibility === 'internal'
                                ? 'Chỉ thành viên trong phòng ban mới xem được'
                                : 'Tất cả tài khoản đều có thể xem'}
                        </p>
                    </div>

                    {/* Tags */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                            Nhãn
                        </label>
                        <div className="flex flex-wrap items-center gap-2 p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 min-h-[42px]">
                            {tags.map((tag) => (
                                <span
                                    key={tag}
                                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-primary-50 text-primary-700 dark:bg-secondary-500/20 dark:text-secondary-400"
                                >
                                    <Tag className="w-3 h-3" />
                                    {tag}
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveTag(tag)}
                                        className="ml-0.5 hover:text-red-500 transition-colors"
                                    >
                                        <X className="w-3 h-3" />
                                    </button>
                                </span>
                            ))}
                            <input
                                type="text"
                                value={tagInput}
                                onChange={(e) => setTagInput(e.target.value)}
                                onKeyDown={handleAddTag}
                                placeholder={tags.length === 0 ? 'Nhấn Enter để thêm nhãn...' : ''}
                                className="flex-1 min-w-[120px] bg-transparent outline-none text-sm text-gray-900 dark:text-white placeholder-gray-400"
                            />
                        </div>
                    </div>

                    {/* WYSIWYG Editor */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                            Nội dung <span className="text-red-500">*</span>
                        </label>
                        <WysiwygEditor
                            content={contentHtml}
                            onChange={handleEditorChange}
                        />
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-800">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-5 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                        >
                            Hủy
                        </button>
                        <button
                            type="submit"
                            disabled={saving || !title.trim() || !contentText.trim()}
                            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {saving ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Save className="w-4 h-4" />
                            )}
                            {entry ? 'Cập nhật' : 'Đề xuất phê duyệt'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
