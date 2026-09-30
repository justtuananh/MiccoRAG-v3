import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './context/authContextCore';
import { isAdminRole, isPrivilegedRole } from './utils/roles';
import Landing from './pages/Landing';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import Documents from './pages/Documents';
import DocumentView from './pages/DocumentView';
import ChatAssistant from './pages/ChatAssistant';
import Expert from './pages/Expert';
import Admin from './pages/Admin';
import Knowledge from './pages/Knowledge';
import GraphKnowledge from './pages/GraphKnowledge';
import Departments from './pages/Departments';
import Approvals from './pages/Approvals';
import ProcessingStatus from './pages/ProcessingStatus';
import WorkspaceManagement from './pages/WorkspaceManagement';
import DashboardLayout from './layouts/DashboardLayout';

const LoadingSpinner = () => (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-gray-950">
        <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
    </div>
);

// Dev-only bypass flag (mirrors AuthContext.jsx) — dùng để không ép logout sai trong chế độ dev-skip
const SKIP_AUTH = import.meta.env.VITE_SKIP_AUTH === 'true';

function ProtectedRoute() {
    const { isAuthenticated, loading, logout } = useAuth();

    // Chống rò rỉ dữ liệu qua back-forward cache (bfcache): nếu trang /dashboard (hoặc
    // route bảo vệ khác) được khôi phục nguyên trạng từ bfcache sau khi đã đăng xuất,
    // state React trong bộ nhớ (isAuthenticated=true, user=...) vẫn là state CŨ trước
    // lúc đăng xuất. Phải kiểm tra lại token thật trong localStorage (không phải state)
    // ngay khi trang được khôi phục, và đăng xuất lại nếu token đã bị xoá.
    useEffect(() => {
        const handlePageShow = (e) => {
            if (!e.persisted) return; // chỉ xử lý khi trang đến từ bfcache
            const hasToken = !!localStorage.getItem('docvault_token');
            if (!hasToken && !SKIP_AUTH) {
                logout();
            }
        };
        window.addEventListener('pageshow', handlePageShow);
        return () => window.removeEventListener('pageshow', handlePageShow);
    }, [logout]);

    if (loading) return <LoadingSpinner />;

    return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

function AdminRoute() {
    const { user, isAuthenticated, loading } = useAuth();

    if (loading) return <LoadingSpinner />;

    if (!isAuthenticated) return <Navigate to="/login" replace />;
    if (!isAdminRole(user?.role)) return <Navigate to="/dashboard" replace />;
    return <Outlet />;
}

function PrivilegedRoute() {
    const { user, isAuthenticated, loading } = useAuth();

    if (loading) return <LoadingSpinner />;

    if (!isAuthenticated) return <Navigate to="/login" replace />;
    if (!isPrivilegedRole(user?.role)) return <Navigate to="/dashboard" replace />;
    return <Outlet />;
}

function PublicOnlyRoute() {
    const { isAuthenticated, loading } = useAuth();

    if (loading) return <LoadingSpinner />;

    return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Outlet />;
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <Routes>
            {/* Root → go to login */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/landing" element={<Landing />} />

            {/* Public-only: redirect to /dashboard if already authenticated */}
            <Route element={<PublicOnlyRoute />}>
              <Route path="/login" element={<AuthPage />} />
              <Route path="/register" element={<AuthPage />} />
            </Route>

            {/* Protected: redirect to /login if not authenticated.
                PrivilegedRoute và AdminRoute được lồng BÊN TRONG ProtectedRoute (không phải
                route anh em) để lớp chống rò rỉ dữ liệu qua bfcache (pageshow listener trong
                ProtectedRoute) áp dụng cho MỌI trang cần đăng nhập, kể cả /admin, /departments,
                /approvals, /graph-knowledge — về ngữ nghĩa cũng đúng hơn vì trang quản trị
                đương nhiên cũng là trang cần đăng nhập. */}
            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/documents/:id" element={<DocumentView />} />
                <Route path="/chat" element={<ChatAssistant />} />
                <Route path="/expert" element={<Expert />} />
                <Route path="/knowledge" element={<Knowledge />} />
                <Route path="/workspaces" element={<WorkspaceManagement />} />
                <Route path="/processing-status" element={<ProcessingStatus />} />
              </Route>

              {/* Privileged approval workflow. */}
              <Route element={<PrivilegedRoute />}>
                <Route element={<DashboardLayout />}>
                  <Route path="/approvals" element={<Approvals />} />
                </Route>
              </Route>

              {/* Admin-only: redirect to /dashboard if not Admin */}
              <Route element={<AdminRoute />}>
                <Route element={<DashboardLayout />}>
                  <Route path="/admin" element={<Admin />} />
                  <Route path="/departments" element={<Departments />} />
                  <Route path="/graph-knowledge" element={<GraphKnowledge />} />
                </Route>
              </Route>
            </Route>
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
