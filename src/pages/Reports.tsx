import { useState } from 'react';
import { motion } from 'framer-motion';
import {
    FileText,
    Download,
    Calendar,
    Clock,
    CheckCircle2,
    Loader2,
    Plus,
    Filter,
    Search,
    FileBarChart,
    FileSpreadsheet,
    FilePieChart
} from 'lucide-react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';

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

type ReportStatus = 'completed' | 'generating' | 'scheduled';
type ReportType = 'sentiment' | 'credibility' | 'competitive' | 'executive';

interface Report {
    id: string;
    name: string;
    type: ReportType;
    status: ReportStatus;
    createdAt: string;
    size: string;
    period: string;
}

const reports: Report[] = [
    {
        id: '1',
        name: 'Monthly Sentiment Analysis - December 2025',
        type: 'sentiment',
        status: 'completed',
        createdAt: '2025-12-28',
        size: '2.4 MB',
        period: 'Dec 1 - Dec 31, 2025'
    },
    {
        id: '2',
        name: 'Q4 Credibility Assessment',
        type: 'credibility',
        status: 'completed',
        createdAt: '2025-12-25',
        size: '4.1 MB',
        period: 'Oct 1 - Dec 31, 2025'
    },
    {
        id: '3',
        name: 'Competitive Analysis Report',
        type: 'competitive',
        status: 'generating',
        createdAt: '2026-01-09',
        size: '-',
        period: 'Jan 1 - Jan 9, 2026'
    },
    {
        id: '4',
        name: 'Weekly Executive Summary',
        type: 'executive',
        status: 'scheduled',
        createdAt: '2026-01-15',
        size: '-',
        period: 'Jan 9 - Jan 15, 2026'
    },
    {
        id: '5',
        name: 'November Sentiment Analysis',
        type: 'sentiment',
        status: 'completed',
        createdAt: '2025-11-30',
        size: '2.1 MB',
        period: 'Nov 1 - Nov 30, 2025'
    },
];

const reportTypes = {
    sentiment: { label: 'Sentiment', icon: FilePieChart, color: 'bg-sentinel-positive/20 text-sentinel-positive' },
    credibility: { label: 'Credibility', icon: FileBarChart, color: 'bg-sentinel-credibility/20 text-sentinel-credibility' },
    competitive: { label: 'Competitive', icon: FileSpreadsheet, color: 'bg-purple-500/20 text-purple-400' },
    executive: { label: 'Executive', icon: FileText, color: 'bg-amber-500/20 text-amber-400' },
};

const statusConfig = {
    completed: { label: 'Completed', icon: CheckCircle2, color: 'bg-sentinel-positive/20 text-sentinel-positive' },
    generating: { label: 'Generating', icon: Loader2, color: 'bg-sentinel-credibility/20 text-sentinel-credibility' },
    scheduled: { label: 'Scheduled', icon: Clock, color: 'bg-muted text-muted-foreground' },
};

