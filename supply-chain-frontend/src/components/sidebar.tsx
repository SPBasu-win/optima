'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Database, 
  TrendingUp, 
  Truck, 
  FileText,
  Upload,
  HelpCircle,
  Settings,
  User
} from 'lucide-react';

const navigation = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Data Management', href: '/data-management', icon: Database },
  { name: 'Data Import', href: '/data-import', icon: Upload },
  { name: 'Demand Forecasting', href: '/demand-forecasting', icon: TrendingUp },
  { name: 'Logistics Optimization', href: '/logistics', icon: Truck },
  { name: 'Document Digitization', href: '/documents', icon: FileText },
];

const bottomNavigation = [
  { name: 'Help and Support', href: '/help', icon: HelpCircle },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col h-full bg-[#1a1a1a] w-64 fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="px-6 py-6">
        <Link href="/" className="flex flex-col">
          <h1 className="text-2xl font-bold text-orange-500 mb-1">Optima</h1>
          <p className="text-sm text-gray-400">AI Supply Chain</p>
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-4 py-4">
        <ul className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || 
              (item.href !== '/' && pathname.startsWith(item.href));
            
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-orange-500/10 text-orange-500 border-r-2 border-orange-500'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Bottom Navigation */}
      <nav className="px-4 py-4 border-t border-gray-700">
        <ul className="space-y-2 mb-4">
          {bottomNavigation.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-orange-500/10 text-orange-500'
                      : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-3" />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>

        {/* User Profile */}
        <div className="flex items-center px-4 py-3 bg-gray-800 rounded-lg">
          <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center mr-3">
            <span className="text-sm font-bold text-black">J</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">John Doe</p>
            <p className="text-xs text-gray-400 truncate">Admin</p>
          </div>
        </div>
      </nav>
    </div>
  );
}
