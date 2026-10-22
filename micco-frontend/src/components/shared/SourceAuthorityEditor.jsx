import { useState } from 'react';
import { useAuth } from '../../context/authContextCore';

export default function SourceAuthorityEditor({ doc, onSaved }) {
    const { authFetch } = useAuth();
    const [issuer, setIssuer] = useState(doc.issuer || '');
    const [scope, setScope] = useState(doc.authority_scope || '');
    const [rank, setRank] = useState(doc.authority_rank ?? '');
    const [reason, setReason] = useState('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const save = async event => {
        event.preventDefault(); setBusy(true); setError('');
        try {
            const response = await authFetch(`/api/documents/${doc.id}/source-authority`, {
                method: 'PUT', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ issuer: issuer.trim(), scope: scope.trim(), rank: rank === '' ? null : Number(rank), reason: reason.trim() }),
            });
            if (!response.ok) throw new Error((await response.json()).detail || 'Không lưu được thẩm quyền nguồn');
            await onSaved(); setReason('');
        } catch (err) { setError(err.message); } finally { setBusy(false); }
    };
    return <details className="border rounded-lg p-3">
        <summary className="cursor-pointer text-sm font-medium">Xác nhận thẩm quyền nguồn</summary>
        <form onSubmit={save} className="space-y-3 mt-3 text-sm">
            <p>Chỉ nhập theo căn cứ đã được người phụ trách nguồn xác nhận. Cấp nhỏ hơn có ưu tiên cao hơn trong cùng phạm vi. Để trống cấp để đánh dấu chưa xác minh.</p>
            <label className="block">Đơn vị/người ban hành<input value={issuer} required={rank !== ''} maxLength={250} onChange={e => setIssuer(e.target.value)} className="block w-full border rounded p-2 dark:bg-gray-800" /></label>
            <label className="block">Phạm vi áp dụng<input value={scope} required={rank !== ''} maxLength={250} onChange={e => setScope(e.target.value)} className="block w-full border rounded p-2 dark:bg-gray-800" /></label>
            <label className="block">Cấp ưu tiên (1–100)<input type="number" min="1" max="100" value={rank} onChange={e => setRank(e.target.value)} className="block w-full border rounded p-2 dark:bg-gray-800" /></label>
            <label className="block">Căn cứ xác nhận *<textarea required maxLength={1000} value={reason} onChange={e => setReason(e.target.value)} className="block w-full border rounded p-2 dark:bg-gray-800" /></label>
            {error && <p role="alert" className="text-red-600">{error}</p>}
            <button disabled={busy || !reason.trim()} className="rounded px-3 py-2 bg-primary-600 text-white disabled:opacity-50">{busy ? 'Đang lưu…' : 'Lưu xác nhận'}</button>
        </form>
    </details>;
}
