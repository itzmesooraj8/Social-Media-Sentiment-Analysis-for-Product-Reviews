export interface Review {
  id: string;
  text: string;
  platform: string;
  username: string;
  sentiment: 'positive' | 'neutral' | 'negative';
  sentiment_label?: string;
  timestamp: string;
  sourceUrl?: string;
  // Deep Analysis Fields
  credibility?: number;
  like_count?: number;
  reply_count?: number;
  retweet_count?: number;
  metadata?: Record<string, any>;
}

export interface DashboardStats {
  totalReviews: number;
  sentimentScore: number;
  averageCredibility: number;
  platformBreakdown: Record<string, number>;
  topKeywords: Array<{ text: string; value: number; sentiment?: string }>;
  recentReviews: Review[];
  credibilityReport?: {
      overallScore: number;
      verifiedReviews: number;
      botsDetected: number;
  };
}
