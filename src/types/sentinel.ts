export interface Review {
  id: string;
  product_id: string;
  // 'platform' maps to the backend column.
  platform: 'reddit' | 'twitter' | 'youtube' | 'amazon' | 'web_upload';
  // 'username' is what the frontend displays (was 'author')
  username: string;
  // 'text' is the content (was 'content')
  text: string;
  sentiment_label: 'positive' | 'neutral' | 'negative';
  sentiment_score: number;
  credibility_score: number;
  created_at: string;
  source_url?: string;
  likes?: number;
  like_count?: number;
  reply_count?: number;
  retweet_count?: number;
  metadata?: any;
  isBot?: boolean;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  platform: string;
  url: string;
  image_url?: string;
  status: 'active' | 'archived' | 'paused';
  last_updated?: string;
  category?: string;
  sku?: string;
  current_sentiment?: number;
}

export interface DashboardMetrics {
  totalReviews: number;
  sentimentDelta: number;
  averageCredibility: number;
  totalReach: number;
}

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low';
export type AlertType = 'bot_detected' | 'spam_cluster' | 'sentiment_shift' | 'review_surge' | 'fake_review';

export interface CredibilityReport {
  overallScore: number;
  verifiedReviews: number;
  botsDetected: number;
  spamClusters: number;
  suspiciousPatterns: number;
  totalAnalyzed: number;
}
