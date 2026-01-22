import { useState, useEffect, useMemo } from 'react';
import { getCompare, getProducts as apiGetProducts, getReviews } from '@/lib/api';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Swords, TrendingUp, Trophy, AlertTriangle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { SentimentDistribution } from '@/components/dashboard/SentimentDistribution';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

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

    // Fetch Products List via React Query
    const { data: productList = [], isLoading: productsLoading } = useQuery({ queryKey: ['products'], queryFn: apiGetProducts });

    useEffect(() => {
        if (Array.isArray(productList)) setProducts(productList as any[]);
    }, [productList]);

    // Fetch reviews for selected products and compute comparison locally
    const { data: reviewsAData = {} } = useQuery({ 
        queryKey: ['reviews', selectedA], 
        queryFn: () => selectedA ? getReviews(selectedA) : Promise.resolve([]), 
        enabled: !!selectedA 
    });
    const { data: reviewsBData = {} } = useQuery({ 
        queryKey: ['reviews', selectedB], 
        queryFn: () => selectedB ? getReviews(selectedB) : Promise.resolve([]), 
        enabled: !!selectedB 
    });

    // Safely extract arrays from potential wrapper objects
    // @ts-ignore
    const reviewsA = Array.isArray(reviewsAData) ? reviewsAData : (Array.isArray(reviewsAData?.data) ? reviewsAData.data : []);
    // @ts-ignore
    const reviewsB = Array.isArray(reviewsBData) ? reviewsBData : (Array.isArray(reviewsBData?.data) ? reviewsBData.data : []);

    useEffect(() => {
        if (!selectedA || !selectedB) return;

        // Compute metrics from reviewsA and reviewsB
        const computeMetrics = (reviews: any[]) => {
            if (!Array.isArray(reviews)) return { counts: { positive: 0, neutral: 0, negative: 0 }, sentimentPercent: 0, avgCred: 0, total: 0 };
            
            const total = reviews.length || 0;
            const counts = { positive: 0, neutral: 0, negative: 0 };
            let credibilitySum = 0;
            
            reviews.forEach(r => {
                // Try to find label in top-level or nested sentiment_analysis
                let label = (r.sentiment_label || r.sentiment || '').toString().toLowerCase();
                let cred = Number(r.credibility_score || r.credibility || 0);

                // Handle nested structure from new AI service
                if (r.sentiment_analysis && Array.isArray(r.sentiment_analysis) && r.sentiment_analysis.length > 0) {
                    const analysis = r.sentiment_analysis[0];
                    if (analysis.label) label = analysis.label.toLowerCase();
                    if (analysis.credibility) cred = Number(analysis.credibility);
                }

                if (label.includes('pos')) counts.positive++;
                else if (label.includes('neg')) counts.negative++;
                else counts.neutral++;
                
                credibilitySum += cred;
            });
            
            const sentimentPercent = total ? (counts.positive / total) * 100 : 0;
            const avgCred = total ? (credibilitySum / total) * 100 : 0;
            return { counts, sentimentPercent, avgCred, total };
        };

        const a = computeMetrics(reviewsA);
        const b = computeMetrics(reviewsB);

        // Mock aspects (Price, Quality, Battery) using sentimentPercent scaled to 0-5
        const aspects = ['Price', 'Quality', 'Battery'].map((subject) => ({
            subject,
            A: Math.round((a.sentimentPercent / 100) * 5 * 10) / 10,
            B: Math.round((b.sentimentPercent / 100) * 5 * 10) / 10,
            fullMark: 5
        }));

        const barData = [
            { name: getName(selectedA), Positive: a.counts.positive, Negative: a.counts.negative, Neutral: a.counts.neutral },
            { name: getName(selectedB), Positive: b.counts.positive, Negative: b.counts.negative, Neutral: b.counts.neutral },
        ];

        const comp: ComparisonData = {
            aspects,
            metrics: {
                productA: { sentiment: a.sentimentPercent, credibility: a.avgCred, reviewCount: a.total },
                productB: { sentiment: b.sentimentPercent, credibility: b.avgCred, reviewCount: b.total },
            },
            barData
        };

        setData(comp);

    }, [selectedA, selectedB, reviewsA, reviewsB]);

    const getName = (id: string) => products.find(p => p.id === id)?.name || productList.find((p:any)=>p.id===id)?.name || 'Product';

    const getWinner = () => {
        if (!data) return null;
        if (data.metrics.productA.sentiment > data.metrics.productB.sentiment) return selectedA;
        if (data.metrics.productB.sentiment > data.metrics.productA.sentiment) return selectedB;
        return null;
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Swords className="h-6 w-6 text-sentinel-credibility" />
                        Competitor War Room
                    </h1>
                    <p className="text-muted-foreground">Head-to-head product comparison</p>
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
                            <Card className="glass-card border-border/50">
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
                            <Card className="glass-card border-border/50">
                                <CardHeader><CardTitle>Sentiment Volume Comparison</CardTitle></CardHeader>
                                <CardContent>
                                    <div className="h-[300px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={data.barData}>
                                                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                                                <XAxis dataKey="name" />
                                                <YAxis />
                                                <Tooltip cursor={{fill: 'transparent'}} contentStyle={{ backgroundColor: 'hsl(var(--card))' }} />
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
                        <Card className="glass-card border-border/50">
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
