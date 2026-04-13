import React from 'react';
import { Activity } from 'lucide-react';

export default function AnalyticsPage() {
  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-4xl font-bold tracking-tight">Analytics</h1>
        <p className="text-foreground/40 mt-2">Detailed performance tracking and call volume trends.</p>
      </header>

      <section className="glass-card rounded-3xl p-20 flex flex-col items-center justify-center text-center">
        <div className="w-20 h-20 rounded-full bg-brand/10 text-brand-light flex items-center justify-center mb-6">
          <Activity size={40} />
        </div>
        <h3 className="text-2xl font-bold">Chart engine coming soon</h3>
        <p className="text-foreground/40 max-w-md mt-2">
          We are currently integrating the data visualization layer to show you real-time call volume and AI accuracy trends.
        </p>
      </section>
    </div>
  );
}
