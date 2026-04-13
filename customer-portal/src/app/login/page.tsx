"use client";

import React from 'react';
import { signIn } from "next-auth/react";
import { Activity, ShieldCheck, Zap, Globe } from 'lucide-react';

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-6 relative overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-brand/10 rounded-full blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent-purple/10 rounded-full blur-[120px]" />

      <div className="max-w-md w-full z-10">
        <div className="text-center mb-10 space-y-4">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-brand/10 border border-brand/20 shadow-2xl shadow-brand/20 mb-4">
            <Activity className="text-brand-light" size={40} />
          </div>
          <h1 className="text-4xl font-black tracking-tighter">
            AVA <span className="text-brand-light">PORTAL</span>
          </h1>
          <p className="text-foreground/40 font-medium">
            AI-Powered Multi-Tenant Voice Platform
          </p>
        </div>

        <div className="glass-card rounded-[40px] p-10 space-y-8">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold">Welcome back</h2>
            <p className="text-sm text-foreground/40">Secure access via corporate SSO authentication.</p>
          </div>

          <div className="grid grid-cols-1 gap-4 py-4">
            <button 
              onClick={() => signIn("azure-ad", { callbackUrl: "/overview" })}
              className="w-full h-16 bg-white text-black hover:bg-white/90 rounded-2xl font-bold flex items-center justify-center gap-4 transition-all active:scale-95 shadow-xl"
            >
              <svg className="w-6 h-6" viewBox="0 0 23 23">
                <path fill="#f3f3f3" d="M0 0h11.5v11.5H0z"/><path fill="#f3f3f3" d="M11.5 0H23v11.5H11.5z"/><path fill="#f3f3f3" d="M0 11.5h11.5V23H0z"/><path fill="#f3f3f3" d="M11.5 11.5H23V23H11.5z"/>
                <path fill="#f25022" d="M1 1h9.5v9.5H1z"/><path fill="#7fbb00" d="M12.5 1h9.5v9.5h-9.5z"/><path fill="#00a1f1" d="M1 12.5h9.5v22H1z" transform="scale(1 .432)"/><path fill="#ffbb00" d="M12.5 12.5h9.5v22h-9.5z" transform="scale(1 .432)"/>
              </svg>
              Sign in with Azure AD
            </button>
          </div>

          <div className="pt-6 border-t border-white/5 space-y-4 text-xs">
            <div className="flex items-center gap-3 text-foreground/40">
              <ShieldCheck size={14} className="text-brand-light" />
              <span>Enterprise-grade data isolation & encryption</span>
            </div>
            <div className="flex items-center gap-3 text-foreground/40">
              <Zap size={14} className="text-accent-purple" />
              <span>Real-time voice AI configuration</span>
            </div>
            <div className="flex items-center gap-3 text-foreground/40">
              <Globe size={14} className="text-accent-blue" />
              <span>Multi-region scale-ready infrastructure</span>
            </div>
          </div>
        </div>

        <p className="mt-8 text-center text-xs text-foreground/20 font-medium tracking-widest uppercase">
          Powered by AntiGravity Voice Agent
        </p>
      </div>
    </div>
  );
}
