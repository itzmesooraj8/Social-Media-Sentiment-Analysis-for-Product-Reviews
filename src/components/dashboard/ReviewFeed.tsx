import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageCircle, Twitter, Youtube, ExternalLink, ThumbsUp, Repeat, MessageSquare } from "lucide-react";
import { formatDistanceToNow } from 'date-fns';

// Define the Review type based on your DB schema
interface Review {
  id: string;
  text: string;
  platform: string;
  username: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentiment_label?: string;
  timestamp: string;
  sourceUrl?: string;
  credibility?: number;
  like_count?: number;
  reply_count?: number;
  retweet_count?: number;
}

interface ReviewFeedProps {
  reviews: Review[];
}

export const ReviewFeed: React.FC<ReviewFeedProps> = ({ reviews }) => {

  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'twitter':
      case 'x':
        return <Twitter className="h-4 w-4 text-blue-400" />;
      case 'youtube':
        return <Youtube className="h-4 w-4 text-red-600" />;
      case 'reddit':
        return <MessageCircle className="h-4 w-4 text-orange-500" />;
      default:
        return <MessageSquare className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'bg-green-100 text-green-800 border-green-200';
      case 'negative': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <Card className="h-full col-span-1 md:col-span-2 lg:col-span-3">
      <CardHeader>
        <CardTitle>Live Review Feed</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-4">
            {reviews.length === 0 ? (
              <div className="text-center text-gray-500 py-10">
                Waiting for live data... Add a product to start tracking.
              </div>
            ) : (
              reviews.map((review) => (
                <div key={review.id} className="flex gap-4 p-4 rounded-lg border bg-card text-card-foreground shadow-sm">
                  <div className="mt-1">
                    {getPlatformIcon(review.platform)}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm">{review.username}</span>
                        <span className="text-xs text-muted-foreground">
                          {review.timestamp ? formatDistanceToNow(new Date(review.timestamp), { addSuffix: true }) : 'Just now'}
                        </span>
                      </div>
                      <Badge variant="outline" className={getSentimentColor(review.sentiment || review.sentiment_label || '')}>
                        {(review.sentiment_label || review.sentiment || 'neutral').toString().toUpperCase()}
                      </Badge>
                    </div>

                    <p className="text-sm text-gray-700 leading-relaxed">
                      {review.text}
                    </p>

                    {/* Engagement Metrics */}
                    <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
                      {(review.like_count || 0) > 0 && (
                        <div className="flex items-center gap-1">
                          <ThumbsUp className="h-3 w-3" />
                          <span>{review.like_count}</span>
                        </div>
                      )}
                      {(review.reply_count || 0) > 0 && (
                        <div className="flex items-center gap-1">
                          <MessageCircle className="h-3 w-3" />
                          <span>{review.reply_count}</span>
                        </div>
                      )}
                      {(review.retweet_count || 0) > 0 && (
                        <div className="flex items-center gap-1">
                          <Repeat className="h-3 w-3" />
                          <span>{review.retweet_count}</span>
                        </div>
                      )}
                      {review.credibility && (
                        <div className="flex items-center gap-1 ml-auto">
                           <span className={review.credibility > 0.7 ? "text-green-600" : review.credibility < 0.4 ? "text-red-600" : "text-yellow-600"}>
                             Cred: {(review.credibility * 100).toFixed(0)}%
                           </span>
                        </div>
                      )}
                    </div>

                    {review.sourceUrl && (
                      <a
                        href={review.sourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-blue-500 hover:underline flex items-center gap-1 mt-2"
                      >
                        View Original <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
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
