import { corsHeaders, jsonResponse } from "../_shared/cors.ts";
import { adminClient } from "../_shared/supabase.ts";

type Body = {
  examSlug?: string;
  examId?: string;
  token?: string;
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }
  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  try {
    const { examSlug, examId, token } = (await req.json()) as Body;
    if (!examSlug || !examId || !token || examId === "sample") {
      return jsonResponse({ ok: false }, 400);
    }

    const supabase = adminClient();
    const { data, error } = await supabase
      .from("mock_access_tokens")
      .select("token, email, exam_slug, exam_id")
      .eq("token", token)
      .eq("exam_slug", examSlug)
      .eq("exam_id", examId)
      .maybeSingle();

    if (error) throw error;
    if (!data) {
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
