import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { User, Lock, Eye, EyeOff, ArrowRight, Sun, Moon, Github, Chrome } from 'lucide-react';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const { isDark, toggleTheme } = useTheme();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setTimeout(() => {
            login(email, password);
            navigate('/dashboard');
        }, 800);
    };

    return (
        <div className="min-h-screen flex bg-[#2a5298] relative overflow-hidden">

            {/* ─── Floating Spheres (Background) ─── */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
                {/* Large sphere – bottom left */}
                <div className="absolute -bottom-20 -left-20 w-[420px] h-[420px] rounded-full animate-float"
                    style={{
                        background: 'radial-gradient(circle at 35% 35%, #5b8def 0%, #1e3a8a 60%, #0f1f4e 100%)',
                        boxShadow: '0 0 80px rgba(30, 58, 138, 0.5), inset 0 -20px 60px rgba(0,0,0,0.3)',
                    }}
                />
                {/* Medium sphere – top center-left */}
                <div className="absolute top-10 left-[22%] w-[220px] h-[220px] rounded-full animate-float-delayed"
                    style={{
                        background: 'radial-gradient(circle at 35% 35%, #6b9cf7 0%, #3060c7 50%, #1e3a8a 100%)',
                        boxShadow: '0 0 60px rgba(79, 70, 229, 0.35), inset 0 -15px 40px rgba(0,0,0,0.25)',
                    }}
                />
                {/* Small sphere – center */}
                <div className="absolute top-[45%] left-[38%] w-[110px] h-[110px] rounded-full animate-float"
                    style={{
                        animationDelay: '1s',
                        background: 'radial-gradient(circle at 30% 30%, #7dacfa 0%, #4272d1 60%, #1e3a8a 100%)',
                        boxShadow: '0 0 40px rgba(59, 130, 246, 0.3), inset 0 -10px 30px rgba(0,0,0,0.2)',
                    }}
                />
                {/* Extra sphere – top right decorative */}
                <div className="absolute -top-10 right-[35%] w-[160px] h-[160px] rounded-full opacity-60 animate-float-delayed"
                    style={{
                        animationDelay: '3s',
                        background: 'radial-gradient(circle at 35% 35%, #87b4f9 0%, #4c7bd4 60%, #2a5298 100%)',
                        boxShadow: '0 0 50px rgba(79, 70, 229, 0.2)',
                    }}
                />
                {/* Bottom-right accent sphere */}
                <div className="absolute bottom-[-60px] right-[-40px] w-[300px] h-[300px] rounded-full opacity-50"
                    style={{
                        background: 'radial-gradient(circle at 40% 40%, #5b8def 0%, #1e3a8a 70%)',
                        boxShadow: '0 0 70px rgba(30, 58, 138, 0.4)',
                    }}
                />
            </div>

            {/* ─── Left Panel (Welcome) ─── */}
            <div className="hidden lg:flex lg:w-1/2 relative z-10 flex-col justify-center px-16 xl:px-24">
                <div className="auth-panel-left">
                    <h1 className="text-5xl xl:text-6xl font-extrabold text-white italic tracking-tight mb-4"
                        style={{ textShadow: '0 4px 30px rgba(0,0,0,0.3)' }}>
                        CHÀO MỪNG LẠI BẠN
                    </h1>
                    <h2 className="text-xl xl:text-2xl font-semibold text-white/90 tracking-wide mb-6 uppercase">
                        Trung tâm tài liệu của bạn
                    </h2>
                    <p className="text-white/60 text-sm leading-relaxed max-w-md">
                        Quản lý an toàn, tìm kiếm nhanh và khai mở thông tin giá trị từ mọi tài liệu
                        với sức mạnh của trí tuệ nhân tạo. Không gian làm việc thông minh bắt đầu từ đây.
                    </p>
                </div>

                {/* Stats pills */}
                <div className="flex gap-4 mt-12 auth-panel-left" style={{ animationDelay: '0.2s' }}>
                    {[
                        { label: 'Tài liệu đã xử lý', value: '1.2M+' },
                        { label: 'Khách hàng doanh nghiệp', value: '2,000+' },
                    ].map((stat) => (
                        <div key={stat.label} className="px-5 py-3 rounded-2xl bg-white/10 backdrop-blur-md border border-white/15">
                            <p className="text-white font-bold text-lg">{stat.value}</p>
                            <p className="text-white/50 text-xs">{stat.label}</p>
                        </div>
                    ))}
                </div>
            </div>

            {/* ─── Right Panel (Form) ─── */}
            <div className="w-full lg:w-1/2 flex items-center justify-center relative z-10 px-6 py-12">
                <div className="w-full max-w-md auth-panel-right">

                    {/* Card */}
                    <div className="bg-white dark:bg-gray-900 rounded-3xl shadow-2xl shadow-black/20 p-8 sm:p-10 relative overflow-hidden">

                        {/* Card subtle top glow */}
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-1 rounded-b-full bg-gradient-to-r from-primary-600 via-secondary-500 to-accent-500" />

                        {/* Dark mode toggle */}
                        <button
                            onClick={toggleTheme}
                            className="absolute top-5 right-5 p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-all"
                        >
                            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                        </button>

                        {/* Header */}
                        <div className="mb-8">
                            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">
                                Đăng nhập
                            </h2>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">
                                Chào mừng quay lại! Vui lòng nhập thông tin để tiếp tục.
                            </p>
                        </div>

                        {/* Form */}
                        <form onSubmit={handleSubmit} className="space-y-5">
                            {/* Email / Username */}
                            <div className="relative group">
                                <div className="absolute left-4 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-focus-within:bg-primary-600/10 dark:group-focus-within:bg-primary-600/20 transition-colors">
                                    <User className="w-4 h-4 text-gray-400 group-focus-within:text-primary-600 dark:group-focus-within:text-primary-400 transition-colors" />
                                </div>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="Địa chỉ email"
                                    className="w-full pl-16 pr-5 py-4 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-600/10 dark:focus:border-secondary-400 dark:focus:ring-secondary-400/10 transition-all text-sm"
                                    required
                                />
                            </div>

                            {/* Password */}
                            <div className="relative group">
                                <div className="absolute left-4 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-focus-within:bg-primary-600/10 dark:group-focus-within:bg-primary-600/20 transition-colors">
                                    <Lock className="w-4 h-4 text-gray-400 group-focus-within:text-primary-600 dark:group-focus-within:text-primary-400 transition-colors" />
                                </div>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Mật khẩu"
                                    className="w-full pl-16 pr-20 py-4 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-600/10 dark:focus:border-secondary-400 dark:focus:ring-secondary-400/10 transition-all text-sm"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 px-2 py-1 text-xs font-bold tracking-wider text-gray-500 hover:text-primary-600 dark:hover:text-secondary-400 transition-colors uppercase"
                                >
                                    {showPassword ? 'ẨN' : 'HIỆN'}
                                </button>
                            </div>

                            {/* Remember me + Forgot */}
                            <div className="flex items-center justify-between">
                                <label className="flex items-center gap-2 cursor-pointer select-none">
                                    <div
                                        onClick={() => setRememberMe(!rememberMe)}
                                        className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all cursor-pointer ${rememberMe
                                            ? 'bg-primary-600 border-primary-600'
                                            : 'border-gray-300 dark:border-gray-600 hover:border-primary-600'
                                            }`}
                                    >
                                        {rememberMe && (
                                            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                            </svg>
                                        )}
                                    </div>
                                    <span className="text-sm text-gray-600 dark:text-gray-400">Ghi nhớ đăng nhập</span>
                                </label>
                                <a href="#" className="text-sm font-semibold text-primary-600 dark:text-secondary-400 hover:underline">
Quên mật khẩu?
                                </a>
                            </div>

                            {/* Sign In Button */}
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-4 rounded-2xl font-bold text-white text-sm tracking-wide transition-all duration-300 disabled:opacity-70 relative overflow-hidden group"
                                style={{
                                    background: 'linear-gradient(135deg, #1e3a8a 0%, #2a5298 50%, #4F46E5 100%)',
                                    boxShadow: '0 8px 32px rgba(30, 58, 138, 0.35)',
                                }}
                            >
                                <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-500" />
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
                                ) : (
                                    <span className="relative z-10 flex items-center justify-center gap-2">
Đăng nhập
                                        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                    </span>
                                )}
                            </button>

                            {/* Divider */}
                            <div className="flex items-center gap-4 my-2">
                                <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
                                <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Hoặc</span>
                                <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
                            </div>

                            {/* Social Sign In */}
                            <button
                                type="button"
                                className="w-full py-4 rounded-2xl font-semibold text-sm text-gray-700 dark:text-gray-300 border-2 border-gray-200 dark:border-gray-700 hover:border-primary-600 dark:hover:border-secondary-400 hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-3 group"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
                                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                                </svg>
Đăng nhập với Google
                            </button>
                        </form>

                        {/* Sign Up Link */}
                        <div className="mt-8 text-center">
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                                Chưa có tài khoản?{' '}
                                <Link to="/register" className="font-bold text-primary-600 dark:text-secondary-400 hover:underline">
                                    Đăng ký
                                </Link>
                            </p>
                        </div>
                    </div>

                    {/* Mobile-only branding */}
                    <div className="lg:hidden text-center mt-8">
                        <p className="text-white/50 text-xs">
                            © 2026 Micco AI. Đã đăng ký bản quyền.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
