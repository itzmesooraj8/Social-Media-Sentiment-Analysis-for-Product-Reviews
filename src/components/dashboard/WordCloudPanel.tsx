
import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Cloud } from 'lucide-react';

interface Topic {
    text: string;
    value: number;
    sentiment?: string; // 'positive' | 'negative' | 'neutral'
}

interface WordCloudPanelProps {
    topics: Topic[];
    isLoading?: boolean;
}

export function WordCloudPanel({ topics, isLoading }: WordCloudPanelProps) {
    // Normalize values for font sizing
    const processedTopics = useMemo(() => {
        if (!topics.length) return [];

        // Safety check for empty values
        const maxVal = Math.max(...topics.map(t => t.value));
        const minVal = Math.min(...topics.map(t => t.value));
        const range = maxVal - minVal || 1;

        return topics.map(t => {
            // Map value to font size 12px - 60px
            const size = 12 + ((t.value - minVal) / range) * 48;

            // Determine color based on sentiment
            let color = "text-muted-foreground";
            if (t.sentiment === "positive") color = "text-green-500";
            else if (t.sentiment === "negative") color = "text-red-500";
            else if (t.sentiment === "neutral") color = "text-blue-400";

            // Add randomness for layout "cloud" feel
            const rotation = Math.random() > 0.8 ? "rotate-90" : "rotate-0";

            return { ...t, size, color, rotation };
        }).sort((a, b) => b.value - a.value); // sort by size for center bias logic if we were using a library, but helpful anyway
    }, [topics]);

    if (isLoading) {
        return (
            <Card className="glass-card border-border/50 h-[300px] animate-pulse">
                <CardHeader><CardTitle>Topic Cloud</CardTitle></CardHeader>
                <CardContent className="h-full bg-muted/20" />
            </Card>
        );
    }

    return (
        <Card className="glass-card border-border/50 h-[400px] flex flex-col">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Cloud className="h-5 w-5 text-primary" />
                    Dominant Topics
                </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 relative overflow-hidden p-6 flex flex-wrap content-center justify-center gap-4">
                {processedTopics.length === 0 ? (
                    <div className="text-muted-foreground text-sm">No topics detected yet.</div>
                ) : (
                    processedTopics.map((topic, i) => (
                        <span
                            key={i}
                            className={`font-bold transition-all duration-300 hover:scale-110 cursor-default ${topic.color} ${topic.rotation === 'rotate-90' ? 'vertical-text' : ''}`}
                            style={{
                                fontSize: `${topic.size}px`,
                                opacity: 0.7 + (topic.size / 60) * 0.3, // Larger words more opaque
                                textShadow: '0 2px 10px rgba(0,0,0,0.1)'
                            }}
                            title={`${topic.text}: ${topic.value} mentions`}
                        >
                            {topic.text}
                        </span>
                    ))
                )}
            </CardContent>
        </Card>
    );
}
