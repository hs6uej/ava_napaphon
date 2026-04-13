import React from 'react';
export const dynamic = 'force-dynamic';
import { Save, Bot, MessageSquare, PhoneForwarded } from 'lucide-react';
import { tenantQuery, query } from '@/lib/db';
import { revalidatePath } from 'next/cache';

async function updateSettings(formData: FormData) {
  'use server';
  
  const tenantId = "tenant-uuid-abc-123"; // Mocking from auth session
  const greeting = formData.get('greeting') as string;
  const prompt = formData.get('prompt') as string;
  const transfer = formData.get('transfer') as string;

  await query(
    "UPDATE tenant_settings SET greeting_message = $1, system_prompt = $2, transfer_number = $3, updated_at = NOW() WHERE tenant_id = $4",
    [greeting, prompt, transfer, tenantId]
  );

  revalidatePath('/settings');
}

async function getSettings(tenantId: string) {
  const res = await tenantQuery(tenantId, "SELECT greeting_message, system_prompt, transfer_number FROM tenant_settings");
  return res.rows[0] || { greeting_message: "", system_prompt: "", transfer_number: "" };
}

export default async function SettingsPage() {
  const tenantId = "tenant-uuid-abc-123";
  const settings = await getSettings(tenantId);

  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-4xl font-bold tracking-tight">AI Settings</h1>
        <p className="text-foreground/40 mt-2">Customize how the AI interacts with your customers and where calls are transferred.</p>
      </header>

      <div className="max-w-4xl">
        <form action={updateSettings} className="space-y-8">
          {/* Greeting Section */}
          <section className="glass-card rounded-3xl p-8 space-y-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-2xl bg-brand/10 text-brand-light"><MessageSquare size={24} /></div>
              <div>
                <h3 className="text-xl font-bold">Initial Greeting</h3>
                <p className="text-sm text-foreground/40">The first words the AI says when a call is answered.</p>
              </div>
            </div>
            
            <textarea 
              name="greeting"
              placeholder="e.g. สวัสดีค่ะ ยินดีต้อนรับสู่ร้านค้าของเรา มีอะไรให้ช่วยไหมคะ?"
              defaultValue={settings.greeting_message}
              rows={3}
              className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-lg focus:outline-none focus:ring-2 focus:ring-brand/50 transition-all placeholder:text-foreground/20"
            />
          </section>

          {/* System Prompt Section */}
          <section className="glass-card rounded-3xl p-8 space-y-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-2xl bg-accent-purple/10 text-accent-purple"><Bot size={24} /></div>
              <div>
                <h3 className="text-xl font-bold">AI System Prompt</h3>
                <p className="text-sm text-foreground/40">Define the personality and knowledge base of your AI agent.</p>
              </div>
            </div>
            
            <textarea 
              name="prompt"
              placeholder="You are an expert customer service agent for a Thai restaurant. Your tone is polite and professional..."
              defaultValue={settings.system_prompt}
              rows={8}
              className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-base focus:outline-none focus:ring-2 focus:ring-brand/50 transition-all placeholder:text-foreground/20 font-mono"
            />
          </section>

          {/* Call Routing Section */}
          <section className="glass-card rounded-3xl p-8 space-y-6">
            <div className="flex items-center gap-3">
              <div className="p-3 rounded-2xl bg-amber-500/10 text-amber-500"><PhoneForwarded size={24} /></div>
              <div>
                <h3 className="text-xl font-bold">Transfer Number</h3>
                <p className="text-sm text-foreground/40">Where to route the call when a human agent is requested.</p>
              </div>
            </div>
            
            <input 
              name="transfer"
              type="text"
              placeholder="+66812345678"
              defaultValue={settings.transfer_number}
              className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-lg focus:outline-none focus:ring-2 focus:ring-brand/50 transition-all placeholder:text-foreground/20"
            />
          </section>

          <div className="flex justify-end pt-4">
            <button 
              type="submit"
              className="flex items-center gap-2 px-8 py-4 bg-brand hover:bg-brand-dark text-white rounded-2xl font-bold shadow-xl shadow-brand/20 transition-all active:scale-95 translate-y-0 hover:-translate-y-1"
            >
              <Save size={20} />
              SAVE CONFIGURATION
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
