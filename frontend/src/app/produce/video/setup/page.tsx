import { PageHeader } from "../../../../components/page-header";
import { StatCard } from "../../../../components/stat-card";
import { labelReady } from "../../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

async function loadStatus(): Promise<Record<string, unknown>> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/local-tools/status`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return asRecord(await response.json());
  } catch {
    return {};
  }
}

export default async function LocalVideoSetupPage() {
  const status = await loadStatus();
  const ollama = asRecord(status.ollama);
  const comfyui = asRecord(status.comfyui);
  const localVideoCommand = asRecord(status.local_video_command);

  const models = Array.isArray(ollama.models) ? ollama.models.map(String) : [];
  const qwenModels = Array.isArray(ollama.qwen_models) ? ollama.qwen_models.map(String) : [];

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="ابزارهای لوکال"
        title="وضعیت Ollama Qwen و موتور ویدیو"
        lead="اینجا میبینی DAMA کدام ابزارهای لوکال را پیدا کرده و برای ساخت واقعی ویدیو چه چیزی کم است."
      >
        <div className="actions">
          <a href="/produce/video">بازگشت به ویدیو</a>
          <a href="/other">سایر</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="Ollama" value={labelReady(Boolean(ollama.ready))} helper={String(ollama.message ?? "")} />
        <StatCard label="Qwen" value={qwenModels.length > 0 ? "پیدا شد" : "پیدا نشد"} helper={String(ollama.preferred_model ?? "")} />
        <StatCard label="ComfyUI" value={labelReady(Boolean(comfyui.ready))} helper={String(comfyui.base_url ?? "")} />
        <StatCard label="موتور ویدیو" value={labelReady(Boolean(localVideoCommand.ready))} helper={String(localVideoCommand.message ?? "")} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">Ollama / Qwen</p>
            <h2>برای بهبود پرامپت</h2>
          </div>

          <dl className="detail-list">
            <div>
              <dt>آدرس</dt>
              <dd>{String(ollama.base_url ?? "")}</dd>
            </div>
            <div>
              <dt>مدل پیشنهادی</dt>
              <dd>{String(ollama.preferred_model ?? "")}</dd>
            </div>
            <div>
              <dt>مدلهای Qwen</dt>
              <dd>{qwenModels.length > 0 ? qwenModels.join(" ") : ""}</dd>
            </div>
            <div>
              <dt>همه مدلها</dt>
              <dd>{models.length > 0 ? models.join(" ") : ""}</dd>
            </div>
          </dl>
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">موتور ویدیو</p>
            <h2>برای ساخت واقعی</h2>
          </div>

          <ol className="simple-steps">
            <li>Ollama/Qwen فقط پرامپت را بهتر میکند.</li>
            <li>برای ساخت واقعی ویدیو باید ComfyUI یا یک اسکریپت لوکال وصل شود.</li>
            <li>اگر آن برنامه Studio همان ComfyUI یا ابزار سازگار باشد از همین مسیر وصلش میکنیم.</li>
            <li>متغیر DAMA_LOCAL_VIDEO_COMMAND مسیر اسکریپت اجرای ویدیو را مشخص میکند.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش جزئیات فنی</summary>
          <pre className="json-block">{JSON.stringify(status, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
