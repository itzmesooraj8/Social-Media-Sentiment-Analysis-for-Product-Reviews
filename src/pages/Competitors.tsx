import { useState, useEffect } from 'react';
import { getCompare, getProducts as apiGetProducts } from '@/lib/api';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend, Tooltip } from 'recharts';
import { Swords, TrendingUp } from 'lucide-react';

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
    const [loading, setLoading] = useState(false);

    // Fetch Products List
    useEffect(() => {
        apiGetProducts().then(d => {
            if (d.success) setProducts(d.data || []);
        }).catch(console.error);
    }, []);

    // Fetch Comparison Data
    useEffect(() => {
        if (selectedA && selectedB) {
            setLoading(true);
            getCompare(selectedA, selectedB)
                .then(d => {
                    if (d.success) setData(d.data);
                    setLoading(false);
                })
                .catch(() => setLoading(false));
        }
    }, [selectedA, selectedB]);

    const getName = (id: string) => products.find(p => p.id === id)?.name || 'Product';

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
                                                stroke="hsl(var(--sentinel-negative))" // Using distinct color (red vs green usually works for contrast)
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
                                    <div className="h-4 bg-muted rounded-full overflow-hidden flex">
                                        <div className="bg-sentinel-positive h-full" style={{ width: `${data.metrics.productA.sentiment}%` }} />
                                        <div className="bg-sentinel-negative h-full" style={{ width: `${data.metrics.productB.sentiment}%` }} />
                                    </div>
                                    <div className="flex justify-between text-sm text-muted-foreground mt-2">
                                        <span>{getName(selectedA)}</span>
                                        <span>{getName(selectedB)}</span>
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
