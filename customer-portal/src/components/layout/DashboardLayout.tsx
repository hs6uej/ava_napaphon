"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  PhoneCall, 
  Settings, 
  LogOut, 
  User,
  Activity
} from 'lucide-react';
import { cn } from '@/lib/utils';

const sidebarItems = [
  { name: 'Overview', href: '/overview', icon: LayoutDashboard },
  { name: 'Call History', href: '/calls', icon: PhoneCall },
  { name: 'AI Settings', href: '/settings', icon: Settings },
  { name: 'Analytics', href: '/analytics', icon: Activity },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside className="w-72 border-r border-border bg-card/10 backdrop-blur-2xl flex flex-col p-6 z-20">
        <div className="flex items-center gap-3 mb-12 px-2">
          <div className="w-10 h-10 rounded-xl bg-brand flex items-center justify-center shadow-lg shadow-brand/20">
            <Activity className="text-white" size={24} />
          </div>
          <span className="text-xl font-bold tracking-tight">AVA <span className="text-brand-light">Portal</span></span>
        </div>

        <nav className="flex-1 space-y-2">
          {sidebarItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "sidebar-link",
                  isActive && "active"
                )}
              >
                <item.icon size={20} />
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-4">
          <div className="p-4 rounded-2xl bg-white/5 border border-white/5 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand to-accent-purple p-[2px]">
              <div className="w-full h-full rounded-full bg-background flex items-center justify-center overflow-hidden">
                <User size={20} />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold truncate max-w-[140px]">Customer Name</span>
              <span className="text-xs text-foreground/40">Tenant Support</span>
            </div>
          </div>
          
          <button className="w-full sidebar-link text-red-400 hover:bg-red-500/10 hover:text-red-300">
            <LogOut size={20} />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto scroll-smooth">
        <div className="fixed top-0 left-72 right-0 h-64 bg-gradient-to-b from-brand/5 to-transparent pointer-events-none -z-10" />
        <div className="p-10 page-fade-in relative">
          {children}
        </div>
      </main>
    </div>
  );
}
