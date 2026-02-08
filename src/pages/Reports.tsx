import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { getReports, downloadReport, exportReport, getProducts } from '@/lib/api';
import { toast } from 'sonner';
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
import { format } from 'date-fns';

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

const reportTypes = {
    sentiment: { label: 'Sentiment', icon: FilePieChart, color: 'bg-sentinel-positive/20 text-sentinel-positive' },
    credibility: { label: 'Credibility', icon: FileBarChart, color: 'bg-sentinel-credibility/20 text-sentinel-credibility' },
    competitive: { label: 'Competitive', icon: FileSpreadsheet, color: 'bg-purple-500/20 text-purple-400' },
    executive: { label: 'Executive', icon: FileText, color: 'bg-amber-500/20 text-amber-400' },
};

const Reports = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [filterType, setFilterType] = useState<string>('all');
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    const handleGenerateReport = async (productId: string, format: 'pdf' | 'excel' | 'csv') => {
        setIsGenerating(true);
        try {
            toast.info(`Generating ${format.toUpperCase()} report...`);
            await exportReport(productId, format);
            toast.success("Report Generated & Downloaded");
            setIsCreateOpen(false);
        } catch (e) {
            toast.error("Failed to generate report");
        } finally {
            setIsGenerating(false);
        }
    };

    const { data: reports = [], isLoading } = useQuery({
        queryKey: ['reports'],
        queryFn: getReports,
        refetchInterval: 10000
    });

    const filteredReports = reports.filter((report: any) => {
        const matchesSearch = report.filename.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesSearch;
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
                    <Button className="bg-sentinel-positive hover:bg-sentinel-positive/90 text-black" onClick={() => setIsCreateOpen(true)}>
                        <Plus className="h-4 w-4 mr-2" />
                        Create Report
                    </Button>
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
                </motion.div>

                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Generate New Report</DialogTitle>
                            <DialogDescription>
                                Select a product to generate a comprehensive sentiment analysis report.
                            </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label>Select Product</Label>
                                <ProductSelector onSelect={(id) => {
                                    // Trigger immediate download or create async task?
                                    // For now, trigger download as per "Real Time" requirement
                                    handleGenerateReport(id, 'pdf');
                                }} />
                            </div>
                        </div>
                    </DialogContent>
                </Dialog>

                {/* Reports List */}
                <motion.div variants={itemVariants}>
                    <Card className="glass-card border-border/50">
                        <CardHeader>
                            <CardTitle>Generated Reports</CardTitle>
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <div className="text-center py-8">Loading reports...</div>
                            ) : filteredReports.length === 0 ? (
                                <div className="text-center py-8 text-muted-foreground">No reports found.</div>
                            ) : (
                                <div className="space-y-4">
                                    {filteredReports.map((report: any) => (
                                        <div key={report.filename} className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
                                            <div className="flex items-center gap-4">
                                                <div className="p-2 rounded bg-sentinel-credibility/20 text-sentinel-credibility">
                                                    <FileText className="h-6 w-6" />
                                                </div>
                                                <div>
                                                    <p className="font-medium">{report.filename}</p>
                                                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                        <Clock className="h-3 w-3" />
                                                        {new Date(report.created_at).toLocaleDateString()}
                                                        <span>•</span>
                                                        <span>{(report.size / 1024).toFixed(1)} KB</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <Button variant="outline" size="sm" onClick={() => downloadReport(report.filename)}>
                                                <Download className="h-4 w-4 mr-2" />
                                                Download
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            </motion.div>
        </DashboardLayout>
    );
};

// Helper Component for Product Selection
const ProductSelector = ({ onSelect }: { onSelect: (id: string) => void }) => {
    const { data: products = [], isLoading } = useQuery({ queryKey: ['products'], queryFn: getProducts });

    if (isLoading) return <div className="text-sm text-muted-foreground p-2">Loading products...</div>;
    if (!products || products.length === 0) return <div className="text-sm p-2">No products found.</div>;

    return (
        <div className="space-y-2 max-h-64 overflow-y-auto border rounded p-2">
            {products.map((p: any) => (
                <div
                    key={p.id}
                    className="flex items-center justify-between p-2 hover:bg-muted/50 rounded cursor-pointer group"
                    onClick={() => onSelect(p.id)}
                >
                    <div>
                        <div className="font-medium text-sm">{p.name}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-[200px]">{p.description}</div>
                    </div>
                    <Button size="sm" variant="ghost" className="opacity-0 group-hover:opacity-100 h-8">Select</Button>
                </div>
            ))}
        </div>
    );
};

export default Reports;
