import { Link } from 'react-router-dom';
import { FileText, Github, Twitter, Linkedin, Mail } from 'lucide-react';

const footerLinks = {
    'Sản phẩm': [
        { label: 'Tính năng', href: '#features' },
        { label: 'Cách hoạt động', href: '#how-it-works' },
        { label: 'Tích hợp', href: '#' },
        { label: 'API', href: '#' },
    ],
    'Công ty': [
        { label: 'Về chúng tôi', href: '#' },
        { label: 'Tuyển dụng', href: '#' },
        { label: 'Blog', href: '#' },
        { label: 'Báo chí', href: '#' },
    ],
    'Pháp lý': [
        { label: 'Chính sách bảo mật', href: '#' },
        { label: 'Điều khoản dịch vụ', href: '#' },
        { label: 'Chính sách cookie', href: '#' },
        { label: 'GDPR', href: '#' },
    ],
    'Hỗ trợ': [
        { label: 'Trung tâm trợ giúp', href: '#' },
        { label: 'Liên hệ', href: '#' },
        { label: 'Trạng thái', href: '#' },
        { label: 'Nhật ký thay đổi', href: '#' },
    ],
};

const socialLinks = [
    { icon: Twitter, href: '#', label: 'Twitter' },
    { icon: Linkedin, href: '#', label: 'LinkedIn' },
    { icon: Github, href: '#', label: 'GitHub' },
    { icon: Mail, href: '#', label: 'Email' },
];

export default function Footer() {
    return (
        <footer id="footer" className="bg-gray-900 dark:bg-gray-950 text-gray-400 pt-20 pb-8 relative overflow-hidden">
            <div className="absolute top-0 left-1/4 w-[400px] h-[400px] bg-primary-600/5 rounded-full blur-[100px]" />

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* CTA Banner */}
                <div className="relative mb-16 rounded-2xl overflow-hidden">
                    <div className="absolute inset-0 gradient-primary opacity-90" />
                    <div className="relative px-8 py-12 sm:px-12 text-center">
                        <h3 className="text-2xl sm:text-3xl font-extrabold text-white mb-4">
                            Sẵn sàng nâng cấp quy trình tài liệu của bạn?
                        </h3>
                        <p className="text-white/80 mb-8 max-w-xl mx-auto">
                            Tham gia cùng hơn 2.000 nhóm đang dùng TKV để quản lý tài liệu thông minh hơn.
                        </p>
                        <Link
                            to="/dashboard"
                            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-600 rounded-xl font-bold hover:shadow-xl hover:shadow-white/20 transition-all duration-300 hover:-translate-y-0.5"
                        >
                            Vào Dashboard
                        </Link>
                    </div>
                </div>

                {/* Footer Grid */}
                <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-8 mb-12">
                    {/* Brand */}
                    <div className="lg:col-span-1">
                        <Link to="/" className="flex items-center gap-4 mb-4">
                            <div className="w-16 h-16 bg-white rounded-xl flex items-center justify-center p-2 shadow-sm border border-gray-100">
                                <img src="/logo-tkv.png" alt="TKV Logo" className="w-full h-full object-contain" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-2xl font-extrabold text-white leading-tight">
                                    TKV
                                </span>
                                <span className="text-sm font-bold text-primary-400">
                                    nền tảng tri thức
                                </span>
                            </div>
                        </Link>
                        <p className="text-sm text-gray-500 mb-6 leading-relaxed">
                            Nền tảng quản lý tài liệu thông minh được hỗ trợ bởi trí tuệ nhân tạo.
                        </p>
                        <div className="flex gap-3">
                            {socialLinks.map(({ icon: Icon, href, label }) => (
                                <a
                                    key={label}
                                    href={href}
                                    aria-label={label}
                                    className="w-9 h-9 rounded-lg bg-gray-800 hover:bg-gray-700 flex items-center justify-center text-gray-400 hover:text-white transition-all duration-200"
                                >
                                    <Icon className="w-4 h-4" />
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Link Columns */}
                    {Object.entries(footerLinks).map(([category, links]) => (
                        <div key={category}>
                            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
                                {category}
                            </h4>
                            <ul className="space-y-3">
                                {links.map((link) => (
                                    <li key={link.label}>
                                        <a
                                            href={link.href}
                                            className="text-sm text-gray-500 hover:text-white transition-colors duration-200"
                                        >
                                            {link.label}
                                        </a>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>

                {/* Bottom Bar */}
                <div className="border-t border-gray-800 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <p className="text-sm text-gray-600">
                        © 2026 TKV. Đã đăng ký bản quyền.
                    </p>
                    <p className="text-sm text-gray-600">
                        Xây dựng với ❤️ dành cho các nhóm hiện đại
                    </p>
                </div>
            </div>
        </footer>
    );
}
