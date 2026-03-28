import { useState, useEffect } from 'react';
import { X, UserPlus, Eye, EyeOff } from 'lucide-react';

const ROLES = ['Tất cả', 'Admin', 'Trưởng phòng', 'Nhân viên'];
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '') + '/api';

export { ROLES };

export default function UserModal({ open, onClose, onSave, editUser }) {
    const [form, setForm] = useState({ name: '', email: '', role: 'Nhân viên', password: '', department_id: '' });
    const [showPass, setShowPass] = useState(false);
    const [saving, setSaving] = useState(false);
    const [departments, setDepartments] = useState([]);

    useEffect(() => {
        fetch(`${API_BASE}/auth/departments`)
            .then(r => r.ok ? r.json() : [])
            .then(setDepartments)
            .catch(() => {});
    }, []);

    useEffect(() => {
        if (editUser) {
            setForm({
                name: editUser.name,
                email: editUser.email,
                role: editUser.role,
                password: '',
                department_id: editUser.department_id || '',
            });
        } else {
            setForm({ name: '', email: '', role: 'Nhân viên', password: '', department_id: '' });
        }
    }, [editUser, open]);

    if (!open) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (form.name.trim().length < 2) {
            alert('Tên phải có ít nhất 2 ký tự');
            return;
        }
        if (!form.department_id) {
            alert('Vui lòng chọn phòng ban');
            return;
        }
        if (!editUser && form.password && form.password.length < 6) {
            alert('Mật khẩu phải có ít nhất 6 ký tự');
            return;
        }
        if (editUser && form.password && form.password.length < 6) {
            alert('Mật khẩu phải có ít nhất 6 ký tự');
            return;
        }

        setSaving(true);
        const payload = { ...form };
        payload.department_id = parseInt(payload.department_id);
        
        await onSave(payload);
        setSaving(false);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
            <div className="relative bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-md mx-4 shadow-2xl border border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-primary-600/10 flex items-center justify-center">
                            <UserPlus className="w-4 h-4 text-primary-700 dark:text-primary-400" />
                        </div>
                        <h3 className="text-base font-bold text-slate-900 dark:text-white">
                            {editUser ? 'Chỉnh sửa người dùng' : 'Thêm người dùng mới'}
                        </h3>
                    </div>
                    <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Họ và Tên</label>
                        <input
                            required
                            value={form.name}
                            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                            placeholder="Nguyễn Văn A"
                            className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 transition-all"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Email</label>
                        <input
                            required
                            type="email"
                            value={form.email}
                            onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                            placeholder="nguyen@congty.vn"
                            className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 transition-all"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Vai trò</label>
                            <select
                                value={form.role}
                                onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
                                className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 transition-all appearance-none cursor-pointer"
                            >
                                {ROLES.filter(r => r !== 'Tất cả').map(r => <option key={r} value={r}>{r}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Phòng ban</label>
                            <select
                                value={form.department_id}
                                onChange={e => setForm(f => ({ ...f, department_id: e.target.value }))}
                                className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 transition-all appearance-none cursor-pointer"
                                required
                            >
                                <option value="">-- Chọn phòng ban * --</option>
                                {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                            </select>
                        </div>
                    </div>
                    {!editUser && (
                        <div>
                            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Mật khẩu</label>
                            <div className="relative">
                                <input
                                    type={showPass ? 'text' : 'password'}
                                    value={form.password}
                                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                                    placeholder="Để trống nếu dùng mặc định"
                                    className="w-full px-3 py-2.5 pr-10 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder-slate-400 outline-none focus:ring-2 focus:ring-primary-600/30 focus:border-primary-600 transition-all"
                                />
                                <button type="button" onClick={() => setShowPass(s => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                                    {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>
                    )}

                    <div className="flex gap-3 pt-2">
                        <button type="button" onClick={onClose} className="flex-1 py-2.5 rounded-lg border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                            Hủy
                        </button>
                        <button type="submit" disabled={saving} className="flex-1 py-2.5 rounded-lg bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                            {saving && <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
                            {editUser ? 'Lưu thay đổi' : 'Thêm người dùng'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
