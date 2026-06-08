import { fulfillCheckoutSession, sendAccessEmail } from "../_shared/fulfill.ts";
import { stripeClient } from "../_shared/stripe.ts";
import { adminClient } from "../_shared/supabase.ts";
import Stripe from "https://esm.sh/stripe@14.21.0?target=deno";

Deno.serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  const stripe = stripeClient();
  const webhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET");
  if (!webhookSecret) {
    return new Response("Webhook secret not configured", { status: 500 });
  }

  const signature = req.headers.get("stripe-signature");
  if (!signature) {
    return new Response("Missing stripe-signature", { status: 400 });
  }

  const body = await req.text();
  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (error) {
    console.error(error);
    return new Response("Invalid signature", { status: 400 });
  }

  if (event.type === "checkout.session.completed") {
    const session = event.data.object as Stripe.Checkout.Session;
    if (session.payment_status === "paid") {
      try {
        const siteUrl = Deno.env.get("SITE_URL") || "https://ai-master.jp";
        const supabase = adminClient();
        const result = await fulfillCheckoutSession(supabase, session, siteUrl);
        await sendAccessEmail(result, siteUrl);
      } catch (error) {
        console.error("Webhook fulfillment failed", error);
        return new Response("Fulfillment failed", { status: 500 });
      }
    }
  }

  return new Response(JSON.stringify({ received: true }), {
    headers: { "Content-Type": "application/json" },
  });
});
