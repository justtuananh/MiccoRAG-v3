import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Upload, X, File, Image,
    ChevronDown, CheckCircle2,
    ChevronLeft, ChevronRight, Trash2, Search, Building2,
    Lock, Globe, MoreHorizontal, Eye, Download, Share2, Clock, XCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { fileTypeIconMap, fileTypeColors, fileTypeBgColors } from '../components/documents/fileTypes';
import DocumentsToolbar from '../components/documents/DocumentsToolbar';
import DocumentRow from '../components/documents/DocumentRow';
import DocumentCard from '../components/documents/DocumentCard';
import Breadcrumb from '../components/shared/Breadcrumb';
import { formatBytes, getExt } from '../utils/formatters';

const categories = ['All', 'Tài liệu', 'Hợp đồng', 'Báo cáo', 'Biên bản', 'Quy trình', 'Khác'];
const ROWS_PER_PAGE = 5;

export default function Documents() {
    const { authFetch } = useAuth();
    const navigate = useNavigate();
    const [documents, setDocuments] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [selectedDeptId, setSelectedDeptId] = useState(null);
    const [view, setView] = useState('table');
    const [search, setSearch] = useState('');
    const [typeFilter, setTypeFilter] = useState('All');
    const [categoryFilter, setCategoryFilter] = useState('All');
    const [dragActive, setDragActive] = useState(false);
    const [showUpload, setShowUpload] = useState(false);
    const [deleteTarget, setDeleteTarget] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadCategory, setUploadCategory] = useState('Tài liệu');
    const [uploadTags, setUploadTags] = useState([]);
    const [uploadThumbnail, setUploadThumbnail] = useState(null);
    const [uploadVisibility, setUploadVisibility] = useState('internal');
    const [uploadTagInput, setUploadTagInput] = useState('');
    const [stagedFiles, setStagedFiles] = useState([]);
    const [uploadSuccess, setUploadSuccess] = useState(false);
    const [uploadError, setUploadError] = useState('');
    const [openMenu, setOpenMenu] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);

    // Fetch departments for filter tabs
    useEffect(() => {
        authFetch('/api/auth/departments')
            .then(r => r.ok ? r.json() : [])
            .then(setDepartments)
            .catch(() => {});
    }, []);

    useEffect(() => { fetchDocuments(); }, [typeFilter, categoryFilter, selectedDeptId]);
    useEffect(() => { setCurrentPage(1); }, [search, typeFilter, categoryFilter, selectedDeptId]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handler = () => setOpenMenu(null);
        document.addEventListener('click', handler);
        return () => document.removeEventListener('click', handler);
    }, []);

    const fetchDocuments = async () => {
        try {
            const params = new URLSearchParams();
            if (typeFilter !== 'All') params.append('type', typeFilter);
            if (categoryFilter !== 'All') params.append('category', categoryFilter);
            if (selectedDeptId !== null) params.append('department_id', selectedDeptId);
            const qs = params.toString();
            const res = await authFetch(`/api/documents${qs ? '?' + qs : ''}`);
            if (res.ok) {
                const data = await res.json();
                setDocuments(Array.isArray(data) ? data : (data.items || []));
            }
        } catch (err) { console.error('Failed to fetch documents:', err); }
    };

    const filteredDocs = documents.filter((doc) => {
        const name = doc.name || doc.original_filename || '';
        return name.toLowerCase().includes(search.toLowerCase());
    });

    // Pagination
    const totalPages = Math.max(1, Math.ceil(filteredDocs.length / ROWS_PER_PAGE));
    const pageDocs = filteredDocs.slice((currentPage - 1) * ROWS_PER_PAGE, currentPage * ROWS_PER_PAGE);

    const handleDrag = useCallback((e) => {
        e.preventDefault(); e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
        else setDragActive(false);
    }, []);

    const stageFiles = (fileList) => {
        if (!fileList?.length) return;
        setStagedFiles(prev => [...prev, ...Array.from(fileList)]);
        setUploadSuccess(false);
        setUploadError('');
    };

    const removeStagedFile = (index) => setStagedFiles(prev => prev.filter((_, i) => i !== index));

    const handleUpload = async () => {
        if (!stagedFiles.length) return;
        setUploading(true);
        setUploadSuccess(false);
        setUploadError('');
        try {
            const formData = new FormData();
            for (const file of stagedFiles) formData.append('files', file);
            formData.append('category', uploadCategory);
            formData.append('visibility', uploadVisibility);
            if (uploadTags.length) formData.append('tags', uploadTags.join(','));
            if (uploadThumbnail) formData.append('thumbnail', uploadThumbnail);
            const res = await authFetch('/api/documents/upload', { method: 'POST', body: formData });
            if (res.ok) {
                await fetchDocuments();
                setUploadSuccess(true);
                setStagedFiles([]);
                setTimeout(() => {
                    setShowUpload(false);
                    setUploadCategory('Tài liệu');
                    setUploadTags([]);
                    setUploadTagInput('');
                    setUploadThumbnail(null);
                    setUploadVisibility('internal');
                    setUploadSuccess(false);
                }, 1500);
            } else {
                const err = await res.json().catch(() => ({}));
                setUploadError(err.detail || `Lỗi ${res.status}`);
            }
        } catch (err) {
            setUploadError(`Lỗi kết nối: ${err.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleThumbnailSelect = (e) => {
        const file = e.target.files?.[0];
        if (file) setUploadThumbnail(file);
    };

    const handleDrop = useCallback((e) => {
        e.preventDefault(); setDragActive(false);
        stageFiles(e.dataTransfer?.files);
    }, []);

    const handleFileInput = (e) => { stageFiles(e.target.files); e.target.value = ''; };

    const closeUploadPanel = () => {
        setShowUpload(false); setStagedFiles([]); setUploadCategory('Tài liệu'); setUploadTags([]); setUploadTagInput('');
        setUploadThumbnail(null); setUploadVisibility('internal'); setUploadSuccess(false); setUploadError('');
    };

    const handleDelete = async (id) => {
        try {
            const res = await authFetch(`/api/documents/${id}`, { method: 'DELETE' });
            if (res.ok) setDocuments(prev => prev.filter(d => d.id !== id));
            else { const err = await res.json().catch(() => ({})); alert(err.detail || 'Xóa thất bại'); }
        } catch (err) { console.error('Delete failed:', err); }
        setDeleteTarget(null);
    };

    const handleDownload = async (doc) => {
        try {
            const res = await authFetch(`/api/documents/${doc.id}/download`);
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a'); a.href = url; a.download = doc.name || doc.original_filename || 'document'; a.click();
                window.URL.revokeObjectURL(url);
            }
        } catch (err) { console.error('Download failed:', err); }
    };

    const totalStagedSize = stagedFiles.reduce((sum, f) => sum + f.size, 0);

    return (
        <div className="space-y-6 px-2 md:px-4">
            <div className="px-2 pt-4">
                <Breadcrumb items={[
                    { label: 'Tổng quan', href: '/dashboard' },
                    { label: 'Tài liệu' },
                ]} />
            </div>

            {/* ══════════════ Department Filter ══════════════ */}
            {departments.length > 0 && (
                <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 mx-2 px-5 py-4">
                    <div className="flex items-center gap-3 overflow-x-auto scrollbar-hide">
                        <Building2 className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider flex-shrink-0 mr-1">Phòng ban:</span>
                        <button
                            onClick={() => setSelectedDeptId(null)}
                            className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                                selectedDeptId === null
                                    ? 'bg-primary-600 text-white shadow-sm'
                                    : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                            }`}
                        >
                            Tất cả
                        </button>
                        {departments.map(dept => (
                            <button
                                key={dept.id}
                                onClick={() => setSelectedDeptId(dept.id)}
                                className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                                    selectedDeptId === dept.id
                                        ? 'bg-primary-600 text-white shadow-sm'
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                                }`}
                            >
                                {dept.name}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* ══════════════ All Documents ══════════════ */}
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden mx-2">

                {/* Table Header Bar */}
                <DocumentsToolbar
                    search={search}
                    onSearchChange={setSearch}
                    view={view}
                    onViewChange={setView}
                    onUploadClick={() => setShowUpload(!showUpload)}
                />

                {/* ─── Upload Modal ─── */}
                {showUpload && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center">
                        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={closeUploadPanel} />
                        <div className="relative bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden flex flex-col border border-gray-200 dark:border-gray-800 animate-fade-in">
                            {/* Header */}
                            <div className="px-6 py-4 flex items-center justify-between bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                                <div className="flex items-center gap-3">
                                    <div className="w-9 h-9 rounded-xl bg-primary-600/10 flex items-center justify-center">
                                        <Upload className="w-4 h-4 text-primary-600" />
                                    </div>
                                    <div>
                                        <h3 className="text-base font-bold text-gray-900 dark:text-white">Tải lên tài liệu</h3>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">Kéo & thả hoặc nhấp để chọn tệp</p>
                                    </div>
                                </div>
                                <button onClick={closeUploadPanel} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Body */}
                            <div className="flex-1 overflow-y-auto p-6 space-y-5">
                                {uploadSuccess ? (
                                    <div className="py-8 text-center">
                                        <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-500/20 flex items-center justify-center mx-auto mb-4">
                                            <CheckCircle2 className="w-8 h-8 text-green-600" />
                                        </div>
                                        <p className="text-lg font-semibold text-gray-900 dark:text-white">Tải lên thành công!</p>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Tài liệu của bạn đã được tải lên thành công.</p>
                                    </div>
                                ) : (
                                    <>
                                        {/* Drop Zone */}
                                        <div
                                            onDragEnter={handleDrag}
                                            onDragLeave={handleDrag}
                                            onDragOver={handleDrag}
                                            onDrop={handleDrop}
                                            onClick={() => document.getElementById('file-input-upload')?.click()}
                                            className={`relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 ${
                                                dragActive
                                                    ? 'border-primary-600 bg-primary-600/5'
                                                    : 'border-gray-200 dark:border-gray-700 hover:border-primary-600/50'
                                            }`}
                                        >
                                            <div className="w-12 h-12 rounded-2xl bg-primary-600/10 flex items-center justify-center mx-auto mb-3">
                                                <Upload className={`w-6 h-6 transition-colors ${dragActive ? 'text-primary-600' : 'text-gray-400'}`} />
                                            </div>
                                            <p className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                                {dragActive ? 'Thả tệp vào đây' : 'Kéo thả tệp hoặc nhấp để chọn'}
                                            </p>
                                            <p className="text-xs text-gray-400">PDF, DOCX, XLSX, PPTX, PNG, JPG, MD, ZIP — Tối đa 50MB</p>
                                            <input
                                                id="file-input-upload"
                                                type="file"
                                                multiple
                                                className="hidden"
                                                onChange={handleFileInput}
                                            />
                                        </div>

                                        {/* Staged Files */}
                                        {stagedFiles.length > 0 && (
                                            <div>
                                                <div className="flex items-center justify-between mb-3">
                                                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                                                        Tệp đã chọn <span className="text-xs font-normal text-gray-400">({stagedFiles.length} • {formatBytes(totalStagedSize)})</span>
                                                    </h4>
                                                    <button onClick={() => setStagedFiles([])} className="text-xs text-red-500 hover:text-red-600 font-medium">Xóa tất cả</button>
                                                </div>
                                                <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                                                    {stagedFiles.map((file, index) => {
                                                        const ext = getExt(file.name);
                                                        const Icon = fileTypeIconMap[ext] || File;
                                                        return (
                                                            <div key={`${file.name}-${index}`} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-800 group">
                                                                <div className={`w-10 h-10 rounded-xl ${fileTypeBgColors[ext] || 'bg-gray-100'} flex items-center justify-center flex-shrink-0`}>
                                                                    <Icon className={`w-5 h-5 ${fileTypeColors[ext] || 'text-gray-500'}`} />
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{file.name}</p>
                                                                    <p className="text-xs text-gray-400">{formatBytes(file.size)} • {ext}</p>
                                                                </div>
                                                                <button onClick={(e) => { e.stopPropagation(); removeStagedFile(index); }} className="p-1.5 rounded-lg text-gray-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors">
                                                                    <X className="w-4 h-4" />
                                                                </button>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        )}

                                        {/* Upload Error */}
                                        {uploadError && (
                                            <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30">
                                                <XCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                                                <p className="text-xs text-red-700 dark:text-red-400">{uploadError}</p>
                                            </div>
                                        )}

                                        {/* Document Info */}
                                        <div className="border-t border-gray-100 dark:border-gray-800 pt-5">
                                            <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Thông tin tài liệu</h4>
                                            <div className="space-y-4">
                                                {/* Category */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Danh mục</label>
                                                    <div className="relative">
                                                        <select
                                                            value={uploadCategory}
                                                            onChange={(e) => setUploadCategory(e.target.value)}
                                                            className="w-full px-3 py-2.5 text-sm rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-primary-500/30 cursor-pointer appearance-none"
                                                        >
                                                            {categories.filter(c => c !== 'All').map(cat => (
                                                                <option key={cat} value={cat}>{cat}</option>
                                                            ))}
                                                        </select>
                                                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                                                    </div>
                                                </div>

                                                {/* Visibility */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Chế độ hiển thị</label>
                                                    <div className="flex gap-2">
                                                        <button
                                                            type="button"
                                                            onClick={() => setUploadVisibility('internal')}
                                                            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border-2 text-sm font-medium transition-all ${
                                                                uploadVisibility === 'internal'
                                                                    ? 'border-primary-600 bg-primary-600/5 text-primary-700 dark:text-primary-400 dark:border-primary-500 dark:bg-primary-500/10'
                                                                    : 'border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                                                            }`}
                                                        >
                                                            <Lock className="w-4 h-4" />
                                                            Nội bộ
                                                        </button>
                                                        <button
                                                            type="button"
                                                            onClick={() => setUploadVisibility('public')}
                                                            className={`flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl border-2 text-sm font-medium transition-all ${
                                                                uploadVisibility === 'public'
                                                                    ? 'border-emerald-600 bg-emerald-600/5 text-emerald-700 dark:text-emerald-400 dark:border-emerald-500 dark:bg-emerald-500/10'
                                                                    : 'border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600'
                                                            }`}
                                                        >
                                                            <Globe className="w-4 h-4" />
                                                            Công khai
                                                        </button>
                                                    </div>
                                                    <p className="text-xs text-gray-400 mt-1.5">
                                                        {uploadVisibility === 'internal'
                                                            ? 'Chỉ thành viên trong phòng ban mới xem được'
                                                            : 'Tất cả tài khoản đều có thể xem'}
                                                    </p>
                                                </div>

                                                {/* Tags */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Thẻ</label>
                                                    <div className="flex flex-wrap items-center gap-1.5 p-2.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 min-h-[42px]">
                                                        {uploadTags.map((tag) => (
                                                            <span key={tag} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700 dark:bg-primary-500/20 dark:text-primary-400">
                                                                {tag}
                                                                <button type="button" onClick={() => setUploadTags(uploadTags.filter(t => t !== tag))} className="hover:text-red-500 transition-colors">
                                                                    <X className="w-3 h-3" />
                                                                </button>
                                                            </span>
                                                        ))}
                                                        <input
                                                            type="text"
                                                            value={uploadTagInput}
                                                            onChange={(e) => setUploadTagInput(e.target.value)}
                                                            onKeyDown={(e) => {
                                                                if (e.key === 'Enter' || e.key === ',') {
                                                                    e.preventDefault();
                                                                    const t = uploadTagInput.replace(/,+$/, '').trim();
                                                                    if (t && !uploadTags.includes(t)) setUploadTags([...uploadTags, t]);
                                                                    setUploadTagInput('');
                                                                }
                                                            }}
                                                            placeholder={uploadTags.length === 0 ? 'Nhấn Enter hoặc , để thêm thẻ...' : ''}
                                                            className="flex-1 min-w-[120px] bg-transparent outline-none text-sm text-gray-900 dark:text-white placeholder-gray-400"
                                                        />
                                                    </div>
                                                </div>

                                                {/* Thumbnail */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Ảnh bìa</label>
                                                    <div className="flex items-center gap-4">
                                                        {uploadThumbnail ? (
                                                            <div className="relative">
                                                                <img src={URL.createObjectURL(uploadThumbnail)} alt="Thumbnail" className="w-16 h-16 rounded-lg object-cover border border-gray-200 dark:border-gray-700" />
                                                                <button
                                                                    onClick={() => setUploadThumbnail(null)}
                                                                    className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600"
                                                                >
                                                                    <X className="w-3 h-3" />
                                                                </button>
                                                            </div>
                                                        ) : (
                                                            <label className="w-16 h-16 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600 flex flex-col items-center justify-center cursor-pointer hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-500/10 transition-colors">
                                                                <Image className="w-5 h-5 text-gray-400" />
                                                                <input type="file" accept="image/*" onChange={handleThumbnailSelect} className="hidden" />
                                                            </label>
                                                        )}
                                                        <span className="text-xs text-gray-400">Chọn ảnh bìa cho tài liệu này</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>

                            {/* Footer */}
                            {!uploadSuccess && (
                                <div className="px-6 py-4 flex items-center justify-end gap-3 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
                                    <button onClick={closeUploadPanel} className="px-5 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                                        Hủy
                                    </button>
                                    <button
                                        onClick={handleUpload}
                                        disabled={!stagedFiles.length || uploading}
                                        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                    >
                                        {uploading ? (
                                            <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Đang tải...</>
                                        ) : (
                                            <><Upload className="w-4 h-4" />Tải lên {stagedFiles.length > 0 ? `${stagedFiles.length} tệp` : ''}</>
                                        )}
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* ─── Table View ─── */}
                {view === 'table' && (
                    <div className="overflow-x-auto relative">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/30">
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Tên</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden sm:table-cell">Danh mục</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Ngày sửa</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden md:table-cell">Kích thước</th>
                                    <th className="px-6 py-4 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider hidden lg:table-cell">Người sở hữu</th>
                                    <th className="px-6 py-4 text-right text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
                                {pageDocs.length === 0 && (
                                    <tr>
                                        <td colSpan={6}>
                                            <div className="px-6 py-14 text-center">
                                                <Search className="w-12 h-12 text-gray-200 dark:text-gray-700 mx-auto mb-3" />
                                                <p className="text-gray-500 dark:text-gray-400 font-medium">Không tìm thấy tài liệu</p>
                                                <p className="text-sm text-gray-400 dark:text-gray-500">Hãy điều chỉnh tìm kiếm hoặc bộ lọc</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                                {pageDocs.map((doc) => (
                                    <DocumentRow
                                        key={doc.id}
                                        doc={doc}
                                        openMenu={openMenu}
                                        onToggleMenu={(id) => setOpenMenu(openMenu === id ? null : id)}
                                        onView={(d) => navigate(`/documents/${d.id}`)}
                                        onDownload={handleDownload}
                                        onDelete={(id) => setDeleteTarget(id)}
                                        tableRowClassName="px-6 py-4"
                                    />
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* ─── Grid View ─── */}
                {view === 'grid' && (
                    <div className="p-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                        {pageDocs.length === 0 && (
                            <div className="col-span-full py-14 text-center">
                                <Search className="w-12 h-12 text-gray-200 dark:text-gray-700 mx-auto mb-3" />
                                <p className="text-gray-500 font-medium">Không tìm thấy tài liệu</p>
                            </div>
                        )}
                        {pageDocs.map((doc) => (
                            <DocumentCard
                                key={doc.id}
                                doc={doc}
                                onView={(d) => navigate(`/documents/${d.id}`)}
                                onDownload={handleDownload}
                                onDelete={(id) => setDeleteTarget(id)}
                            />
                        ))}
                    </div>
                )}

                {/* ─── Pagination ─── */}
                {filteredDocs.length > 0 && (
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 px-6 py-4 border-t border-gray-100 dark:border-gray-800">
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            Hiển thị {Math.min((currentPage - 1) * ROWS_PER_PAGE + 1, filteredDocs.length)} đến{' '}
                            {Math.min(currentPage * ROWS_PER_PAGE, filteredDocs.length)} trong số {filteredDocs.length} tài liệu
                        </p>
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="p-2 rounded border border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                                <ChevronLeft className="w-4 h-4" />
                            </button>
                            {Array.from({ length: totalPages }, (_, i) => i + 1)
                                .filter(p => p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1)
                                .reduce((acc, p, idx, arr) => {
                                    if (idx > 0 && p - arr[idx - 1] > 1) acc.push('...');
                                    acc.push(p);
                                    return acc;
                                }, [])
                                .map((p, i) =>
                                    p === '...' ? (
                                        <span key={`dots-${i}`} className="px-2 text-gray-400 text-sm">…</span>
                                    ) : (
                                        <button
                                            key={p}
                                            onClick={() => setCurrentPage(p)}
                                            className={`w-8 h-8 rounded text-sm font-medium transition-colors ${currentPage === p
                                                ? 'bg-primary-600 text-white'
                                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700'
                                                }`}
                                        >
                                            {p}
                                        </button>
                                    )
                                )
                            }
                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="p-2 rounded border border-gray-200 dark:border-gray-700 text-gray-500 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                            >
                                <ChevronRight className="w-4 h-4" />
                            </button>
                            <span className="ml-2 text-sm text-gray-400 hidden sm:inline">
                                Trang {currentPage} / {totalPages}
                            </span>
                        </div>
                    </div>
                )}
            </div>

            {/* ─── Delete Modal ─── */}
            {deleteTarget && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => setDeleteTarget(null)} />
                    <div className="relative bg-white dark:bg-gray-900 rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl border border-gray-200 dark:border-gray-800 animate-fade-in">
                        <div className="w-10 h-10 rounded-md bg-red-100 dark:bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                            <Trash2 className="w-5 h-5 text-red-500" />
                        </div>
                        <h3 className="text-base font-bold text-gray-900 dark:text-white text-center mb-2">Xóa tài liệu</h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-5">Bạn có chắc chắn muốn xóa tài liệu này không? Hành động này không thể hoàn tác.</p>
                        <div className="flex gap-3">
                            <button onClick={() => setDeleteTarget(null)} className="flex-1 px-4 py-2 rounded-md border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">Hủy</button>
                            <button onClick={() => handleDelete(deleteTarget)} className="flex-1 px-4 py-2 rounded-md bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors">Xóa</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
