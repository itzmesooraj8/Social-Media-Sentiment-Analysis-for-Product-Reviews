import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  MessageCircle, Twitter, Youtube, ExternalLink,
  Heart, MessageSquare, Repeat, ShieldCheck, ShieldAlert
} from "lucide-react";
import { formatDistanceToNow } from 'date-fns';
import { Review } from '@/types/sentinel';
import { cn } from '@/lib/utils';
import { Badge } from "@/components/ui/badge";

interface ReviewFeedProps {
  reviews: Review[];
}

export const ReviewFeed: React.FC<ReviewFeedProps> = ({ reviews }) => {

  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'twitter': return <Twitter className="h-3.5 w-3.5 text-[#1DA1F2]" />;
      case 'youtube': return <Youtube className="h-3.5 w-3.5 text-[#FF0000]" />;
      case 'reddit': return <MessageCircle className="h-3.5 w-3.5 text-[#FF4500]" />;
      default: return <MessageSquare className="h-3.5 w-3.5 text-muted-foreground" />;
    }
  };

  const getSentimentStyles = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20';
      case 'negative': return 'bg-red-500/10 text-red-500 border-red-500/20';
      default: return 'bg-slate-500/10 text-slate-500 border-slate-500/20';
    }
  };

  return (
    <div className="glass-card h-[400px] flex flex-col overflow-hidden relative group">
      {/* Premium Header */}
      <div className="p-4 border-b border-border/50 flex justify-between items-center bg-black/20 backdrop-blur-sm z-10">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-sentinel-highlight animate-pulse" />
          <h3 className="font-semibold text-sm tracking-wide uppercase text-muted-foreground">Live Intelligence Feed</h3>
        </div>
        <div className="text-[10px] font-mono text-muted-foreground px-2 py-0.5 rounded border border-white/10">
          {reviews.length} EVENTS
        </div>
      </div>

      <ScrollArea className="flex-1 p-0">
        <div className="p-4 space-y-3">
          <AnimatePresence initial={false}>
            {reviews.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center h-[280px] text-muted-foreground"
              >
                <div className="w-16 h-16 rounded-full border border-white/10 flex items-center justify-center mb-4 relative">
                  <div className="absolute inset-0 bg-sentinel-highlight/5 rounded-full animate-ping opacity-20" />
                  <MessageSquare className="h-6 w-6 opacity-30" />
                </div>
                <p className="text-sm font-medium">Awaiting Signals</p>
                <p className="text-xs opacity-50 mt-1">Listening to global channels...</p>
              </motion.div>
            ) : (
              reviews.map((review, idx) => (
                <motion.div
                  key={review.id}
                  initial={{ opacity: 0, x: -20, height: 0 }}
                  animate={{ opacity: 1, x: 0, height: 'auto' }}
                  transition={{ duration: 0.3, delay: idx * 0.05 }}
                  className="group/item relative pl-4 border-l-2 border-transparent hover:border-sentinel-highlight transition-all"
                >
                  {/* Timeline node */}
                  <div className="absolute left-[-5px] top-3 w-2 h-2 rounded-full bg-border group-hover/item:bg-sentinel-highlight transition-colors" />

                  <div className="p-3 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="p-1 rounded-md bg-white/5">
                          {getPlatformIcon(review.platform)}
                        </div>
                        <span className="text-xs font-semibold text-foreground/90">
                          {review.author || review.username || 'Anonymous'}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {(review.created_at || review.timestamp) ? formatDistanceToNow(new Date(review.created_at || review.timestamp || new Date()), { addSuffix: true }) : 'Just now'}
                        </span>
                      </div>
                      <div className={cn("text-[10px] font-medium px-2 py-0.5 rounded border uppercase tracking-wider", getSentimentStyles(
                        review.sentiment_label ||
                        review.sentiment ||
                        (review.sentiment_analysis as any)?.[0]?.label ||
                        (review.sentiment_analysis as any)?.label ||
                        'NEUTRAL'
                      ))}>
                        {
                          review.sentiment_label ||
                          review.sentiment ||
                          (review.sentiment_analysis as any)?.[0]?.label ||
                          (review.sentiment_analysis as any)?.label ||
                          'NEUTRAL'
                        }
                      </div>
                    </div>

                    {/* Content */}
                    <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                      {review.content || review.text}
                    </p>

                    {/* Footer Metrics */}
                    <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/5 opacity-60 group-hover/item:opacity-100 transition-opacity">
                      <div className="flex gap-3 text-[10px] font-mono text-muted-foreground">
                        {review.credibility !== undefined && review.credibility >= 0.7 && (
                          <span className="flex items-center gap-1 text-emerald-500">
                            <ShieldCheck className="h-3 w-3" /> VERIFIED
                          </span>
                        )}
                        {review.credibility !== undefined && review.credibility < 0.4 && (
                          <span className="flex items-center gap-1 text-red-500">
                            <ShieldAlert className="h-3 w-3" /> BOT?
                          </span>
                        )}
                        <span className="flex items-center gap-1"><Heart className="h-3 w-3" /> {review.like_count || 0}</span>
                      </div>

                      {(review.source_url || review.sourceUrl) && (
                        <a href={review.source_url || review.sourceUrl} target="_blank" rel="noreferrer" className="text-muted-foreground hover:text-white transition-colors">
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </ScrollArea>

      {/* Bottom fade for infinity scroll effect */}
      <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-black to-transparent pointer-events-none" />
    </div>
  );
};
