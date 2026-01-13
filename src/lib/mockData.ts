import { 
  SentimentDataPoint, 
  AspectScore, 
  Alert, 
  PlatformBreakdown, 
  TopKeyword, 
  CredibilityReport,
  DashboardData,
  AlertType,
  AlertSeverity,
  Platform,
  SentimentType
} from '@/types/sentinel';
import { subDays, format, subHours, subMinutes } from 'date-fns';

// Utility functions for random data generation
const randomBetween = (min: number, max: number): number => 
  Math.floor(Math.random() * (max - min + 1)) + min;

const randomFloat = (min: number, max: number, decimals: number = 2): number =>
  parseFloat((Math.random() * (max - min) + min).toFixed(decimals));

const pickRandom = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)];

// Generate sentiment trend data for the past 30 days
export const generateSentimentTrends = (days: number = 30): SentimentDataPoint[] => {
  const data: SentimentDataPoint[] = [];
  let basePositive = 45;
  let baseNeutral = 35;
  let baseNegative = 20;

  for (let i = days - 1; i >= 0; i--) {
    const date = format(subDays(new Date(), i), 'MMM dd');
    
    // Add some variance while keeping totals reasonable
    const positiveVariance = randomBetween(-8, 12);
    const neutralVariance = randomBetween(-5, 5);
    const negativeVariance = randomBetween(-6, 8);

    const positive = Math.max(20, Math.min(70, basePositive + positiveVariance));
    const neutral = Math.max(15, Math.min(50, baseNeutral + neutralVariance));
    const negative = Math.max(5, Math.min(40, baseNegative + negativeVariance));
    const total = randomBetween(300, 800);

    data.push({
      date,
      positive,
      neutral,
      negative,
      total
    });

    // Gradual drift for more realistic trends
    basePositive += randomFloat(-1, 1);
    baseNeutral += randomFloat(-0.5, 0.5);
    baseNegative += randomFloat(-1, 1);
  }

  return data;
};

// Generate aspect-based sentiment scores
export const generateAspectScores = (): AspectScore[] => {
  const aspects = ['Price', 'Quality', 'Battery', 'Screen', 'Shipping', 'Service'];
  
  return aspects.map(aspect => {
    const score = randomFloat(2.5, 4.8);
    let sentiment: SentimentType;
    
    if (score >= 4) sentiment = 'positive';
    else if (score >= 3) sentiment = 'neutral';
    else sentiment = 'negative';

    return {
      aspect,
      score,
      sentiment,
      reviewCount: randomBetween(150, 2500)
    };
  });
};

// Generate recent alerts
export const generateAlerts = (count: number = 8): Alert[] => {
  const alertConfigs: { type: AlertType; messages: string[]; severity: AlertSeverity }[] = [
    { 
      type: 'bot_detected', 
      messages: [
        'Bot pattern detected: Identical review text from 23 accounts',
        'Automated posting pattern identified across Reddit threads',
        'Coordinated review activity detected from new accounts'
      ],
      severity: 'high'
    },
    { 
      type: 'spam_cluster', 
      messages: [
        'Spam cluster identified: 47 reviews with similar structure',
        'Potential review farm activity detected',
        'Duplicate content pattern across multiple platforms'
      ],
      severity: 'critical'
    },
    { 
      type: 'review_surge', 
      messages: [
        'Unusual review surge: +340% in last 2 hours',
        'Abnormal review velocity detected for product SKU-4521',
        'Review volume anomaly flagged for investigation'
      ],
      severity: 'medium'
    },
    { 
      type: 'sentiment_shift', 
      messages: [
        'Major sentiment shift: -28% in positive reviews today',
        'Negative sentiment spike detected on Twitter',
        'Rapid sentiment decline following product update'
      ],
      severity: 'medium'
    },
    { 
      type: 'fake_review', 
      messages: [
        'Potential fake review flagged: Credibility score 12%',
        'Suspicious review pattern: Same user, multiple products',
        'Review authenticity below threshold'
      ],
      severity: 'low'
    }
  ];

  const platforms: Platform[] = ['twitter', 'reddit', 'youtube', 'forums'];
  
  return Array.from({ length: count }, (_, i) => {
    const config = pickRandom(alertConfigs);
    const minutesAgo = randomBetween(5, 180);
    
    return {
      id: `alert-${Date.now()}-${i}`,
      type: config.type,
      severity: config.severity,
      message: pickRandom(config.messages),
      timestamp: subMinutes(new Date(), minutesAgo),
      metadata: {
        platform: pickRandom(platforms),
        confidence: randomFloat(0.65, 0.98)
      }
    };
  }).sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
};

