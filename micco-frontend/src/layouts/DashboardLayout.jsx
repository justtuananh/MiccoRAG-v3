import { useState, useEffect } from 'react';
import { Link, useLocation, Outlet, useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import Logo from '../assets/logo.png';
import {
    LayoutDashboard, FolderOpen, Upload, MessageSquare, BookOpen, Building2,
    X, Sun, Moon, Bell,
    Search, LogOut, ChevronDown, FileText,
    ChevronLeft, ChevronRight, ShieldCheck, ClipboardCheck
} from 'lucide-react';

const sidebarItems = [
    { label: 'Tổng quan', path: '/dashboard', icon: LayoutDashboard, desc: 'Thống kê & tổng hợp' },
    { label: 'Tài liệu', path: '/documents', icon: FolderOpen, desc: 'Tất cả tệp của bạn' },
    { label: 'Trợ lý AI', path: '/chat', icon: MessageSquare, desc: 'Trò chuyện với tài liệu' },
    { label: 'Tri thức', path: '/knowledge', icon: BookOpen, desc: 'Sơ đồ tri thức' },
];

export default function DashboardLayout() {
    const { isDark, toggleTheme } = useTheme();
    const { user, logout, authFetch } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [mobileOpen, setMobileOpen] = useState(false);
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [pendingCount, setPendingCount] = useState(0);

    useEffect(() => {
        if (user?.role !== 'Admin' && user?.role !== 'Trưởng phòng') return;
        authFetch('/api/approvals/count')
            .then(r => r.ok ? r.json() : null)
            .then(data => data && setPendingCount(data.count || 0))
            .catch(() => { });
    }, [user?.role]);

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const SidebarContent = ({ showCloseButton = false }) => (
        <div className="flex flex-col h-full relative">
            {/* Logo & Brand & Toggle */}
            <div className={`px-4 py-4 flex items-center justify-between border-b border-gray-100 dark:border-gray-800 mb-2`}>
                <Link to="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-primary-600 shadow-sm">
                        <img src={Logo} alt="Micco" className="w-6 h-6" />
                    </div>
                    {sidebarOpen && (
                        <span className="text-sm font-bold text-gray-900 dark:text-white">
                            Micco
                        </span>
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
                <header className="flex-shrink-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-800">
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

                            <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 transition-colors relative">
                                <Bell className="w-5 h-5" />
                                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
                            </button>

                            <div className="relative">
                                <button
                                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                                    className="flex items-center gap-2 p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                                >
                                    <div className="w-7 h-7 rounded-full bg-primary-600 flex items-center justify-center text-white text-[10px] font-bold">
                                        {user?.name?.split(' ').map(n => n[0]).join('') || 'AJ'}
                                    </div>
                                    <ChevronDown className="w-4 h-4 text-gray-400 hidden sm:block" />
                                </button>

                                {userMenuOpen && (
                                    <div className="absolute right-0 top-12 w-44 bg-white dark:bg-gray-900 rounded-md shadow-lg border border-gray-200 dark:border-gray-800 py-1 animate-fade-in">
                                        <button
                                            onClick={handleLogout}
                                            className="flex items-center gap-2 w-full px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
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
                </main>
            </div>
        </div>
    );
}
