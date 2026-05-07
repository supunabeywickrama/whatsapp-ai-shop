import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'WhatsApp Shop Admin',
  description: 'Admin dashboard for the WhatsApp AI Automation System',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
