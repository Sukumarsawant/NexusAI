import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { KnowledgeBasePage } from './pages/KnowledgeBasePage';
import { ChatPage } from './pages/ChatPage';
import { ObservabilityPage } from './pages/ObservabilityPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { api } from './services/api';
import { User } from './types';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('nexus_token'));
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    return localStorage.getItem('nexus_theme') === 'dark';
  });

  const navigate = useNavigate();

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('nexus_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('nexus_theme', 'light');
    }
  }, [darkMode]);

  useEffect(() => {
    const verifyUser = async () => {
      const storedToken = localStorage.getItem('nexus_token');
      if (!storedToken) {
        setLoading(false);
        return;
      }
      try {
        const u = await api.getMe();
        setUser(u);
      } catch (e) {
        console.warn('Session expired or invalid token');
        localStorage.removeItem('nexus_token');
        setUser(null);
        setToken(null);
      } finally {
        setLoading(false);
      }
    };
    verifyUser();
  }, [token]);

  const handleLoginSuccess = (loggedInUser: User, accessToken: string) => {
    localStorage.setItem('nexus_token', accessToken);
    setUser(loggedInUser);
    setToken(accessToken);
  };

  const handleLogout = () => {
    localStorage.removeItem('nexus_token');
    setUser(null);
    setToken(null);
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center text-slate-500">
        <div className="flex items-center space-x-2 text-sm">
          <div className="h-4 w-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          <span>Initializing NexusAI Enterprise Workspace...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors">
      {token && user ? (
        <>
          <Navbar
            user={user}
            onLogout={handleLogout}
            darkMode={darkMode}
            setDarkMode={setDarkMode}
          />
          <div className="flex-1 flex overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto p-6 lg:p-8 bg-slate-50/50 dark:bg-slate-950/50">
              <div className="max-w-7xl mx-auto">
                <Routes>
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/knowledge" element={<KnowledgeBasePage />} />
                  <Route path="/chat" element={<ChatPage />} />
                  <Route path="/observability" element={<ObservabilityPage />} />
                  <Route path="/evaluation" element={<EvaluationPage />} />
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </div>
            </main>
          </div>
        </>
      ) : (
        <Routes>
          <Route path="/login" element={<LoginPage onLoginSuccess={handleLoginSuccess} />} />
          <Route path="/register" element={<RegisterPage onLoginSuccess={handleLoginSuccess} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      )}
    </div>
  );
};
