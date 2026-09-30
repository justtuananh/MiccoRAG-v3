import { Search, LayoutGrid, List, Plus, SlidersHorizontal, ArrowUpDown } from 'lucide-react';

export default function DocumentsToolbar({
    search, onSearchChange, view, onViewChange, onUploadClick,
    filtersOpen, onToggleFilters, typeFilter, onTypeFilterChange,
    categoryFilter, onCategoryFilterChange, tagFilter, onTagFilterChange,
    statusFilter, onStatusFilterChange, sortOrder, onSortOrderChange,
    categories,
}) {
    return (
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 sm:px-6 py-4 border-b border-gray-100 dark:border-gray-800">
            <h2 className="text-base font-bold text-gray-900 dark:text-white">Tất cả tài liệu</h2>
            <div className="flex w-full sm:w-auto flex-wrap items-center gap-2">
                {/* Search */}
                <div className="relative flex w-full sm:w-auto items-center order-last sm:order-none">
                    <Search className="absolute left-3 w-4 h-4 text-gray-400 pointer-events-none" />
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => onSearchChange(e.target.value)}
                        placeholder="Tìm kiếm..."
                        aria-label="Tìm kiếm tài liệu"
                        className="pl-9 pr-4 py-2 text-sm rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 outline-none focus:border-primary-600 dark:focus:border-primary-500 w-full sm:w-52 transition-all"
                    />
                </div>
                {/* View toggle */}
                <div className="flex items-center border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
                    <button aria-label="Dạng bảng" title="Dạng bảng" onClick={() => onViewChange('table')} className={`p-2 transition-colors ${view === 'table' ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 bg-white dark:bg-gray-900'}`}>
                        <List className="w-4 h-4" />
                    </button>
                    <button aria-label="Dạng lưới" title="Dạng lưới" onClick={() => onViewChange('grid')} className={`p-2 transition-colors ${view === 'grid' ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 bg-white dark:bg-gray-900'}`}>
                        <LayoutGrid className="w-4 h-4" />
                    </button>
                </div>
                {/* Sort/filter icons */}
                <button aria-label="Bộ lọc" aria-expanded={filtersOpen} title="Bộ lọc" onClick={onToggleFilters} className="p-2 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 bg-white dark:bg-gray-900 transition-colors">
                    <SlidersHorizontal className="w-4 h-4" />
                </button>
                <button aria-label="Sắp xếp" title="Sắp xếp" onClick={() => onSortOrderChange(sortOrder === 'newest' ? 'name' : 'newest')} className="p-2 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 bg-white dark:bg-gray-900 transition-colors">
                    <ArrowUpDown className="w-4 h-4" />
                </button>
                {/* Upload */}
                <button aria-label="Tải lên tài liệu" onClick={onUploadClick} className="btn-primary flex items-center gap-2 !py-2 !px-4 text-sm">
                    <Plus className="w-4 h-4" />
                    <span className="hidden sm:inline">Tải lên</span>
                </button>
            </div>
            {filtersOpen && (
                <div className="grid w-full grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 border-t border-gray-100 dark:border-gray-800 pt-4">
                    <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Loại tệp
                        <select aria-label="Lọc theo loại tệp" value={typeFilter} onChange={event => onTypeFilterChange(event.target.value)} className="mt-1 block w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm">
                            {['All', 'PDF', 'DOCX', 'XLSX', 'PPTX', 'TXT', 'MD', 'PNG', 'JPG'].map(type => <option key={type} value={type}>{type === 'All' ? 'Tất cả' : type}</option>)}
                        </select>
                    </label>
                    <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Danh mục
                        <select aria-label="Lọc theo danh mục" value={categoryFilter} onChange={event => onCategoryFilterChange(event.target.value)} className="mt-1 block w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm">
                            {categories.map(category => <option key={category} value={category}>{category === 'All' ? 'Tất cả' : category}</option>)}
                        </select>
                    </label>
                    <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Thẻ
                        <input aria-label="Lọc theo thẻ" value={tagFilter} onChange={event => onTagFilterChange(event.target.value)} placeholder="Nhập thẻ..." className="mt-1 block w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm" />
                    </label>
                    <label className="text-xs font-medium text-gray-600 dark:text-gray-300">Trạng thái
                        <select aria-label="Lọc theo trạng thái" value={statusFilter} onChange={event => onStatusFilterChange(event.target.value)} className="mt-1 block w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm">
                            <option value="All">Tất cả</option><option value="indexed">Đã lập chỉ mục</option><option value="processing">Đang xử lý</option><option value="pending">Chờ duyệt</option><option value="failed">Thất bại</option><option value="rejected">Bị từ chối</option>
                        </select>
                    </label>
                </div>
            )}
        </div>
    );
}
