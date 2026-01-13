
-- Enable RLS on core tables
alter table products enable row level security;
alter table reviews enable row level security;
alter table sentiment_analysis enable row level security;

-- Create policies for Products
-- Allow users to see only their own products
create policy "Users can view their own products"
on products for select
using (auth.uid() = user_id);

-- Allow users to insert their own products
create policy "Users can check their own products"
on products for insert
with check (auth.uid() = user_id);

-- Allow users to delete their own products
create policy "Users can delete their own products"
on products for delete
using (auth.uid() = user_id);

-- Reviews and Analysis often don't have a direct 'user_id' column if they link to product.
-- You might need to join or denormalize, but for simplicity, we often let users read reviews 
-- if they own the parent product. OR, we just make reviews readable by authenticated users 
-- if strict privacy isn't the concern, but data modification is.

-- Simple approach: Authenticated users can read reviews (to simplify dashboard queries)
create policy "Authenticated users can read reviews"
on reviews for select
to authenticated
using (true);

-- Authenticated users can read analysis
create policy "Authenticated users can read analysis"
on sentiment_analysis for select
to authenticated
using (true);

-- Backend (Service Role) bypasses RLS, so the scraper/scheduler will still work fine.
