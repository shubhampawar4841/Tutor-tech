'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
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

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
      <div className="flex-1 flex flex-col min-h-0 bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800">
        <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
          <div className="flex items-center flex-shrink-0 px-4">
            <Link href="/" className="text-xl font-bold text-blue-600 dark:text-blue-400">
              DeepTutor
            </Link>
          </div>
          <nav className="mt-5 flex-1 px-2 space-y-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
                    isActive
                      ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400'
                      : 'text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-50'
                  }`}
                >
                  <Icon
                    className={`mr-3 flex-shrink-0 h-5 w-5 ${
                      isActive
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-zinc-400 group-hover:text-zinc-500 dark:group-hover:text-zinc-300'
                    }`}
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
}







