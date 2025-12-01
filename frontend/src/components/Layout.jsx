import React from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  ChartPieIcon,
  MapIcon, 
  ChartBarIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'
import ChatSidebar from './ChatSidebar'

const navigation = [
  { name: 'Inicio', href: '/', icon: HomeIcon },
  { name: 'Dashboard', href: '/dashboard', icon: ChartPieIcon },
  { name: 'Mapa', href: '/map', icon: MapIcon },
  { name: 'Analizador', href: '/analyzer', icon: ChartBarIcon },
  { name: 'Búsqueda', href: '/property-search', icon: MagnifyingGlassIcon },
]

export default function Layout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm fixed top-0 left-0 right-0 z-20">
        <div className="max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-2xl font-bold text-primary-600">
                  Real Estate Risk
                </h1>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                        isActive
                          ? 'border-primary-500 text-gray-900'
                          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                      }`}
                    >
                      <item.icon className="h-5 w-5 mr-2" />
                      {item.name}
                    </Link>
                  )
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        <div className="sm:hidden">
          <div className="pt-2 pb-3 space-y-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`block pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
                    isActive
                      ? 'bg-primary-50 border-primary-500 text-primary-700'
                      : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800'
                  }`}
                >
                  <div className="flex items-center">
                    <item.icon className="h-5 w-5 mr-3" />
                    {item.name}
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Main content - with padding for fixed nav and right sidebar */}
      <main className="pt-16 pr-96">
        <Outlet />
      </main>

      {/* Chat Sidebar - Available everywhere */}
      <ChatSidebar />

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto pr-96">
        <div className="max-w-full px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2024 Real Estate Risk Platform. Detección de fraude inmobiliario en Colombia.
          </p>
        </div>
      </footer>
    </div>
  )
}
