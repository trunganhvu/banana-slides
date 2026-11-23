import { DurableObject } from "cloudflare:workers";

export interface Env {
  BANANA_CONTAINER: DurableObjectNamespace<BananaSlidesContainer>;
  // Required database & auth secrets
  DATABASE_URL?: string;
  SECRET_KEY?: string;
  GOOGLE_CLIENT_ID?: string;
  ADMIN_EMAILS?: string;
  CORS_ORIGINS?: string;
  ACCESS_CODE?: string;
  // AI provider configuration
  AI_PROVIDER_FORMAT?: string;
  GOOGLE_API_KEY?: string;
  GOOGLE_API_BASE?: string;
  OPENAI_API_KEY?: string;
  OPENAI_API_BASE?: string;
  ANTHROPIC_API_KEY?: string;
  TEXT_MODEL?: string;
  IMAGE_MODEL?: string;
  IMAGE_CAPTION_MODEL?: string;
  // Cloudflare R2 FUSE mount configuration
  R2_ACCOUNT_ID?: string;
  R2_BUCKET_NAME?: string;
  AWS_ACCESS_KEY_ID?: string;
  AWS_SECRET_ACCESS_KEY?: string;
  // Runtime defaults
  FLASK_ENV?: string;
  OUTPUT_LANGUAGE?: string;
}

const CONTAINER_PORT = 5000;
const INACTIVITY_TIMEOUT_MS = 15 * 60 * 1000;
const STARTUP_WAIT_ATTEMPTS = 120;
const STARTUP_POLL_INTERVAL_MS = 500;

const FORWARDED_ENV_KEYS: ReadonlyArray<keyof Env> = [
  "DATABASE_URL",
  "SECRET_KEY",
  "GOOGLE_CLIENT_ID",
  "ADMIN_EMAILS",
  "CORS_ORIGINS",
  "ACCESS_CODE",
  "AI_PROVIDER_FORMAT",
  "GOOGLE_API_KEY",
  "GOOGLE_API_BASE",
  "OPENAI_API_KEY",
  "OPENAI_API_BASE",
  "ANTHROPIC_API_KEY",
  "TEXT_MODEL",
  "IMAGE_MODEL",
  "IMAGE_CAPTION_MODEL",
  "R2_ACCOUNT_ID",
  "R2_BUCKET_NAME",
  "AWS_ACCESS_KEY_ID",
  "AWS_SECRET_ACCESS_KEY",
  "FLASK_ENV",
  "OUTPUT_LANGUAGE",
];

function buildContainerEnv(env: Env): Record<string, string> {
  const result: Record<string, string> = {
    IN_DOCKER: "1",
    UPLOAD_FOLDER: "/app/uploads",
    FLASK_ENV: env.FLASK_ENV || "production",
    OUTPUT_LANGUAGE: env.OUTPUT_LANGUAGE || "vi",
  };

  for (const key of FORWARDED_ENV_KEYS) {
    const val = env[key];
    if (typeof val === "string" && val.length > 0) {
      result[key] = val;
    }
  }

  return result;
}

export class BananaSlidesContainer extends DurableObject<Env> {
  private starting: Promise<void> | undefined;

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
    const container = ctx.container;
    if (container?.running) {
      void ctx.blockConcurrencyWhile(() =>
        container.setInactivityTimeout(INACTIVITY_TIMEOUT_MS)
      );
    }
  }

  async fetch(request: Request): Promise<Response> {
    this.starting ??= this.startAndWaitForPort().finally(() => {
      this.starting = undefined;
    });
    await this.starting;

    const url = new URL(request.url);
    url.protocol = "http:";
    url.host = "container";

    const forwarded = new Request(url, request);
    forwarded.headers.delete("host");
    return this.ctx.container!.getTcpPort(CONTAINER_PORT).fetch(forwarded);
  }

  private async startAndWaitForPort(): Promise<void> {
    const container = this.ctx.container;
    if (!container) {
      throw new Error("Container binding is not configured on BananaSlidesContainer.");
    }

    if (!container.running) {
      container.start({
        enableInternet: true,
        env: buildContainerEnv(this.env),
      });
    }

    await container.setInactivityTimeout(INACTIVITY_TIMEOUT_MS);

    const port = container.getTcpPort(CONTAINER_PORT);
    for (let attempt = 0; attempt < STARTUP_WAIT_ATTEMPTS; attempt += 1) {
      try {
        const res = await port.fetch("http://container/health");
        if (res.ok) {
          return;
        }
      } catch {
        // Container is still booting tigrisfs / Flask; wait and retry health check.
      }
      await new Promise((resolve) => setTimeout(resolve, STARTUP_POLL_INTERVAL_MS));
    }

    throw new Error("Banana Slides backend container failed readiness check on /health.");
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const instance = env.BANANA_CONTAINER.getByName("primary");
    return instance.fetch(request);
  },
};
