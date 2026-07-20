import { Outlet } from 'react-router-dom'
import RoleNavbar from '../navbars/RoleNavbar'
import ClientSidebar from '../sidebars/ClientSidebar'
import { SidebarProvider, useSidebar } from '../../context/SidebarContext'

function ClientLayoutContent() {
  const { isCollapsed, isMobileOpen, closeMobile } = useSidebar()
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0f172a] text-gray-900 dark:text-gray-100 transition-colors duration-300">
      <RoleNavbar role="client" />
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden transition-opacity duration-300"
          onClick={closeMobile}
        />
      )}
      <div className="flex">
        <ClientSidebar />
        <main className={`flex-1 mt-16 lg:mt-16 p-4 sm:p-6 lg:p-8 animate-fade-in transition-all duration-300 ${
          isCollapsed ? 'lg:ml-20' : 'lg:ml-64'
        }`}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default function ClientLayout() {
  return (
    <SidebarProvider>
      <ClientLayoutContent />
    </SidebarProvider>
  )
}
