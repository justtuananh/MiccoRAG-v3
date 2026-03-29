import { useState, useEffect, useRef } from 'react';
import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { ragChatApi } from '../utils/api';
import Logo from '../assets/logo.png';
import {
    LayoutDashboard, FolderOpen, Upload, MessageSquare, BookOpen, Building2,
    X, Sun, Moon, Bell,
    Search, LogOut, ChevronDown, FileText, User, Key,
    ChevronLeft, ChevronRight, ShieldCheck, ClipboardCheck, GitBranch,
    Activity, Users
} from 'lucide-react';

const sidebarItems = [
    { label: 'Tổng quan', path: '/dashboard', icon: LayoutDashboard, desc: 'Thống kê & tổng hợp' },
    { label: 'Tài liệu', path: '/documents', icon: FolderOpen, desc: 'Tất cả tệp của bạn' },
    { label: 'Tiến trình', path: '/processing-status', icon: Activity, desc: 'Theo dõi xử lý tài liệu' },
    { label: 'Trợ lý AI', path: '/chat', icon: MessageSquare, desc: 'Trò chuyện với tài liệu' },
    { label: 'Chuyên gia', path: '/expert', icon: Users, desc: 'Tìm & kết nối chuyên gia' },
    { label: 'Tri thức', path: '/knowledge', icon: BookOpen, desc: 'Quản lý bài viết tri thức' },
    { label: 'Đồ thị tri thức', path: '/graph-knowledge', icon: GitBranch, desc: 'Sơ đồ tri thức dạng graph' },
];

