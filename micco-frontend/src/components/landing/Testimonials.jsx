import { Star, Quote } from 'lucide-react';
import { testimonials } from '../../data/mockData';

export default function Testimonials() {
    return (
        <section id="testimonials" className="py-24 bg-white dark:bg-gray-950 relative">
            <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-secondary-500/5 rounded-full blur-[100px]" />

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <span className="inline-block px-4 py-1.5 rounded-full text-sm font-medium bg-secondary-500/10 text-secondary-600 dark:text-secondary-400 dark:bg-secondary-500/20 mb-4">
                        Khách hàng nói gì
                    </span>
                    <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-gray-900 dark:text-white mb-4">
                        Được các nhóm yêu thích
                        <br />
                        <span className="text-gradient">trên toàn thế giới</span>
                    </h2>
                </div>

                <div className="grid md:grid-cols-3 gap-8">
                    {testimonials.map((testimonial, index) => (
                        <div
                            key={testimonial.name}
                            className="relative bg-white dark:bg-gray-900 rounded-2xl p-8 border border-gray-100 dark:border-gray-800 card-hover"
                        >
                            <Quote className="w-10 h-10 text-primary-600/10 dark:text-primary-400/10 mb-4" />

                            {/* Stars */}
                            <div className="flex gap-1 mb-4">
                                {[...Array(testimonial.rating)].map((_, i) => (
                                    <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
                                ))}
                            </div>

                            <p className="text-gray-600 dark:text-gray-400 leading-relaxed mb-6 text-sm">
                                "{testimonial.quote}"
                            </p>

                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-600 to-secondary-500 flex items-center justify-center text-white font-bold text-sm">
                                    {testimonial.name.split(' ').map(n => n[0]).join('')}
                                </div>
                                <div>
                                    <p className="font-semibold text-gray-900 dark:text-white text-sm">
                                        {testimonial.name}
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400">
                                        {testimonial.role}, {testimonial.company}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