const Reports = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState<string>('all');
    const [isCreateOpen, setIsCreateOpen] = useState(false);

    const filteredReports = reports.filter(report => {
        const matchesSearch = report.name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesType = filterType === 'all' || report.type === filterType;
        return matchesSearch && matchesType;
    });

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
                        <h1 className="text-2xl font-bold">Reports</h1>
                        <p className="text-muted-foreground">Generate and manage your analysis reports</p>
                    </div>
                    <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                        <DialogTrigger asChild>
                            <Button className="bg-sentinel-positive hover:bg-sentinel-positive/90 text-black">
                                <Plus className="h-4 w-4 mr-2" />
                                Create Report
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="glass-card border-border/50">
                            <DialogHeader>
                                <DialogTitle>Create New Report</DialogTitle>
                                <DialogDescription>
                                    Configure and generate a new analysis report
                                </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4 py-4">
                                <div className="space-y-2">
                                    <Label>Report Name</Label>
                                    <Input placeholder="Enter report name" className="glass-card border-border/50" />
                                </div>
                                <div className="space-y-2">
                                    <Label>Report Type</Label>
                                    <Select defaultValue="sentiment">
                                        <SelectTrigger className="glass-card border-border/50">
                                            <SelectValue placeholder="Select type" />
                                        </SelectTrigger>
                                        <SelectContent className="glass-card border-border/50">
                                            <SelectItem value="sentiment">Sentiment Analysis</SelectItem>
                                            <SelectItem value="credibility">Credibility Assessment</SelectItem>
                                            <SelectItem value="competitive">Competitive Analysis</SelectItem>
                                            <SelectItem value="executive">Executive Summary</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <div className="space-y-2">
                                    <Label>Date Range</Label>
                                    <div className="grid grid-cols-2 gap-2">
                                        <Input type="date" className="glass-card border-border/50" />
                                        <Input type="date" className="glass-card border-border/50" />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label>Include Sections</Label>
                                    <div className="space-y-2">
                                        <div className="flex items-center space-x-2">
                                            <Checkbox id="trends" defaultChecked />
                                            <label htmlFor="trends" className="text-sm">Sentiment Trends</label>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <Checkbox id="aspects" defaultChecked />
                                            <label htmlFor="aspects" className="text-sm">Aspect Analysis</label>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <Checkbox id="alerts" defaultChecked />
                                            <label htmlFor="alerts" className="text-sm">Alert Summary</label>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                            <Checkbox id="credibility" />
                                            <label htmlFor="credibility" className="text-sm">Credibility Report</label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
                                <Button className="bg-sentinel-positive hover:bg-sentinel-positive/90 text-black" onClick={() => setIsCreateOpen(false)}>
                                    Generate Report
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </motion.div>

                {/* Filters */}
                <motion.div variants={itemVariants} className="flex flex-col sm:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search reports..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 glass-card border-border/50"
                        />
                    </div>
                    <Select value={filterType} onValueChange={setFilterType}>
                        <SelectTrigger className="w-full sm:w-[180px] glass-card border-border/50">
                            <Filter className="h-4 w-4 mr-2" />
                            <SelectValue placeholder="Filter by type" />
                        </SelectTrigger>
                        <SelectContent className="glass-card border-border/50">
                            <SelectItem value="all">All Types</SelectItem>
                            <SelectItem value="sentiment">Sentiment</SelectItem>
                            <SelectItem value="credibility">Credibility</SelectItem>
                            <SelectItem value="competitive">Competitive</SelectItem>
                            <SelectItem value="executive">Executive</SelectItem>
                        </SelectContent>
                    </Select>
                </motion.div>

                {/* Report Templates */}
                <motion.div variants={itemVariants}>
                    <h2 className="text-lg font-semibold mb-4">Quick Templates</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {Object.entries(reportTypes).map(([key, config]) => (
                            <Card
                                key={key}
                                className="glass-card border-border/50 cursor-pointer hover:border-sentinel-positive/50 transition-all group"
                                onClick={() => setIsCreateOpen(true)}
                            >
                                <CardContent className="pt-6">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg ${config.color}`}>
                                            <config.icon className="h-5 w-5" />
                                        </div>
                                        <div>
                                            <p className="font-medium group-hover:text-sentinel-positive transition-colors">{config.label}</p>
                                            <p className="text-xs text-muted-foreground">Quick generate</p>
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </motion.div>

                {/* Reports List */}
                <motion.div variants={itemVariants}>
                    <h2 className="text-lg font-semibold mb-4">Recent Reports</h2>
                    <Card className="glass-card border-border/50">
                        <CardContent className="p-0">
                            <div className="divide-y divide-border/50">
                                {filteredReports.map((report, index) => {
                                    const typeConfig = reportTypes[report.type];
                                    const statusConf = statusConfig[report.status];

                                    return (
                                        <motion.div
                                            key={report.id}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: index * 0.05 }}
                                            className="flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-accent/30 transition-colors gap-4"
                                        >
                                            <div className="flex items-start gap-3">
                                                <div className={`p-2 rounded-lg ${typeConfig.color}`}>
                                                    <typeConfig.icon className="h-5 w-5" />
                                                </div>
                                                <div>
                                                    <p className="font-medium">{report.name}</p>
                                                    <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                                                        <Calendar className="h-3 w-3" />
                                                        <span>{report.period}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3 sm:gap-4">
                                                <Badge variant="outline" className={statusConf.color}>
                                                    <statusConf.icon className={`h-3 w-3 mr-1 ${report.status === 'generating' ? 'animate-spin' : ''}`} />
                                                    {statusConf.label}
                                                </Badge>
                                                {report.status === 'completed' && (
                                                    <>
                                                        <span className="text-sm text-muted-foreground hidden sm:block">{report.size}</span>
                                                        <Button size="sm" variant="outline" className="gap-2">
                                                            <Download className="h-4 w-4" />
                                                            <span className="hidden sm:inline">Download</span>
                                                        </Button>
                                                    </>
                                                )}
                                            </div>
                                        </motion.div>
                                    );
                                })}
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>

                {/* Stats Cards */}
                <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Card className="glass-card border-border/50">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Reports Generated</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">47</div>
                            <p className="text-xs text-muted-foreground">This month</p>
                        </CardContent>
                    </Card>
                    <Card className="glass-card border-border/50">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Storage Used</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">2.8 GB</div>
                            <p className="text-xs text-muted-foreground">of 10 GB</p>
                        </CardContent>
                    </Card>
                    <Card className="glass-card border-border/50">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">Scheduled Reports</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">3</div>
                            <p className="text-xs text-muted-foreground">Upcoming</p>
                        </CardContent>
                    </Card>
                </motion.div>
            </motion.div>
        </DashboardLayout>
    );
};

export default Reports;
