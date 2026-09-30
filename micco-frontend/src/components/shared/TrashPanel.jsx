import { useState } from 'react';
import { useAuth } from '../../context/authContextCore';

export default function TrashPanel({ listPath, restorePath, onRestored }) {
    const { authFetch } = useAuth();
    const [open, setOpen] = useState(false);
    const [items, setItems] = useState([]);
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const load = async () => {
        const response = await authFetch(listPath);
        if (!response.ok) throw new Error('Không thể tải thùng rác');
        const data = await response.json();
        setItems(Array.isArray(data) ? data : data.items || []);
    };
    const show = async () => {
        setOpen(true); setBusy(true); setError('');
        try { await load(); } catch (err) { setError(err.message); } finally { setBusy(false); }
    };
    const restore = async (id) => {
        setBusy(true); setError('');
        try {
            const response = await authFetch(restorePath(id), { method: 'POST' });
            if (!response.ok) throw new Error((await response.json()).detail || 'Không thể khôi phục');
            await load(); await onRestored();
        } catch (err) { setError(err.message); } finally { setBusy(false); }
    };
    return <div className="mb-4">
        <button type="button" onClick={show} className="border rounded-lg px-3 py-2">Thùng rác</button>
        {open && <section aria-label="Thùng rác" className="mt-3 border rounded-xl p-4 space-y-3">
            <div className="flex justify-between gap-3"><p>Có thể khôi phục trong 30 ngày. Nội dung cần hoàn tất xử lý trước khi hỏi đáp.</p><button type="button" onClick={() => setOpen(false)}>Đóng</button></div>
            {error && <p role="alert" className="text-red-600">{error}</p>}
            {!busy && !items.length && <p>Thùng rác trống.</p>}
            {items.map(item => <div key={item.id} className="flex justify-between gap-3 border-t pt-2"><span className="min-w-0 break-words">{item.name || item.title}</span><button type="button" disabled={busy} onClick={() => restore(item.id)} className="shrink-0 text-primary-600 disabled:opacity-50">Khôi phục</button></div>)}
            {busy && <p role="status">Đang xử lý…</p>}
        </section>}
    </div>;
}
