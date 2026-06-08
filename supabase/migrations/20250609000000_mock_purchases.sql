-- 有料模擬試験: Stripe 買い切り購入とメールリンク用アクセストークン

create table if not exists public.mock_purchases (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  exam_slug text not null,
  exam_id text not null,
  exam_title text not null default '',
  stripe_session_id text not null unique,
  stripe_payment_intent_id text,
  amount_yen integer not null default 980,
  created_at timestamptz not null default now(),
  constraint mock_purchases_exam_unique unique (email, exam_slug, exam_id)
);

create index if not exists mock_purchases_email_idx on public.mock_purchases (email);
create index if not exists mock_purchases_exam_idx on public.mock_purchases (exam_slug, exam_id);

create table if not exists public.mock_access_tokens (
  token uuid primary key default gen_random_uuid(),
  purchase_id uuid not null references public.mock_purchases (id) on delete cascade,
  email text not null,
  exam_slug text not null,
  exam_id text not null,
  created_at timestamptz not null default now(),
  last_used_at timestamptz,
  constraint mock_access_tokens_purchase_unique unique (purchase_id)
);

create index if not exists mock_access_tokens_lookup_idx
  on public.mock_access_tokens (token, exam_slug, exam_id);

alter table public.mock_purchases enable row level security;
alter table public.mock_access_tokens enable row level security;

-- Edge Functions は service_role で操作。anon からの直接読み書きは不可。
