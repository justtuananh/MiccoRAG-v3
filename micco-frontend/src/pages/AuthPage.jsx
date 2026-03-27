import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { User, Mail, Lock, ArrowRight, Sun, Moon, ShieldCheck, Building2 } from 'lucide-react';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '') + '/api';

// Async wrappers for auth that handle navigation and errors
function useAuthHandlers() {
    const navigate = useNavigate();
    const { login, register } = useAuth();

    const handleLogin = async (email, password, setLoading, setError) => {
        const result = await login(email, password);
        if (result.success) {
            navigate('/dashboard');
        } else {
            setLoading(false);
            setError(result.error || 'Đăng nhập thất bại');
        }
    };

    const handleRegister = async (name, email, password, departmentId, setLoading, setError) => {
        const result = await register(name, email, password, departmentId);
        if (result.success) {
            navigate('/dashboard');
        } else {
            setLoading(false);
            setError(result.error || 'Đăng ký thất bại');
        }
    };

    return { handleLogin, handleRegister };
}

export default function AuthPage() {
    const location = useLocation();
    const [isSignUp, setIsSignUp] = useState(location.pathname === '/register');
    const navigate = useNavigate();
    const { isDark, toggleTheme } = useTheme();
    const { handleLogin, handleRegister } = useAuthHandlers();

    // Sync URL → state
    useEffect(() => {
        setIsSignUp(location.pathname === '/register');
    }, [location.pathname]);

    const toggle = (toSignUp) => {
        setIsSignUp(toSignUp);
        navigate(toSignUp ? '/register' : '/login', { replace: true });
    };

    return (
        <div className="min-h-screen flex bg-[#2a5298] relative overflow-hidden">

            {/* ─── Floating Spheres (Background) ─── */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
                <div className="absolute -bottom-20 -left-20 w-[420px] h-[420px] rounded-full animate-float"
                    style={{
                        background: 'radial-gradient(circle at 35% 35%, #5b8def 0%, #1e3a8a 60%, #0f1f4e 100%)',
                        boxShadow: '0 0 80px rgba(30, 58, 138, 0.5), inset 0 -20px 60px rgba(0,0,0,0.3)',
                    }}
                />
                <div className="absolute top-10 left-[22%] w-[220px] h-[220px] rounded-full animate-float-delayed"
                    style={{
                        background: 'radial-gradient(circle at 35% 35%, #6b9cf7 0%, #3060c7 50%, #1e3a8a 100%)',
                        boxShadow: '0 0 60px rgba(79, 70, 229, 0.35), inset 0 -15px 40px rgba(0,0,0,0.25)',
                    }}
                />
                <div className="absolute top-[45%] left-[38%] w-[110px] h-[110px] rounded-full animate-float"
                    style={{
                        animationDelay: '1s',
                        background: 'radial-gradient(circle at 30% 30%, #7dacfa 0%, #4272d1 60%, #1e3a8a 100%)',
                        boxShadow: '0 0 40px rgba(59, 130, 246, 0.3), inset 0 -10px 30px rgba(0,0,0,0.2)',
                    }}
                />
                <div className="absolute -top-10 right-[35%] w-[160px] h-[160px] rounded-full opacity-60 animate-float-delayed"
                    style={{
                        animationDelay: '3s',
                        background: 'radial-gradient(circle at 35% 35%, #87b4f9 0%, #4c7bd4 60%, #2a5298 100%)',
                        boxShadow: '0 0 50px rgba(79, 70, 229, 0.2)',
                    }}
                />
                <div className="absolute bottom-[-60px] right-[-40px] w-[300px] h-[300px] rounded-full opacity-50"
                    style={{
                        background: 'radial-gradient(circle at 40% 40%, #5b8def 0%, #1e3a8a 70%)',
                        boxShadow: '0 0 70px rgba(30, 58, 138, 0.4)',
                    }}
                />
            </div>

            {/* ─── Main Container ─── */}
            <div className="relative z-10 w-full flex items-center justify-center px-4 py-8">
                <div className="w-full max-w-[1000px] min-h-[620px] relative rounded-3xl overflow-hidden shadow-2xl shadow-black/30">

                    {/* ── Form Panels (behind the overlay) ── */}
                    <div className="absolute inset-0 hidden lg:flex">

                        {/* Đăng nhập — trái */}
                        <div className="w-1/2 flex items-center justify-center bg-white dark:bg-gray-900 p-8 sm:p-12">
                            <SignInForm
                                onLogin={handleLogin}
                                isDark={isDark}
                                toggleTheme={toggleTheme}
                                onToggle={() => toggle(true)}
                            />
                        </div>

                        {/* Đăng ký — phải */}
                        <div className="w-1/2 flex items-center justify-center bg-white dark:bg-gray-900 p-8 sm:p-12">
                            <SignUpForm
                                onRegister={handleRegister}
                                isDark={isDark}
                                toggleTheme={toggleTheme}
                                onToggle={() => toggle(false)}
                            />
                        </div>
                    </div>

                    {/* ── Sliding Overlay Panel ── */}
                    <div
                        className="absolute top-0 w-1/2 h-full transition-transform duration-700 ease-[cubic-bezier(0.68,-0.15,0.27,1.15)] z-20"
                        style={{ transform: isSignUp ? 'translateX(0%)' : 'translateX(100%)' }}
                    >
                        <div
                            className="w-full h-full flex flex-col items-center justify-center px-10 text-center relative overflow-hidden"
                            style={{
                                background: 'linear-gradient(135deg, #1e3a8a 0%, #2a5298 40%, #4F46E5 100%)',
                            }}
                        >
                            {/* Decorative circles inside overlay */}
                            <div className="absolute -top-16 -left-16 w-48 h-48 rounded-full bg-white/5" />
                            <div className="absolute -bottom-20 -right-20 w-56 h-56 rounded-full bg-white/5" />
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 rounded-full border border-white/10" />

                            {/* Dark mode toggle */}
                            <button
                                onClick={toggleTheme}
                                className="absolute top-5 right-5 p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white/70 hover:text-white transition-all"
                            >
                                {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                            </button>

                            {/* Content that transitions */}
                            <div
                                key={isSignUp ? 'overlay-signin' : 'overlay-signup'}
                                className="relative z-10 animate-fade-in"
                            >
                                <h2 className="text-4xl font-extrabold text-white italic mb-3"
                                    style={{ textShadow: '0 4px 20px rgba(0,0,0,0.25)' }}>
                                    {isSignUp ? 'CHÀO MỪNG TRỞ LẠI' : 'THAM GIA NGAY'}
                                </h2>
                                <p className="text-white/70 text-sm mb-8 max-w-xs mx-auto leading-relaxed">
                                    {isSignUp
                                        ? 'Bạn đã có tài khoản? Đăng nhập để truy cập tài liệu và trợ lý AI của bạn.'
                                        : 'Tạo tài khoản miễn phí và khám phá sức mạnh quản lý tài liệu thông minh cùng AI.'}
                                </p>
                                <button
                                    onClick={() => toggle(!isSignUp)}
                                    className="px-8 py-3 rounded-2xl border-2 border-white text-white font-bold text-sm tracking-wide hover:bg-white hover:text-[#1e3a8a] transition-all duration-300 active:scale-95"
                                >
                                    {isSignUp ? 'ĐĂNG NHẬP' : 'ĐĂNG KÝ'}
                                </button>

                                {/* Feature tags */}
                                <div className="flex flex-wrap gap-2 justify-center mt-8">
                                    {['🔒 Bảo mật', '🤖 Hỗ trợ AI', '⚡ Nhanh chóng'].map((tag) => (
                                        <span key={tag} className="px-3 py-1.5 rounded-xl bg-white/10 text-white/70 text-xs font-medium backdrop-blur-sm border border-white/10">
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* ── Mobile Layout (stacked, no slider) ── */}
                    <div className="lg:hidden relative z-10 bg-white dark:bg-gray-900 min-h-[620px] flex items-center justify-center p-6">
                        {isSignUp ? (
                            <SignUpForm
                                onRegister={handleRegister}
                                isDark={isDark}
                                toggleTheme={toggleTheme}
                                onToggle={() => toggle(false)}
                                mobile
                            />
                        ) : (
                            <SignInForm
                                onLogin={handleLogin}
                                isDark={isDark}
                                toggleTheme={toggleTheme}
                                onToggle={() => toggle(true)}
                                mobile
                            />
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}


/* ═══════════════════════════════════════════════
   Sign In Form
   ═══════════════════════════════════════════════ */
function SignInForm({ onLogin, isDark, toggleTheme, onToggle, mobile }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [rememberMe, setRememberMe] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        onLogin(email, password, setLoading, setError);
    };

    return (
        <div className="w-full max-w-sm">
            {mobile && (
                <button onClick={toggleTheme}
                    className="absolute top-5 right-5 p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 transition-all">
                    {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </button>
            )}

            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-1">Đăng nhập</h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">Chào mừng trở lại! Nhập thông tin để tiếp tục.</p>

            {error && (
                <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 text-sm font-medium">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                {/* Email */}
                <div className="relative group">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-focus-within:bg-primary-600/10 dark:group-focus-within:bg-primary-600/20 transition-colors">
                        <User className="w-4 h-4 text-gray-400 group-focus-within:text-primary-600 dark:group-focus-within:text-primary-400 transition-colors" />
                    </div>
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                        placeholder="Địa chỉ Email"
                        className="w-full pl-16 pr-5 py-3.5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-600/10 dark:focus:border-secondary-400 dark:focus:ring-secondary-400/10 transition-all text-sm"
                        required
                    />
                </div>

                {/* Password */}
                <div className="relative group">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-focus-within:bg-primary-600/10 dark:group-focus-within:bg-primary-600/20 transition-colors">
                        <Lock className="w-4 h-4 text-gray-400 group-focus-within:text-primary-600 dark:group-focus-within:text-primary-400 transition-colors" />
                    </div>
                    <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)}
                        placeholder="Mật khẩu"
                        className="w-full pl-16 pr-20 py-3.5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-600/10 dark:focus:border-secondary-400 dark:focus:ring-secondary-400/10 transition-all text-sm"
                        required
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 px-2 py-1 text-xs font-bold tracking-wider text-gray-500 hover:text-primary-600 dark:hover:text-secondary-400 transition-colors uppercase">
                        {showPassword ? 'ẨN' : 'HIỆN'}
                    </button>
                </div>

                {/* Remember + Forgot */}
                <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                        <div onClick={() => setRememberMe(!rememberMe)}
                            className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all cursor-pointer ${rememberMe ? 'bg-primary-600 border-primary-600' : 'border-gray-300 dark:border-gray-600 hover:border-primary-600'}`}>
                            {rememberMe && (
                                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                        </div>
                        <span className="text-sm text-gray-600 dark:text-gray-400">Ghi nhớ đăng nhập</span>
                    </label>
                    <a href="#" className="text-sm font-semibold text-primary-600 dark:text-secondary-400 hover:underline">Quên mật khẩu?</a>
                </div>

                {/* Submit */}
                <button type="submit" disabled={loading}
                    className="w-full py-3.5 rounded-2xl font-bold text-white text-sm tracking-wide transition-all duration-300 disabled:opacity-70 relative overflow-hidden group"
                    style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #2a5298 50%, #4F46E5 100%)', boxShadow: '0 8px 32px rgba(30, 58, 138, 0.35)' }}>
                    <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-500" />
                    {loading
                        ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
                        : <span className="relative z-10 flex items-center justify-center gap-2">Đăng nhập <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" /></span>
                    }
                </button>

                {/* Divider */}
                <div className="flex items-center gap-4">
                    <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
                    <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Hoặc</span>
                    <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
                </div>

                {/* Google */}
                <button type="button"
                    className="w-full py-3.5 rounded-2xl font-semibold text-sm text-gray-700 dark:text-gray-300 border-2 border-gray-200 dark:border-gray-700 hover:border-primary-600 dark:hover:border-secondary-400 hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-3">
                    <GoogleIcon />
                    Đăng nhập với Google
                </button>
            </form>

            {/* Toggle (mobile only) */}
            {mobile && (
                <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
                    Chưa có tài khoản?{' '}
                    <button onClick={onToggle} className="font-bold text-primary-600 dark:text-secondary-400 hover:underline">Đăng ký</button>
                </p>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════════════
   Sign Up Form
   ═══════════════════════════════════════════════ */
function SignUpForm({ onRegister, isDark, toggleTheme, onToggle, mobile }) {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [departmentId, setDepartmentId] = useState('');
    const [departments, setDepartments] = useState([]);
    const [agreeTerms, setAgreeTerms] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        fetch(`${API_BASE}/auth/departments`)
            .then(r => r.ok ? r.json() : [])
            .then(setDepartments)
            .catch(() => {});
    }, []);

    const passwordsMatch = !confirmPassword || password === confirmPassword;

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!passwordsMatch) return;
        setLoading(true);
        setError('');
        onRegister(name, email, password, departmentId ? parseInt(departmentId) : null, setLoading, setError);
    };

    return (
        <div className="w-full max-w-sm">
            {mobile && (
                <button onClick={toggleTheme}
                    className="absolute top-5 right-5 p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 transition-all">
                    {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                </button>
            )}

            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-1">Đăng ký</h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm mb-4">Tạo tài khoản để bắt đầu sử dụng.</p>

            {error && (
                <div className="mb-4 px-4 py-3 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 text-red-600 dark:text-red-400 text-sm font-medium">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3.5">
                {/* Name */}
                <div className="relative group">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-focus-within:bg-primary-600/10 dark:group-focus-within:bg-primary-600/20 transition-colors">
                        <User className="w-4 h-4 text-gray-400 group-focus-within:text-primary-600 dark:group-focus-within:text-primary-400 transition-colors" />
                    </div>
                    <input type="text" value={name} onChange={(e) => setName(e.target.value)}
                        placeholder="Họ và tên"
                        className="w-full pl-16 pr-5 py-3 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-600/10 dark:focus:border-secondary-400 dark:focus:ring-secondary-400/10 transition-all text-sm"
                        required
                    />
                </div>

                {/* Email */}
                <div className="relative group">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-focus-within:bg-primary-600/10 dark:group-focus-within:bg-primary-600/20 transition-colors">
                        <Mail className="w-4 h-4 text-gray-400 group-focus-within:text-primary-600 dark:group-focus-within:text-primary-400 transition-colors" />
                    </div>
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                        placeholder="Địa chỉ Email"
                        className="w-full pl-16 pr-5 py-3 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-600/10 dark:focus:border-secondary-400 dark:focus:ring-secondary-400/10 transition-all text-sm"
                        required
                    />
                </div>

                {/* Department */}
                <div className="relative group">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-focus-within:bg-primary-600/10 dark:group-focus-within:bg-primary-600/20 transition-colors">
                        <Building2 className="w-4 h-4 text-gray-400 group-focus-within:text-primary-600 dark:group-focus-within:text-primary-400 transition-colors" />
                    </div>
                    <select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}
                        className="w-full pl-16 pr-5 py-3 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-600/10 dark:focus:border-secondary-400 dark:focus:ring-secondary-400/10 transition-all text-sm appearance-none cursor-pointer"
                    >
                        <option value="">-- Chọn phòng ban --</option>
                        {departments.map(d => (
                            <option key={d.id} value={d.id}>{d.name}</option>
                        ))}
                    </select>
                </div>

                {/* Password */}
                <div className="relative group">
                    <div className="absolute left-4 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center group-focus-within:bg-primary-600/10 dark:group-focus-within:bg-primary-600/20 transition-colors">
                        <Lock className="w-4 h-4 text-gray-400 group-focus-within:text-primary-600 dark:group-focus-within:text-primary-400 transition-colors" />
                    </div>
                    <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)}
                        placeholder="Mật khẩu"
                        className="w-full pl-16 pr-20 py-3 rounded-2xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:border-primary-600 focus:ring-2 focus:ring-primary-600/10 dark:focus:border-secondary-400 dark:focus:ring-secondary-400/10 transition-all text-sm"
                        required minLength={6}
                    />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 px-2 py-1 text-xs font-bold tracking-wider text-gray-500 hover:text-primary-600 dark:hover:text-secondary-400 transition-colors uppercase">
                        {showPassword ? 'ẨN' : 'HIỆN'}
                    </button>
                </div>

                {/* Confirm Password */}
                <div className="relative group">
                    <div className={`absolute left-4 top-1/2 -translate-y-1/2 w-9 h-9 rounded-xl flex items-center justify-center transition-colors ${!passwordsMatch ? 'bg-red-100 dark:bg-red-900/30' : 'bg-gray-100 dark:bg-gray-800 group-focus-within:bg-primary-600/10 dark:group-focus-within:bg-primary-600/20'}`}>
                        <ShieldCheck className={`w-4 h-4 transition-colors ${!passwordsMatch ? 'text-red-500' : 'text-gray-400 group-focus-within:text-primary-600 dark:group-focus-within:text-primary-400'}`} />
                    </div>
                    <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Xác nhận mật khẩu"
                        className={`w-full pl-16 pr-5 py-3 rounded-2xl border bg-gray-50 dark:bg-gray-800/50 text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:ring-2 transition-all text-sm ${!passwordsMatch ? 'border-red-400 focus:border-red-500 focus:ring-red-500/10' : 'border-gray-200 dark:border-gray-700 focus:border-primary-600 focus:ring-primary-600/10 dark:focus:border-secondary-400 dark:focus:ring-secondary-400/10'}`}
                        required
                    />
                    {!passwordsMatch && <p className="text-xs text-red-500 mt-1 ml-1 font-medium">Mật khẩu không khớp</p>}
                </div>

                {/* Terms */}
                <div className="flex items-start gap-2 pt-0.5">
                    <div onClick={() => setAgreeTerms(!agreeTerms)}
                        className={`w-5 h-5 mt-0.5 rounded-md border-2 flex items-center justify-center transition-all cursor-pointer flex-shrink-0 ${agreeTerms ? 'bg-primary-600 border-primary-600' : 'border-gray-300 dark:border-gray-600 hover:border-primary-600'}`}>
                        {agreeTerms && (
                            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                        )}
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                        Tôi đồng ý với <a href="#" className="text-primary-600 dark:text-secondary-400 hover:underline font-medium">Điều khoản sử dụng</a> và <a href="#" className="text-primary-600 dark:text-secondary-400 hover:underline font-medium">Chính sách bảo mật</a>
                    </span>
                </div>

                {/* Submit */}
                <button type="submit" disabled={loading || !passwordsMatch || !agreeTerms}
                    className="w-full py-3.5 rounded-2xl font-bold text-white text-sm tracking-wide transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed relative overflow-hidden group"
                    style={{ background: 'linear-gradient(135deg, #1e3a8a 0%, #2a5298 50%, #4F46E5 100%)', boxShadow: '0 8px 32px rgba(30, 58, 138, 0.35)' }}>
                    <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-500" />
                    {loading
                        ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
                        : <span className="relative z-10 flex items-center justify-center gap-2">Tạo tài khoản <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" /></span>
                    }
                </button>

                {/* Divider */}
                <div className="flex items-center gap-4">
                    <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
                    <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Hoặc</span>
                    <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
                </div>

                {/* Google */}
                <button type="button"
                    className="w-full py-3 rounded-2xl font-semibold text-sm text-gray-700 dark:text-gray-300 border-2 border-gray-200 dark:border-gray-700 hover:border-primary-600 dark:hover:border-secondary-400 hover:shadow-lg transition-all duration-300 flex items-center justify-center gap-3">
                    <GoogleIcon />
                    Đăng ký với Google
                </button>
            </form>

            {/* Toggle (mobile only) */}
            {mobile && (
                <p className="mt-5 text-center text-sm text-gray-500 dark:text-gray-400">
                    Đã có tài khoản?{' '}
                    <button onClick={onToggle} className="font-bold text-primary-600 dark:text-secondary-400 hover:underline">Đăng nhập</button>
                </p>
            )}
        </div>
    );
}


/* ═══════════════════════════════════════════════
   Google SVG Icon
   ═══════════════════════════════════════════════ */
function GoogleIcon() {
    return (
        <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
        </svg>
    );
}
