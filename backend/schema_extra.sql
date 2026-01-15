-- Extra schema additions for Alerts, Settings, Integrations, Topic Analysis

-- Alerts table: stores generated alerts from the ingestion/AI pipeline
create table if not exists alerts (
  id serial primary key,
  type text not null,
  severity text not null,
  title text not null,
  message text not null,
  platform text,
  is_read boolean default false,
  created_at timestamptz default now()
);

-- User settings: key/value per user
create table if not exists user_settings (
  user_id text not null,
  key text not null,
  value text,
  updated_at timestamptz default now(),
  primary key (user_id, key)
);

-- Integrations: store platform API keys and sync info
create table if not exists integrations (
  id serial primary key,
  platform text not null,
  status text,
  last_sync timestamptz,
  api_key text,
  is_enabled boolean default false
);

-- Topic analysis: stores topic clustering results
create table if not exists topic_analysis (
  id serial primary key,
  topic_name text not null,
  sentiment numeric,
  size integer,
  keywords text[],
  created_at timestamptz default now()
);
