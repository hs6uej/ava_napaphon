import React from 'react';
export const dynamic = 'force-dynamic';
import { Search, Filter, PhoneIncoming, PhoneOutgoing, MoreVertical, Download, PhoneCall } from 'lucide-react';
import { tenantQuery } from '../../lib/db';
import { formatDuration, formatDate, cn } from '../../lib/utils';

async function getCalls(tenantId: string) {
  const res = await tenantQuery(
    tenantId, 
    "SELECT id, caller_number, start_time, duration_seconds, outcome, is_outbound FROM call_records ORDER BY start_time DESC"
  );
  return res.rows;
}

export default async function CallsPage() {
  const tenantId = "tenant-uuid-abc-123";
  const calls = await getCalls(tenantId);

  return (
    <div className="space-y-10">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Call History</h1>
          <p className="text-foreground/40 mt-2">Browse and analyze all interactions between the AI and your customers.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-6 py-3 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-all font-semibold text-sm">
            <Download size={18} />
            EXPORT CSV
          </button>
        </div>
      </header>

      {/* Filters & Search */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-foreground/20" size={20} />
          <input 
            type="text" 
            placeholder="Search by phone number..." 
            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-brand/50 transition-all placeholder:text-foreground/20"
          />
        </div>
        <button className="flex items-center gap-2 px-6 py-4 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-all font-semibold">
          <Filter size={20} />
          FILTERS
        </button>
      </div>

      <section className="glass-card rounded-3xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-white/[0.02] border-b border-white/5 text-foreground/40 text-sm font-medium">
                <th className="px-8 py-5 font-semibold uppercase tracking-wider">Direction</th>
                <th className="px-8 py-5 font-semibold uppercase tracking-wider">Caller Number</th>
                <th className="px-8 py-5 font-semibold uppercase tracking-wider">Timestamp</th>
                <th className="px-8 py-5 font-semibold uppercase tracking-wider">Duration</th>
                <th className="px-8 py-5 font-semibold uppercase tracking-wider">Outcome</th>
                <th className="px-8 py-5 text-right font-semibold uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {calls.map((call) => (
                <tr key={call.id} className="group hover:bg-white/5 transition-all">
                  <td className="px-8 py-6">
                    {call.is_outbound ? (
                      <div className="flex items-center gap-2 text-brand-light">
                        <PhoneOutgoing size={18} />
                        <span className="text-xs font-bold uppercase">Outbound</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 text-accent-purple">
                        <PhoneIncoming size={18} />
                        <span className="text-xs font-bold uppercase">Inbound</span>
                      </div>
                    )}
                  </td>
                  <td className="px-8 py-6 font-semibold">{call.caller_number}</td>
                  <td className="px-8 py-6 text-foreground/60">{formatDate(call.start_time)}</td>
                  <td className="px-8 py-6 text-foreground/60">{formatDuration(call.duration_seconds)}</td>
                  <td className="px-8 py-6">
                    <span className={cn(
                      "px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest",
                      call.outcome === 'completed' ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"
                    )}>
                      {call.outcome}
                    </span>
                  </td>
                  <td className="px-8 py-6 text-right">
                    <button className="p-2 rounded-lg hover:bg-white/10 transition-all text-foreground/40 hover:text-foreground">
                      <MoreVertical size={20} />
                    </button>
                  </td>
                </tr>
              ))}
              {calls.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-8 py-20 text-center">
                    <div className="flex flex-col items-center gap-3 text-foreground/20">
                      <PhoneCall size={48} />
                      <span className="text-xl font-medium">No call logs found.</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
