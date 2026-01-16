'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import {
  BookOpen,
  Brain,
  HelpCircle,
  Search,
  Notebook,
  GraduationCap,
  PenTool,
  MessageSquare,
  LayoutDashboard,
  Lightbulb,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Knowledge Base', href: '/knowledge-base', icon: BookOpen },
  { name: 'Solve', href: '/solve', icon: Brain },
  { name: 'Questions', href: '/questions', icon: HelpCircle },
  { name: 'Research', href: '/research', icon: Search },
  { name: 'Notebook', href: '/notebook', icon: Notebook },
  { name: 'Guided Learning', href: '/guide', icon: GraduationCap },
  { name: 'Co-Writer', href: '/co-writer', icon: PenTool },
  { name: 'IdeaGen', href: '/ideagen', icon: Lightbulb },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
];

export default function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="md:hidden">
      <div className="flex items-center justify-between h-16 px-4 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800">
        <Link href="/" className="text-xl font-bold text-blue-600 dark:text-blue-400">
          DeepTutor
        </Link>
        <button
          onClick={() => setOpen(!open)}
          className="text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-50"
        >
          {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>
      {open && (
        <div className="bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800">
          <nav className="px-2 pt-2 pb-3 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setOpen(false)}
                  className={`flex items-center px-3 py-2 text-base font-medium rounded-md ${
                    isActive
                      ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400'
                      : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-50'
                  }`}
                >
                  <Icon className="mr-3 h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      )}
    </div>
  );
}







