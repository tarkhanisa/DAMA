from pathlib import Path

ROOT = Path("I:/DAMA")


def write_file(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def append_once(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8") if target.exists() else ""

    if marker not in text:
        target.write_text(text.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
        print(f"Updated {path}")
    else:
        print(f"Skipped {path}")


api_path = ROOT / "backend/src/api/publishing.py"
api_text = api_path.read_text(encoding="utf-8")

if '@router.get("/local-video/jobs/{job_id}/output")' not in api_text:
    api_text += r'''


@router.get("/local-video/jobs/{job_id}/output")
def api_get_local_video_output(job_id: str):
    from pathlib import Path

    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    from src.services.local_video_service import get_video_job

    job = get_video_job(job_id)

    if not isinstance(job, dict):
        raise HTTPException(status_code=404, detail="Local video job not found.")

    output_path = Path(str(job.get("output_path") or ""))

    if not output_path.is_file():
        raise HTTPException(status_code=404, detail="Local video output file not found.")

    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename=output_path.name,
    )


@router.post("/local-video/jobs/{job_id}/open-output-folder")
def api_open_local_video_output_folder(job_id: str):
    from pathlib import Path
    import os
    import subprocess
    import sys

    from fastapi import HTTPException

    from src.services.local_video_service import get_video_job

    job = get_video_job(job_id)

    if not isinstance(job, dict):
        raise HTTPException(status_code=404, detail="Local video job not found.")

    output_path = Path(str(job.get("output_path") or ""))

    if not output_path:
        raise HTTPException(status_code=404, detail="Local video output path is empty.")

    folder = output_path.parent

    if not folder.exists():
        raise HTTPException(status_code=404, detail="Local video output folder not found.")

    try:
        if os.name == "nt":
            os.startfile(str(folder))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not open output folder: {exc}") from exc

    return {
        "ok": True,
        "folder": str(folder),
        "message": "Output folder open request sent.",
    }
'''

api_path.write_text(api_text.strip() + "\n", encoding="utf-8")
print("Patched publishing API with video output endpoints.")


write_file(
    "frontend/src/components/local-video-output-actions.tsx",
    r'''
"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type LocalVideoOutputActionsProps = {
  apiBaseUrl: string;
  jobId: string;
  outputPath: string;
  hasOutput: boolean;
};

export function LocalVideoOutputActions({
  apiBaseUrl,
  jobId,
  outputPath,
  hasOutput
}: LocalVideoOutputActionsProps) {
  const [message, setMessage] = useState("");

  const outputUrl = `${apiBaseUrl}/publishing/local-video/jobs/${jobId}/output`;

  async function copyOutputPath() {
    setMessage("");

    if (!outputPath) {
      setMessage("هنوز مسیر خروجی وجود ندارد.");
      return;
    }

    try {
      await navigator.clipboard.writeText(outputPath);
      setMessage("مسیر خروجی کپی شد.");
    } catch {
      setMessage("کپی خودکار انجام نشد. مسیر را دستی کپی کن.");
    }
  }

  async function openOutputFolder() {
    setMessage("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/local-video/jobs/${jobId}/open-output-folder`,
        {
          method: "POST"
        }
      );

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("درخواست باز کردن فولدر خروجی ارسال شد.");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    }
  }

  function openVideoInNewWindow() {
    if (!hasOutput) {
      setMessage("هنوز ویدیوی خروجی ساخته نشده است.");
      return;
    }

    window.open(outputUrl, "_blank", "noopener,noreferrer");
  }

  return (
    <div className="local-video-actions">
      <button type="button" onClick={openVideoInNewWindow} disabled={!hasOutput}>
        مشاهده ویدیو
      </button>

      <button type="button" onClick={openOutputFolder} disabled={!hasOutput}>
        باز کردن فولدر خروجی
      </button>

      <button type="button" onClick={copyOutputPath} disabled={!outputPath}>
        کپی مسیر فایل
      </button>

      <a href={`/produce/video/${jobId}`}>به‌روزرسانی وضعیت</a>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
    ''',
)


write_file(
    "frontend/src/app/produce/video/[jobId]/page.tsx",
    r'''
import { LocalVideoOutputActions } from "../../../../components/local-video-output-actions";
import { PageHeader } from "../../../../components/page-header";
import { RunLocalVideoJobAction } from "../../../../components/run-local-video-job-action";
import { StatCard } from "../../../../components/stat-card";
import { formatPersianDate, shortId } from "../../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type Props = {
  params: Promise<{
    jobId: string;
  }>;
};

type StepState = "done" | "active" | "waiting" | "failed";

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

async function loadJob(jobId: string): Promise<Record<string, unknown>> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/local-video/jobs/${jobId}`, {
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

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "ثبت‌شده",
    queued: "در صف اجرا",
    dry_run: "Dry-run انجام شد",
    blocked: "نیازمند تنظیم",
    running: "در حال اجرا",
    completed: "ساخته شد",
    failed: "خطا"
  };

  return labels[status] ?? "نامشخص";
}

function statusHelper(status: string): string {
  const labels: Record<string, string> = {
    draft: "درخواست آماده اجراست.",
    queued: "در صف موتور لوکال قرار گرفته است.",
    dry_run: "فایل ورودی آماده شده؛ هنوز خروجی نهایی ساخته نشده.",
    blocked: "موتور لوکال یا تنظیمات ناقص است.",
    running: "در حال ساخت ویدیو.",
    completed: "خروجی MP4 ساخته شده است.",
    failed: "اجرای ویدیو با خطا متوقف شده است."
  };

  return labels[status] ?? "وضعیت دقیق مشخص نیست.";
}

function engineLabel(job: Record<string, unknown>): string {
  const engine = String(job.engine ?? job.mode ?? "").trim();

  if (engine) {
    return engine;
  }

  const outputPath = String(job.output_path ?? "");

  if (outputPath) {
    return "FFmpeg Local";
  }

  return "Local Video";
}

function stepState(status: string, step: "request" | "prompt" | "prepare" | "render" | "review"): StepState {
  if (status === "failed" && step === "render") {
    return "failed";
  }

  if (step === "request") {
    return "done";
  }

  if (step === "prompt") {
    return ["dry_run", "running", "completed"].includes(status) ? "done" : "active";
  }

  if (step === "prepare") {
    return ["dry_run", "running", "completed"].includes(status) ? "done" : "waiting";
  }

  if (step === "render") {
    if (status === "completed") {
      return "done";
    }

    if (status === "running") {
      return "active";
    }

    return "waiting";
  }

  if (step === "review") {
    return status === "completed" ? "active" : "waiting";
  }

  return "waiting";
}

function stepLabel(state: StepState): string {
  const labels: Record<StepState, string> = {
    done: "انجام شد",
    active: "فعال",
    waiting: "در انتظار",
    failed: "خطا"
  };

  return labels[state];
}

function StepCard({
  title,
  description,
  state
}: {
  title: string;
  description: string;
  state: StepState;
}) {
  return (
    <article className={`video-step-card ${state}`}>
      <span>{stepLabel(state)}</span>
      <h3>{title}</h3>
      <p>{description}</p>
    </article>
  );
}

export default async function LocalVideoJobPage({ params }: Props) {
  const { jobId } = await params;
  const job = await loadJob(jobId);

  const status = String(job.status ?? "");
  const outputPath = String(job.output_path ?? "");
  const error = String(job.error ?? "");
  const hasOutput = status === "completed" && Boolean(outputPath);
  const outputUrl = `${API_BASE_URL}/publishing/local-video/jobs/${jobId}/output`;

  return (
    <main className="page-shell video-workbench-page">
      <PageHeader
        eyebrow="Video Workbench"
        title={String(job.title ?? "ویدیوی لوکال")}
        lead={statusHelper(status)}
      >
        <div className="actions">
          <a href="/produce/video">بازگشت به ویدیوها</a>
          <a href="/produce/video/setup">تنظیم ابزارهای لوکال</a>
          <a href="/produce">تولید</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وضعیت" value={statusLabel(status)} helper={`شناسه: ${shortId(jobId)}`} />
        <StatCard label="موتور" value={engineLabel(job)} helper="قابل توسعه به Motion / AI / Cloud" />
        <StatCard label="مدت" value={`${String(job.duration_seconds ?? "")} ثانیه`} helper={`FPS: ${String(job.fps ?? "24")}`} />
        <StatCard label="نسبت تصویر" value={String(job.aspect_ratio ?? "16:9")} helper={String(job.project_name ?? "")} />
      </section>

      <section className="video-workbench-grid">
        <section className="panel video-preview-panel">
          <div className="panel-heading">
            <p className="eyebrow">خروجی</p>
            <h2>پیش‌نمایش ویدیو</h2>
          </div>

          {hasOutput ? (
            <video
              className="local-video-preview"
              controls
              preload="metadata"
              src={outputUrl}
            />
          ) : (
            <div className="empty-video-preview">
              <strong>هنوز ویدیوی خروجی ساخته نشده است.</strong>
              <p>بعد از اجرای موتور لوکال، پیش‌نمایش MP4 همین‌جا نمایش داده می‌شود.</p>
            </div>
          )}

          <div className="output-path-box">
            <span>مسیر خروجی</span>
            <code>{outputPath || "هنوز خروجی ساخته نشده"}</code>
          </div>

          <LocalVideoOutputActions
            apiBaseUrl={API_BASE_URL}
            jobId={jobId}
            outputPath={outputPath}
            hasOutput={hasOutput}
          />
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">اجرا</p>
            <h2>Dry-run یا موتور لوکال</h2>
          </div>

          <p className="muted-note">
            Dry-run فقط فایل ورودی را آماده می‌کند. اجرای موتور لوکال با تنظیم فعلی، خروجی MP4 ساده و سبک می‌سازد.
            در نسخه‌های بعدی، همین بخش به موتورهای Motion Graphics، ComfyUI و Cloud Video وصل می‌شود.
          </p>

          <RunLocalVideoJobAction apiBaseUrl={API_BASE_URL} jobId={jobId} />

          {error ? (
            <div className="video-error-box">
              <strong>خطای اجرا</strong>
              <p>{error}</p>
            </div>
          ) : null}
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">فرایند</p>
          <h2>مراحل تولید ویدیو</h2>
        </div>

        <div className="video-step-grid">
          <StepCard
            title="ثبت درخواست"
            description="عنوان، تصویر شروع، پرامپت، مدت و نسبت تصویر ثبت شده است."
            state={stepState(status, "request")}
          />
          <StepCard
            title="بهبود پرامپت"
            description="Qwen می‌تواند پرامپت حرکت را شفاف‌تر و مناسب‌تر کند."
            state={stepState(status, "prompt")}
          />
          <StepCard
            title="آماده‌سازی"
            description="ورودی موتور لوکال ساخته می‌شود و مسیر فایل‌ها بررسی می‌شود."
            state={stepState(status, "prepare")}
          />
          <StepCard
            title="رندر"
            description="موتور لوکال خروجی MP4 یا خروجی موتورهای آینده را می‌سازد."
            state={stepState(status, "render")}
          />
          <StepCard
            title="مرور خروجی"
            description="پیش‌نمایش، مسیر فایل، نسخه بعدی و انتشار بررسی می‌شود."
            state={stepState(status, "review")}
          />
        </div>
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">پرامپت</p>
            <h2>حرکت و حس ویدیو</h2>
          </div>

          <div className="generated-output">
            <p>{String(job.prompt ?? "بدون پرامپت")}</p>
          </div>

          {String(job.negative_prompt ?? "") ? (
            <>
              <h3 className="section-subtitle">پرامپت منفی</h3>
              <div className="generated-output secondary-output">
                <p>{String(job.negative_prompt ?? "")}</p>
              </div>
            </>
          ) : null}
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">مشخصات</p>
            <h2>فایل‌ها و تنظیمات</h2>
          </div>

          <dl className="detail-list">
            <div>
              <dt>تصویر شروع</dt>
              <dd>{String(job.start_image ?? "")}</dd>
            </div>
            <div>
              <dt>تصویر پایان</dt>
              <dd>{String(job.end_image ?? "") || ""}</dd>
            </div>
            <div>
              <dt>زمان ثبت</dt>
              <dd>{formatPersianDate(String(job.created_at ?? ""))}</dd>
            </div>
            <div>
              <dt>آخرین به‌روزرسانی</dt>
              <dd>{formatPersianDate(String(job.updated_at ?? ""))}</dd>
            </div>
          </dl>
        </section>
      </section>

      <section className="panel quiet-panel">
        <div className="panel-heading">
          <p className="eyebrow">موتورهای آینده</p>
          <h2>مسیر توسعه ویدیوهای پیچیده‌تر</h2>
        </div>

        <div className="video-engine-roadmap">
          <article>
            <h3>Motion Graphics Local</h3>
            <p>ساخت ویدیوی دوبعدی با کشیده‌شدن خطوط، حرکت لایه‌ها، تایپوگرافی متحرک و افکت‌های افتر افکت‌طور.</p>
          </article>
          <article>
            <h3>ComfyUI / Stable Diffusion</h3>
            <p>اتصال workflowهای تصویر و image-to-video در صورت آماده بودن موتور مناسب روی سیستم.</p>
          </article>
          <article>
            <h3>Cloud Video Connectors</h3>
            <p>اتصال اختیاری به سرویس‌های بیرونی مثل Veo، Opal یا ابزارهای مشابه، بدون قفل‌کردن هسته DAMA.</p>
          </article>
        </div>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش جزئیات فنی</summary>
          <pre className="json-block">{JSON.stringify(job, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Video workbench */",
    r'''
/* Video workbench */
.video-workbench-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr);
  gap: 1rem;
  align-items: start;
}

.video-preview-panel {
  display: grid;
  gap: 1rem;
}

.local-video-preview,
.empty-video-preview {
  width: 100%;
  min-height: 320px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 1.25rem;
  background: #0f172a;
  box-shadow: var(--shadow);
}

.local-video-preview {
  display: block;
  max-height: 560px;
}

.empty-video-preview {
  display: grid;
  place-items: center;
  padding: 2rem;
  text-align: center;
  color: white;
}

.empty-video-preview p {
  max-width: 36rem;
  margin: 0.6rem auto 0;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.9;
}

.output-path-box {
  display: grid;
  gap: 0.45rem;
  padding: 0.9rem 1rem;
  border: 1px dashed rgba(15, 23, 42, 0.18);
  border-radius: 1rem;
  background: rgba(248, 250, 252, 0.85);
}

.output-path-box span {
  color: var(--muted);
  font-size: 0.85rem;
  font-weight: 800;
}

.output-path-box code {
  overflow-wrap: anywhere;
  direction: ltr;
  text-align: left;
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
}

.local-video-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  align-items: center;
}

.local-video-actions button,
.local-video-actions a {
  display: inline-flex;
  min-height: 2.55rem;
  align-items: center;
  justify-content: center;
  padding: 0 0.95rem;
  border: 0;
  border-radius: 999px;
  background: var(--text);
  color: white;
  text-decoration: none;
  font-weight: 900;
  cursor: pointer;
}

.local-video-actions button:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.video-error-box {
  display: grid;
  gap: 0.4rem;
  margin-top: 1rem;
  padding: 0.9rem 1rem;
  border: 1px solid rgba(180, 35, 24, 0.28);
  border-radius: 1rem;
  background: rgba(254, 242, 242, 0.9);
  color: #7f1d1d;
}

.video-error-box p {
  margin: 0;
  overflow-wrap: anywhere;
  line-height: 1.8;
}

.video-step-grid,
.video-engine-roadmap {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.8rem;
}

.video-step-card,
.video-engine-roadmap article {
  min-height: 9rem;
  padding: 1rem;
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 1.1rem;
  background: rgba(255, 255, 255, 0.82);
}

.video-step-card span {
  display: inline-flex;
  margin-bottom: 0.55rem;
  padding: 0.22rem 0.55rem;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 900;
}

.video-step-card h3,
.video-engine-roadmap h3,
.section-subtitle {
  margin: 0 0 0.5rem;
}

.video-step-card p,
.video-engine-roadmap p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}

