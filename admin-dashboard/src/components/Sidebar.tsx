'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3, BadgePercent, Boxes, LayoutDashboard,
  Megaphone, MessageSquare, Tags, Users, Building2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const nav = [
  { href: '/',              icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/inventory',     icon: Boxes,           label: 'Inventory' },
  { href: '/categories',    icon: Tags,            label: 'Categories' },
  { href: '/brands',        icon: Building2,       label: 'Brands' },
  { href: '/conversations', icon: MessageSquare,   label: 'Live Inbox' },
  { href: '/customers',     icon: Users,           label: 'Customers' },
  { href: '/discounts',     icon: BadgePercent,    label: 'Discounts' },
  { href: '/broadcasts',    icon: Megaphone,       label: 'Broadcasts' },
  { href: '/analytics',     icon: BarChart3,       label: 'Analytics' },
];

export default function Sidebar() {
  const path = usePathname();

  return (
    <aside className="flex flex-col w-60 min-h-screen border-r bg-card shrink-0">
      <div className="flex items-center gap-2 px-6 py-5 border-b">
        <span className="text-2xl">📱</span>
        <span className="font-bold text-sm leading-tight">
          WhatsApp<br />
          <span className="text-primary">Shop Admin</span>
        </span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, icon: Icon, label }) => {
          const active = href === '/' ? path === '/' : path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                active
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground',
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 py-4 border-t">
        <p className="text-xs text-muted-foreground">WhatsApp AI Automation</p>
      </div>
    </aside>
  );
}
