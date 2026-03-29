import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';
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
import DashboardLayout from './layouts/DashboardLayout';

function ProtectedRoute() {
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-gray-950">
                <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

function PublicOnlyRoute() {
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-gray-950">
                <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

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

            {/* Protected: redirect to /login if not authenticated */}
            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/documents/:id" element={<DocumentView />} />
                <Route path="/chat" element={<ChatAssistant />} />
                <Route path="/expert" element={<Expert />} />
                <Route path="/knowledge" element={<Knowledge />} />
                <Route path="/graph-knowledge" element={<GraphKnowledge />} />
                <Route path="/admin" element={<Admin />} />
                <Route path="/departments" element={<Departments />} />
                <Route path="/approvals" element={<Approvals />} />
                <Route path="/processing-status" element={<ProcessingStatus />} />
              </Route>
            </Route>
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
