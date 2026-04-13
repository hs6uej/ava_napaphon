import { redirect } from 'next/navigation';

export default function RootPage() {
  // Automatically redirect the base URL to the Dashboard Overview
  redirect('/overview');
}
