import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  BarChart3,
  FileText,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
  Twitter,
  MessageSquare,
  Youtube,
  Users,
  Package,
  Link2,
  HelpCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface AppSidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
  { icon: BarChart3, label: 'Analytics', path: '/analytics' },
  { icon: FileText, label: 'Reports', path: '/reports' },
  { icon: Bell, label: 'Alerts', path: '/alerts' },
  { icon: Package, label: 'Products', path: '/products' },

  { icon: Link2, label: 'Integrations', path: '/integrations' },
  { icon: Settings, label: 'Settings', path: '/settings' },
  { icon: HelpCircle, label: 'Help', path: '/help' },
];

const platformIcons = {
  twitter: Twitter,
  reddit: MessageSquare,
  youtube: Youtube,
  forums: Users,
};

export function AppSidebar({ collapsed, onToggle }: AppSidebarProps) {
  const location = useLocation();
  const [platform, setPlatform] = useState('all');
  const [productId, setProductId] = useState('');

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 280 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className={cn(
        'fixed left-0 top-0 z-40 h-screen glass-card rounded-none border-r border-border/50',
        'flex flex-col'
      )}
    >
      {/* Logo Section */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-border/50">
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-2"
            >
              <div className="relative">
                <Zap className="h-7 w-7 text-sentinel-positive" />
                <div className="absolute inset-0 h-7 w-7 text-sentinel-positive blur-sm opacity-50">
                  <Zap className="h-7 w-7" />
                </div>
              </div>
              <span className="font-bold text-lg gradient-text">Sentinel</span>
            </motion.div>
          )}
        </AnimatePresence>

        {collapsed && (
          <div className="relative mx-auto">
            <Zap className="h-7 w-7 text-sentinel-positive" />
            <div className="absolute inset-0 h-7 w-7 text-sentinel-positive blur-sm opacity-50">
              <Zap className="h-7 w-7" />
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={cn(
                    'flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-200',
                    'hover:bg-accent/50',
                    isActive && 'bg-accent text-foreground shadow-sm',
                    collapsed && 'justify-center px-2'
                  )}
                >
                  <item.icon
                    className={cn(
                      'h-5 w-5 flex-shrink-0 transition-colors',
                      isActive ? 'text-sentinel-positive' : 'text-muted-foreground'
                    )}
                  />
                  <AnimatePresence mode="wait">
                    {!collapsed && (
                      <motion.span
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: 'auto' }}
                        exit={{ opacity: 0, width: 0 }}
                        transition={{ duration: 0.2 }}
                        className={cn(
                          'text-sm font-medium',
                          isActive ? 'text-foreground' : 'text-muted-foreground'
                        )}
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </NavLink>
              </li>
            );
          })}
        </ul>

        {/* Filters Section */}
        <AnimatePresence mode="wait">
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="mt-8 space-y-4"
            >
              <div className="px-2">
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Data Filters
                </h3>

                {/* Platform Select */}
                <div className="space-y-2 mb-4">
                  <Label className="text-xs text-muted-foreground">Platform</Label>
                  <Select value={platform} onValueChange={setPlatform}>
                    <SelectTrigger className="glass-card border-border/50 h-9">
                      <SelectValue placeholder="Select platform" />
                    </SelectTrigger>
                    <SelectContent className="glass-card border-border/50">
                      <SelectItem value="all">All Platforms</SelectItem>
                      <SelectItem value="twitter">
                        <div className="flex items-center gap-2">
                          <Twitter className="h-4 w-4" />
                          Twitter/X
                        </div>
                      </SelectItem>
                      <SelectItem value="reddit">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="h-4 w-4" />
                          Reddit
                        </div>
                      </SelectItem>
                      <SelectItem value="youtube">
                        <div className="flex items-center gap-2">
                          <Youtube className="h-4 w-4" />
                          YouTube
                        </div>
                      </SelectItem>
                      <SelectItem value="forums">
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          Forums
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Product ID Input */}
                <div className="space-y-2">
                  <Label className="text-xs text-muted-foreground">Product ID</Label>
                  <Input
                    value={productId}
                    onChange={(e) => setProductId(e.target.value)}
                    placeholder="SKU-12345"
                    className="glass-card border-border/50 h-9 text-sm"
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* Toggle Button */}
      <div className="p-3 border-t border-border/50">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggle}
          className={cn(
            'w-full justify-center hover:bg-accent/50 transition-all',
            collapsed ? 'px-2' : 'px-3'
          )}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span className="text-sm">Collapse</span>
            </>
          )}
        </Button>
      </div>
    </motion.aside>
  );
}
