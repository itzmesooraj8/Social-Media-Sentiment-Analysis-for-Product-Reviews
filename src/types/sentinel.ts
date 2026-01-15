export interface Sentiment {
  score: number;
  label: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  confidence: number;
  keywords?: string[];
}

export interface Review {
  id: string;
  // Critical: Handles both new 'username' and old 'author' fields
  username: string; 
  author?: string; 
  
  content: string;
  rating?: number;
  date: string; // ISO string from DB 'created_at'
  platform: 'twitter' | 'reddit' | 'youtube' | 'amazon' | 'unknown';
  
  // Enriched Data
  sentiment: Sentiment;
  credibility: number; // 0-100 score
  is_spam?: boolean;
}

export interface Product {
  id: string;
  name: string;
  description?: string;
  category?: string;
  platform?: string;
  sentiment_score?: number;
  review_count?: number;
  created_at?: string;
}

export interface DashboardMetrics {
  totalReviews: number;
  sentimentScore: number;
  averageCredibility: number;
  platformBreakdown: Record<string, number>;
  sentimentTrends?: { date: string; sentiment: number; volume: number }[];
  engagementRate?: number;
  totalReach?: number;
}

export interface Sentiment {
  score: number;
  label: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  confidence: number;
  keywords?: string[];
}

export interface Review {
  id: string;
  // The backend now prioritizes 'username' but some legacy rows have 'author'.
  // This type definition handles both to prevent TS errors.
  username: string;
  author?: string; // Legacy fallback
  
  content: string;
  rating?: number;
  date: string; // ISO string from DB 'created_at'
  platform: 'twitter' | 'reddit' | 'youtube' | 'amazon' | 'unknown';
  
  // Enriched Data
  sentiment: Sentiment;
  credibility: number; // 0-100 score
  is_spam?: boolean;
}

export interface Product {
  id: string;
  name: string;
  description?: string;
  category?: string;
  platform?: string;
  sentiment_score?: number;
  review_count?: number;
  created_at?: string;
}

export interface DashboardMetrics {
  totalReviews: number;
  sentimentScore: number;
  averageCredibility: number;
  platformBreakdown: Record<string, number>;
  sentimentTrends?: { date: string; sentiment: number; volume: number }[];
}
// Sentinel Engine Type Definitions

export type Platform = 'twitter' | 'reddit' | 'youtube' | 'forums';
export type SentimentType = 'positive' | 'neutral' | 'negative';
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical';
export type AlertType = 'bot_detected' | 'spam_cluster' | 'review_surge' | 'sentiment_shift' | 'fake_review';

export interface SentimentDataPoint {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
  total: number;
}

export interface AspectScore {
  aspect: string;
  score: number;
  sentiment: SentimentType;
  reviewCount: number;
}

export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  message: string;
  timestamp: Date;
  metadata?: {
    reviewId?: string;
    platform?: Platform;
    confidence?: number;
  };
}

export interface MetricCard {
  title: string;
  value: number | string;
  change?: number;
  changeType?: 'positive' | 'negative' | 'neutral';
  subtitle?: string;
  icon?: string;
}

export interface PlatformBreakdown {
  platform: Platform;
  positive: number;
  neutral: number;
  negative: number;
  total: number;
}

export interface TopKeyword {
  word: string;
  count: number;
  sentiment: SentimentType;
  trend: 'up' | 'down' | 'stable';
}

export interface CredibilityReport {
  overallScore: number;
  botsDetected: number;
  spamClusters: number;
  suspiciousPatterns: number;
  verifiedReviews: number;
  totalAnalyzed: number;
}

export interface DashboardFilters {
  platform: Platform | 'all';
  productId: string;
  dateRange: {
    start: Date;
    end: Date;
  };
  sentimentFilter: SentimentType[];
  credibilityThreshold: number;
}

export interface Review {
  id: string;
  platform: Platform;
  username: string;
  text: string;
  sentiment: SentimentType;
  credibility: number;
  credibilityReasons?: string[];
  sourceUrl?: string;
  timestamp: Date | string;
  likes: number;
  aspects: { name: string; sentiment: SentimentType }[];
  isBot: boolean;
}

export interface DashboardData {
  metrics: {
    totalReviews: number;
    sentimentDelta: number;
    botsDetected: number;
    averageCredibility: number;
  };
  sentimentTrends: SentimentDataPoint[];
  aspectScores: AspectScore[];
  alerts: Alert[];
  platformBreakdown: PlatformBreakdown[];
  topKeywords: TopKeyword[];
  credibilityReport: CredibilityReport;
  recentReviews: Review[];
  lastUpdated: Date;
}

// API Response types for future backend integration
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  error?: string;
  timestamp: Date;
}

export interface FetchDashboardParams {
  productId: string;
  platform: Platform | 'all';
  startDate: string;
  endDate: string;
}
