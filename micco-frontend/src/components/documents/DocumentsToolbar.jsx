import { Search, LayoutGrid, List, Plus, SlidersHorizontal, ArrowUpDown } from 'lucide-react';

export default function DocumentsToolbar({ search, onSearchChange, view, onViewChange, onUploadClick }) {
    return (
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-800">
            <h2 className="text-base font-bold text-gray-900 dark:text-white">Tất cả tài liệu</h2>
            <div className="flex items-center gap-2">
                {/* Search */}
                <div className="relative hidden sm:flex items-center">
                    <Search className="absolute left-3 w-4 h-4 text-gray-400 pointer-events-none" />
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => onSearchChange(e.target.value)}
                        placeholder="Tìm kiếm..."
                        className="pl-9 pr-4 py-2 text-sm rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 outline-none focus:border-primary-600 dark:focus:border-primary-500 w-52 transition-all"
                    />
                </div>
                {/* View toggle */}
                <div className="flex items-center border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
                    <button onClick={() => onViewChange('table')} className={`p-2 transition-colors ${view === 'table' ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 bg-white dark:bg-gray-900'}`}>
                        <List className="w-4 h-4" />
                    </button>
                    <button onClick={() => onViewChange('grid')} className={`p-2 transition-colors ${view === 'grid' ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 bg-white dark:bg-gray-900'}`}>
                        <LayoutGrid className="w-4 h-4" />
                    </button>
                </div>
                {/* Sort/filter icons */}
                <button className="p-2 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 bg-white dark:bg-gray-900 transition-colors">
                    <SlidersHorizontal className="w-4 h-4" />
                </button>
                <button className="p-2 rounded-xl border border-gray-200 dark:border-gray-700 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 bg-white dark:bg-gray-900 transition-colors">
                    <ArrowUpDown className="w-4 h-4" />
                </button>
                {/* Upload */}
                <button onClick={onUploadClick} className="btn-primary flex items-center gap-2 !py-2 !px-4 text-sm">
                    <Plus className="w-4 h-4" />
                    <span className="hidden sm:inline">Tải lên</span>
                </button>
            </div>
        </div>
    );
}
