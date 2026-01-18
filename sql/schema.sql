-- Supabase schema for Sentiment Beacon (Phase 1)
-- Run this in the Supabase SQL editor to reset DB

-- Create products table
create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  keywords text[] default array[]::text[],
  track_reddit boolean default false,
  track_twitter boolean default false,
  track_youtube boolean default true,
  created_at timestamptz default now()
);

-- Create reviews table
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

create index if not exists idx_reviews_product on reviews(product_id);
create index if not exists idx_reviews_created_at on reviews(created_at);

-- Enable Row Level Security but allow public read/write for demo only
alter table products enable row level security;
alter table reviews enable row level security;

create policy "allow_public_products" on products
  for all using (true) with check (true);

create policy "allow_public_reviews" on reviews
  for all using (true) with check (true);

-- NOTE: Replace the permissive policies with authenticated policies in production.
