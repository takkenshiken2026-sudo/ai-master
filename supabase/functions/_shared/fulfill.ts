import type { SupabaseClient } from "https://esm.sh/@supabase/supabase-js@2.49.1";
import type Stripe from "https://esm.sh/stripe@14.21.0?target=deno";
import { MOCK_PRICE_YEN } from "./stripe.ts";

export type FulfillResult = {
  email: string;
  examSlug: string;
  examId: string;
  examTitle: string;
  token: string;
  playPath: string;
  alreadyOwned: boolean;
};

function playPath(examSlug: string, examId: string) {
  if (examId === "bundle") {
    return `/exams/${examSlug}/mock/index.html`;
  }
  return `/exams/${examSlug}/mock/play.html?exam=${encodeURIComponent(examId)}`;
}

function accessUrl(siteUrl: string, examSlug: string, examId: string, token: string) {
  const base = siteUrl.replace(/\/$/, "");
  return `${base}${playPath(examSlug, examId)}&access=${encodeURIComponent(token)}`;
}

export async function fulfillCheckoutSession(
  supabase: SupabaseClient,
  session: Stripe.Checkout.Session,
  siteUrl: string
): Promise<FulfillResult> {
  const email = session.customer_details?.email || session.customer_email;
  const examSlug = session.metadata?.exam_slug;
  const examId = session.metadata?.exam_id;
  const examTitle = session.metadata?.exam_title || examId || "模擬試験";

  if (!email || !examSlug || !examId) {
    throw new Error("Checkout session is missing purchase metadata");
  }

  const { data: existingPurchase } = await supabase
    .from("mock_purchases")
    .select("id, email, exam_slug, exam_id, exam_title")
    .eq("email", email)
    .eq("exam_slug", examSlug)
    .eq("exam_id", examId)
    .maybeSingle();

  let purchaseId = existingPurchase?.id;

  if (!purchaseId) {
    const { data: inserted, error: insertError } = await supabase
      .from("mock_purchases")
      .insert({
        email,
        exam_slug: examSlug,
        exam_id: examId,
        exam_title: examTitle,
        stripe_session_id: session.id,
        stripe_payment_intent_id:
          typeof session.payment_intent === "string"
            ? session.payment_intent
            : session.payment_intent?.id ?? null,
        amount_yen: session.amount_total ?? MOCK_PRICE_YEN,
      })
      .select("id")
      .single();

    if (insertError) {
      if (insertError.code === "23505") {
        const { data: retry } = await supabase
          .from("mock_purchases")
          .select("id")
          .eq("stripe_session_id", session.id)
          .maybeSingle();
        purchaseId = retry?.id;
      } else {
        throw insertError;
      }
    } else {
      purchaseId = inserted.id;
    }
  }

  if (!purchaseId) {
    throw new Error("Failed to resolve purchase record");
  }

  const { data: existingToken } = await supabase
    .from("mock_access_tokens")
    .select("token")
    .eq("purchase_id", purchaseId)
    .maybeSingle();

  let token = existingToken?.token;

  if (!token) {
    const { data: tokenRow, error: tokenError } = await supabase
      .from("mock_access_tokens")
      .insert({
        purchase_id: purchaseId,
        email,
        exam_slug: examSlug,
        exam_id: examId,
      })
      .select("token")
      .single();

    if (tokenError) throw tokenError;
    token = tokenRow.token;
  }

  return {
    email,
    examSlug,
    examId,
    examTitle,
    token,
    playPath: playPath(examSlug, examId),
    alreadyOwned: Boolean(existingPurchase),
  };
}

export async function sendAccessEmail(
  result: FulfillResult,
  siteUrl: string
): Promise<boolean> {
  const apiKey = Deno.env.get("RESEND_API_KEY");
  const from = Deno.env.get("RESEND_FROM") || "AIマスター <noreply@ai-master.jp>";
  if (!apiKey) return false;

  const link = accessUrl(siteUrl, result.examSlug, result.examId, result.token);
  const subject = `【AIマスター】${result.examTitle} の受験リンク`;
  const html = `
    <p>${result.examTitle} のご購入ありがとうございます。</p>
    <p>以下のリンクから、いつでも模擬試験を受験できます（買い切り）。</p>
    <p><a href="${link}">${link}</a></p>
    <p>リンクは第三者と共有しないでください。</p>
  `;

  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from,
      to: [result.email],
      subject,
      html,
    }),
  });

  return res.ok;
}

export function publicFulfillPayload(result: FulfillResult, siteUrl: string) {
  const link = accessUrl(siteUrl, result.examSlug, result.examId, result.token);
  return {
    email: result.email,
    examSlug: result.examSlug,
    examId: result.examId,
    examTitle: result.examTitle,
    token: result.token,
    playPath: result.playPath,
    accessUrl: link,
    alreadyOwned: result.alreadyOwned,
  };
}
