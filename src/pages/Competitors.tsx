import { useState, useEffect } from 'react';
import { getCompare, getProducts as apiGetProducts, triggerScrape } from '@/lib/api';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Swords, Trophy, AlertTriangle, RefreshCw } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface ComparisonData {
    aspects: { subject: string; A: number; B: number; fullMark: number }[];
    metrics: {
        productA: { sentiment: number; credibility: number; reviewCount: number };
        productB: { sentiment: number; credibility: number; reviewCount: number };
    };
    barData: { name: string; Positive: number; Negative: number; Neutral: number }[];
}

const Competitors = () => {
    const [products, setProducts] = useState<any[]>([]);
    const [selectedA, setSelectedA] = useState<string>('');
    const [selectedB, setSelectedB] = useState<string>('');
    const [data, setData] = useState<ComparisonData | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const { toast } = useToast();
    const queryClient = useQueryClient();

    // Fetch Products List via React Query
    const { data: productList = [] } = useQuery({ queryKey: ['products'], queryFn: apiGetProducts });

    useEffect(() => {
        if (Array.isArray(productList)) {
            setProducts(productList as any[]);
            // Auto-select first two products for instant value
            if (productList.length >= 2 && !selectedA && !selectedB) {
                setSelectedA(productList[0].id);
                setSelectedB(productList[1].id);
            }
        }
    }, [productList]);

    // Aggressive Polling Mode: 1s interval when analyzing
    const pollInterval = isAnalyzing ? 1000 : 0;

    // Server-side Comparison
    const { data: compareRes } = useQuery({
        queryKey: ['compare', selectedA, selectedB],
        queryFn: () => getCompare(selectedA, selectedB),
        enabled: !!selectedA && !!selectedB,
        refetchInterval: pollInterval
    });

    useEffect(() => {
        if (!selectedA || !selectedB || !compareRes?.success) return;

        const metrics = compareRes.data.metrics;
        if (!metrics) return;
        if (!metrics.productA || !metrics.productB) return;

        const mA = metrics.productA;
        const mB = metrics.productB;

        // Use real aspect data if available
        const subjects = new Set([...Object.keys(mA.aspects || {}), ...Object.keys(mB.aspects || {})]);
        if (subjects.size === 0) {
            ['Price', 'Quality', 'Service'].forEach(s => subjects.add(s));
        }

        const aspects = Array.from(subjects).map((subject) => ({
            subject: subject,
            A: mA.aspects?.[subject] || 0,
            B: mB.aspects?.[subject] || 0,
            fullMark: 5
        }));

        const barData = [
            { name: getName(selectedA), Positive: mA.counts.positive, Negative: mA.counts.negative, Neutral: mA.counts.neutral },
            { name: getName(selectedB), Positive: mB.counts.positive, Negative: mB.counts.negative, Neutral: mB.counts.neutral },
        ];

        const comp: ComparisonData = {
            aspects,
            metrics: {
                productA: { sentiment: mA.sentiment, credibility: mA.credibility, reviewCount: mA.reviewCount },
                productB: { sentiment: mB.sentiment, credibility: mB.credibility, reviewCount: mB.reviewCount },
            },
            barData
        };

        setData(comp);

    }, [compareRes, selectedA, selectedB]);

    const getName = (id: string) => products.find(p => p.id === id)?.name || productList.find((p: any) => p.id === id)?.name || 'Product';

    const getWinner = () => {
        if (!data) return null;
        if (data.metrics.productA.sentiment > data.metrics.productB.sentiment) return selectedA;
        if (data.metrics.productB.sentiment > data.metrics.productA.sentiment) return selectedB;
        return null;
    };

    const handleLiveAnalysis = async () => {
        if (!selectedA || !selectedB) {
            toast({ title: "Select Products", description: "Please select two contenders first.", variant: "destructive" });
            return;
        }
        setIsAnalyzing(true);
        toast({ title: "War Room Activated", description: "Deploying agents for both contenders..." });

        try {
            await Promise.all([triggerScrape(selectedA), triggerScrape(selectedB)]);
            queryClient.invalidateQueries({ queryKey: ['compare', selectedA, selectedB] });

            // Poll for 30s
            setTimeout(() => {
                setIsAnalyzing(false);
                toast({ title: "Analysis Complete", description: "Refresh completed." });
            }, 30000);

        } catch (e) {
            setIsAnalyzing(false);
            toast({ title: "Error", description: "Failed to start scraping.", variant: "destructive" });
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold flex items-center gap-2">
                            <Swords className="h-6 w-6 text-sentinel-credibility" />
                            Competitor War Room
                            {isAnalyzing && (
                                <span className="text-xs bg-yellow-500/10 text-yellow-500 px-2 py-0.5 rounded animate-pulse border border-yellow-500/20">
                                    ⚡ Syncing...
                                </span>
                            )}
                        </h1>
                        <p className="text-muted-foreground">Head-to-head product comparison</p>
                    </div>
                    <div>
                        <Button
                            variant="outline"
                            disabled={!selectedA || !selectedB || isAnalyzing}
                            onClick={handleLiveAnalysis}
                        >
                            <RefreshCw className={`mr-2 h-4 w-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
                            {isAnalyzing ? 'Analyzing...' : 'Live Analysis'}
                        </Button>
                    </div>
                </div>

                {/* Selection Controls */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className={`glass-card ${getWinner() === selectedA ? 'border-sentinel-positive' : 'border-sentinel-positive/30'}`}>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle className="text-sentinel-positive">Contender A</CardTitle>
                            {getWinner() === selectedA && <Badge className="bg-sentinel-positive text-white"><Trophy className="w-3 h-3 mr-1" /> Winner</Badge>}
                        </CardHeader>
                        <CardContent>
                            <Select value={selectedA} onValueChange={setSelectedA}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select Product A" />
                                </SelectTrigger>
                                <SelectContent>
                                    {products.map(p => (
                                        <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </CardContent>
                    </Card>

                    <Card className={`glass-card ${getWinner() === selectedB ? 'border-sentinel-positive' : 'border-sentinel-negative/30'}`}>
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle className="text-sentinel-negative">Contender B</CardTitle>
                            {getWinner() === selectedB && <Badge className="bg-sentinel-positive text-white"><Trophy className="w-3 h-3 mr-1" /> Winner</Badge>}
                        </CardHeader>
                        <CardContent>
                            <Select value={selectedB} onValueChange={setSelectedB}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select Product B" />
                                </SelectTrigger>
                                <SelectContent>
                                    {products.map(p => (
                                        <SelectItem key={p.id} value={p.id} disabled={p.id === selectedA}>{p.name}</SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </CardContent>
                    </Card>
                </div>

                {/* Comparison Viz */}
                {(!selectedA || !selectedB) && (
                    <div className="text-sm text-muted-foreground flex items-center gap-2">
                        <AlertTriangle className="h-4 w-4" /> Select two products to unlock comparison.
                    </div>
                )}
                {data && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">

                        {/* Top Row: Radar & Metrics */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                            {/* Radar Chart */}
                            <Card className={`glass-card border-border/50 ${isAnalyzing ? 'border-yellow-500/20' : ''}`}>
                                <CardHeader>
                                    <CardTitle>Aspect Battle</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="h-[300px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data.aspects}>
                                                <PolarGrid stroke="hsl(var(--border))" />
                                                <PolarAngleAxis dataKey="subject" tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                                                <PolarRadiusAxis angle={30} domain={[0, 5]} stroke="hsl(var(--border))" />
                                                <Radar
                                                    name={getName(selectedA)}
                                                    dataKey="A"
                                                    stroke="hsl(var(--sentinel-positive))"
                                                    fill="hsl(var(--sentinel-positive))"
                                                    fillOpacity={0.3}
                                                />
                                                <Radar
                                                    name={getName(selectedB)}
                                                    dataKey="B"
                                                    stroke="hsl(var(--sentinel-negative))"
                                                    fill="hsl(var(--sentinel-negative))"
                                                    fillOpacity={0.3}
                                                />
                                                <Legend />
                                                <Tooltip
                                                    contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))' }}
                                                />
                                            </RadarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Bar Chart: Counts */}
                            <Card className={`glass-card border-border/50 ${isAnalyzing ? 'border-yellow-500/20' : ''}`}>
                                <CardHeader><CardTitle>Sentiment Volume Comparison</CardTitle></CardHeader>
                                <CardContent>
                                    <div className="h-[300px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={data.barData}>
                                                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                                                <XAxis dataKey="name" />
                                                <YAxis />
                                                <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ backgroundColor: 'hsl(var(--card))' }} />
                                                <Legend />
                                                <Bar dataKey="Positive" fill="hsl(var(--sentinel-positive))" />
                                                <Bar dataKey="Neutral" fill="hsl(var(--muted))" />
                                                <Bar dataKey="Negative" fill="hsl(var(--sentinel-negative))" />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Detailed Comparison Table */}
                        <Card className={`glass-card border-border/50 ${isAnalyzing ? 'border-yellow-500/20' : ''}`}>
                            <CardHeader>
                                <CardTitle>Head-to-Head Stats</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead className="w-[200px]">Metric</TableHead>
                                            <TableHead className="text-center text-sentinel-positive font-bold">{getName(selectedA)}</TableHead>
                                            <TableHead className="text-center text-sentinel-negative font-bold">{getName(selectedB)}</TableHead>
                                            <TableHead className="text-right">Difference</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        <TableRow>
                                            <TableCell className="font-medium">Sentiment Score</TableCell>
                                            <TableCell className="text-center text-xl">{data.metrics.productA.sentiment.toFixed(1)}%</TableCell>
                                            <TableCell className="text-center text-xl">{data.metrics.productB.sentiment.toFixed(1)}%</TableCell>
                                            <TableCell className="text-right font-mono">
                                                {Math.abs(data.metrics.productA.sentiment - data.metrics.productB.sentiment).toFixed(1)}%
                                            </TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell className="font-medium">Review Volume</TableCell>
                                            <TableCell className="text-center">{data.metrics.productA.reviewCount}</TableCell>
                                            <TableCell className="text-center">{data.metrics.productB.reviewCount}</TableCell>
                                            <TableCell className="text-right font-mono">
                                                {Math.abs(data.metrics.productA.reviewCount - data.metrics.productB.reviewCount)}
                                            </TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell className="font-medium">Credibility Score</TableCell>
                                            <TableCell className="text-center">{data.metrics.productA.credibility.toFixed(1)}%</TableCell>
                                            <TableCell className="text-center">{data.metrics.productB.credibility.toFixed(1)}%</TableCell>
                                            <TableCell className="text-right font-mono">
                                                {Math.abs(data.metrics.productA.credibility - data.metrics.productB.credibility).toFixed(1)}%
                                            </TableCell>
                                        </TableRow>
                                    </TableBody>
                                </Table>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
};

export default Competitors;
