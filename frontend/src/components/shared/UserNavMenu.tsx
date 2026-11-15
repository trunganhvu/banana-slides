import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { LogIn, LogOut, ShieldCheck, User as UserIcon, ChevronDown } from 'lucide-react';

export const UserNavMenu: React.FC = () => {
  const { user, logout, openLoginModal } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!user) {
    return (
      <button
        onClick={openLoginModal}
        className="flex items-center gap-2 px-3.5 py-1.5 text-sm font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 dark:bg-amber-950/40 dark:text-amber-300 dark:hover:bg-amber-900/50 rounded-xl border border-amber-200/60 dark:border-amber-800/50 transition-colors shadow-sm"
      >
        <LogIn className="w-4 h-4" />
        <span>Đăng nhập</span>
      </button>
    );
  }

  const isAdmin = user.role === 'admin';

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1 pl-2 pr-2.5 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors border border-gray-200/60 dark:border-zinc-700/60"
      >
        {user.avatar ? (
          <img
            src={user.avatar}
            alt={user.name}
            className="w-7 h-7 rounded-full object-cover border border-amber-400"
          />
        ) : (
          <div className="w-7 h-7 rounded-full bg-amber-500 text-white flex items-center justify-center font-bold text-xs">
            {user.name?.charAt(0)?.toUpperCase() || 'U'}
          </div>
        )}
        <span className="text-sm font-medium text-gray-800 dark:text-gray-200 max-w-[110px] truncate">
          {user.name}
        </span>
        {isAdmin && (
          <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-md bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-200">
            Admin
          </span>
        )}
        <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-white dark:bg-zinc-900 shadow-xl border border-gray-100 dark:border-zinc-800 py-1.5 z-50 animate-in fade-in zoom-in-95 duration-100">
          <div className="px-3.5 py-2.5 border-b border-gray-100 dark:border-zinc-800">
            <p className="text-xs font-semibold text-gray-900 dark:text-white truncate">
              {user.name}
            </p>
            <p className="text-xs text-gray-400 truncate">
              {user.email}
            </p>
          </div>

          {isAdmin && (
            <button
              onClick={() => {
                setIsOpen(false);
                navigate('/admin');
              }}
              className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:text-gray-200 dark:hover:bg-zinc-800/80 transition-colors"
            >
              <ShieldCheck className="w-4 h-4 text-amber-500" />
              <span>Quản trị hệ thống (Admin)</span>
            </button>
          )}

          <button
            onClick={() => {
              setIsOpen(false);
              logout();
            }}
            className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs font-medium text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Đăng xuất</span>
          </button>
        </div>
      )}
    </div>
  );
};
