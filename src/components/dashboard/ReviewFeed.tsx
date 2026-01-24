import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageCircle, Twitter, Youtube, ExternalLink, Heart, MessageSquare, Repeat, ShieldCheck, ShieldAlert } from "lucide-react";
import { formatDistanceToNow } from 'date-fns';
import { Review } from '@/types/sentinel';

interface ReviewFeedProps {
  reviews: Review[];
}

export const ReviewFeed: React.FC<ReviewFeedProps> = ({ reviews }) => {

  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'twitter': return <Twitter className="h-4 w-4 text-blue-400" />;
      case 'youtube': return <Youtube className="h-4 w-4 text-red-600" />;
      case 'reddit': return <MessageCircle className="h-4 w-4 text-orange-500" />;
      default: return <MessageSquare className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'bg-green-100 text-green-800 border-green-200';
      case 'negative': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // 0-1 Score to visual
  const getCredibilityBadge = (score?: number) => {
      if (score === undefined) return null;
      const pct = Math.round(score * 100);
      if (score >= 0.7) {
          return (
              <div className="flex items-center gap-1 text-xs text-green-600 font-medium" title="Verified Credible">
                  <ShieldCheck className="h-3 w-3" /> {pct}% Trust
              </div>
          );
      } else if (score < 0.4) {
          return (
              <div className="flex items-center gap-1 text-xs text-red-500 font-medium" title="Low Credibility / Potential Bot">
                  <ShieldAlert className="h-3 w-3" /> {pct}% Trust
              </div>
          );
      }
      return <div className="text-xs text-gray-400">{pct}% Trust</div>;
  };

  return (
    <Card className="h-full col-span-1 md:col-span-2 lg:col-span-3">
      <CardHeader>
        <CardTitle>Live Intelligence Feed</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-4">
            {reviews.length === 0 ? (
              <div className="text-center text-gray-500 py-10">
                Waiting for live data...
              </div>
            ) : (
              reviews.map((review) => (
                <div key={review.id} className="flex gap-4 p-4 rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-all">
                  <div className="mt-1">
                    {getPlatformIcon(review.platform)}
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm">{review.username}</span>
                        <span className="text-xs text-muted-foreground">
                          {review.timestamp ? formatDistanceToNow(new Date(review.timestamp), { addSuffix: true }) : 'Just now'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                          {getCredibilityBadge(review.credibility)}
                          <Badge variant="outline" className={getSentimentColor(review.sentiment || review.sentiment_label || '')}>
                            {(review.sentiment_label || review.sentiment || 'neutral').toString().toUpperCase()}
                          </Badge>
                      </div>
                    </div>

                    <p className="text-sm text-gray-700 leading-relaxed">
                      {review.text}
                    </p>

                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100">
                        <div className="flex gap-4 text-xs text-gray-500">
                            <span className="flex items-center gap-1" title="Likes"><Heart className="h-3 w-3" /> {review.like_count || 0}</span>
                            <span className="flex items-center gap-1" title="Replies"><MessageSquare className="h-3 w-3" /> {review.reply_count || 0}</span>
                            <span className="flex items-center gap-1" title="Retweets"><Repeat className="h-3 w-3" /> {review.retweet_count || 0}</span>
                        </div>
                        {review.sourceUrl && (
                        <a
                            href={review.sourceUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs text-blue-500 hover:underline flex items-center gap-1"
                        >
                            Original <ExternalLink className="h-3 w-3" />
                        </a>
                        )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};
