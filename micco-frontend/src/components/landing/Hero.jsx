import { Link } from 'react-router-dom';
import { FileText, ArrowRight, Shield, Sparkles } from 'lucide-react';

export default function Hero() {
    return (
        <section className="relative min-h-screen flex items-center overflow-hidden">
            {/* Background Gradient */}
            <div className="absolute inset-0 gradient-primary opacity-[0.03] dark:opacity-[0.08]" />
            <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-secondary-500/10 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/3" />
            <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-accent-500/10 rounded-full blur-[100px] translate-y-1/2 -translate-x-1/3" />

            {/* Floating elements */}
            <div className="absolute top-32 right-20 hidden lg:block animate-float">
                <div className="glass rounded-2xl p-4 shadow-xl dark:glass-dark">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-accent-500/20 flex items-center justify-center">
                            <Shield className="w-5 h-5 text-accent-500" />
                        </div>
                        <div>
                            <p className="text-sm font-semibold text-gray-900 dark:text-white">Bảo mật</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Mã hóa 256-bit AES</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="absolute bottom-40 right-40 hidden lg:block animate-float-delayed">
                <div className="glass rounded-2xl p-4 shadow-xl dark:glass-dark">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-secondary-500/20 flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-secondary-500" />
                        </div>
                        <div>
                            <p className="text-sm font-semibold text-gray-900 dark:text-white">Hỗ trợ AI</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Phân tích thông minh</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="absolute top-60 left-10 hidden xl:block animate-float">
                <div className="glass rounded-2xl p-3 shadow-xl dark:glass-dark">
                    <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">1.247 tài liệu đang quản lý</span>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-16">
                <div className="max-w-3xl">
                    {/* Badge */}
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-600/10 dark:bg-primary-600/20 border border-primary-600/20 mb-8 animate-fade-in-up">
                        <Sparkles className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                        <span className="text-sm font-medium text-primary-600 dark:text-primary-400">
                            Nền tảng quản lý tri thức thông minh
                        </span>
                    </div>

                    {/* Headline */}
                    <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-tight text-gray-900 dark:text-white mb-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
                        Quản lý tài liệu{' '}
                        <span className="text-gradient">thông minh</span>{' '}
                        cùng AI
                    </h1>

                    {/* Subheadline */}
                    <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-400 mb-10 max-w-xl leading-relaxed animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                        Lưu trữ, tổ chức và tra cứu tri thức từ tài liệu của bạn ngay lập tức.
                        Để AI thay đổi cách nhóm bạn làm việc với thông tin.
                    </p>

                    {/* CTA Buttons */}
                    <div className="flex flex-wrap gap-4 animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
                        <Link to="/register" className="btn-primary text-lg !px-8 !py-4 flex items-center gap-2 group">
                            Bắt đầu ngay
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link to="/dashboard" className="btn-secondary text-lg !px-8 !py-4 dark:bg-gray-800 dark:text-white dark:border-gray-700 dark:hover:border-secondary-400">
                            Dùng thử
                        </Link>
                    </div>

                    {/* Trust indicators */}
                    <div className="mt-12 flex items-center gap-8 animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
                        <div className="flex -space-x-3">
                            {['bg-primary-600', 'bg-secondary-500', 'bg-accent-500', 'bg-amber-500'].map((bg, i) => (
                                <div key={i} className={`w-10 h-10 rounded-full ${bg} border-2 border-white dark:border-gray-950 flex items-center justify-center text-white text-xs font-bold`}>
                                    {String.fromCharCode(65 + i)}
                                </div>
                            ))}
                        </div>
                        <div>
                            <p className="text-sm font-semibold text-gray-900 dark:text-white">Được tin dùng bởi 2.000+ nhóm</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">Cùng các doanh nghiệp hàng đầu Việt Nam</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
