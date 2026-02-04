import React, { useState, useEffect } from 'react';
import { getAlerts, resolveAlert as apiResolveAlert, createAlert, getProducts } from '@/lib/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Bell,
    AlertTriangle,
    Bot,
    Flame,
    TrendingDown,
    ShieldAlert,
    Filter,
    Search,
    CheckCircle2,
    XCircle,
    Clock,
    Eye,
    MoreHorizontal,
    Settings,
    BellOff,
    Trash2,
    Plus
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { AlertSeverity, AlertType } from '@/types/sentinel';
import { useToast } from '@/hooks/use-toast';

const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.05 }
    }
};

const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
};

interface AlertItem {
    id: string;
    type: AlertType;
    severity: AlertSeverity;
    title: string;
    message: string;
    timestamp: Date;
    platform: string;
    isRead: boolean;
    isResolved: boolean;
    details?: {
        confidence?: number;
        reviewCount?: number;
        affectedProducts?: string[];
    };
}


const alertTypeConfig: any = {
    bot_detected: { icon: Bot, label: 'Bot Detected', color: 'text-sentinel-negative' },
    spam_cluster: { icon: Flame, label: 'Spam Cluster', color: 'text-orange-400' },
    sentiment_shift: { icon: TrendingDown, label: 'Sentiment Shift', color: 'text-sentinel-credibility' },
    review_surge: { icon: AlertTriangle, label: 'Review Surge', color: 'text-amber-400' },
    fake_review: { icon: ShieldAlert, label: 'Fake Review', color: 'text-purple-400' },
    keyword_monitor: { icon: Search, label: 'Keyword Monitor', color: 'text-blue-400' }
};

const severityConfig: any = {
    critical: { color: 'bg-sentinel-negative/20 text-sentinel-negative border-sentinel-negative/50', priority: 4 },
    high: { color: 'bg-orange-500/20 text-orange-400 border-orange-500/50', priority: 3 },
    medium: { color: 'bg-sentinel-credibility/20 text-sentinel-credibility border-sentinel-credibility/50', priority: 2 },
    low: { color: 'bg-muted text-muted-foreground border-border', priority: 1 },
};

const formatTimeAgo = (date: Date) => {
    if (!date) return '';
    const d = new Date(date);
    const seconds = Math.floor((new Date().getTime() - d.getTime()) / 1000);
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
};

