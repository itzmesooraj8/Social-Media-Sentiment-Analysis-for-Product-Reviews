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
  AlertTriangle,
  Save
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
  DialogFooter
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
  const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);

  // Form State
  const [configPlatform, setConfigPlatform] = useState<string>('youtube');
  const [apiKey, setApiKey] = useState('');
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');

  const [isSaving, setIsSaving] = useState(false);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);
  const { toast } = useToast();

  const { data: statusData, isLoading, refetch } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: getSystemStatus,
    refetchInterval: 10000
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
      }))
        // Filter out disconnected items to effectively "Delete" them from the list
        // The user can re-add them via the "Add Integration" button
        .filter(i => i.status === 'connected');

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

  const handleTestConnection = async (id: string, platform: string) => {
    setTestingConnection(id);
    try {
      const res = await fetch(`/api/integrations/test/${platform}`, { method: 'POST' });
      if (res.ok) {
        toast({ title: 'Connection Successful', description: 'API connection is verified.', variant: "default" });
      } else {
        const err = await res.json();
        toast({ title: 'Connection Failed', description: err.detail || 'Could not verify credentials.', variant: "destructive" });
      }
    } catch (e) {
      toast({ title: 'Connection Error', description: 'Network error.', variant: "destructive" });
    } finally {
      setTestingConnection(null);
    }
  };

  const handleSaveConfig = async () => {
    setIsSaving(true);
    try {
      const platform = selectedIntegration ? selectedIntegration.platform : configPlatform;
      const payload: any = {
        platform: platform,
        enabled: true,
        credentials: {}
      };

      if (platform === 'youtube') {
        payload.credentials = { key: apiKey };
      } else if (platform === 'reddit') {
        payload.credentials = { client_id: clientId, client_secret: clientSecret };
      } else if (platform === 'twitter') {
        payload.credentials = { bearer_token: apiKey };
      }

      const res = await fetch('/api/integrations/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        toast({ title: "Configuration Saved", description: "System updated. Validating connection..." });
        // Auto test
        await handleTestConnection(platform, platform);
        refetch();
        setIsAddDialogOpen(false);
        setIsConfigDialogOpen(false);
      } else {
        throw new Error("Failed to save config");
      }
    } catch (e) {
      toast({ title: "Error", description: "Failed to save configuration.", variant: "destructive" });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (platform: string) => {
    if (!confirm(`Are you sure you want to remove ${platform} integration?`)) return;

    try {
      // Optimistic update
      setIntegrations(prev => prev.filter(i => i.platform !== platform));

      const res = await fetch(`/api/integrations/${platform}`, { method: 'DELETE' });
      if (res.ok) {
        toast({ title: "Integration Removed", description: `${platform} credentials have been cleared.` });
        // Force refetch to sync backend state
        refetch();
      } else {
        toast({ title: "Error", description: "Failed to remove integration.", variant: "destructive" });
        // Revert on error (optional, or just let refetch handle it)
        refetch();
      }
    } catch (e) {
      toast({ title: "Error", description: "Network error.", variant: "destructive" });
    }
  };

  const openConfig = (int: Integration) => {
    setSelectedIntegration(int);
    setConfigPlatform(int.platform);
    setApiKey('');
    setClientId('');
    setClientSecret('');
    setIsConfigDialogOpen(true);
  };

  const openAdd = () => {
    setSelectedIntegration(null);
    setConfigPlatform('youtube');
    setApiKey('');
    setClientId('');
    setClientSecret('');
    setIsAddDialogOpen(true);
  }

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
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Integrations</h1>
            <p className="text-muted-foreground">Real-time Data Sources</p>
          </div>

          <Button className="bg-sentinel-credibility hover:bg-sentinel-credibility/90" onClick={openAdd}>
            <Plus className="h-4 w-4 mr-2" />
            Add Integration
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass-card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-sentinel-positive/10"><Link2 className="h-5 w-5 text-sentinel-positive" /></div>
              <div><p className="text-2xl font-bold">{activeCount}</p><p className="text-sm text-muted-foreground">Active</p></div>
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-sentinel-credibility/10"><Zap className="h-5 w-5 text-sentinel-credibility" /></div>
              <div><p className="text-2xl font-bold">{totalReviews.toLocaleString()}</p><p className="text-sm text-muted-foreground">Reviews</p></div>
            </div>
          </div>
          {/* ... other cards (simplified for brevity) ... */}
        </div>

        {/* Integrations List */}
        <div className="space-y-4">
          {integrations.map((integration) => {
            const PlatformIcon = platformIcons[integration.platform];
            return (
              <motion.div key={integration.id} className="glass-card p-5">
                <div className="flex flex-col md:flex-row md:items-center gap-4">
                  <div className="flex items-center gap-4 flex-1">
                    <div className={cn('p-3 rounded-xl', platformColors[integration.platform])}>
                      <PlatformIcon className="h-6 w-6" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{integration.name}</h3>
                        <Badge variant="outline" className={cn('text-xs', statusConfig[integration.status]?.color)}>
                          {statusConfig[integration.status]?.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{integration.reviewsCollected} reviews</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Button variant="outline" size="sm" onClick={() => handleTestConnection(integration.id, integration.platform)} disabled={testingConnection === integration.id}>
                      {testingConnection === integration.id ? <RefreshCw className="h-4 w-4 animate-spin" /> : "Test"}
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => openConfig(integration)}>
                      <Settings className="h-4 w-4 mr-2" /> Configure
                    </Button>
                    <Button variant="outline" size="sm" className="text-sentinel-negative hover:text-sentinel-negative" onClick={() => handleDelete(integration.platform)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* CONFIG DIALOG */}
        <Dialog open={isConfigDialogOpen || isAddDialogOpen} onOpenChange={(open) => { if (!open) { setIsConfigDialogOpen(false); setIsAddDialogOpen(false); } }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{isAddDialogOpen ? "Add Integration" : `Configure ${selectedIntegration?.name}`}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {isAddDialogOpen && (
                <div className="space-y-2">
                  <Label>Platform</Label>
                  <Select value={configPlatform} onValueChange={setConfigPlatform}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="youtube">YouTube</SelectItem>
                      <SelectItem value="reddit">Reddit</SelectItem>
                      <SelectItem value="twitter">Twitter</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}

              {(configPlatform === 'youtube' || selectedIntegration?.platform === 'youtube') && (
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <Input value={apiKey} onChange={e => setApiKey(e.target.value)} type="password" placeholder="AIza..." />
                </div>
              )}

              {(configPlatform === 'reddit' || selectedIntegration?.platform === 'reddit') && (
                <>
                  <div className="space-y-2">
                    <Label>Client ID</Label>
                    <Input value={clientId} onChange={e => setClientId(e.target.value)} placeholder="Client ID" />
                  </div>
                  <div className="space-y-2">
                    <Label>Client Secret</Label>
                    <Input value={clientSecret} onChange={e => setClientSecret(e.target.value)} type="password" placeholder="Secret" />
                  </div>
                </>
              )}

              {(configPlatform === 'twitter' || selectedIntegration?.platform === 'twitter') && (
                <div className="space-y-2">
                  <Label>Bearer Token</Label>
                  <Input value={apiKey} onChange={e => setApiKey(e.target.value)} type="password" placeholder="AAAA..." />
                </div>
              )}
            </div>
            <DialogFooter>
              <Button onClick={handleSaveConfig} disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Configuration"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

      </div>
    </DashboardLayout>
  );
};

export default Integrations;

