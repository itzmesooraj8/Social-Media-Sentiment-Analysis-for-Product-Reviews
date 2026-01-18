-- Supabase Phase 1 schema for Sentiment Beacon
-- Run in Supabase SQL Editor

-- Enable uuid-ossp (if needed) - Supabase provides gen_random_uuid()

-- Products table
create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  keywords text[] default array[]::text[],
  track_reddit boolean default false,
  track_twitter boolean default false,
  track_youtube boolean default true,
  created_at timestamptz default now()
);

-- Reviews table
create table if not exists reviews (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references products(id) on delete cascade,
  content text not null,
  platform text not null,
  sentiment_score double precision,
  sentiment_label text,
  emotion text,
  credibility_score double precision,
  source_url text,
  created_at timestamptz default now()
);

-- Indexes for queries
create index if not exists idx_reviews_product on reviews(product_id);
create index if not exists idx_reviews_created_at on reviews(created_at);

-- Enable Row Level Security but allow public read/write for demo (NOT for production)
alter table products enable row level security;
alter table reviews enable row level security;

-- RLS policy: allow all users to select/insert/update/delete (demo only)
create policy "allow_public_read_write_products" on products
  for all using (true) with check (true);

create policy "allow_public_read_write_reviews" on reviews
  for all using (true) with check (true);

-- Note: In production, replace above policies with strict auth-based policies.
