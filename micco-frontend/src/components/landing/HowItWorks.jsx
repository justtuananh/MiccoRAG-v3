import { Upload, Cpu, LineChart } from 'lucide-react';

const steps = [
    {
        icon: Upload,
        step: '01',
        title: 'Tải tài liệu lên',
        description: 'Kéo thả tệp của bạn hoặc dùng nút tải lên. Hỗ trợ PDF, DOCX, XLSX, hình ảnh và hơn 50 định dạng tệp.',
        color: 'from-primary-600 to-secondary-500',
    },
    {
        icon: Cpu,
        step: '02',
        title: 'AI xử lý & lập chỉ mục',
        description: 'Công cụ AI tự động đọc, lập chỉ mục và hiểu nội dung của từng tài liệu bạn tải lên.',
        color: 'from-secondary-500 to-accent-500',
    },
    {
        icon: LineChart,
        step: '03',
        title: 'Nhận thông tin tức thì',
        description: 'Tìm kiếm, đặt câu hỏi và nhận câu trả lời chính xác. Tạo tóm tắt và tìm thông tin quan trọng chỉ trong vài giây.',
        color: 'from-accent-500 to-accent-600',
    },
];

export default function HowItWorks() {
    return (
        <section id="how-it-works" className="py-24 bg-slate-50 dark:bg-gray-900 relative overflow-hidden">
            <div className="absolute top-0 left-1/2 w-[500px] h-[500px] bg-primary-600/5 rounded-full blur-[100px] -translate-x-1/2 -translate-y-1/2" />

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-accent-500/10 text-accent-600 dark:text-accent-400 dark:bg-accent-500/20 mb-4">
                        Cách hoạt động
                    </span>
                    <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gray-900 dark:text-white mb-4">
                        Ba bước đơn giản để
                        <br />
                        <span className="text-gradient">chuyển đổi quy trình làm việc</span>
                    </h2>
                    <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
                        Bắt đầu chỉ trong vài phút, không phải vài ngày. Nền tảng được thiết kế để tăng năng suất tức thì.
                    </p>
                </div>

                <div className="grid md:grid-cols-3 gap-8 relative">
                    {/* Connecting line */}
                    <div className="hidden md:block absolute top-24 left-[20%] right-[20%] h-0.5 bg-gradient-to-r from-primary-600 via-secondary-500 to-accent-500 opacity-20" />

                    {steps.map((step, index) => {
                        const Icon = step.icon;
                        return (
                            <div key={step.title} className="relative text-center group">
                                <div className="relative inline-flex mb-6">
                                    <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center shadow-xl group-hover:scale-110 transition-transform duration-300`}>
                                        <Icon className="w-9 h-9 text-white" />
                                    </div>
                                    <span className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-white dark:bg-gray-800 shadow-lg flex items-center justify-center text-sm font-bold text-gray-900 dark:text-white border border-gray-100 dark:border-gray-700">
                                        {step.step}
                                    </span>
                                </div>
                                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                                    {step.title}
                                </h3>
                                <p className="text-gray-600 dark:text-gray-400 leading-relaxed max-w-xs mx-auto">
                                    {step.description}
                                </p>
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}
