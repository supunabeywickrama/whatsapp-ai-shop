import Link from 'next/link';
import {
  Boxes, Tags, MessageSquare, Megaphone, Users, BadgePercent, BarChart3,
} from 'lucide-react';

const tiles = [
  { href: '/inventory',     icon: Boxes,        title: 'Inventory',     desc: 'Add, edit, delete products' },
  { href: '/categories',    icon: Tags,         title: 'Categories',    desc: 'Tree of categories & brands' },
  { href: '/conversations', icon: MessageSquare,title: 'Live Inbox',    desc: 'Take over from the AI' },
  { href: '/customers',     icon: Users,        title: 'Customers',     desc: 'Profiles & chat history' },
  { href: '/discounts',     icon: BadgePercent, title: 'Discounts',     desc: 'Codes & campaigns' },
  { href: '/broadcasts',    icon: Megaphone,    title: 'Broadcasts',    desc: 'Scheduled WhatsApp blasts' },
  { href: '/analytics',     icon: BarChart3,    title: 'Analytics',     desc: 'Volume, funnel, AI cost' },
];

export default function Home() {
  return (
    <main className="container py-12">
      <header className="mb-10">
        <h1 className="text-4xl font-bold tracking-tight">
          WhatsApp Shop <span className="text-primary">Admin</span>
        </h1>
        <p className="text-muted-foreground mt-2">
          End-to-end command center for the AI sales agent.
        </p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map(({ href, icon: Icon, title, desc }) => (
          <Link
            key={href}
            href={href}
            className="group rounded-2xl border bg-card p-6 shadow-sm transition hover:shadow-lg hover:border-primary"
          >
            <Icon className="mb-4 h-8 w-8 text-primary transition group-hover:scale-110" />
            <h2 className="text-xl font-semibold">{title}</h2>
            <p className="text-sm text-muted-foreground mt-1">{desc}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
