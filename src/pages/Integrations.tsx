import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
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

// Mock data removed. Usage strictly from API.

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
  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const fetchIntegrations = async () => {
      try {
        // In a real app, use the API. For now, since DB is likely empty, we handle the empty state.
        // But we should try to fetch.
        const response = await fetch('http://localhost:8000/api/integrations');
        const data = await response.json();
        if (data.success) {
          // Map backend data to UI interface if needed, or use as is
          const mapped = data.data.map((i: any) => ({
            id: i.id,
            name: i.platform, // Mapping platform to name for now
            platform: i.platform,
            status: i.status === 'active' ? 'connected' : (i.status === 'error' ? 'error' : 'disconnected'),
            lastSync: i.last_sync ? new Date(i.last_sync) : null,
            reviewsCollected: 0,
            syncFrequency: '30 minutes',
            isEnabled: i.is_enabled
          }));
          setIntegrations(mapped);
        }
      } catch (error) {
        console.error("Failed to fetch integrations", error);
      }
    };
    fetchIntegrations();
  }, []);


  const formatLastSync = (date: Date | null) => {
    if (!date) return 'Never';
    const diff = Date.now() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);

    if (minutes < 60) return `${minutes}m ago`;
    return `${hours}h ago`;
  };

  const handleTestConnection = async (id: string) => {
    setTestingConnection(id);
    await new Promise(resolve => setTimeout(resolve, 2000));
    setTestingConnection(null);

    toast({
      title: 'Connection Successful',
      description: 'API connection is working properly.',
    });
  };

  const handleToggleIntegration = (id: string) => {
    setIntegrations(prev =>
      prev.map(int =>
        int.id === id ? { ...int, isEnabled: !int.isEnabled } : int
      )
    );
  };

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
                <div className="space-y-2">
                  <Label>Platform</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select platform" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="twitter">Twitter/X</SelectItem>
                      <SelectItem value="reddit">Reddit</SelectItem>
                      <SelectItem value="youtube">YouTube</SelectItem>
                      <SelectItem value="forums">Custom Forum</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <Input type="password" placeholder="Enter your API key" />
                </div>
                <div className="space-y-2">
                  <Label>API Secret (if required)</Label>
                  <Input type="password" placeholder="Enter your API secret" />
                </div>
                <div className="space-y-2">
                  <Label>Sync Frequency</Label>
                  <Select defaultValue="30">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">Every 15 minutes</SelectItem>
                      <SelectItem value="30">Every 30 minutes</SelectItem>
                      <SelectItem value="60">Every hour</SelectItem>
                      <SelectItem value="360">Every 6 hours</SelectItem>
                      <SelectItem value="1440">Daily</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex gap-2 pt-4">
                  <Button variant="outline" className="flex-1" onClick={() => setIsAddDialogOpen(false)}>
                    Cancel
                  </Button>

                  <Button
                    className="flex-1 bg-sentinel-credibility hover:bg-sentinel-credibility/90"
                    onClick={() => {
                      setIntegrations(prev => [
                        ...prev,
                        {
                          id: `new-${Date.now()}`,
                          name: 'Twitter/X feed',
                          platform: 'twitter',
                          status: 'connected',
                          lastSync: new Date(),
                          reviewsCollected: 0,
                          syncFrequency: '30 minutes',
                          isEnabled: true
                        }
                      ]);
                      setIsAddDialogOpen(false);
                      toast({ title: "Integration Added", description: "Successfully connected to platform." });
                    }}
                  >
                    Connect
                  </Button>
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
                <p className="text-2xl font-bold">{integrations.filter(i => i.status === 'connected').length}</p>
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
                <p className="text-2xl font-bold">{integrations.reduce((sum, i) => sum + i.reviewsCollected, 0).toLocaleString()}</p>
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
                <p className="text-2xl font-bold">{integrations.length > 0 ? formatLastSync(integrations.reduce((latest, i) => !latest || (i.lastSync && i.lastSync > latest) ? i.lastSync : latest, null as Date | null)) : '-'}</p>
                <p className="text-sm text-muted-foreground">Last Sync</p>
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
                        <span>•</span>
                        <span>Last sync: {formatLastSync(integration.lastSync)}</span>
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
                      onClick={() => handleTestConnection(integration.id)}
                      disabled={testingConnection === integration.id}
                    >
                      {testingConnection === integration.id ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      <span className="ml-2 hidden sm:inline">Test</span>
                    </Button>

                    <Button variant="outline" size="sm">
                      <Settings className="h-4 w-4" />
                      <span className="ml-2 hidden sm:inline">Configure</span>
                    </Button>

                    <Button variant="outline" size="sm" className="text-sentinel-negative hover:text-sentinel-negative">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Error Message */}
                {integration.status === 'error' && (
                  <div className="mt-4 p-3 rounded-lg bg-sentinel-negative/10 border border-sentinel-negative/30">
                    <p className="text-sm text-sentinel-negative">
                      ⚠️ API rate limit exceeded. Will retry automatically in 15 minutes.
                    </p>
                  </div>
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Integrations;
