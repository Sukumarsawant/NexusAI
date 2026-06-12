import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Database, MessageSquare, Activity, Award } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/knowledge', label: 'Knowledge Base', icon: Database },
    { to: '/chat', label: 'AI Chat', icon: MessageSquare },
    { to: '/observability', label: 'Observability', icon: Activity },
    { to: '/evaluation', label: 'Evaluation', icon: Award },
  ];

  return (
    <aside className="w-64 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between p-4 transition-colors">
      <div className="space-y-1">
        <div className="px-3 py-2 text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
          Platform
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300 border border-brand-200/50 dark:border-brand-800/50'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/50'
                }`
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </div>

      <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-800 text-xs text-slate-500 dark:text-slate-400 space-y-1.5">
        <div className="font-medium text-slate-700 dark:text-slate-300">Architecture</div>
        <div>LangGraph Multi-Agent</div>
        <div>pgvector Hybrid Search</div>
        <div>Google GenAI SDK (3.8)</div>
      </div>
    </aside>
  );
};
