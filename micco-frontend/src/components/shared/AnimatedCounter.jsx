// src/components/shared/AnimatedCounter.jsx
import { useState, useEffect } from 'react';

export default function AnimatedCounter({ target, suffix = '', prefix = '' }) {
    const num = typeof target === 'string' ? parseFloat(target) : target;
    return <Counter key={String(num)} num={num} suffix={suffix} prefix={prefix} />;
}

function Counter({ num, suffix, prefix }) {
    const [count, setCount] = useState(0);

    useEffect(() => {
        if (isNaN(num)) return;
        const duration = 2000;
        const steps = 60;
        const stepTime = duration / steps;
        let current = 0;

        const timer = setInterval(() => {
            current += num / steps;
            if (current >= num) {
                setCount(num);
                clearInterval(timer);
            } else {
                setCount(Math.round(current * 10) / 10);
            }
        }, stepTime);

        return () => clearInterval(timer);
    }, [num]);

    const display = !Number.isInteger(num)
        ? count.toFixed(1)
        : Math.round(count).toLocaleString();

    return <span>{prefix}{display}{suffix}</span>;
}
