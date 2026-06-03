export interface Env {
  AI: Ai;
  IMAGEN_PROXY_AUTH_TOKEN?: string;
}

const ALLOWED_ASPECT_RATIOS = new Set(["1:1", "3:4", "4:3", "9:16", "16:9"]);
const ALLOWED_PERSON_GENERATION = new Set(["dont_allow", "allow_adult", "allow_all"]);

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Authorization, Content-Type",
    },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return jsonResponse({});
    }
    if (request.method !== "POST") {
      return jsonResponse({ error: "Method not allowed" }, 405);
    }

    if (env.IMAGEN_PROXY_AUTH_TOKEN) {
      const expected = `Bearer ${env.IMAGEN_PROXY_AUTH_TOKEN}`;
      if (request.headers.get("Authorization") !== expected) {
        return jsonResponse({ error: "Unauthorized" }, 401);
      }
    }

    const body = (await request.json()) as {
      prompt?: string;
      aspect_ratio?: string;
      person_generation?: string;
    };

    if (!body.prompt || typeof body.prompt !== "string") {
      return jsonResponse({ error: "prompt is required" }, 422);
    }

    const aspectRatio = body.aspect_ratio || "1:1";
    const personGeneration = body.person_generation || "dont_allow";

    if (!ALLOWED_ASPECT_RATIOS.has(aspectRatio)) {
      return jsonResponse({ error: "Invalid aspect_ratio" }, 422);
    }
    if (!ALLOWED_PERSON_GENERATION.has(personGeneration)) {
      return jsonResponse({ error: "Invalid person_generation" }, 422);
    }

    const input = {
      prompt: body.prompt,
      aspect_ratio: aspectRatio,
      person_generation: personGeneration,
    };

    try {
      const result = await env.AI.run("google/imagen-4", input, {
        gateway: { id: "default" },
      });
      return jsonResponse(result);
    } catch (gatewayError) {
      try {
        const result = await env.AI.run("google/imagen-4", input);
        return jsonResponse(result);
      } catch (directError) {
        return jsonResponse(
          {
            error: "Imagen generation failed",
            gateway_error:
              gatewayError instanceof Error
                ? { name: gatewayError.name, message: gatewayError.message, stack: gatewayError.stack }
                : String(gatewayError),
            direct_error:
              directError instanceof Error
                ? { name: directError.name, message: directError.message, stack: directError.stack }
                : String(directError),
          },
          502,
        );
      }
    }
  },
};
