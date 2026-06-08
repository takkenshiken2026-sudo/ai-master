# 有料模擬試験（Stripe + Supabase）

G検定・生成AIパスポートの有料模擬試験（`mock_01`〜`mock_03`）を **1回 ¥980 買い切り** で販売するためのセットアップ手順です。`sample` は引き続き無料です。

## 概要

| 項目 | 内容 |
|------|------|
| 価格 | ¥980 / 模擬試験1回（買い切り・再受験可） |
| 決済 | Stripe Checkout |
| 購入記録 | Supabase（`mock_purchases`） |
| 再入場 | メールの受験リンク、またはブラウザの localStorage |

`checkoutEnabled: false` の間は、従来どおり無料で受験できます。

## 1. Supabase プロジェクト

1. [Supabase](https://supabase.com/) でプロジェクトを作成
2. SQL Editor で `supabase/migrations/20250609000000_mock_purchases.sql` を実行
3. **Project Settings → API** から以下を控える
   - Project URL → `supabaseUrl`
   - `anon` `public` key → `supabaseAnonKey`
   - `service_role` key → Edge Functions のシークレット用（フロントに載せない）

## 2. Edge Functions のデプロイ

[Supabase CLI](https://supabase.com/docs/guides/cli) をインストールし、プロジェクトをリンクします。

```bash
supabase login
supabase link --project-ref <your-project-ref>
```

以下のシークレットを設定します。

```bash
supabase secrets set \
  STRIPE_SECRET_KEY=sk_live_... \
  STRIPE_WEBHOOK_SECRET=whsec_... \
  SITE_URL=https://ai-master.jp \
  RESEND_API_KEY=re_... \
  RESEND_FROM="AIマスター <noreply@ai-master.jp>"
```

`RESEND_*` はメール送信を使う場合のみ。未設定でも購入完了画面に受験リンクが表示されます。

Functions をデプロイします。

```bash
supabase functions deploy create-mock-checkout
supabase functions deploy fulfill-mock-session
supabase functions deploy verify-mock-access
supabase functions deploy stripe-webhook --no-verify-jwt
```

`stripe-webhook` は Stripe からの署名検証のみ行うため `--no-verify-jwt` が必要です。

## 3. Stripe

1. [Stripe Dashboard](https://dashboard.stripe.com/) で Checkout を有効化
2. **Developers → Webhooks** でエンドポイントを追加
   - URL: `https://<project-ref>.supabase.co/functions/v1/stripe-webhook`
   - イベント: `checkout.session.completed`
3. 署名シークレットを `STRIPE_WEBHOOK_SECRET` に設定

テスト時は `sk_test_...` / `whsec_...` を使い、本番切り替え時に `sk_live_...` に差し替えます。

## 4. フロントエンドの有効化

`assets/data/mock-commerce.json` を編集します。

```json
{
  "checkoutEnabled": true,
  "supabaseUrl": "https://xxxx.supabase.co",
  "supabaseAnonKey": "eyJ...",
  "priceYen": 980,
  "currency": "jpy"
}
```

GitHub Pages に push すると本番で有料化が有効になります。ローカル確認時は `python3 -m http.server` で同じ JSON を読み込みます。

## 5. 購入フロー

1. 模擬試験一覧で「購入する」→ Stripe Checkout（¥980）
2. 決済完了 → `success.html?session_id=...` でトークン発行
3. Webhook でも同様に fulfillment（冪等）
4. 受験リンク `play.html?exam=mock_01&access=<token>` をメール送信（Resend 設定時）
5. 再入場時はリンクまたは localStorage のトークンで `verify-mock-access` を検証

## 関連ファイル

| パス | 役割 |
|------|------|
| `assets/js/mock-commerce.js` | Checkout 開始・トークン管理 |
| `assets/js/exam-mock-index.js` | 一覧の購入/受験 UI |
| `exams/*/mock/play.html` | 受験ゲート |
| `exams/*/mock/success.html` | 購入完了画面 |
| `supabase/functions/create-mock-checkout` | Checkout Session 作成 |
| `supabase/functions/stripe-webhook` | 決済完了 webhook |
| `supabase/functions/fulfill-mock-session` | 成功ページからの fulfillment |
| `supabase/functions/verify-mock-access` | トークン検証 |
