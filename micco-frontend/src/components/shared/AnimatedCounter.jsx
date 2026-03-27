// src/components/shared/AnimatedCounter.jsx
import { useState, useEffect } from 'react';

export default function AnimatedCounter({ target, suffix = '', prefix = '' }) {
    const [count, setCount] = useState(0);
    const num = typeof target === 'string' ? parseFloat(target) : target;

    useEffect(() => {
        if (isNaN(num)) { setCount(0); return; }
        setCount(0);
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
