import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../../context/ThemeContext';
import { FileText, Sun, Moon, Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function Navbar() {
    const { isDark, toggleTheme } = useTheme();
    const location = useLocation();
    const [mobileOpen, setMobileOpen] = useState(false);

    const links = [
        { label: 'Tính năng', href: '#features' },
        { label: 'Cách hoạt động', href: '#how-it-works' },
        { label: 'Khách hàng nói gì', href: '#testimonials' },
        { label: 'Liên hệ', href: '#footer' },
    ];

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-lg border-b border-gray-200/50 dark:border-gray-800/50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-4">
                        <div className="w-16 h-16 bg-white rounded-xl flex items-center justify-center p-2 shadow-sm border border-gray-100 dark:border-gray-800">
                            <img src="/logo-tkv.png" alt="TKV Logo" className="w-full h-full object-contain" />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-2xl font-extrabold text-gray-900 dark:text-white leading-tight">
                                TKV
                            </span>
                            <span className="text-sm font-bold text-primary-600 dark:text-primary-400">
                                nền tảng tri thức
                            </span>
                        </div>
                    </Link>

                    {/* Desktop Nav Links */}
                    <div className="hidden md:flex items-center gap-8">
                        {links.map((link) => (
                            <a
                                key={link.label}
                                href={link.href}
                                className="text-sm font-medium text-gray-600 hover:text-primary-600 dark:text-gray-400 dark:hover:text-secondary-400 transition-colors"
                            >
                                {link.label}
                            </a>
                        ))}
                    </div>

                    {/* Desktop Actions */}
                    <div className="hidden md:flex items-center gap-3">
                        <button
                            onClick={toggleTheme}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400 transition-colors"
                            aria-label="Chuyển chế độ tối"
                        >
                            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                        </button>
                        <Link
                            to="/dashboard"
                            className="btn-primary text-sm !px-5 !py-2.5"
                        >
                            Vào Dashboard
                        </Link>
                    </div>

                    {/* Mobile Menu Button */}
                    <button
                        onClick={() => setMobileOpen(!mobileOpen)}
                        className="md:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
                    >
                        {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                    </button>
                </div>
            </div>

            {/* Mobile Menu */}
            {mobileOpen && (
                <div className="md:hidden bg-white dark:bg-gray-950 border-t border-gray-200 dark:border-gray-800 animate-fade-in">
                    <div className="px-4 py-4 space-y-3">
                        {links.map((link) => (
                            <a
                                key={link.label}
                                href={link.href}
                                onClick={() => setMobileOpen(false)}
                                className="block py-2 text-gray-600 dark:text-gray-400 hover:text-primary-600 font-medium"
                            >
                                {link.label}
                            </a>
                        ))}
                        <div className="pt-3 border-t border-gray-200 dark:border-gray-800 flex gap-3">
                            <Link to="/login" className="btn-secondary text-sm flex-1 text-center" onClick={() => setMobileOpen(false)}>
    Đăng nhập
                            </Link>
                            <Link to="/register" className="btn-primary text-sm flex-1 text-center" onClick={() => setMobileOpen(false)}>
    Bắt đầu ngay
                            </Link>
                        </div>
                    </div>
                </div>
            )}
        </nav>
    );
}
