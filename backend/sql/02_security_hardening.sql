-- Security Hardening Migration

-- 1. Fix Security Definer Views (Error)
-- "security_invoker = true" ensures the view checks permissions of the caller, not the owner.
ALTER VIEW public.sentiment_trends SET (security_invoker = true);
ALTER VIEW public.product_stats SET (security_invoker = true);

-- 2. Fix RLS Disabled on Reports (Error)
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
-- Create a strict read policy (Authenticated users only)
-- Backend can still write via Service Role.
DROP POLICY IF EXISTS "Authenticated read reports" ON public.reports;
CREATE POLICY "Authenticated read reports" ON public.reports FOR SELECT TO authenticated USING (true);

-- 3. Fix Mutable Search Path on Functions (Warning)
ALTER FUNCTION public.handle_new_user SET search_path = public;

-- 4. Remove Permissive Insert/Update Policies (Warning)
-- The Backend uses the Service Role (which bypasses RLS) to insert data.
-- Therefore, we do NOT need to allow public or authenticated users to insert directly.
-- Removing these policies secures the database from frontend attacks (e.g. users inserting fake reviews directly).

DROP POLICY IF EXISTS "Enable insert for all users" ON public.alerts;
DROP POLICY IF EXISTS "Enable insert for all users" ON public.integrations;
DROP POLICY IF EXISTS "Enable update for all users" ON public.integrations;
DROP POLICY IF EXISTS "Enable insert for all users" ON public.products;
DROP POLICY IF EXISTS "Enable insert for all users" ON public.reviews;

-- 5. Ensure Authenticated Read Access (for Realtime Subscriptions)
-- Users need SELECT access to receive realtime updates, even if they can't insert.

-- Alerts
DROP POLICY IF EXISTS "Authenticated read alerts" ON public.alerts;
CREATE POLICY "Authenticated read alerts" ON public.alerts FOR SELECT TO authenticated USING (true);

-- Integrations
DROP POLICY IF EXISTS "Authenticated read integrations" ON public.integrations;
CREATE POLICY "Authenticated read integrations" ON public.integrations FOR SELECT TO authenticated USING (true);

-- Products (Ensure users can read)
DROP POLICY IF EXISTS "Authenticated read products" ON public.products;
CREATE POLICY "Authenticated read products" ON public.products FOR SELECT TO authenticated USING (true);

-- Reviews (Ensure users can read)
DROP POLICY IF EXISTS "Authenticated read reviews" ON public.reviews;
CREATE POLICY "Authenticated read reviews" ON public.reviews FOR SELECT TO authenticated USING (true);
