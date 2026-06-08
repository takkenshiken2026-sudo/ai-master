import { corsHeaders, jsonResponse } from "../_shared/cors.ts";
import { adminClient } from "../_shared/supabase.ts";

type Body = {
  examSlug?: string;
  examId?: string;
  token?: string;
};

const MOCK_EXAM_IDS = ["mock_01", "mock_02", "mock_03"];
const BUNDLE_EXAM_ID = "bundle";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  try {
    const { examSlug, examId, token } = (await req.json()) as Body;
    if (
      !examSlug ||
      !examId ||
      !token ||
      examId === "sample" ||
      !MOCK_EXAM_IDS.includes(examId)
    ) {
      return jsonResponse({ ok: false }, 400);
    }

    const supabase = adminClient();
    const { data, error } = await supabase
      .from("mock_access_tokens")
      .select("token, email, exam_slug, exam_id")
      .eq("token", token)
      .eq("exam_slug", examSlug)
      .maybeSingle();

    if (error) throw error;
    if (!data) {
      return jsonResponse({ ok: false });
    }

    const bundleAccess =
      data.exam_id === BUNDLE_EXAM_ID && MOCK_EXAM_IDS.includes(examId);
    const singleAccess = data.exam_id === examId;
    if (!bundleAccess && !singleAccess) {
      return jsonResponse({ ok: false });
    }

    await supabase
      .from("mock_access_tokens")
      .update({ last_used_at: new Date().toISOString() })
      .eq("token", token);

    return jsonResponse({
      ok: true,
      email: data.email,
      examSlug: data.exam_slug,
      examId: data.exam_id,
    });
  } catch (error) {
    console.error(error);
    return jsonResponse(
      { ok: false, error: error instanceof Error ? error.message : "Verify failed" },
      500
    );
  }
});
