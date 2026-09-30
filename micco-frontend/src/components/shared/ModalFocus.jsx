import { useEffect, useRef } from 'react';

/** Keyboard focus stays inside a modal and returns to its opener on close. */
export default function ModalFocus({ children, label, onClose, className, ...rest }) {
    const container = useRef(null);
    const close = useRef(onClose);
    useEffect(() => { close.current = onClose; }, [onClose]);
    useEffect(() => {
        const previous = document.activeElement;
        const root = container.current;
        const controls = () => [...root.querySelectorAll('button, input, select, textarea, a[href], [tabindex], [contenteditable="true"]')]
            .filter(el => !el.disabled && (el.tabIndex >= 0 || el.isContentEditable) && el.getClientRects().length);
        (controls()[0] || root).focus();
        const keydown = event => {
            if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); close.current?.(); }
            if (event.key !== 'Tab') return;
            const items = controls();
            if (!items.length) { event.preventDefault(); root.focus(); return; }
            const first = items[0], last = items[items.length - 1];
            if (event.shiftKey && (document.activeElement === first || !root.contains(document.activeElement))) {
                event.preventDefault(); last.focus();
            } else if (!event.shiftKey && (document.activeElement === last || !root.contains(document.activeElement))) {
                event.preventDefault(); first.focus();
            }
        };
        root.addEventListener('keydown', keydown);
        return () => { root.removeEventListener('keydown', keydown); if (previous?.isConnected) previous.focus(); };
    }, []);
    return <div {...rest} ref={container} role="dialog" aria-modal="true" aria-label={label} tabIndex={-1} className={className}>{children}</div>;
}
