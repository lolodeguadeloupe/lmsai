'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/button';
import {
  HomeIcon,
  BookOpenIcon,
  PlusIcon,
  ChartBarIcon,
  CogIcon,
  UserIcon,
  Bars3Icon,
  XMarkIcon,
  SparklesIcon,
  AcademicCapIcon,
} from '@heroicons/react/24/outline';
import { useAuthStore } from '@/store/auth';
import { clsx } from 'clsx';

const navigation = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: HomeIcon,
  },
  {
    name: 'Mes Cours',
    href: '/courses',
    icon: BookOpenIcon,
  },
  {
    name: 'Créer un Cours',
    href: '/courses/create',
    icon: PlusIcon,
    highlight: true,
  },
  {
    name: 'Analytiques',
    href: '/analytics',
    icon: ChartBarIcon,
  },
  {
    name: 'Paramètres',
    href: '/settings',
    icon: CogIcon,
  },
];

export default function Navigation() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const { user, signOut } = useAuthStore();

  const isActivePath = (href: string) => {
    if (href === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Desktop Navigation */}
      <nav className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white border-r border-gray-200 px-6 pb-4">
          {/* Logo */}
          <div className="flex h-16 shrink-0 items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <SparklesIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">AI Course</span>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-7">
              <li>
                <ul role="list" className="-mx-2 space-y-1">
                  {navigation.map((item) => (
                    <li key={item.name}>
                      <Link
                        href={item.href}
                        className={clsx(
                          isActivePath(item.href)
                            ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                            : 'text-gray-700 hover:text-blue-700 hover:bg-gray-50',
                          item.highlight && !isActivePath(item.href)
                            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700 hover:text-white'
                            : '',
                          'group flex gap-x-3 rounded-md p-3 text-sm leading-6 font-semibold transition-all duration-200'
                        )}
                      >
                        <item.icon
                          className={clsx(
                            isActivePath(item.href) ? 'text-blue-700' : 'text-gray-400 group-hover:text-blue-700',
                            item.highlight && !isActivePath(item.href) ? 'text-white' : '',
                            'h-5 w-5 shrink-0'
                          )}
                          aria-hidden="true"
                        />
                        {item.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </li>

              {/* User section */}
              <li className="mt-auto">
                <div className="flex items-center gap-x-4 p-3 text-sm font-semibold leading-6 text-gray-900 border-t border-gray-200">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500">
                    <UserIcon className="h-4 w-4 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {user?.name || 'Utilisateur'}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {user?.email || 'Non connecté'}
                    </p>
                  </div>
                </div>
                
                {user && (
                  <div className="mt-2 px-3">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      onClick={signOut}
                    >
                      Se déconnecter
                    </Button>
                  </div>
                )}
              </li>
            </ul>
          </nav>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <div className="lg:hidden">
        {/* Mobile menu button */}
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-700 lg:hidden"
            onClick={() => setIsMobileMenuOpen(true)}
          >
            <span className="sr-only">Open sidebar</span>
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>

          {/* Logo */}
          <div className="flex flex-1 items-center gap-x-4 self-stretch">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <SparklesIcon className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">AI Course</span>
            </Link>
          </div>

          {/* User menu */}
          {user && (
            <div className="flex items-center gap-x-4">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500">
                <UserIcon className="h-4 w-4 text-white" />
              </div>
            </div>
          )}
        </div>

        {/* Mobile menu overlay */}
        {isMobileMenuOpen && (
          <div className="relative z-50 lg:hidden">
            <div className="fixed inset-0 bg-gray-900/80" onClick={() => setIsMobileMenuOpen(false)} />
            
            <div className="fixed inset-0 flex">
              <div className="relative mr-16 flex w-full max-w-xs flex-1">
                <div className="absolute left-full top-0 flex w-16 justify-center pt-5">
                  <button
                    type="button"
                    className="-m-2.5 p-2.5"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <span className="sr-only">Close sidebar</span>
                    <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                  </button>
                </div>

                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4">
                  {/* Logo */}
                  <div className="flex h-16 shrink-0 items-center">
                    <Link 
                      href="/" 
                      className="flex items-center space-x-2"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <SparklesIcon className="w-5 h-5 text-white" />
                      </div>
                      <span className="text-xl font-bold text-gray-900">AI Course</span>
                    </Link>
                  </div>

                  {/* Navigation */}
                  <nav className="flex flex-1 flex-col">
                    <ul role="list" className="flex flex-1 flex-col gap-y-7">
                      <li>
                        <ul role="list" className="-mx-2 space-y-1">
                          {navigation.map((item) => (
                            <li key={item.name}>
                              <Link
                                href={item.href}
                                onClick={() => setIsMobileMenuOpen(false)}
                                className={clsx(
                                  isActivePath(item.href)
                                    ? 'bg-blue-50 text-blue-700'
                                    : 'text-gray-700 hover:text-blue-700 hover:bg-gray-50',
                                  item.highlight && !isActivePath(item.href)
                                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700'
                                    : '',
                                  'group flex gap-x-3 rounded-md p-3 text-sm leading-6 font-semibold'
                                )}
                              >
                                <item.icon
                                  className={clsx(
                                    isActivePath(item.href) ? 'text-blue-700' : 'text-gray-400 group-hover:text-blue-700',
                                    item.highlight && !isActivePath(item.href) ? 'text-white' : '',
                                    'h-5 w-5 shrink-0'
                                  )}
                                  aria-hidden="true"
                                />
                                {item.name}
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </li>

                      {/* User section */}
                      <li className="mt-auto">
                        <div className="flex items-center gap-x-4 p-3 text-sm font-semibold leading-6 text-gray-900 border-t border-gray-200">
                          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-500">
                            <UserIcon className="h-4 w-4 text-white" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {user?.name || 'Utilisateur'}
                            </p>
                            <p className="text-xs text-gray-500 truncate">
                              {user?.email || 'Non connecté'}
                            </p>
                          </div>
                        </div>
                        
                        {user && (
                          <div className="mt-2 px-3">
                            <Button 
                              variant="outline" 
                              size="sm" 
                              className="w-full"
                              onClick={() => {
                                signOut();
                                setIsMobileMenuOpen(false);
                              }}
                            >
                              Se déconnecter
                            </Button>
                          </div>
                        )}
                      </li>
                    </ul>
                  </nav>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}