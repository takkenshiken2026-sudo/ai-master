import { corsHeaders, jsonResponse } from "../_shared/cors.ts";
import {
  fulfillCheckoutSession,
  publicFulfillPayload,
  sendAccessEmail,
} from "../_shared/fulfill.ts";
import { stripeClient } from "../_shared/stripe.ts";
import { adminClient } from "../_shared/supabase.ts";

type Body = { sessionId?: string };

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  try {
    const siteUrl = Deno.env.get("SITE_URL") || "https://ai-master.jp";
    const { sessionId } = (await req.json()) as Body;
    if (!sessionId) {
      return jsonResponse({ error: "sessionId is required" }, 400);
    }

    const stripe = stripeClient();
    const session = await stripe.checkout.sessions.retrieve(sessionId);

    if (session.payment_status !== "paid") {
      return jsonResponse({ error: "Payment not completed" }, 402);
    }

    const supabase = adminClient();
    const result = await fulfillCheckoutSession(supabase, session, siteUrl);
    const emailSent = await sendAccessEmail(result, siteUrl);

    return jsonResponse({
      ...publicFulfillPayload(result, siteUrl),
      emailSent,
    });
  } catch (error) {
    console.error(error);
    return jsonResponse(
      { error: error instanceof Error ? error.message : "Fulfillment failed" },
      500
    );
  }
});
