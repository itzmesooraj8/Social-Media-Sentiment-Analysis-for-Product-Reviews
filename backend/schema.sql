-- Enable RLS (if not already)
alter table reviews enable row level security;
alter table sentiment_analysis enable row level security;

-- Create a function to calculate dashboard stats efficiently in DB
create or replace function get_dashboard_stats()
returns json
language plpgsql
as $$
declare
  total_count integer;
  avg_sentiment numeric;
  avg_credibility numeric;
  platform_counts json;
begin
  -- Get total reviews
  select count(*) into total_count from reviews;

  -- Get Average Sentiment (Mapped: POSITIVE=1, NEUTRAL=0.5, NEGATIVE=0)
  -- and Average Credibility
  select 
    coalesce(avg(
      case 
        when label = 'POSITIVE' then 100 
        when label = 'NEUTRAL' then 50 
        else 0 
      end
    ), 0),
    coalesce(avg(credibility), 0)
  into avg_sentiment, avg_credibility
  from sentiment_analysis;

  -- Get Platform Breakdown
  select json_object_agg(platform, count)
  into platform_counts
  from (
    select platform, count(*) as count
    from reviews
    group by platform
  ) p;

  return json_build_object(
    'totalReviews', total_count,
    'sentimentScore', avg_sentiment,
    'averageCredibility', avg_credibility,
    'platformBreakdown', platform_counts
  );
end;
$$;