// Generate platform breakdown
export const generatePlatformBreakdown = (): PlatformBreakdown[] => {
  const platforms: Platform[] = ['twitter', 'reddit', 'youtube', 'forums'];
  
  return platforms.map(platform => {
    const total = randomBetween(1500, 5000);
    const positive = randomBetween(30, 60);
    const negative = randomBetween(10, 30);
    const neutral = 100 - positive - negative;
    
    return {
      platform,
      positive,
      neutral,
      negative,
      total
    };
  });
};

// Generate top keywords
export const generateTopKeywords = (): TopKeyword[] => {
  const positiveWords = ['excellent', 'amazing', 'love', 'perfect', 'great', 'fantastic', 'recommend'];
  const negativeWords = ['terrible', 'awful', 'broken', 'disappointed', 'waste', 'poor', 'defective'];
  const neutralWords = ['okay', 'decent', 'average', 'expected', 'standard', 'normal'];
  
  const keywords: TopKeyword[] = [];
  
  positiveWords.slice(0, 4).forEach(word => {
    keywords.push({
      word,
      count: randomBetween(80, 450),
      sentiment: 'positive',
      trend: pickRandom(['up', 'stable', 'up'])
    });
  });
  
  negativeWords.slice(0, 3).forEach(word => {
    keywords.push({
      word,
      count: randomBetween(30, 150),
      sentiment: 'negative',
      trend: pickRandom(['down', 'up', 'stable'])
    });
  });
  
  neutralWords.slice(0, 2).forEach(word => {
    keywords.push({
      word,
      count: randomBetween(50, 200),
      sentiment: 'neutral',
      trend: 'stable'
    });
  });
  
  return keywords.sort((a, b) => b.count - a.count);
};

// Generate credibility report
export const generateCredibilityReport = (): CredibilityReport => {
  const totalAnalyzed = randomBetween(10000, 15000);
  const botsDetected = randomBetween(20, 80);
  const spamClusters = randomBetween(3, 12);
  const suspiciousPatterns = randomBetween(50, 200);
  const verifiedReviews = totalAnalyzed - botsDetected - suspiciousPatterns;
  
  return {
    overallScore: randomFloat(78, 96),
    botsDetected,
    spamClusters,
    suspiciousPatterns,
    verifiedReviews,
    totalAnalyzed
  };
};

// Generate complete dashboard data
export const generateDashboardData = (): DashboardData => {
  const sentimentTrends = generateSentimentTrends(30);
  const latestTrend = sentimentTrends[sentimentTrends.length - 1];
  const previousTrend = sentimentTrends[sentimentTrends.length - 8];
  
  const sentimentDelta = latestTrend.positive - previousTrend.positive;
  
  return {
    metrics: {
      totalReviews: randomBetween(10000, 15000),
      sentimentDelta: parseFloat(sentimentDelta.toFixed(1)),
      botsDetected: randomBetween(15, 45),
      averageCredibility: randomFloat(82, 96)
    },
    sentimentTrends,
    aspectScores: generateAspectScores(),
    alerts: generateAlerts(8),
    platformBreakdown: generatePlatformBreakdown(),
    topKeywords: generateTopKeywords(),
    credibilityReport: generateCredibilityReport(),
    lastUpdated: new Date()
  };
};

// Simulated API delay for realistic loading states
export const fetchDashboardData = async (): Promise<DashboardData> => {
  await new Promise(resolve => setTimeout(resolve, randomBetween(500, 1500)));
  return generateDashboardData();
};
