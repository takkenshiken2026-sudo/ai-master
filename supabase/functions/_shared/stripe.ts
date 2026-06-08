import Stripe from "https://esm.sh/stripe@14.21.0?target=deno";

export function stripeClient() {
  const key = Deno.env.get("STRIPE_SECRET_KEY");
  if (!key) throw new Error("STRIPE_SECRET_KEY is not configured");
  return new Stripe(key, { apiVersion: "2024-06-20" });
}

export const MOCK_PRICE_YEN = 980;
