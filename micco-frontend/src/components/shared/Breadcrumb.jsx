// src/components/shared/Breadcrumb.jsx
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

export default function Breadcrumb({ items }) {
    if (!items?.length) return null;

    return (
        <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 mb-4">
            {items.map((item, index) => {
                const isLast = index === items.length - 1;
                return (
                    <span key={item.href ?? item.label} className="flex items-center gap-1">
                        {index > 0 && (
                            <ChevronRight className="w-3.5 h-3.5 text-slate-300 dark:text-slate-600" />
                        )}
                        {isLast || !item.href ? (
                            <span
                                aria-current={isLast ? 'page' : undefined}
                                className={
                                    isLast
                                        ? 'text-slate-400 dark:text-slate-500'
                                        : 'hover:text-primary-600 dark:hover:text-primary-400 cursor-pointer transition-colors'
                                }
                            >
                                {item.label}
                            </span>
                        ) : (
                            <Link
                                to={item.href}
                                className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                            >
                                {item.label}
                            </Link>
                        )}
                    </span>
                );
            })}
        </nav>
    );
}
