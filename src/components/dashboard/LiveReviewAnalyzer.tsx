import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Sparkles, Brain, Target, Shield, TrendingUp, TrendingDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface AnalysisResult {
  sentiment: 'positive' | 'neutral' | 'negative';
  confidence: number;
  emotions: { name: string; score: number }[];
  keyPhrases: string[];
  credibilityScore: number;
  aspects: { name: string; sentiment: 'positive' | 'neutral' | 'negative' }[];
}

export function LiveReviewAnalyzer() {
  const [reviewText, setReviewText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const analyzeReview = async () => {
    if (!reviewText.trim()) return;
    
    setIsAnalyzing(true);
    
    // Simulate API call with realistic delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Generate mock analysis based on text content
    const positiveWords = ['great', 'excellent', 'amazing', 'love', 'fantastic', 'best', 'perfect', 'wonderful'];
    const negativeWords = ['bad', 'terrible', 'awful', 'hate', 'worst', 'poor', 'disappointing', 'broken'];
    
    const lowerText = reviewText.toLowerCase();
    const positiveCount = positiveWords.filter(w => lowerText.includes(w)).length;
    const negativeCount = negativeWords.filter(w => lowerText.includes(w)).length;
    
    let sentiment: 'positive' | 'neutral' | 'negative' = 'neutral';
    let confidence = 65 + Math.random() * 20;
    
    if (positiveCount > negativeCount) {
      sentiment = 'positive';
      confidence = 75 + Math.random() * 20;
    } else if (negativeCount > positiveCount) {
      sentiment = 'negative';
      confidence = 70 + Math.random() * 25;
    }
    
    const emotions = [
      { name: 'Joy', score: sentiment === 'positive' ? 60 + Math.random() * 30 : 10 + Math.random() * 20 },
      { name: 'Trust', score: 40 + Math.random() * 40 },
      { name: 'Anticipation', score: 30 + Math.random() * 30 },
      { name: 'Anger', score: sentiment === 'negative' ? 40 + Math.random() * 40 : 5 + Math.random() * 15 },
      { name: 'Fear', score: 5 + Math.random() * 20 },
      { name: 'Surprise', score: 20 + Math.random() * 30 },
    ].sort((a, b) => b.score - a.score);
    
    const keyPhrases = reviewText
      .split(/[.,!?]/)
      .filter(p => p.trim().length > 10)
      .slice(0, 4)
      .map(p => p.trim().substring(0, 40));
    
    const aspects = [
      { name: 'Quality', sentiment: sentiment },
      { name: 'Value', sentiment: Math.random() > 0.5 ? sentiment : 'neutral' as const },
      { name: 'Service', sentiment: Math.random() > 0.6 ? sentiment : 'neutral' as const },
      { name: 'Shipping', sentiment: Math.random() > 0.7 ? 'positive' as const : 'neutral' as const },
    ];
    
    setResult({
      sentiment,
      confidence,
      emotions,
      keyPhrases: keyPhrases.length ? keyPhrases : ['No distinct phrases detected'],
      credibilityScore: 70 + Math.random() * 25,
      aspects,
    });
    
    setIsAnalyzing(false);
  };

  const sentimentConfig = {
    positive: { color: 'text-sentinel-positive', bg: 'bg-sentinel-positive/10', label: 'Positive', icon: TrendingUp },
    neutral: { color: 'text-sentinel-neutral', bg: 'bg-muted', label: 'Neutral', icon: Target },
    negative: { color: 'text-sentinel-negative', bg: 'bg-sentinel-negative/10', label: 'Negative', icon: TrendingDown },
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-card p-6"
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 rounded-lg bg-sentinel-credibility/10">
          <Brain className="h-5 w-5 text-sentinel-credibility" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Live Review Analyzer</h3>
          <p className="text-sm text-muted-foreground">Paste any review for instant sentiment analysis</p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="relative">
          <Textarea
            value={reviewText}
            onChange={(e) => setReviewText(e.target.value)}
            placeholder="Paste a product review here to analyze its sentiment, emotions, and credibility..."
            className="min-h-[120px] resize-none bg-background/50 border-border/50 focus:border-sentinel-credibility/50"
          />
          <span className="absolute bottom-2 right-2 text-xs text-muted-foreground">
            {reviewText.length} characters
          </span>
        </div>

        <Button
          onClick={analyzeReview}
          disabled={!reviewText.trim() || isAnalyzing}
          className="w-full bg-sentinel-credibility hover:bg-sentinel-credibility/90 text-white"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4 mr-2" />
              Analyze Sentiment
            </>
          )}
        </Button>

        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="space-y-4 pt-4 border-t border-border/50"
            >
              {/* Main Sentiment Result */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={cn('p-3 rounded-xl', sentimentConfig[result.sentiment].bg)}>
                    {(() => {
                      const Icon = sentimentConfig[result.sentiment].icon;
                      return <Icon className={cn('h-6 w-6', sentimentConfig[result.sentiment].color)} />;
                    })()}
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Detected Sentiment</p>
                    <p className={cn('text-xl font-bold', sentimentConfig[result.sentiment].color)}>
                      {sentimentConfig[result.sentiment].label}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Confidence</p>
                  <p className="text-2xl font-bold">{result.confidence.toFixed(1)}%</p>
                </div>
              </div>

              {/* Credibility Score */}
              <div className="p-4 rounded-lg bg-background/50">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-sentinel-credibility" />
                    <span className="text-sm font-medium">Credibility Score</span>
                  </div>
                  <span className="text-sentinel-credibility font-bold">{result.credibilityScore.toFixed(0)}%</span>
                </div>
                <Progress value={result.credibilityScore} className="h-2" />
              </div>

              {/* Emotions Grid */}
              <div>
                <h4 className="text-sm font-medium mb-3">Emotion Detection</h4>
                <div className="grid grid-cols-2 gap-2">
                  {result.emotions.slice(0, 6).map((emotion) => (
                    <div key={emotion.name} className="flex items-center justify-between p-2 rounded-lg bg-background/50">
                      <span className="text-sm">{emotion.name}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-sentinel-credibility rounded-full transition-all"
                            style={{ width: `${emotion.score}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground w-8">{emotion.score.toFixed(0)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Aspect Analysis */}
              <div>
                <h4 className="text-sm font-medium mb-3">Aspect Analysis</h4>
                <div className="flex flex-wrap gap-2">
                  {result.aspects.map((aspect) => (
                    <Badge 
                      key={aspect.name}
                      variant="outline"
                      className={cn(
                        'border',
                        aspect.sentiment === 'positive' && 'border-sentinel-positive/30 text-sentinel-positive bg-sentinel-positive/5',
                        aspect.sentiment === 'neutral' && 'border-border text-muted-foreground',
                        aspect.sentiment === 'negative' && 'border-sentinel-negative/30 text-sentinel-negative bg-sentinel-negative/5'
                      )}
                    >
                      {aspect.name}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Key Phrases */}
              <div>
                <h4 className="text-sm font-medium mb-3">Key Phrases Extracted</h4>
                <div className="space-y-1">
                  {result.keyPhrases.map((phrase, i) => (
                    <p key={i} className="text-sm text-muted-foreground">
                      • {phrase}
                    </p>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
