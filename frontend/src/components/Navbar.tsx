import React from 'react';
import { Bot, Sun, Moon, LogOut, CheckCircle2, AlertTriangle } from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  user: User | null;
  onLogout: () => void;
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  systemReady?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onLogout,
  darkMode,
  setDarkMode,
  systemReady = true,
}) => {
  return (
    <header className="h-16 border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-30 transition-colors">
      <div className="flex items-center space-x-3">
        <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white shadow-sm">
          <Bot className="h-5 w-5" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
              Nexus<span className="text-brand-500">AI</span>
            </span>
            <span className="text-xs px-2 py-0.5 rounded-full font-medium bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300 border border-brand-200 dark:border-brand-800">
              Enterprise RAG
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {/* System Status Pill */}
        <div className="hidden sm:flex items-center space-x-1.5 text-xs px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
          {systemReady ? (
            <>
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              <span>Multi-Agent Engine Active</span>
            </>
          ) : (
            <>
              <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
              <span>Degraded Engine</span>
            </>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        {/* User Info & Logout */}
        {user && (
          <div className="flex items-center space-x-3 pl-3 border-l border-slate-200 dark:border-slate-800">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-medium text-slate-800 dark:text-slate-200">
                {user.full_name || user.email.split('@')[0]}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                {user.email}
              </div>
            </div>
            <button
              onClick={onLogout}
              className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
