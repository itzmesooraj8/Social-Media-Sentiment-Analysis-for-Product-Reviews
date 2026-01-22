import { useState, useEffect, useMemo } from 'react';
import { getCompare, getProducts as apiGetProducts, getReviews } from '@/lib/api';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, Tooltip } from 'recharts';
import { Swords, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { SentimentDistribution } from '@/components/dashboard/SentimentDistribution';

interface ComparisonData {
    aspects: { subject: string; A: number; B: number; fullMark: number }[];
    metrics: {
        productA: { sentiment: number; credibility: number; reviewCount: number };
        productB: { sentiment: number; credibility: number; reviewCount: number };
    };
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

        const comp: ComparisonData = {
            aspects,
            metrics: {
                productA: { sentiment: a.sentimentPercent, credibility: a.avgCred, reviewCount: a.total },
                productB: { sentiment: b.sentimentPercent, credibility: b.avgCred, reviewCount: b.total },
            }
        };

        setData(comp);

    }, [selectedA, selectedB, reviewsA, reviewsB]);

    const getName = (id: string) => products.find(p => p.id === id)?.name || productList.find((p:any)=>p.id===id)?.name || 'Product';

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
                    <Card className="glass-card border-sentinel-positive/30">
                        <CardHeader>
                            <CardTitle className="text-sentinel-positive">Contender A</CardTitle>
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

                    <Card className="glass-card border-sentinel-negative/30">
                        <CardHeader>
                            <CardTitle className="text-sentinel-negative">Contender B</CardTitle>
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
                    <div className="text-sm text-muted-foreground">Select two products to compare.</div>
                )}
                {data && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4">

                        {/* Radar Chart */}
                        <Card className="glass-card border-border/50">
                            <CardHeader>
                                <CardTitle>Aspect Battle</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="h-[400px]">
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

                        {/* Metrics Head-to-Head */}
                        <div className="space-y-6">
                            <Card className="glass-card border-border/50">
                                <CardHeader><CardTitle>Sentiment Score</CardTitle></CardHeader>
                                <CardContent>
                                    <div className="flex items-center justify-between text-4xl font-bold mb-2">
                                        <div className="text-sentinel-positive">{data.metrics.productA.sentiment.toFixed(0)}%</div>
                                        <div className="text-muted-foreground text-sm">VS</div>
                                        <div className="text-sentinel-negative">{data.metrics.productB.sentiment.toFixed(0)}%</div>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <div className="text-sm text-muted-foreground">{getName(selectedA)}</div>
                                            <SentimentDistribution data={[{ name: 'Positive', value: Math.round(data.metrics.productA.sentiment) }, { name: 'Neutral', value: Math.round(100 - data.metrics.productA.sentiment - 0) }, { name: 'Negative', value: Math.round(0) }]} height={120} />
                                        </div>
                                        <div>
                                            <div className="text-sm text-muted-foreground">{getName(selectedB)}</div>
                                            <SentimentDistribution data={[{ name: 'Positive', value: Math.round(data.metrics.productB.sentiment) }, { name: 'Neutral', value: Math.round(100 - data.metrics.productB.sentiment - 0) }, { name: 'Negative', value: Math.round(0) }]} height={120} />
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="glass-card border-border/50">
                                <CardHeader><CardTitle>Review Volume</CardTitle></CardHeader>
                                <CardContent className="flex items-center justify-around text-center">
                                    <div>
                                        <div className="text-2xl font-bold">{data.metrics.productA.reviewCount}</div>
                                        <div className="text-sm text-muted-foreground">Reviews</div>
                                    </div>
                                    <TrendingUp className="text-muted-foreground h-6 w-6" />
                                    <div>
                                        <div className="text-2xl font-bold">{data.metrics.productB.reviewCount}</div>
                                        <div className="text-sm text-muted-foreground">Reviews</div>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
};

export default Competitors;