const Alerts = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [filterSeverity, setFilterSeverity] = useState<string>('all');
    const queryClient = useQueryClient();
    const { toast } = useToast();

    // Create Alert State
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [newAlertKeyword, setNewAlertKeyword] = useState('');
    const [newAlertThreshold, setNewAlertThreshold] = useState('0.5');
    const [newAlertEmail, setNewAlertEmail] = useState('');

    const { data: alertsDataResp, isLoading } = useQuery({
        queryKey: ['alerts'],
        queryFn: async () => {
            const data = await getAlerts();
            return data;
        },
        refetchInterval: 5000
    });

    const [alerts, setAlerts] = useState<AlertItem[]>(alertsDataResp || []);

    // Keep local state in sync with server data
    useEffect(() => {
        if (alertsDataResp) setAlerts(alertsDataResp);
    }, [alertsDataResp]);

    // Fetch Products for Dropdown
    const [products, setProducts] = useState<any[]>([]);
    const [selectedProductId, setSelectedProductId] = useState<string>("all");

    useQuery({
        queryKey: ['products-simple-list'],
        queryFn: async () => {
            const p = await getProducts();
            setProducts(p);
            return p;
        },
        staleTime: 1000 * 60 * 5
    });

    const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);

    const filteredAlerts = alerts.filter(alert => {
        const matchesSearch = alert.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            alert.message?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesSeverity = filterSeverity === 'all' || alert.severity === filterSeverity;
        return matchesSearch && matchesSeverity;
    });

    const activeAlerts = filteredAlerts.filter(a => !a.isResolved);
    const resolvedAlerts = filteredAlerts.filter(a => a.isResolved);
    const unreadCount = alerts.filter(a => !a.isRead && !a.isResolved).length;

    const markReadMutation = useMutation({
        mutationFn: async (id: string) => {
            await fetch(`/api/alerts/${id}/read`, { method: 'POST' });
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] })
    });

    const resolveMutation = useMutation({
        mutationFn: async (id: string) => {
            await apiResolveAlert(id);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
        }
    });

    const createMutation = useMutation({
        mutationFn: async (data: any) => {
            await createAlert(data);
        },
        onSuccess: () => {
            toast({ title: "Alert Created", description: `Monitoring for "${newAlertKeyword}"` });
            setIsCreateOpen(false);
            setNewAlertKeyword('');
            queryClient.invalidateQueries({ queryKey: ['alerts'] });
        },
        onError: () => {
            toast({ title: "Error", description: "Failed to create alert", variant: "destructive" });
        }
    });

    const handleCreateAlert = () => {
        if (!newAlertKeyword || !newAlertEmail) return;
        createMutation.mutate({
            keyword: newAlertKeyword,
            threshold: parseFloat(newAlertThreshold),
            email: newAlertEmail,
            product_id: selectedProductId === 'all' ? null : selectedProductId
        });
    };

    const markAsRead = (id: string) => {
        markReadMutation.mutate(id);
    };

    const resolveAlert = (id: string) => {
        resolveMutation.mutate(id);
        // Optimistic update
        setAlerts(prev => prev.map(a => a.id === id ? { ...a, isResolved: true, isRead: true } : a));
    };

    const deleteAlert = (id: string) => {
        setAlerts(prev => prev.filter(a => a.id !== id));
    };

    return (
        <DashboardLayout>
            <motion.div
                variants={containerVariants}
                initial="hidden"
                animate="visible"
                className="space-y-6"
            >
                {/* Page Header */}
                <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-2xl font-bold">Alerts</h1>
                            {unreadCount > 0 && (
                                <Badge className="bg-sentinel-negative text-white">
                                    {unreadCount} new
                                </Badge>
                            )}
                        </div>
                        <p className="text-muted-foreground">Monitor and manage system alerts</p>
                    </div>
                    <div className="flex gap-2">
                        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                            <DialogTrigger asChild>
                                <Button className="gap-2 bg-sentinel-gradient text-white hover:opacity-90 shadow-lg shadow-sentinel-credibility/20 font-semibold border-none transition-all hover:scale-105">
                                    <Plus className="h-4 w-4" />
                                    Create Alert
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="glass-card border-border">
                                <DialogHeader>
                                    <DialogTitle>Create New Alert</DialogTitle>
                                    <DialogDescription>
                                        Monitor keywords and receive notifications when sentiment drops.
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4 py-4">
                                    <div className="space-y-2">
                                        <Label>Target Product (Optional)</Label>
                                        <Select value={selectedProductId} onValueChange={setSelectedProductId}>
                                            <SelectTrigger className="glass-card border-border/50">
                                                <SelectValue placeholder="Select a product" />
                                            </SelectTrigger>
                                            <SelectContent className="glass-card border-border/50">
                                                <SelectItem value="all">All Products (Global)</SelectItem>
                                                {products.map(p => (
                                                    <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                                                ))}
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="keyword">Keyword</Label>
                                        <Input
                                            id="keyword"
                                            placeholder="e.g. 'battery life', 'competitor name'"
                                            value={newAlertKeyword}
                                            onChange={(e) => setNewAlertKeyword(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="threshold">Sentiment Threshold (0.0 - 1.0)</Label>
                                        <Input
                                            id="threshold"
                                            type="number"
                                            step="0.1"
                                            min="0"
                                            max="1"
                                            value={newAlertThreshold}
                                            onChange={(e) => setNewAlertThreshold(e.target.value)}
                                        />
                                        <p className="text-xs text-muted-foreground">Alert if sentiment drops below this value.</p>
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="email">Email Notification</Label>
                                        <Input
                                            id="email"
                                            type="email"
                                            placeholder="you@company.com"
                                            value={newAlertEmail}
                                            onChange={(e) => setNewAlertEmail(e.target.value)}
                                        />
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                                    <Button onClick={handleCreateAlert} disabled={createMutation.isPending}>
                                        {createMutation.isPending ? 'Creating...' : 'Create Alert'}
                                    </Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>

                        <Button variant="outline" className="gap-2">
                            <Settings className="h-4 w-4" />
                            Alert Settings
                        </Button>
                    </div>
                </motion.div>

                {/* Stats Cards */}
                <motion.div variants={itemVariants} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <Card className="glass-card border-border/50">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-sentinel-negative/20">
                                    <AlertTriangle className="h-5 w-5 text-sentinel-negative" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{activeAlerts.filter(a => a.severity === 'critical').length}</p>
                                    <p className="text-xs text-muted-foreground">Critical</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="glass-card border-border/50">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-orange-500/20">
                                    <Bell className="h-5 w-5 text-orange-400" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{activeAlerts.filter(a => a.severity === 'high').length}</p>
                                    <p className="text-xs text-muted-foreground">High Priority</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="glass-card border-border/50">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-sentinel-credibility/20">
                                    <Clock className="h-5 w-5 text-sentinel-credibility" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{activeAlerts.length}</p>
                                    <p className="text-xs text-muted-foreground">Active</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="glass-card border-border/50">
                        <CardContent className="pt-6">
                            <div className="flex items-center gap-3">
                                <div className="p-2 rounded-lg bg-sentinel-positive/20">
                                    <CheckCircle2 className="h-5 w-5 text-sentinel-positive" />
                                </div>
                                <div>
                                    <p className="text-2xl font-bold">{resolvedAlerts.length}</p>
                                    <p className="text-xs text-muted-foreground">Resolved</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Filters */}
                <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search alerts..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 glass-card border-border/50"
                        />
                    </div>
                    <Select value={filterSeverity} onValueChange={setFilterSeverity}>
                        <SelectTrigger className="w-full sm:w-[180px] glass-card border-border/50">
                            <Filter className="h-4 w-4 mr-2" />
                            <SelectValue placeholder="Severity" />
                        </SelectTrigger>
                        <SelectContent className="glass-card border-border/50">
                            <SelectItem value="all">All Severities</SelectItem>
                            <SelectItem value="critical">Critical</SelectItem>
                            <SelectItem value="high">High</SelectItem>
                            <SelectItem value="medium">Medium</SelectItem>
                            <SelectItem value="low">Low</SelectItem>
                        </SelectContent>
                    </Select>
                </motion.div>

                {/* Alerts Tabs */}
                <motion.div variants={itemVariants}>
                    <Tabs defaultValue="active" className="space-y-4">
                        <TabsList className="glass-card border-border/50">
                            <TabsTrigger value="active" className="gap-2">
                                Active
                                <Badge variant="secondary" className="ml-1">{activeAlerts.length}</Badge>
                            </TabsTrigger>
                            <TabsTrigger value="resolved" className="gap-2">
                                Resolved
                                <Badge variant="secondary" className="ml-1">{resolvedAlerts.length}</Badge>
                            </TabsTrigger>
                            <TabsTrigger value="settings">Settings</TabsTrigger>
                        </TabsList>

                        <TabsContent value="active">
                            <Card className="glass-card border-border/50">
                                <CardContent className="p-0">
                                    <AnimatePresence>
                                        {activeAlerts.length === 0 ? (
                                            <div className="p-8 text-center">
                                                <CheckCircle2 className="h-12 w-12 mx-auto text-sentinel-positive mb-4" />
                                                <p className="text-lg font-medium">No Alerts</p>
                                                <p className="text-muted-foreground">No active alerts at this time</p>
                                            </div>
                                        ) : (
                                            <div className="divide-y divide-border/50">
                                                {activeAlerts.map((alert, index) => {
                                                    const typeConfig = alertTypeConfig[alert.type] || alertTypeConfig['bot_detected']; // Fallback
                                                    const sevConfig = severityConfig[alert.severity] || severityConfig['low'];

                                                    return (
                                                        <motion.div
                                                            key={alert.id}
                                                            initial={{ opacity: 0, x: -20 }}
                                                            animate={{ opacity: 1, x: 0 }}
                                                            exit={{ opacity: 0, x: 20 }}
                                                            transition={{ delay: index * 0.05 }}
                                                            className={`p-4 hover:bg-accent/30 transition-colors ${!alert.isRead ? 'bg-accent/10' : ''}`}
                                                        >
                                                            <div className="flex items-start gap-4">
                                                                <div className={`p-2 rounded-lg ${sevConfig.color} border`}>
                                                                    <typeConfig.icon className="h-5 w-5" />
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <div className="flex items-start justify-between gap-4">
                                                                        <div>
                                                                            <div className="flex items-center gap-2">
                                                                                <h3 className="font-medium">{alert.title}</h3>
                                                                                {!alert.isRead && (
                                                                                    <span className="w-2 h-2 rounded-full bg-sentinel-positive" />
                                                                                )}
                                                                            </div>
                                                                            <p className="text-sm text-muted-foreground mt-1">{alert.message}</p>
                                                                            <div className="flex items-center gap-3 mt-2">
                                                                                <Badge variant="outline" className={sevConfig.color}>
                                                                                    {alert.severity}
                                                                                </Badge>
                                                                                <span className="text-xs text-muted-foreground">{alert.platform}</span>
                                                                                <span className="text-xs text-muted-foreground">{formatTimeAgo(alert.timestamp)}</span>
                                                                                {alert.details?.confidence && (
                                                                                    <span className="text-xs text-muted-foreground">
                                                                                        {alert.details.confidence}% confidence
                                                                                    </span>
                                                                                )}
                                                                            </div>
                                                                        </div>
                                                                        <DropdownMenu>
                                                                            <DropdownMenuTrigger asChild>
                                                                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                                                                    <MoreHorizontal className="h-4 w-4" />
                                                                                </Button>
                                                                            </DropdownMenuTrigger>
                                                                            <DropdownMenuContent align="end" className="glass-card border-border/50">
                                                                                <DropdownMenuItem onClick={() => markAsRead(alert.id)}>
                                                                                    <Eye className="h-4 w-4 mr-2" />
                                                                                    Mark as read
                                                                                </DropdownMenuItem>
                                                                                <DropdownMenuItem onClick={() => resolveAlert(alert.id)}>
                                                                                    <CheckCircle2 className="h-4 w-4 mr-2" />
                                                                                    Resolve
                                                                                </DropdownMenuItem>
                                                                                <DropdownMenuSeparator />
                                                                                <DropdownMenuItem onClick={() => deleteAlert(alert.id)} className="text-sentinel-negative">
                                                                                    <Trash2 className="h-4 w-4 mr-2" />
                                                                                    Delete
                                                                                </DropdownMenuItem>
                                                                            </DropdownMenuContent>
                                                                        </DropdownMenu>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </motion.div>
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </AnimatePresence>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="resolved">
                            <Card className="glass-card border-border/50">
                                <CardContent className="p-0">
                                    {resolvedAlerts.length === 0 ? (
                                        <div className="p-8 text-center">
                                            <Clock className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                                            <p className="text-lg font-medium">No resolved alerts</p>
                                            <p className="text-muted-foreground">Resolved alerts will appear here</p>
                                        </div>
                                    ) : (
                                        <div className="divide-y divide-border/50">
                                            {resolvedAlerts.map((alert, index) => {
                                                const typeConfig = alertTypeConfig[alert.type];

                                                return (
                                                    <motion.div
                                                        key={alert.id}
                                                        initial={{ opacity: 0, x: -20 }}
                                                        animate={{ opacity: 1, x: 0 }}
                                                        transition={{ delay: index * 0.05 }}
                                                        className="p-4 hover:bg-accent/30 transition-colors opacity-60"
                                                    >
                                                        <div className="flex items-start gap-4">
                                                            <div className="p-2 rounded-lg bg-muted">
                                                                <typeConfig.icon className="h-5 w-5 text-muted-foreground" />
                                                            </div>
                                                            <div className="flex-1">
                                                                <div className="flex items-center gap-2">
                                                                    <h3 className="font-medium line-through">{alert.title}</h3>
                                                                    <Badge variant="outline" className="bg-sentinel-positive/20 text-sentinel-positive">
                                                                        Resolved
                                                                    </Badge>
                                                                </div>
                                                                <p className="text-sm text-muted-foreground mt-1">{alert.message}</p>
                                                                <span className="text-xs text-muted-foreground mt-2 block">
                                                                    {formatTimeAgo(alert.timestamp)}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </motion.div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="settings">
                            <Card className="glass-card border-border/50">
                                <CardHeader>
                                    <CardTitle>Alert Preferences</CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="space-y-4">
                                        <h3 className="text-sm font-medium">Notification Channels</h3>
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <Label>Email Notifications</Label>
                                                    <p className="text-xs text-muted-foreground">Receive alerts via email</p>
                                                </div>
                                                <Switch defaultChecked />
                                            </div>
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <Label>Push Notifications</Label>
                                                    <p className="text-xs text-muted-foreground">Browser push notifications</p>
                                                </div>
                                                <Switch defaultChecked />
                                            </div>
                                            <div className="flex items-center justify-between">
                                                <div>
                                                    <Label>Slack Integration</Label>
                                                    <p className="text-xs text-muted-foreground">Send alerts to Slack channel</p>
                                                </div>
                                                <Switch />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <h3 className="text-sm font-medium">Alert Types</h3>
                                        <div className="space-y-3">
                                            {Object.entries(alertTypeConfig).map(([key, config]) => (
                                                <div key={key} className="flex items-center justify-between">
                                                    <div className="flex items-center gap-2">
                                                        <config.icon className={`h-4 w-4 ${config.color}`} />
                                                        <Label>{config.label}</Label>
                                                    </div>
                                                    <Switch defaultChecked />
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <h3 className="text-sm font-medium">Severity Threshold</h3>
                                        <Select defaultValue="low">
                                            <SelectTrigger className="glass-card border-border/50">
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent className="glass-card border-border/50">
                                                <SelectItem value="critical">Critical only</SelectItem>
                                                <SelectItem value="high">High and above</SelectItem>
                                                <SelectItem value="medium">Medium and above</SelectItem>
                                                <SelectItem value="low">All alerts</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>

                                    <Button className="bg-sentinel-positive hover:bg-sentinel-positive/90 text-black">
                                        Save Preferences
                                    </Button>
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </motion.div>
            </motion.div>
        </DashboardLayout>
    );
};

export default Alerts;