.video-step-card.done {
  border-color: rgba(22, 163, 74, 0.25);
  background: rgba(240, 253, 244, 0.9);
}

.video-step-card.active {
  border-color: rgba(37, 99, 235, 0.25);
  background: rgba(239, 246, 255, 0.92);
}

.video-step-card.failed {
  border-color: rgba(180, 35, 24, 0.28);
  background: rgba(254, 242, 242, 0.92);
}

.secondary-output {
  opacity: 0.88;
}

.video-engine-roadmap {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

@media (max-width: 1100px) {
  .video-workbench-grid,
  .video-step-grid,
  .video-engine-roadmap {
    grid-template-columns: 1fr;
  }
}
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-12 Completed",
    r'''
## Release Pack AI-12 Completed

Name:

Video Workbench Dashboard

Added files:

- frontend/src/components/local-video-output-actions.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/app/produce/video/[jobId]/page.tsx
- frontend/src/app/globals.css
- docs/project-status.md

Added behavior:

- local video output can be streamed from the backend
- dashboard can preview completed MP4 outputs
- dashboard shows output path and copy/open actions
- dashboard can request opening the output folder on the local machine
- video job detail page is now a production workbench
- process steps are visible: request, prompt, prepare, render, review
- future engines are framed: Motion Graphics, ComfyUI/Stable Diffusion, Cloud Video Connectors

Next recommended step:

Release Pack AI-13: Local Motion Graphics Engine

Goal:

- add a local 2D motion graphics renderer
- support line-drawing animation, pan/zoom, layer motion, animated text and simple After Effects-style compositions
- keep outputs in the same Video Workbench
    ''',
)

print("Release Pack AI-12 applied successfully.")
