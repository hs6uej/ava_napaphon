import React from 'react';
export const dynamic = 'force-dynamic';
import { 
  PhoneCall, 
  Clock, 
  BarChart3, 
  TrendingUp,
  Activity
} from 'lucide-react';
import { tenantQuery } from '../../lib/db';
import { formatDuration, formatDate, cn } from '../../lib/utils';
// import { auth } from '@/lib/auth'; // In production, we would use auth() to get the tenantId

async function getStats(tenantId: string) {
  // Mocking stats fetching for the demonstration
  // In production: SELECT COUNT(*) as total, AVG(duration) as avg_dur FROM call_records WHERE tenant_id = $1
  const res = await tenantQuery(tenantId, "SELECT COUNT(*) as count FROM call_records");
  const totalCalls = res.rows[0]?.count || 0;
  
  return {
    totalCalls,
    avgDuration: "2m 15s",
    apiSuccess: "98.2%",
    activePrompts: 3
  };
}

async function getRecentCalls(tenantId: string) {
  const res = await tenantQuery(
    tenantId, 
    "SELECT id, caller_number, start_time, duration_seconds, outcome FROM call_records ORDER BY start_time DESC LIMIT 5"
  );
  return res.rows;
}

export default async function OverviewPage() {
  const tenantId = "tenant-uuid-abc-123"; // Mocked tenant ID for now
  const stats = await getStats(tenantId);
  const recentCalls = await getRecentCalls(tenantId);

  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-4xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-foreground/40 mt-2">Welcome back. Here's what's happening with your Voice AI.</p>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="stat-card">
          <div className="text-brand-light mb-4"><PhoneCall size={28} /></div>
          <div className="text-sm font-semibold text-foreground/40 uppercase tracking-wider">Total Calls</div>
          <div className="text-3xl font-bold mt-1">{stats.totalCalls}</div>
          <div className="flex items-center gap-1 text-emerald-400 text-xs mt-3">
            <TrendingUp size={14} /> <span>+12.5% vs last week</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="text-accent-purple mb-4"><Clock size={28} /></div>
          <div className="text-sm font-semibold text-foreground/40 uppercase tracking-wider">Avg. Duration</div>
          <div className="text-3xl font-bold mt-1">{stats.avgDuration}</div>
          <div className="text-foreground/20 text-xs mt-3">Consistent with yesterday</div>
        </div>

        <div className="stat-card">
          <div className="text-accent-blue mb-4"><BarChart3 size={28} /></div>
          <div className="text-sm font-semibold text-foreground/40 uppercase tracking-wider">AI Success Rate</div>
          <div className="text-3xl font-bold mt-1">{stats.apiSuccess}</div>
          <div className="flex items-center gap-1 text-emerald-400 text-xs mt-3">
            <TrendingUp size={14} /> <span>Optimal Performance</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="text-brand-light mb-4"><Activity size={28} /></div>
          <div className="text-sm font-semibold text-foreground/40 uppercase tracking-wider">Active Prompts</div>
          <div className="text-3xl font-bold mt-1">{stats.activePrompts}</div>
          <div className="text-foreground/20 text-xs mt-3">Across all DIDs</div>
        </div>
      </div>

      {/* Recent Activity */}
      <section className="glass-card rounded-3xl p-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold">Recent Activity</h2>
          <button className="text-brand-light text-sm font-semibold hover:underline transition-all">View all calls</button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/5 text-foreground/40 text-sm font-medium">
                <th className="pb-4 font-semibold uppercase tracking-wider">Caller</th>
                <th className="pb-4 font-semibold uppercase tracking-wider">Date & Time</th>
                <th className="pb-4 font-semibold uppercase tracking-wider">Duration</th>
                <th className="pb-4 font-semibold uppercase tracking-wider">Status</th>
                <th className="pb-4 text-right"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {recentCalls.map((call) => (
                <tr key={call.id} className="group hover:bg-white/5 transition-all">
                  <td className="py-5 font-semibold">{call.caller_number}</td>
                  <td className="py-5 text-foreground/60">{formatDate(call.start_time)}</td>
                  <td className="py-5 text-foreground/60">{formatDuration(call.duration_seconds)}</td>
                  <td className="py-5">
                    <span className={cn(
                      "px-3 py-1 rounded-full text-xs font-bold uppercase tracking-tighter",
                      call.outcome === 'completed' ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"
                    )}>
                      {call.outcome}
                    </span>
                  </td>
                  <td className="py-5 text-right">
                    <button className="opacity-0 group-hover:opacity-100 px-4 py-2 rounded-lg bg-white/5 text-xs font-bold transition-all border border-white/10">DETAILS</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
