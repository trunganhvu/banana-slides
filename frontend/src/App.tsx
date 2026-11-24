import { useEffect, useState } from 'react';
import { BrowserRouter, HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Home } from './pages/Home';
import { Landing } from './pages/Landing';
import { History } from './pages/History';
import { OutlineEditor } from './pages/OutlineEditor';
import { DetailEditor } from './pages/DetailEditor';
import { TemplateSetupPage } from './pages/TemplateSetupPage';
import { SlidePreview } from './pages/SlidePreview';
import { SettingsPage } from './pages/Settings';
import { AdminDashboard } from './pages/AdminDashboard';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginModal } from './components/shared/LoginModal';
import { useProjectStore } from './store/useProjectStore';
import { useToast, AccessCodeGuard, DesktopTitleBar, UpdateChecker, ApiKeyReminderModal } from './components/shared';
import { getDesktopTopInset } from './components/shared/UpdateChecker';
import { useT } from './hooks/useT';
import { isDesktop } from '@/utils';

const appI18n = {
  zh: {
    loading: 'Đang tải dữ liệu...',
  },
  en: {
    loading: 'Loading...',
  },
};

function LoadingScreen() {
  const t = useT(appI18n);
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0c0f17]">
      <div className="flex flex-col items-center gap-3">
        <div className="w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-semibold text-slate-600 dark:text-slate-400">{t('loading')}</span>
      </div>
    </div>
  );
}

function SessionSyncIndicator() {
  const { user, isSyncingSession } = useAuth();
  const t = useT(appI18n);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!user || !isSyncingSession) {
      setVisible(false);
      return;
    }
    const timer = window.setTimeout(() => {
      setVisible(true);
    }, 400);
    return () => window.clearTimeout(timer);
  }, [user, isSyncingSession]);

  if (!visible) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed top-4 left-1/2 -translate-x-1/2 z-50 pointer-events-none flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/95 dark:bg-slate-900/95 backdrop-blur-md shadow-md border border-slate-200 dark:border-slate-700/80 text-xs font-medium text-slate-700 dark:text-slate-200"
    >
      <span className="w-3.5 h-3.5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin" />
      <span>{t('loading')}</span>
    </div>
  );
}

function RootRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return user ? <Home /> : <Landing />;
}

function PublicLandingRoute() {
  const { user } = useAuth();
  if (user) {
    return <Navigate to="/" replace />;
  }
  return <Landing />;
}

function ProtectedRoute({ children, adminOnly = false }: { children: React.ReactNode; adminOnly?: boolean }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  if (adminOnly && !user.is_admin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  const { user } = useAuth();
  const { currentProject, syncProject, error, setError } = useProjectStore();
  const { show, ToastContainer } = useToast();

  // Restore project state only when authenticated
  useEffect(() => {
    const savedProjectId = localStorage.getItem('currentProjectId');
    if (user && savedProjectId && !currentProject) {
      syncProject();
    }
  }, [user, currentProject, syncProject]);

  // Show global error
  useEffect(() => {
    if (error) {
      show({ message: error, type: 'error' });
      setError(null);
    }
  }, [error, setError, show]);

  const Router = isDesktop ? HashRouter : BrowserRouter;

  return (
    <Router>
      <DesktopTitleBar />
      <Routes>
        <Route path="/" element={<RootRoute />} />
        <Route path="/landing" element={<PublicLandingRoute />} />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute adminOnly>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/project/:projectId/outline"
          element={
            <ProtectedRoute>
              <OutlineEditor />
            </ProtectedRoute>
          }
        />
        <Route
          path="/project/:projectId/detail"
          element={
            <ProtectedRoute>
              <DetailEditor />
            </ProtectedRoute>
          }
        />
        <Route
          path="/project/:projectId/template-setup"
          element={
            <ProtectedRoute>
              <TemplateSetupPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/project/:projectId/preview"
          element={
            <ProtectedRoute>
              <SlidePreview />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ApiKeyReminderModal />
      <LoginModal />
      <SessionSyncIndicator />
      <ToastContainer />
    </Router>
  );
}

function App() {
  return (
    <AuthProvider>
      <UpdateChecker />
      <div style={isDesktop ? { paddingTop: `${getDesktopTopInset()}px` } : undefined}>
        <AccessCodeGuard>
          <AppRoutes />
        </AccessCodeGuard>
      </div>
    </AuthProvider>
  );
}

export default App;
