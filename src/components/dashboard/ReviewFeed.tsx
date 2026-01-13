import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Twitter, MessageSquare, Youtube, Users, ThumbsUp, ThumbsDown, Flag, ExternalLink, Filter, ChevronDown } from 'lucide-react';
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
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface Review {
  id: string;
  platform: 'twitter' | 'reddit' | 'youtube' | 'forums';
  username: string;
  text: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  credibility: number;
  timestamp: Date;
  likes: number;
  aspects: { name: string; sentiment: 'positive' | 'neutral' | 'negative' }[];
  isBot: boolean;
}

const mockReviews: Review[] = [
  {
    id: '1',
    platform: 'twitter',
    username: '@tech_reviewer',
    text: 'Just tested the new product and I\'m absolutely blown away! The build quality is exceptional and performance exceeds expectations. Highly recommend to anyone looking for premium quality.',
    sentiment: 'positive',
    credibility: 92,
    timestamp: new Date(Date.now() - 1000 * 60 * 5),
    likes: 234,
    aspects: [{ name: 'Quality', sentiment: 'positive' }, { name: 'Performance', sentiment: 'positive' }],
    isBot: false,
  },
  {
    id: '2',
    platform: 'reddit',
    username: 'u/honest_buyer',
    text: 'Mixed feelings about this purchase. The product itself is decent but shipping took forever and customer service was unresponsive. Would rate 3/5 stars.',
    sentiment: 'neutral',
    credibility: 85,
    timestamp: new Date(Date.now() - 1000 * 60 * 30),
    likes: 45,
    aspects: [{ name: 'Product', sentiment: 'neutral' }, { name: 'Shipping', sentiment: 'negative' }, { name: 'Service', sentiment: 'negative' }],
    isBot: false,
  },
  {
    id: '3',
    platform: 'youtube',
    username: 'GadgetGuru',
    text: 'Complete disappointment. Broke after 2 weeks of normal use. Tried to get a refund but no luck. Save your money and look elsewhere.',
    sentiment: 'negative',
    credibility: 78,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
    likes: 567,
    aspects: [{ name: 'Durability', sentiment: 'negative' }, { name: 'Support', sentiment: 'negative' }],
    isBot: false,
  },
  {
    id: '4',
    platform: 'forums',
    username: 'PowerUser2024',
    text: 'Been using this for 6 months now. Still works perfectly. Great value for the price point. The latest update added some nice features too.',
    sentiment: 'positive',
    credibility: 88,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5),
    likes: 123,
    aspects: [{ name: 'Value', sentiment: 'positive' }, { name: 'Durability', sentiment: 'positive' }],
    isBot: false,
  },
  {
    id: '5',
    platform: 'twitter',
    username: '@deal_finder',
    text: 'BUY NOW BEST PRICE CLICK LINK IN BIO!!! Amazing product everyone needs this!!!',
    sentiment: 'positive',
    credibility: 23,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 8),
    likes: 2,
    aspects: [],
    isBot: true,
  },
  {
    id: '6',
    platform: 'reddit',
    username: 'u/detailed_reviewer',
    text: 'Comprehensive review after 3 months: Pros - excellent display, fast processing, great battery. Cons - camera could be better, app ecosystem is limited. Overall solid 4/5.',
    sentiment: 'positive',
    credibility: 95,
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 12),
    likes: 892,
    aspects: [{ name: 'Display', sentiment: 'positive' }, { name: 'Performance', sentiment: 'positive' }, { name: 'Camera', sentiment: 'negative' }],
    isBot: false,
  },
];

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

export function ReviewFeed() {
  const [filter, setFilter] = useState<'all' | 'positive' | 'neutral' | 'negative'>('all');
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);

  const filteredReviews = mockReviews.filter(
    review => filter === 'all' || review.sentiment === filter
  );

  const formatTime = (date: Date) => {
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
                    <span className="text-sm font-medium">Credibility Score</span>
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
                  <Button variant="outline" size="sm" className="flex-1">
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
