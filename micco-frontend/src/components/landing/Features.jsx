import { Shield, Search, MessageSquare, Lock } from 'lucide-react';

const features = [
    {
        icon: Shield,
        title: 'Lưu trữ đám mây an toàn',
        description: 'Mã hóa chuẩn doanh nghiệp với AES 256-bit. Tài liệu của bạn luôn được bảo vệ theo tiêu chuẩn bảo mật cao nhất.',
        color: 'from-primary-600 to-primary-700',
        shadow: 'shadow-primary-600/20',
        iconBg: 'bg-primary-600/10 dark:bg-primary-600/20',
        iconColor: 'text-primary-600 dark:text-primary-400',
    },
    {
        icon: Search,
        title: 'Tìm kiếm & lọc thông minh',
        description: 'Tìm mọi tài liệu trong vài mili giây với tìm kiếm ngữ nghĩa bằng AI. Lọc theo loại, ngày, thẻ và nhiều hơn nữa.',
        color: 'from-secondary-500 to-secondary-600',
        shadow: 'shadow-secondary-500/20',
        iconBg: 'bg-secondary-500/10 dark:bg-secondary-500/20',
        iconColor: 'text-secondary-500 dark:text-secondary-400',
    },
    {
        icon: MessageSquare,
        title: 'Trợ lý trò chuyện tài liệu AI',
        description: 'Đặt câu hỏi về tài liệu và nhận câu trả lời chính xác ngay lập tức kèm theo nguồn tham chiếu.',
        color: 'from-accent-500 to-accent-600',
        shadow: 'shadow-accent-500/20',
        iconBg: 'bg-accent-500/10 dark:bg-accent-500/20',
        iconColor: 'text-accent-500 dark:text-accent-400',
    },
    {
        icon: Lock,
        title: 'Phân quyền truy cập theo vai trò',
        description: 'Phân quyền chi tiết cho vai trò Quản trị viên, Trưởng phòng và Nhân viên. Kiểm soát ai được xem và chỉnh sửa từng tài liệu.',
        color: 'from-amber-500 to-amber-600',
        shadow: 'shadow-amber-500/20',
        iconBg: 'bg-amber-500/10 dark:bg-amber-500/20',
        iconColor: 'text-amber-500 dark:text-amber-400',
    },
];

export default function Features() {
    return (
        <section id="features" className="py-24 bg-white dark:bg-gray-950 relative">
            <div className="absolute inset-0 bg-gradient-to-b from-slate-50 to-white dark:from-gray-950 dark:to-gray-900 opacity-50" />

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="text-center mb-16">
                    <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-primary-600/10 text-primary-600 dark:text-primary-400 dark:bg-primary-600/20 mb-4">
                        Tính năng
                    </span>
                    <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gray-900 dark:text-white mb-4">
                        Mọi thứ bạn cần để
                        <br />
                        <span className="text-gradient">quản lý tài liệu thông minh</span>
                    </h2>
                    <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                        Bộ tính năng mạnh mẽ dành cho các nhóm hiện đại cần quản lý tài liệu
                        an toàn, dễ tìm kiếm và được tăng cường bởi AI.
                    </p>
                </div>

                {/* Feature Cards */}
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {features.map((feature, index) => {
                        const Icon = feature.icon;
                        return (
                            <div
                                key={feature.title}
                                className={`group relative bg-white dark:bg-gray-900 rounded-2xl p-6 border border-gray-100 dark:border-gray-800 card-hover`}
                                style={{ animationDelay: `${index * 0.1}s` }}
                            >
                                <div className={`w-14 h-14 rounded-xl ${feature.iconBg} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300`}>
                                    <Icon className={`w-7 h-7 ${feature.iconColor}`} />
                                </div>
                                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                                    {feature.title}
                                </h3>
                                <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                                    {feature.description}
                                </p>

                                {/* Bottom gradient line */}
                                <div className={`absolute bottom-0 left-4 right-4 h-1 rounded-full bg-gradient-to-r ${feature.color} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}
