import { corsHeaders, jsonResponse } from "../_shared/cors.ts";
import { MOCK_PRICE_YEN, stripeClient } from "../_shared/stripe.ts";

type CheckoutBody = {
  examSlug?: string;
  examId?: string;
  examTitle?: string;
  email?: string;
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  try {
    const siteUrl = Deno.env.get("SITE_URL") || "https://ai-master.jp";
    const body = (await req.json()) as CheckoutBody;
    const examSlug = body.examSlug?.trim();
    const examId = body.examId?.trim();
    const examTitle = body.examTitle?.trim() || "模擬試験";

    if (!examSlug || !examId || examId === "sample") {
      return jsonResponse({ error: "Invalid exam" }, 400);
    }

    const stripe = stripeClient();
    const successUrl =
      `${siteUrl.replace(/\/$/, "")}/exams/${examSlug}/mock/success.html?session_id={CHECKOUT_SESSION_ID}`;
    const cancelUrl =
      `${siteUrl.replace(/\/$/, "")}/exams/${examSlug}/mock/`;

    const session = await stripe.checkout.sessions.create({
      mode: "payment",
      customer_email: body.email?.trim() || undefined,
      line_items: [
        {
          quantity: 1,
          price_data: {
            currency: "jpy",
            unit_amount: MOCK_PRICE_YEN,
            product_data: {
              name: `${examTitle}（買い切り）`,
              description: "AIマスター 模擬試験 1回分",
            },
          },
        },
      ],
      metadata: {
        exam_slug: examSlug,
        exam_id: examId,
        exam_title: examTitle,
      },
      success_url: successUrl,
      cancel_url: cancelUrl,
    });

    if (!session.url) {
      return jsonResponse({ error: "Failed to create checkout session" }, 500);
    }

    return jsonResponse({ url: session.url, sessionId: session.id });
  } catch (error) {
    console.error(error);
    return jsonResponse(
      { error: error instanceof Error ? error.message : "Checkout failed" },
      500
    );
  }
});
