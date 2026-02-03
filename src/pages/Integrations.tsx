import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { getSystemStatus } from '@/lib/api';
import {
  Link2,
  Plus,
  Twitter,
  Youtube,
  MessageSquare,
  Users,
  CheckCircle,
  XCircle,
  RefreshCw,
  Settings,
  Trash2,
  Clock,
  Zap,
  AlertTriangle
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

interface Integration {
  id: string;
  name: string;
  platform: 'twitter' | 'reddit' | 'youtube' | 'forums';
  status: 'connected' | 'disconnected' | 'error';
  lastSync: Date | null;
  reviewsCollected: number;
  syncFrequency: string;
  isEnabled: boolean;
}

const platformIcons = {
  twitter: Twitter,
  reddit: MessageSquare,
  youtube: Youtube,
  forums: Users,
};

const platformColors = {
  twitter: 'text-blue-400 bg-blue-400/10',
  reddit: 'text-orange-500 bg-orange-500/10',
  youtube: 'text-red-500 bg-red-500/10',
  forums: 'text-purple-400 bg-purple-400/10',
};

const Integrations = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [selectedFrequency, setSelectedFrequency] = useState<string>('30');
  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  const { toast } = useToast();

  const { data: statusData, isLoading } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: getSystemStatus,
    refetchInterval: 30000
  });

  useEffect(() => {
    if (statusData) {
      const counts = statusData.counts || { reddit: 0, youtube: 0, twitter: 0 };

      // Defaults based on backend status
      const defaults = [
        {
          id: 'twitter',
          name: 'Twitter/X',
          platform: 'twitter' as const,
          key: 'twitter',
          reviews: counts.twitter
        },
        {
          id: 'reddit',
          name: 'Reddit',
          platform: 'reddit' as const,
          key: 'reddit',
          reviews: counts.reddit
        },
        {
          id: 'youtube',
          name: 'YouTube',
          platform: 'youtube' as const,
          key: 'youtube',
          reviews: counts.youtube
        },
      ];

      const mapped: Integration[] = defaults.map(d => ({
        id: d.id,
        name: d.name,
        platform: d.platform,
        // @ts-ignore
        status: statusData[d.key] ? 'connected' : 'disconnected',
        // @ts-ignore
        lastSync: statusData[d.key] ? new Date() : null,
        reviewsCollected: d.reviews || 0,
        syncFrequency: '30 minutes',
        // @ts-ignore
        isEnabled: !!statusData[d.key]
      }));

      // Load specific persistent "Custom" integrations from localStorage if we had any
      // For now, we just stick to the live system status
      setIntegrations(mapped);
    }
  }, [statusData]);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="space-y-6">
          <div className="h-8 w-48 bg-muted animate-pulse rounded" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-24 bg-card rounded-xl animate-pulse" />)}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const formatLastSync = (date: Date | null) => {
    if (!date) return 'Never';
    return "Recent";
  };

  const handleTestConnection = async (id: string, platform: string) => {
    setTestingConnection(id);
    try {
      const res = await fetch(`http://localhost:8000/api/integrations/test/${platform}`, { method: 'POST' });
      if (res.ok) {
        toast({
          title: 'Connection Successful',
          description: 'API connection is verified and working.',
          variant: "default" // success
        });
      } else {
        const err = await res.json();
        toast({
          title: 'Connection Failed',
          description: err.detail || 'Could not verify credentials.',
          variant: "destructive"
        });
      }
    } catch (e) {
      toast({
        title: 'Connection Error',
        description: 'Network error or backend offline.',
        variant: "destructive"
      });
    } finally {
      setTestingConnection(null);
    }
  };

  const handleToggleIntegration = (id: string) => {
    setIntegrations(prev =>
      prev.map(int =>
        int.id === id ? { ...int, isEnabled: !int.isEnabled } : int
      )
    );
    toast({ title: "Status Updated", description: "Integration availability toggled." });
  };

  const handleDelete = (id: string) => {
    toast({
      title: "Cannot Delete System Integration",
      description: "This integration is defined in server configuration (.env). Set credentials to empty to remove it permanently.",
      variant: "destructive"
    });
  };

  const activeCount = integrations.filter(i => i.status === 'connected').length;
  const totalReviews = integrations.reduce((sum, i) => sum + i.reviewsCollected, 0);

  const statusConfig = {
    connected: { icon: CheckCircle, color: 'text-sentinel-positive', label: 'Connected' },
    disconnected: { icon: XCircle, color: 'text-muted-foreground', label: 'Disconnected' },
    error: { icon: AlertTriangle, color: 'text-sentinel-negative', label: 'Error' },
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Integrations</h1>
            <p className="text-muted-foreground">Connect and manage your data sources</p>
          </div>

          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-sentinel-credibility hover:bg-sentinel-credibility/90">
                <Plus className="h-4 w-4 mr-2" />
                Add Integration
              </Button>
            </DialogTrigger>
            <DialogContent className="glass-card border-border/50">
              <DialogHeader>
                <DialogTitle>Add New Integration</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded text-sm text-foreground">
                  Note: To add a new system integration, please configure the <code>.env</code> file on the server.
                </div>
                <div className="flex justify-end pt-4">
                  <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>Close</Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass-card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-sentinel-positive/10">
                <Link2 className="h-5 w-5 text-sentinel-positive" />
              </div>
              <div>
                <p className="text-2xl font-bold">{activeCount}</p>
                <p className="text-sm text-muted-foreground">Active Connections</p>
              </div>
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-sentinel-credibility/10">
                <Zap className="h-5 w-5 text-sentinel-credibility" />
              </div>
              <div>
                <p className="text-2xl font-bold">{totalReviews.toLocaleString()}</p>
                <p className="text-sm text-muted-foreground">Total Reviews Collected</p>
              </div>
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-sentinel-warning/10">
                <Clock className="h-5 w-5 text-sentinel-warning" />
              </div>
              <div>
                <p className="text-2xl font-bold">Live</p>
                <p className="text-sm text-muted-foreground">System Status</p>
              </div>
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-sentinel-negative/10">
                <AlertTriangle className="h-5 w-5 text-sentinel-negative" />
              </div>
              <div>
                <p className="text-2xl font-bold">{integrations.filter(i => i.status === 'error').length}</p>
                <p className="text-sm text-muted-foreground">Errors</p>
              </div>
            </div>
          </div>
        </div>

        {/* Integrations List */}
        <div className="space-y-4">
          {integrations.map((integration, index) => {
            const PlatformIcon = platformIcons[integration.platform];
            const StatusIcon = statusConfig[integration.status].icon;

            return (
              <motion.div
                key={integration.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className={cn(
                  'glass-card p-5 transition-all duration-200',
                  integration.status === 'error' && 'border-sentinel-negative/30'
                )}
              >
                <div className="flex flex-col md:flex-row md:items-center gap-4">
                  {/* Platform Info */}
                  <div className="flex items-center gap-4 flex-1">
                    <div className={cn(
                      'p-3 rounded-xl',
                      platformColors[integration.platform]
                    )}>
                      <PlatformIcon className="h-6 w-6" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold">{integration.name}</h3>
                        <Badge
                          variant="outline"
                          className={cn(
                            'text-xs',
                            statusConfig[integration.status].color
                          )}
                        >
                          <StatusIcon className="h-3 w-3 mr-1" />
                          {statusConfig[integration.status].label}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{integration.reviewsCollected.toLocaleString()} reviews collected</span>
                        <span>•</span>
                        <span>Syncs every {integration.syncFrequency}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <Label htmlFor={`toggle-${integration.id}`} className="text-sm text-muted-foreground">
                        Enabled
                      </Label>
                      <Switch
                        id={`toggle-${integration.id}`}
                        checked={integration.isEnabled}
                        onCheckedChange={() => handleToggleIntegration(integration.id)}
                      />
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestConnection(integration.id, integration.platform)}
                      disabled={testingConnection === integration.id || integration.status === 'disconnected'}
                    >
                      {testingConnection === integration.id ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      <span className="ml-2 hidden sm:inline">Test</span>
                    </Button>

                    <Button variant="outline" size="sm" onClick={() => toast({ title: "Configuration", description: "Use .env file to configure this integration." })}>
                      <Settings className="h-4 w-4" />
                      <span className="ml-2 hidden sm:inline">Configure</span>
                    </Button>

                    <Button variant="outline" size="sm" className="text-sentinel-negative hover:text-sentinel-negative" onClick={() => handleDelete(integration.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Integrations;