export default function DashboardLayout() {
    const { isDark, toggleTheme } = useTheme();
    const { user, logout, authFetch } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [mobileOpen, setMobileOpen] = useState(false);
    const [pendingCount, setPendingCount] = useState(0);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [profileModalOpen, setProfileModalOpen] = useState(false);
    const [profileUpdating, setProfileUpdating] = useState(false);
    const [profileError, setProfileError] = useState('');
    const [profileSuccess, setProfileSuccess] = useState(false);
    const [profileData, setProfileData] = useState({ name: '', password: '' });
    const [lastRequester, setLastRequester] = useState(null);
    const [showApprovalToast, setShowApprovalToast] = useState(false);
    const isFirstLoad = useRef(true);

    useEffect(() => {
        if (user?.role !== 'Admin' && user?.role !== 'Trưởng phòng') return;
        
        const fetchCount = () => {
            authFetch('/api/approvals/count')
                .then(r => r.ok ? r.json() : null)
                .then(data => {
                    if (data && typeof data.count === 'number') {
                        if (!isFirstLoad.current && data.count > pendingCount) {
                            setLastRequester(data.last_requester);
                            setShowApprovalToast(true);
                            setTimeout(() => setShowApprovalToast(false), 5000);
                        }
                        setPendingCount(data.count);
                        isFirstLoad.current = false;
                    }
                })
                .catch(() => { });
        };

        fetchCount();
        const interval = setInterval(fetchCount, 30000); // 30s polling
        return () => clearInterval(interval);
    }, [user?.role, authFetch]);

    // Close user menu on outside click
    useEffect(() => {
        if (!userMenuOpen) return;
        const handler = () => setUserMenuOpen(false);
        document.addEventListener('click', handler);
        return () => document.removeEventListener('click', handler);
    }, [userMenuOpen]);

    const handleLogout = async () => {
        // Clear all per-user chat history before logging out
        try {
            await ragChatApi.clearAllHistory();
        } catch (_) {
            // Best-effort — do not block logout even if the call fails
        }
        logout();
        navigate('/', { replace: true });
    };

    const handleProfileUpdate = async (e) => {
        e.preventDefault();
        setProfileUpdating(true);
        setProfileError('');
        setProfileSuccess(false);
        try {
            const body = {};
            if (profileData.name.trim()) body.name = profileData.name.trim();
            if (profileData.password.trim()) body.password = profileData.password.trim();

            if (Object.keys(body).length === 0) {
                setProfileError('Vui lòng nhập thông tin cần thay đổi');
                return;
            }

            const res = await authFetch('/api/auth/me', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (res.ok) {
                setProfileSuccess(true);
                setProfileData({ name: '', password: '' });
                // Re-fetch user in AuthContext or just wait for page reload later
                // Actually, let's just show success and close
                setTimeout(() => {
                    setProfileModalOpen(false);
                    setProfileSuccess(false);
                    window.location.reload(); // Quickest way to refresh across all components
                }, 1500);
            } else {
                const err = await res.json();
                setProfileError(err.detail || 'Cập nhật thất bại');
            }
        } catch (err) {
            setProfileError('Đã có lỗi xảy ra');
        } finally {
            setProfileUpdating(false);
        }
    };

    const SidebarContent = ({ showCloseButton = false }) => (
        <div className="flex flex-col h-full relative">
            {/* Logo & Brand & Toggle */}
            <div className={`px-4 py-4 flex items-center justify-between border-b border-gray-100 dark:border-gray-800 mb-2`}>
                <Link to="/dashboard" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                    <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center p-1.5 shadow-sm border border-gray-100 dark:border-gray-800">
                        <img src="/logo-tkv.png" alt="TKV" className="w-full h-full object-contain" />
                    </div>
                    {sidebarOpen && (
                        <div className="flex flex-col">
                            <span className="text-lg font-extrabold text-gray-900 dark:text-white leading-tight">
                                TKV
                            </span>
                            <span className="text-[11px] font-bold text-primary-600 dark:text-primary-400">
                                nền tảng tri thức
                            </span>
                        </div>
                    )}
                </Link>
                
                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="p-1 px-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 dark:text-gray-500 transition-colors"
                >
                    {sidebarOpen ? <ChevronLeft className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                </button>
            </div>

            {/* Nav Items */}
            <nav className="flex-1 px-3 py-2 space-y-0.5">
                {sidebarItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = location.pathname === item.path;
                    return (
                        <Link
                            key={item.label}
                            to={item.path}
                            onClick={() => setMobileOpen(false)}
                            className={`
                                flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200
                                ${sidebarOpen ? 'justify-start' : 'justify-center'}
                                ${isActive
                                    ? 'bg-primary-600 text-white shadow-sm'
                                    : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                                }
                            `}
                        >
                            <Icon className="w-4.5 h-4.5 flex-shrink-0" />
                            {sidebarOpen && (
                                <span className="text-xs font-bold leading-tight">{item.label}</span>
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Approvals Link — visible to Admin & Trưởng phòng */}
            {(user?.role === 'Admin' || user?.role === 'Trưởng phòng') && (
                <div className="px-3 pb-1">
                    <Link
                        to="/approvals"
                        onClick={() => setMobileOpen(false)}
                        className={`
                            flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200
                            ${sidebarOpen ? 'justify-start' : 'justify-center'}
                            ${location.pathname === '/approvals'
                                ? 'bg-primary-600 text-white shadow-sm'
                                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }
                        `}
                    >
                        <ClipboardCheck className="w-4.5 h-4.5 flex-shrink-0" />
                        {sidebarOpen && (
                            <span className="text-xs font-bold flex-1">Phê duyệt</span>
                        )}
                        {pendingCount > 0 && (
                            <span className="ml-auto min-w-[1rem] h-4 px-1 rounded-full bg-amber-500 text-white text-[10px] font-bold flex items-center justify-center">
                                {pendingCount}
                            </span>
                        )}
                    </Link>
                </div>
            )}

            {/* Admin Links */}
            {user?.role === 'Admin' && (
                <div className="px-3 pb-4 space-y-0.5 border-t border-gray-100 dark:border-gray-800 pt-4 mt-2">
                    <Link
                        to="/admin"
                        onClick={() => setMobileOpen(false)}
                        className={`
                            flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200
                            ${sidebarOpen ? 'justify-start' : 'justify-center'}
                            ${location.pathname === '/admin'
                                ? 'bg-primary-600 text-white shadow-sm'
                                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                            }
                        `}
                    >
                        <ShieldCheck className="w-4.5 h-4.5 flex-shrink-0" />
                        {sidebarOpen && <span className="text-xs font-bold">Quản trị</span>}
                    </Link>
                </div>
            )}
        </div>
    );

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-gray-950 flex">
            {/* Desktop Sidebar */}
            <aside
                className={`
                    hidden lg:flex flex-col fixed top-0 left-0 h-screen 
                    bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 
                    z-30 transition-all duration-300 ease-in-out
                    ${sidebarOpen ? 'w-52' : 'w-16'}
                `}
            >
                <SidebarContent />
            </aside>

            {/* Mobile Sidebar Overlay */}
            {mobileOpen && (
                <div className="lg:hidden fixed inset-0 z-40">
                    <div
                        className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
                        onClick={() => setMobileOpen(false)}
                    />
                    <aside className="relative w-64 h-full bg-white dark:bg-gray-900 shadow-2xl animate-slide-in">
                        <SidebarContent showCloseButton={true} />
                    </aside>
                </div>
            )}

            {/* Main Content */}
            <div className={`flex-1 flex flex-col h-screen transition-all duration-300 ${sidebarOpen ? 'lg:ml-52' : 'lg:ml-16'}`}>
                {/* Top Bar */}
                <header className="flex-shrink-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-800 relative z-50">
                    <div className="flex items-center justify-between px-4 lg:px-6 h-12">
                        <div className="flex items-center gap-4 flex-1">
                            {/* Deleted top search bar per user request */}
                        </div>

                        <div className="flex items-center gap-3">
                            <button
                                onClick={toggleTheme}
                                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 transition-colors"
                                aria-label="Toggle dark mode"
                            >
                                {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                            </button>

                            <Link 
                                to={(user?.role === 'Admin' || user?.role === 'Trưởng phòng') ? "/approvals" : "/dashboard"}
                                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 transition-colors relative"
                            >
                                <Bell className="w-5 h-5" />
                                {pendingCount > 0 && (
                                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                                )}
                            </Link>

                            {/* User Menu với Dropdown */}
                            <div className="relative" onClick={e => e.stopPropagation()}>
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setUserMenuOpen(!userMenuOpen);
                                    }}
                                    className="flex items-center gap-2 p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer relative z-50 pointer-events-auto"
                                >
                                    <div className="w-7 h-7 rounded-full bg-primary-600 flex items-center justify-center text-white text-[10px] font-bold">
                                        {user?.name?.split(' ').map(n => n[0]).join('') || 'AJ'}
                                    </div>
                                    <ChevronDown className="w-4 h-4 text-gray-400" />
                                </button>

                                {/* Dropdown Menu */}
                                {userMenuOpen && (
                                    <div
                                        className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-100 dark:border-gray-800 py-1 z-[100] pointer-events-auto"
                                        onClick={e => e.stopPropagation()}
                                    >
                                        <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-800">
                                            <p className="text-sm font-semibold text-gray-900 dark:text-white uppercase tracking-tight">{user?.name || 'Admin'}</p>
                                            <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">{user?.email || 'admin@micco.vn'}</p>
                                        </div>
                                        <button
                                            onClick={() => {
                                                setUserMenuOpen(false);
                                                setProfileData({ name: user?.name || '', password: '' });
                                                setProfileModalOpen(true);
                                            }}
                                            className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors"
                                        >
                                            <User className="w-4 h-4" />
                                            Thông tin cá nhân
                                        </button>
                                        <button
                                            onClick={handleLogout}
                                            className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/40 transition-all font-bold cursor-pointer"
                                        >
                                            <LogOut className="w-4 h-4" />
                                            Đăng xuất
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto relative">
                    <Outlet />
                    
                    {/* Floating Toast for New Approvals */}
                    {showApprovalToast && (
                        <div className="fixed bottom-6 right-6 z-[100] animate-slide-in-up">
                            <Link 
                                to="/approvals"
                                onClick={() => setShowApprovalToast(false)}
                                className="flex items-center gap-3 px-4 py-3 bg-amber-500 text-white rounded-xl shadow-2xl hover:bg-amber-600 transition-all border-2 border-white/20"
                            >
                                <Bell className="w-5 h-5 animate-bounce" />
                                <div>
                                    <p className="text-sm font-bold">Yêu cầu phê duyệt mới!</p>
                                    <p className="text-[10px] opacity-90">
                                        {lastRequester ? `Tài khoản ${lastRequester} vừa gửi yêu cầu.` : 'Có nội dung mới đang chờ bạn xem xét.'}
                                    </p>
                                </div>
                                <X className="w-4 h-4 ml-2" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShowApprovalToast(false); }} />
                            </Link>
                        </div>
                    )}
                </main>
            </div>

            {/* Profile Modal */}
            {profileModalOpen && (
                <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => !profileUpdating && setProfileModalOpen(false)} />
                    <div className="relative w-full max-w-md bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-100 dark:border-gray-800 overflow-hidden animate-fade-in">
                        <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between bg-gray-50/50 dark:bg-gray-800/50">
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white">Cập nhật thông tin</h3>
                            <button onClick={() => setProfileModalOpen(false)} className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 transition-colors">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <form onSubmit={handleProfileUpdate} className="p-6 space-y-4">
                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-500 uppercase tracking-widest">Họ và tên</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                    <input
                                        type="text"
                                        value={profileData.name}
                                        onChange={e => setProfileData(prev => ({ ...prev, name: e.target.value }))}
                                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none transition-all dark:text-white"
                                        placeholder="Tên của bạn"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-xs font-bold text-gray-500 uppercase tracking-widest">Mật khẩu mới (để trống nếu không đổi)</label>
                                <div className="relative">
                                    <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                    <input
                                        type="password"
                                        value={profileData.password}
                                        onChange={e => setProfileData(prev => ({ ...prev, password: e.target.value }))}
                                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 outline-none transition-all dark:text-white"
                                        placeholder="••••••••"
                                    />
                                </div>
                            </div>

                            {profileError && (
                                <div className="p-3 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 rounded-xl flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
                                    <X className="w-4 h-4" />
                                    {profileError}
                                </div>
                            )}

                            {profileSuccess && (
                                <div className="p-3 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20 rounded-xl flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 font-bold">
                                    <ShieldCheck className="w-4 h-4" />
                                    Cập nhật thành công! Trình duyệt sẽ tải lại...
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={profileUpdating}
                                className="w-full py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-xl font-bold shadow-lg shadow-primary-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                {profileUpdating ? 'Đang cập nhật...' : 'Lưu thay đổi'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
