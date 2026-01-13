import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Twitter, MessageSquare, Youtube, Users, ThumbsUp, ThumbsDown, Flag, ExternalLink, Filter, ChevronDown, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

import { Review } from '@/types/sentinel';

const platformIcons = {
  twitter: Twitter,
  reddit: MessageSquare,
  youtube: Youtube,
  forums: Users,
};

const platformColors = {
  twitter: 'text-blue-400',
  reddit: 'text-orange-500',
  youtube: 'text-red-500',
  forums: 'text-purple-400',
};

interface ReviewFeedProps {
  reviews?: Review[];
}

export function ReviewFeed({ reviews = [] }: ReviewFeedProps) {
  const [filter, setFilter] = useState<'all' | 'positive' | 'neutral' | 'negative'>('all');
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);

  const displayReviews = reviews && reviews.length > 0 ? reviews : [];

  const filteredReviews = displayReviews.filter(
    review => filter === 'all' || review.sentiment === filter
  );

  const formatTime = (dateInput: Date | string) => {
    const date = new Date(dateInput);
    const diff = Date.now() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const sentimentStyles = {
    positive: 'bg-sentinel-positive/10 text-sentinel-positive border-sentinel-positive/30',
    neutral: 'bg-muted text-muted-foreground border-border',
    negative: 'bg-sentinel-negative/10 text-sentinel-negative border-sentinel-negative/30',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold">Recent Reviews</h3>
          <p className="text-sm text-muted-foreground">Live feed from all platforms</p>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              <Filter className="h-4 w-4" />
              {filter === 'all' ? 'All' : filter.charAt(0).toUpperCase() + filter.slice(1)}
              <ChevronDown className="h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setFilter('all')}>All Reviews</DropdownMenuItem>
            <DropdownMenuItem onClick={() => setFilter('positive')}>Positive Only</DropdownMenuItem>
            <DropdownMenuItem onClick={() => setFilter('neutral')}>Neutral Only</DropdownMenuItem>
            <DropdownMenuItem onClick={() => setFilter('negative')}>Negative Only</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <ScrollArea className="h-[400px] pr-4">
        <div className="space-y-3">
          <AnimatePresence>
            {filteredReviews.map((review, index) => {
              const PlatformIcon = platformIcons[review.platform];

              return (
                <motion.div
                  key={review.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2, delay: index * 0.05 }}
                  onClick={() => setSelectedReview(review)}
                  className={cn(
                    'p-4 rounded-lg bg-background/50 border border-border/50 cursor-pointer',
                    'hover:border-sentinel-credibility/30 transition-all duration-200',
                    review.isBot && 'border-sentinel-warning/30 bg-sentinel-warning/5'
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className={cn('p-2 rounded-lg bg-muted', platformColors[review.platform])}>
                      <PlatformIcon className="h-4 w-4" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-sm">{review.username}</span>
                        <span className="text-xs text-muted-foreground">{formatTime(review.timestamp)}</span>
                        {review.isBot && (
                          <Badge variant="outline" className="text-sentinel-warning border-sentinel-warning/30 text-xs">
                            Bot Suspected
                          </Badge>
                        )}
                      </div>

                      <p className="text-sm text-foreground/80 line-clamp-2 mb-2">
                        {review.text}
                      </p>

                      <div className="flex items-center gap-3">
                        <Badge
                          variant="outline"
                          className={cn('text-xs', sentimentStyles[review.sentiment])}
                        >
                          {review.sentiment}
                        </Badge>

                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <ThumbsUp className="h-3 w-3" />
                          {review.likes}
                        </span>

                        <span className={cn(
                          'text-xs',
                          review.credibility > 70 ? 'text-sentinel-positive' :
                            review.credibility > 40 ? 'text-sentinel-warning' : 'text-sentinel-negative'
                        )}>
                          {review.credibility}% credible
                        </span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </ScrollArea>

      {/* Review Detail Modal */}
      <Dialog open={!!selectedReview} onOpenChange={() => setSelectedReview(null)}>
        <DialogContent className="glass-card border-border/50 max-w-lg">
          {selectedReview && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  {(() => {
                    const Icon = platformIcons[selectedReview.platform];
                    return <Icon className={cn('h-5 w-5', platformColors[selectedReview.platform])} />;
                  })()}
                  Review Details
                </DialogTitle>
              </DialogHeader>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{selectedReview.username}</span>
                  <Badge
                    variant="outline"
                    className={cn('text-xs', sentimentStyles[selectedReview.sentiment])}
                  >
                    {selectedReview.sentiment}
                  </Badge>
                </div>

                <p className="text-sm text-foreground/90 leading-relaxed">
                  {selectedReview.text}
                </p>

                <div className="p-3 rounded-lg bg-background/50">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Credibility Score</span>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger>
                            <Info className="h-4 w-4 text-muted-foreground hover:text-foreground transition-colors" />
                          </TooltipTrigger>
                          <TooltipContent className="glass-card border-border p-3 max-w-[200px]">
                            <p className="font-semibold text-xs mb-1">Analysis Factors:</p>
                            {selectedReview.credibilityReasons && selectedReview.credibilityReasons.length > 0 ? (
                              <ul className="list-disc pl-3 space-y-1">
                                {selectedReview.credibilityReasons.map((r, i) => (
                                  <li key={i} className="text-xs text-muted-foreground">{r}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-xs text-muted-foreground">Standard stylistic patterns</p>
                            )}
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    </div>

                    <span className={cn(
                      'font-bold',
                      selectedReview.credibility > 70 ? 'text-sentinel-positive' :
                        selectedReview.credibility > 40 ? 'text-sentinel-warning' : 'text-sentinel-negative'
                    )}>
                      {selectedReview.credibility}%
                    </span>
                  </div>
                  <Progress value={selectedReview.credibility} className="h-2" />
                </div>

                {selectedReview.aspects.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Aspect Analysis</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedReview.aspects.map((aspect) => (
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
                )}

                {selectedReview.isBot && (
                  <div className="p-3 rounded-lg bg-sentinel-warning/10 border border-sentinel-warning/30">
                    <p className="text-sm text-sentinel-warning font-medium">
                      ⚠️ This review has been flagged as potential bot activity
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Patterns detected: Promotional language, low engagement ratio, suspicious account age
                    </p>
                  </div>
                )}

                <div className="flex gap-2 pt-2">
                  <Button variant="outline" size="sm" className="flex-1">
                    <Flag className="h-4 w-4 mr-2" />
                    Report
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => {
                      if (selectedReview.sourceUrl) {
                        window.open(selectedReview.sourceUrl, '_blank');
                      } else {
                        // Mock toast or alert
                        alert('Source URL not available for this review');
                      }
                    }}
                  >
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Source
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
