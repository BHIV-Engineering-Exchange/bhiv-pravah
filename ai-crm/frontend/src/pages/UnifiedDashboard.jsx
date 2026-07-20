import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, Building2, Package, Truck, 
  ShoppingCart, Bot, Mail, GraduationCap, Brain,
  BarChart3, Store, Settings
} from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/ui/Card';
import MetricCard from '../components/common/charts/MetricCard';
import Button from '../components/common/ui/Button';
import { LoadingSpinner } from '../components/common/ui/Spinner';
import { unifiedAPI } from '../services/api/unifiedAPI';
import Dashboard from './Dashboard';
import CRM from './CRM';
import Logistics from './Logistics';
import Inventory from './Inventory';
import Suppliers from './Suppliers';
import Products from './Products';
import Agents from './Agents';
import Emails from './Emails';
import Learning from './Learning';
import Decisions from './Decisions';
import Reports from './Reports';

export const UnifiedDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState('overview');

  const pages = [
    { id: 'overview', name: 'Overview', icon: LayoutDashboard },
    { id: 'crm', name: 'CRM Management', icon: Building2 },
    { id: 'logistics', name: 'Logistics & Inventory', icon: Truck },
    { id: 'inventory', name: 'Inventory', icon: Package },
    { id: 'suppliers', name: 'Supplier Management', icon: Store },
    { id: 'products', name: 'Product Catalog', icon: ShoppingCart },
    { id: 'agents', name: 'AI Agents', icon: Bot },
    { id: 'emails', name: 'EMS Automation', icon: Mail },
    { id: 'learning', name: 'RL Learning', icon: GraduationCap },
    { id: 'decisions', name: 'AI Decisions', icon: Brain },
    { id: 'reports', name: 'Analytics', icon: BarChart3 },
  ];

  useEffect(() => {
    setTimeout(() => {
      setLoading(false);
    }, 500);
  }, []);

  const renderPage = () => {
    switch (currentPage) {
      case 'overview':
        return <Dashboard />;
      case 'crm':
        return <CRM />;
      case 'logistics':
        return <Logistics />;
      case 'inventory':
        return <Inventory />;
      case 'suppliers':
        return <Suppliers />;
      case 'products':
        return <Products />;
      case 'agents':
        return <Agents />;
      case 'emails':
        return <Emails />;
      case 'learning':
        return <Learning />;
      case 'decisions':
        return <Decisions />;
      case 'reports':
        return <Reports />;
      default:
        return <Dashboard />;
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading unified dashboard..." />;
  }

  return (
    <div className="flex gap-6 animate-fade-in">
      {/* Sidebar Navigation */}
      <aside className="w-64 flex-shrink-0">
        <Card className="sticky top-6">
          <CardHeader>
            <CardTitle className="text-xl">🧭 Navigation</CardTitle>
          </CardHeader>
          <CardContent>
            <nav className="space-y-2">
              {pages.map((page) => {
                const Icon = page.icon;
                return (
                  <button
                    key={page.id}
                    onClick={() => setCurrentPage(page.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                      currentPage === page.id
                        ? 'bg-primary text-primary-foreground shadow-lg'
                        : 'hover:bg-muted text-foreground'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{page.name}</span>
                  </button>
                );
              })}
            </nav>
          </CardContent>
        </Card>
      </aside>

      {/* Main Content */}
      <main className="flex-1 min-w-0">
        {renderPage()}
      </main>
    </div>
  );
};

export default UnifiedDashboard;

