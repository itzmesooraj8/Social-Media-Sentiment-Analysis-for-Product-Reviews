import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/context/AuthContext';
import { motion } from 'framer-motion';
import {
  Settings as SettingsIcon,
  User,
  Bell,
  Shield,
  Palette,
  Database,
  Key,
  Globe,
  Zap,
  ChevronRight,
  Save,
  Mail,
  Smartphone,
  Lock,
  Eye,
  EyeOff,
  Check
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useTheme } from '@/components/ThemeProvider';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

const Settings = () => {
  const { theme, setTheme } = useTheme();
  const [showApiKey, setShowApiKey] = useState(false);
  const [saved, setSaved] = useState(false);

  // Settings State (defaults); real values fetched from backend
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const [credibilityThreshold, setCredibilityThreshold] = useState([75]);
  const [realTimeAnalysis, setRealTimeAnalysis] = useState(true);
  const [botDetection, setBotDetection] = useState(true);
  const [sentimentAlerts, setSentimentAlerts] = useState(true);

  const { data: settingsResp } = useQuery({
    queryKey: ['settings', user?.id],
    queryFn: async () => {
      const uid = user?.id || 'default';
      const res = await fetch(`/api/settings?user_id=${encodeURIComponent(uid)}`);
      const json = await res.json();
      return (json.data || []) as Array<{ key: string; value: string }>;
    },
    enabled: !!user || true
  });

  // Profile State
  const [profile, setProfile] = useState({
    firstName: "Sentinel",
    lastName: "Admin",
    email: "admin@sentinel.ai",
    org: "Sentinel Engine Inc."
  });

  useEffect(() => {
    if (!settingsResp) return;
    // settingsResp is an array of { user_id, key, value }
    const map: Record<string, string> = {};
    settingsResp.forEach((s: any) => { map[s.key] = s.value; });

    if (map['setting_credibilityThreshold']) setCredibilityThreshold([parseInt(map['setting_credibilityThreshold'])]);
    if (map['setting_realTimeAnalysis']) setRealTimeAnalysis(map['setting_realTimeAnalysis'] !== 'false');
    if (map['setting_botDetection']) setBotDetection(map['setting_botDetection'] !== 'false');
    if (map['setting_sentimentAlerts']) setSentimentAlerts(map['setting_sentimentAlerts'] !== 'false');

    // Load Profile Settings
    if (map['profile_firstName']) setProfile(prev => ({ ...prev, firstName: map['profile_firstName'] }));
    if (map['profile_lastName']) setProfile(prev => ({ ...prev, lastName: map['profile_lastName'] }));
    if (map['profile_email']) setProfile(prev => ({ ...prev, email: map['profile_email'] }));
    if (map['profile_org']) setProfile(prev => ({ ...prev, org: map['profile_org'] }));
  }, [settingsResp]);

  const saveSettingsMutation = useMutation({
    mutationFn: async (payloads: Array<{ user_id: string; key: string; value: any }>) => {
      await Promise.all(payloads.map(p => fetch('/api/settings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p) })));
    },
    onSuccess: () => {
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    }
  });

  const handleProfileChange = (field: string, value: string) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    const uid = user?.id || 'default';
    const payloads = [
      { user_id: uid, key: 'setting_credibilityThreshold', value: String(credibilityThreshold[0]) },
      { user_id: uid, key: 'setting_realTimeAnalysis', value: String(realTimeAnalysis) },
      { user_id: uid, key: 'setting_botDetection', value: String(botDetection) },
      { user_id: uid, key: 'setting_sentimentAlerts', value: String(sentimentAlerts) },
      // Profile Payloads
      { user_id: uid, key: 'profile_firstName', value: profile.firstName },
      { user_id: uid, key: 'profile_lastName', value: profile.lastName },
      { user_id: uid, key: 'profile_email', value: profile.email },
      { user_id: uid, key: 'profile_org', value: profile.org }
    ];

    saveSettingsMutation.mutate(payloads);
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
        <motion.div variants={itemVariants}>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Manage your account and application preferences</p>
        </motion.div>

        {/* Settings Tabs */}
        <motion.div variants={itemVariants}>
          <Tabs defaultValue="general" className="space-y-6">
            <TabsList className="glass-card border-border/50 flex-wrap h-auto p-1">
              <TabsTrigger value="general" className="gap-2">
                <SettingsIcon className="h-4 w-4" />
                General
              </TabsTrigger>
              <TabsTrigger value="profile" className="gap-2">
                <User className="h-4 w-4" />
                Profile
              </TabsTrigger>
              <TabsTrigger value="notifications" className="gap-2">
                <Bell className="h-4 w-4" />
                Notifications
              </TabsTrigger>
              <TabsTrigger value="api" className="gap-2">
                <Key className="h-4 w-4" />
                API
              </TabsTrigger>
              <TabsTrigger value="appearance" className="gap-2">
                <Palette className="h-4 w-4" />
                Appearance
              </TabsTrigger>
              <TabsTrigger value="security" className="gap-2">
                <Shield className="h-4 w-4" />
                Security
              </TabsTrigger>
            </TabsList>

            {/* General Settings */}
            <TabsContent value="general">
              <div className="grid gap-6">
                <Card className="glass-card border-border/50">
                  <CardHeader>
                    <CardTitle>Analysis Settings</CardTitle>
                    <CardDescription>Configure how Sentinel Engine analyzes reviews</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-2">
                      <Label>Default Platform</Label>
                      <Select defaultValue="all">
                        <SelectTrigger className="glass-card border-border/50">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="glass-card border-border/50">
                          <SelectItem value="all">All Platforms</SelectItem>
                          <SelectItem value="twitter">Twitter/X</SelectItem>
                          <SelectItem value="reddit">Reddit</SelectItem>
                          <SelectItem value="youtube">YouTube</SelectItem>
                          <SelectItem value="forums">Forums</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Analysis Language</Label>
                      <Select defaultValue="en">
                        <SelectTrigger className="glass-card border-border/50">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="glass-card border-border/50">
                          <SelectItem value="en">English</SelectItem>
                          <SelectItem value="es">Spanish</SelectItem>
                          <SelectItem value="fr">French</SelectItem>
                          <SelectItem value="de">German</SelectItem>
                          <SelectItem value="auto">Auto-detect</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Credibility Threshold</Label>
                          <p className="text-xs text-muted-foreground">Minimum score to mark as verified</p>
                        </div>
                        <span className="text-sm font-medium">{credibilityThreshold}%</span>
                      </div>
                      <Slider
                        value={credibilityThreshold}
                        onValueChange={setCredibilityThreshold}
                        max={100}
                        min={0}
                        step={5}
                        className="w-full"
                      />
                    </div>

                    <Separator />

                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Real-time Analysis</Label>
                          <p className="text-xs text-muted-foreground">Analyze reviews as they come in</p>
                        </div>
                        <Switch
                          checked={realTimeAnalysis}
                          onCheckedChange={setRealTimeAnalysis}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Bot Detection</Label>
                          <p className="text-xs text-muted-foreground">Automatically flag suspicious reviews</p>
                        </div>
                        <Switch
                          checked={botDetection}
                          onCheckedChange={setBotDetection}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <Label>Sentiment Alerts</Label>
                          <p className="text-xs text-muted-foreground">Alert on significant sentiment changes</p>
                        </div>
                        <Switch
                          checked={sentimentAlerts}
                          onCheckedChange={setSentimentAlerts}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="glass-card border-border/50">
                  <CardHeader>
                    <CardTitle>Data Retention</CardTitle>
                    <CardDescription>Configure how long data is stored</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Keep raw reviews for</Label>
                      <Select defaultValue="90">
                        <SelectTrigger className="glass-card border-border/50">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="glass-card border-border/50">
                          <SelectItem value="30">30 days</SelectItem>
                          <SelectItem value="60">60 days</SelectItem>
                          <SelectItem value="90">90 days</SelectItem>
                          <SelectItem value="180">180 days</SelectItem>
                          <SelectItem value="365">1 year</SelectItem>
                          <SelectItem value="unlimited">Unlimited</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Archive old reports</Label>
                        <p className="text-xs text-muted-foreground">Move old reports to archive</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Profile Settings */}
            <TabsContent value="profile">
              <Card className="glass-card border-border/50">
                <CardHeader>
                  <CardTitle>Profile Information</CardTitle>
                  <CardDescription>Update your personal details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center gap-6">
                    <div className="h-20 w-20 rounded-full bg-gradient-to-br from-sentinel-positive to-sentinel-credibility flex items-center justify-center">
                      <span className="text-2xl font-bold text-black">SE</span>
                    </div>
                    <div>
                      <Button variant="outline" size="sm">Change Avatar</Button>
                      <p className="text-xs text-muted-foreground mt-1">JPG, PNG or GIF. Max 2MB.</p>
                    </div>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label>First Name</Label>
                      <Input
                        value={profile.firstName}
                        onChange={(e) => handleProfileChange('firstName', e.target.value)}
                        className="glass-card border-border/50"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Last Name</Label>
                      <Input
                        value={profile.lastName}
                        onChange={(e) => handleProfileChange('lastName', e.target.value)}
                        className="glass-card border-border/50"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Email</Label>
                    <Input
                      value={profile.email}
                      onChange={(e) => handleProfileChange('email', e.target.value)}
                      type="email"
                      className="glass-card border-border/50"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Organization</Label>
                    <Input
                      value={profile.org}
                      onChange={(e) => handleProfileChange('org', e.target.value)}
                      className="glass-card border-border/50"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Role</Label>
                    <Input defaultValue="Administrator" disabled className="glass-card border-border/50" />
                  </div>

                  <div className="space-y-2">
                    <Label>Timezone</Label>
                    <Select defaultValue="utc">
                      <SelectTrigger className="glass-card border-border/50">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="glass-card border-border/50">
                        <SelectItem value="utc">UTC</SelectItem>
                        <SelectItem value="est">Eastern Time (EST)</SelectItem>
                        <SelectItem value="pst">Pacific Time (PST)</SelectItem>
                        <SelectItem value="gmt">GMT</SelectItem>
                        <SelectItem value="cet">Central European Time</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Notifications Settings */}
            <TabsContent value="notifications">
              <Card className="glass-card border-border/50">
                <CardHeader>
                  <CardTitle>Notification Preferences</CardTitle>
                  <CardDescription>Choose how you want to be notified</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <h3 className="text-sm font-medium flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      Email Notifications
                    </h3>
                    <div className="space-y-3 pl-6">
                      <div className="flex items-center justify-between">
                        <Label>Critical Alerts</Label>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Daily Digest</Label>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Weekly Reports</Label>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Product Updates</Label>
                        <Switch />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-4">
                    <h3 className="text-sm font-medium flex items-center gap-2">
                      <Smartphone className="h-4 w-4" />
                      Push Notifications
                    </h3>
                    <div className="space-y-3 pl-6">
                      <div className="flex items-center justify-between">
                        <Label>Browser Notifications</Label>
                        <Switch defaultChecked />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label>Mobile Push</Label>
                        <Switch />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-4">
                    <h3 className="text-sm font-medium">Quiet Hours</h3>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Enable Quiet Hours</Label>
                        <p className="text-xs text-muted-foreground">Pause non-critical notifications</p>
                      </div>
                      <Switch />
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
                        <Label>From</Label>
                        <Input type="time" defaultValue="22:00" className="glass-card border-border/50" />
                      </div>
                      <div className="space-y-2">
                        <Label>To</Label>
                        <Input type="time" defaultValue="08:00" className="glass-card border-border/50" />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* API Settings */}
            <TabsContent value="api">
              <div className="grid gap-6">
                <Card className="glass-card border-border/50">
                  <CardHeader>
                    <CardTitle>API Configuration</CardTitle>
                    <CardDescription>Manage your API keys and endpoints</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-2">
                      <Label>API Key</Label>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <Input
                            type={showApiKey ? 'text' : 'password'}
                            defaultValue="sk-sentinel-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                            className="glass-card border-border/50 pr-10"
                            readOnly
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                            onClick={() => setShowApiKey(!showApiKey)}
                          >
                            {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </Button>
                        </div>
                        <Button variant="outline">Regenerate</Button>
                      </div>
                      <p className="text-xs text-muted-foreground">Keep this key secure. Never share it publicly.</p>
                    </div>

                    <div className="space-y-2">
                      <Label>API Endpoint</Label>
                      <Input
                        defaultValue="https://api.sentinel-engine.ai/v1"
                        className="glass-card border-border/50"
                        readOnly
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Webhook URL</Label>
                      <Input
                        placeholder="https://your-server.com/webhook"
                        className="glass-card border-border/50"
                      />
                      <p className="text-xs text-muted-foreground">Receive real-time alerts via webhook</p>
                    </div>
                  </CardContent>
                </Card>

                <Card className="glass-card border-border/50">
                  <CardHeader>
                    <CardTitle>Usage & Limits</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>API Calls This Month</span>
                        <span>8,432 / 10,000</span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: '84.32%' }}
                          transition={{ duration: 1, ease: 'easeOut' }}
                          className="h-full bg-sentinel-credibility rounded-full"
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Reviews Analyzed</span>
                        <span>142,890 / 500,000</span>
                      </div>
                      <div className="h-2 rounded-full bg-muted overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: '28.58%' }}
                          transition={{ duration: 1, ease: 'easeOut', delay: 0.1 }}
                          className="h-full bg-sentinel-positive rounded-full"
                        />
                      </div>
                    </div>
                    <Badge variant="outline" className="bg-sentinel-positive/20 text-sentinel-positive">
                      Pro Plan
                    </Badge>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Appearance Settings */}
            <TabsContent value="appearance">
              <Card className="glass-card border-border/50">
                <CardHeader>
                  <CardTitle>Appearance</CardTitle>
                  <CardDescription>Customize the look and feel</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <Label>Theme</Label>
                    <div className="grid grid-cols-3 gap-4">
                      {['light', 'dark', 'system'].map((t) => (
                        <button
                          key={t}
                          onClick={() => setTheme(t as 'light' | 'dark' | 'system')}
                          className={`p-4 rounded-xl border-2 transition-all ${theme === t
                            ? 'border-sentinel-positive bg-sentinel-positive/10'
                            : 'border-border hover:border-sentinel-positive/50'
                            }`}
                        >
                          <div className={`h-8 w-8 mx-auto rounded-lg mb-2 ${t === 'light' ? 'bg-white' : t === 'dark' ? 'bg-gray-900' : 'bg-gradient-to-br from-white to-gray-900'
                            }`} />
                          <span className="text-sm capitalize">{t}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Compact Mode</Label>
                        <p className="text-xs text-muted-foreground">Reduce spacing and padding</p>
                      </div>
                      <Switch />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Animations</Label>
                        <p className="text-xs text-muted-foreground">Enable UI animations</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <Label>Blur Effects</Label>
                        <p className="text-xs text-muted-foreground">Enable glassmorphism blur</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Security Settings */}
            <TabsContent value="security">
              <div className="grid gap-6">
                <Card className="glass-card border-border/50">
                  <CardHeader>
                    <CardTitle>Password</CardTitle>
                    <CardDescription>Update your password</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Current Password</Label>
                      <Input type="password" className="glass-card border-border/50" />
                    </div>
                    <div className="space-y-2">
                      <Label>New Password</Label>
                      <Input type="password" className="glass-card border-border/50" />
                    </div>
                    <div className="space-y-2">
                      <Label>Confirm New Password</Label>
                      <Input type="password" className="glass-card border-border/50" />
                    </div>
                    <Button variant="outline">Update Password</Button>
                  </CardContent>
                </Card>

                <Card className="glass-card border-border/50">
                  <CardHeader>
                    <CardTitle>Two-Factor Authentication</CardTitle>
                    <CardDescription>Add an extra layer of security</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-sentinel-positive/20">
                          <Shield className="h-5 w-5 text-sentinel-positive" />
                        </div>
                        <div>
                          <p className="font-medium">Two-Factor Authentication</p>
                          <p className="text-xs text-muted-foreground">Currently disabled</p>
                        </div>
                      </div>
                      <Button variant="outline">Enable</Button>
                    </div>
                  </CardContent>
                </Card>

                <Card className="glass-card border-border/50">
                  <CardHeader>
                    <CardTitle>Active Sessions</CardTitle>
                    <CardDescription>Manage your active sessions</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 rounded-lg bg-accent/30">
                        <div className="flex items-center gap-3">
                          <Globe className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <p className="text-sm font-medium">Chrome on macOS</p>
                            <p className="text-xs text-muted-foreground">Current session · San Francisco, US</p>
                          </div>
                        </div>
                        <Badge className="bg-sentinel-positive/20 text-sentinel-positive">Active</Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 rounded-lg hover:bg-accent/30 transition-colors">
                        <div className="flex items-center gap-3">
                          <Smartphone className="h-5 w-5 text-muted-foreground" />
                          <div>
                            <p className="text-sm font-medium">Safari on iPhone</p>
                            <p className="text-xs text-muted-foreground">Last active 2 hours ago · San Francisco, US</p>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm">Revoke</Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>
          </Tabs>
        </motion.div>

        {/* Save Button */}
        <motion.div variants={itemVariants} className="flex justify-end">
          <Button
            onClick={handleSave}
            className="bg-sentinel-positive hover:bg-sentinel-positive/90 text-black gap-2"
          >
            {saved ? (
              <>
                <Check className="h-4 w-4" />
                Saved!
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                Save Changes
              </>
            )}
          </Button>
        </motion.div>
      </motion.div>
    </DashboardLayout>
  );
};

export default Settings;
