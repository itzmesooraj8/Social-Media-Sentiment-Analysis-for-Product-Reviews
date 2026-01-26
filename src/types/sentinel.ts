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
  platformBreakdown: PlatformBreakdown[];
  topKeywords: Array<{ text: string; value: number; sentiment?: string }>;
  recentReviews: Review[];
  credibilityReport?: CredibilityReport;
}

export interface PlatformBreakdown {
  platform: string;
  positive: number;
  neutral: number;
  negative: number;
  count?: number; // Total count alias
  total?: number; // Total count alias
}

export interface CredibilityReport {
  overallScore: number;
  verifiedReviews: number;
  botsDetected: number;
  spamClusters: number;
  suspiciousPatterns: number;
  totalAnalyzed: number;
}

export interface AspectScore {
  aspect: string;
  score: number;
  reviewCount?: number;
}

export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertType = 'bot_detected' | 'spam_cluster' | 'review_surge' | 'sentiment_shift' | 'fake_review';

export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  timestamp: string | Date;
  metadata?: Record<string, any>;
  is_read?: boolean;
}

