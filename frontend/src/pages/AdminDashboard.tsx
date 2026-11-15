import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { apiClient } from '@/api/client';
import {
  Users,
  LogIn,
  Sparkles,
  Cpu,
  FolderOpen,
  ArrowLeft,
  RefreshCw,
  Search,
  ShieldCheck,
  ShieldAlert,
  Clock
} from 'lucide-react';
import { Card, Button, useToast } from '@/components/shared';

interface AdminStats {
  total_users: number;
  total_visits: number;
  total_generations: number;
  total_tokens_in: number;
  total_tokens_out: number;
  total_projects: number;
}

interface AdminUserItem {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'user' | 'admin';
  login_count: number;
  generation_count: number;
  tokens_in: number;
  tokens_out: number;
  project_count: number;
  created_at?: string;
  last_login_at?: string;
}

export const AdminDashboard: React.FC = () => {
  const { user, isLoading: authLoading, openLoginModal } = useAuth();
  const navigate = useNavigate();
  const { show } = useToast();

  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [statsRes, usersRes] = await Promise.all([
        apiClient.get('/api/admin/stats'),
        apiClient.get('/api/admin/users')
      ]);

      if (statsRes.data?.data) {
        setStats(statsRes.data.data);
      }
      if (usersRes.data?.data?.users) {
        setUsers(usersRes.data.data.users);
      }
    } catch (err: any) {
      console.error('Failed to load admin data:', err);
      show({
        message: err.response?.data?.error || 'Không thể tải dữ liệu quản trị viên',
        type: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && user?.role === 'admin') {
      fetchData();
    }
  }, [authLoading, user]);

  const filteredUsers = useMemo(() => {
    if (!searchTerm.trim()) return users;
    const term = searchTerm.toLowerCase();
    return users.filter(
      u => u.name?.toLowerCase().includes(term) || u.email?.toLowerCase().includes(term)
    );
  }, [users, searchTerm]);

  const formatNumber = (num: number = 0) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toLocaleString();
  };

  const formatDate = (isoStr?: string) => {
    if (!isoStr) return 'Chưa đăng nhập';
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return isoStr;
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-zinc-950 text-gray-500">
        <RefreshCw className="w-6 h-6 animate-spin mr-2" />
        <span>Đang kiểm tra quyền truy cập...</span>
      </div>
    );
  }

  if (!user || user.role !== 'admin') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-zinc-950 px-4">
        <div className="w-16 h-16 rounded-2xl bg-red-100 text-red-600 dark:bg-red-950/50 dark:text-red-400 flex items-center justify-center mb-4">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
          Truy cập bị từ chối
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 text-center max-w-sm">
          Bạn cần đăng nhập bằng tài khoản Quản trị viên (Admin) để xem trang này.
        </p>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={() => navigate('/')}>
            Về trang chủ
          </Button>
          {!user && (
            <Button variant="primary" onClick={openLoginModal}>
              Đăng nhập Admin
            </Button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50/70 dark:bg-zinc-950 text-gray-900 dark:text-gray-100 p-4 sm:p-6 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-gray-200/80 dark:border-zinc-800">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/')}
              className="p-2 rounded-xl text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-zinc-800 transition-colors"
              title="Về trang chủ"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
                  Quản trị hệ thống
                </h1>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  Admin
                </span>
              </div>
              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                Bảng điều khiển theo dõi người dùng, lượt truy cập, lượng sử dụng và token
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={fetchData}
              disabled={isLoading}
              className="flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Làm mới</span>
            </Button>
          </div>
        </div>

        {/* 5 KPI Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
          <div className="bg-white dark:bg-zinc-900 border border-gray-200/80 dark:border-zinc-800/80 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center justify-between text-gray-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Người dùng</span>
              <div className="p-2 bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400 rounded-xl">
                <Users className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : formatNumber(stats?.total_users)}
            </div>
            <div className="text-[11px] text-gray-400 mt-1">Tổng tài khoản</div>
          </div>

          <div className="bg-white dark:bg-zinc-900 border border-gray-200/80 dark:border-zinc-800/80 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center justify-between text-gray-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Lượt truy cập</span>
              <div className="p-2 bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400 rounded-xl">
                <LogIn className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : formatNumber(stats?.total_visits)}
            </div>
            <div className="text-[11px] text-gray-400 mt-1">Số lần đăng nhập</div>
          </div>

          <div className="bg-white dark:bg-zinc-900 border border-gray-200/80 dark:border-zinc-800/80 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center justify-between text-gray-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Lượt sử dụng</span>
              <div className="p-2 bg-purple-50 text-purple-600 dark:bg-purple-950/50 dark:text-purple-400 rounded-xl">
                <Sparkles className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : formatNumber(stats?.total_generations)}
            </div>
            <div className="text-[11px] text-gray-400 mt-1">Lần tạo dàn ý / slide</div>
          </div>

          <div className="bg-white dark:bg-zinc-900 border border-gray-200/80 dark:border-zinc-800/80 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center justify-between text-gray-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Tokens In / Out</span>
              <div className="p-2 bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400 rounded-xl">
                <Cpu className="w-4 h-4" />
              </div>
            </div>
            <div className="text-lg font-bold flex items-baseline gap-1">
              <span>{isLoading ? '...' : formatNumber(stats?.total_tokens_in)}</span>
              <span className="text-xs text-gray-400 font-normal">/</span>
              <span className="text-amber-600 dark:text-amber-400">
                {isLoading ? '...' : formatNumber(stats?.total_tokens_out)}
              </span>
            </div>
            <div className="text-[11px] text-gray-400 mt-1">Input / Output Tokens</div>
          </div>

          <div className="bg-white dark:bg-zinc-900 border border-gray-200/80 dark:border-zinc-800/80 rounded-2xl p-4 shadow-sm col-span-2 sm:col-span-1">
            <div className="flex items-center justify-between text-gray-400 mb-2">
              <span className="text-xs font-medium uppercase tracking-wider">Tổng Project</span>
              <div className="p-2 bg-indigo-50 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-400 rounded-xl">
                <FolderOpen className="w-4 h-4" />
              </div>
            </div>
            <div className="text-2xl font-bold">
              {isLoading ? '...' : formatNumber(stats?.total_projects)}
            </div>
            <div className="text-[11px] text-gray-400 mt-1">Tất cả người dùng</div>
          </div>
        </div>

        {/* User Management Section */}
        <div className="bg-white dark:bg-zinc-900 border border-gray-200/80 dark:border-zinc-800/80 rounded-2xl overflow-hidden shadow-sm">
          <div className="p-4 sm:p-5 border-b border-gray-100 dark:border-zinc-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold">Danh sách người dùng</h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Quản lý và thống kê chi tiết theo từng tài khoản
              </p>
            </div>

            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Tìm theo tên hoặc email..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-gray-200 dark:border-zinc-700 bg-gray-50/50 dark:bg-zinc-800 focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50/60 dark:bg-zinc-800/40 text-gray-500 dark:text-gray-400 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Người dùng</th>
                  <th className="py-3 px-4">Vai trò</th>
                  <th className="py-3 px-4 text-center">Số Project</th>
                  <th className="py-3 px-4 text-center">Lượt tạo</th>
                  <th className="py-3 px-4 text-center">Tokens (In / Out)</th>
                  <th className="py-3 px-4 text-center">Lượt truy cập</th>
                  <th className="py-3 px-4">Đăng nhập cuối</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-gray-400">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
                      <span>Đang tải dữ liệu người dùng...</span>
                    </td>
                  </tr>
                ) : filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-gray-400">
                      Chưa có người dùng nào phù hợp.
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map(u => (
                    <tr
                      key={u.id}
                      className="hover:bg-gray-50/50 dark:hover:bg-zinc-800/30 transition-colors"
                    >
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-3">
                          {u.avatar ? (
                            <img
                              src={u.avatar}
                              alt={u.name}
                              className="w-8 h-8 rounded-full object-cover border border-amber-300 flex-shrink-0"
                            />
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-amber-500/20 text-amber-700 dark:text-amber-300 font-bold flex items-center justify-center flex-shrink-0">
                              {u.name?.charAt(0)?.toUpperCase() || 'U'}
                            </div>
                          )}
                          <div className="min-w-0">
                            <div className="font-medium text-gray-900 dark:text-white truncate">
                              {u.name || 'Người dùng'}
                            </div>
                            <div className="text-[11px] text-gray-400 truncate">{u.email}</div>
                          </div>
                        </div>
                      </td>

                      <td className="py-3.5 px-4">
                        {u.role === 'admin' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                            <ShieldCheck className="w-3 h-3" />
                            Admin
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-700 dark:bg-zinc-800 dark:text-gray-300">
                            Thành viên
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-center">
                        <span className="inline-block px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300">
                          {u.project_count || 0}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-center">
                        <span className="font-semibold text-purple-600 dark:text-purple-400">
                          {u.generation_count || 0}
                        </span>
                      </td>

                      <td className="py-3.5 px-4 text-center">
                        <div className="font-mono text-[11px]">
                          <span className="text-gray-600 dark:text-gray-300">
                            {formatNumber(u.tokens_in)}
                          </span>
                          <span className="text-gray-400 mx-1">/</span>
                          <span className="text-amber-600 dark:text-amber-400 font-semibold">
                            {formatNumber(u.tokens_out)}
                          </span>
                        </div>
                      </td>

                      <td className="py-3.5 px-4 text-center text-gray-600 dark:text-gray-300">
                        {u.login_count || 0}
                      </td>

                      <td className="py-3.5 px-4 text-gray-400 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-gray-300" />
                          <span>{formatDate(u.last_login_at)}</span>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
