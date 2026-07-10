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


def patch_backend_check() -> None:
    target = ROOT / "scripts/backend-check.ps1"
    text = target.read_text(encoding="utf-8")

    if "smoke_test_publishing_review.py" in text:
        print("Skipped backend-check patch.")
        return

    if '"./backend/tests/smoke_test_publishing_ai_enhancer.py"' in text:
        text = text.replace(
            '"./backend/tests/smoke_test_publishing_ai_enhancer.py"',
            '"./backend/tests/smoke_test_publishing_ai_enhancer.py",\n    "./backend/tests/smoke_test_publishing_review.py"',
            1,
        )
    elif '".\\backend\\tests\\smoke_test_publishing_ai_enhancer.py"' in text:
        text = text.replace(
            '".\\backend\\tests\\smoke_test_publishing_ai_enhancer.py"',
            '".\\backend\\tests\\smoke_test_publishing_ai_enhancer.py",\n    ".\\backend\\tests\\smoke_test_publishing_review.py"',
            1,
        )
    else:
        text = text.rstrip() + r'''

$PublishingReviewSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_publishing_review.py"
$PublishingReviewPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $PublishingReviewSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_publishing_review.py..."
    & $PublishingReviewPython $PublishingReviewSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_publishing_review.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required = [
        '".\\frontend\\src\\app\\publishing\\variants\\[variantId]\\page.tsx",',
        '".\\frontend\\src\\components\\review-publishing-variant-form.tsx",',
    ]

    for line in required:
        if line not in text:
            marker = '".\\frontend\\src\\app\\publishing\\variants\\page.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)

    if "Publishing variant review form is missing review endpoint." not in text:
        block = r'''
$PublishingVariantDetailPage = Read-TextFile ".\frontend\src\app\publishing\variants\[variantId]\page.tsx"
$PublishingVariantReviewForm = Read-TextFile ".\frontend\src\components\review-publishing-variant-form.tsx"

if ($PublishingVariantDetailPage -notmatch "ReviewPublishingVariantForm") {
    throw "Publishing variant detail page does not include review form."
}

if ($PublishingVariantReviewForm -notmatch "/review") {
    throw "Publishing variant review form is missing review endpoint."
}

if ($PublishingVariantReviewForm -notmatch "approved") {
    throw "Publishing variant review form is missing approved status."
}
'''.strip()

        text = text.replace(
            'Write-Host "Frontend production readiness check passed."',
            block + '\n\nWrite-Host "Frontend production readiness check passed."'
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


# Patch backend variant service with review workflow.
service_path = ROOT / "backend/src/services/publishing_variant_service.py"
service = service_path.read_text(encoding="utf-8")

if '"ready_for_publish"' not in service:
    service = service.replace(
        '"approved",',
        '"approved",\n    "ready_for_publish",',
        1,
    )

if "def review_variant(" not in service:
    service += r'''


def review_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    variants = read_variants()
    status = normalize_status(str(payload.get("status") or "ready_for_review"))

    for index, variant in enumerate(variants):
        if variant.get("id") != variant_id:
            continue

        updated = dict(variant)

        if "variant_title" in payload:
            updated["variant_title"] = clean_text(str(payload.get("variant_title") or ""))

        if "variant_body" in payload:
            updated["variant_body"] = clean_text(str(payload.get("variant_body") or ""))

        updated["status"] = status
        updated["review_notes"] = clean_text(str(payload.get("review_notes") or ""))
        updated["reviewed_by"] = clean_text(str(payload.get("reviewed_by") or "operator"))
        updated["reviewed_at"] = utc_now()
        updated["updated_at"] = utc_now()

        history = updated.get("review_history")
        if not isinstance(history, list):
            history = []

        history.append(
            {
                "status": status,
                "review_notes": updated["review_notes"],
                "reviewed_by": updated["reviewed_by"],
                "reviewed_at": updated["reviewed_at"],
            }
        )

        updated["review_history"] = history

        variants[index] = updated
        write_variants(variants)

        return updated

    return None
'''

service_path.write_text(service.strip() + "\n", encoding="utf-8")
print("Patched publishing_variant_service.py")


# Patch publishing API.
api_path = ROOT / "backend/src/api/publishing.py"
api = api_path.read_text(encoding="utf-8")

if "review_variant" not in api:
    api = api.replace(
        "update_variant_status,",
        "update_variant_status,\n    review_variant,",
        1,
    )

if '@router.patch("/variants/{variant_id}/review")' not in api:
    api += r'''


@router.patch("/variants/{variant_id}/review")
def api_review_variant(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    variant = review_variant(variant_id, payload)

    if not variant:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return variant
'''

api_path.write_text(api.strip() + "\n", encoding="utf-8")
print("Patched backend/src/api/publishing.py")


write_file(
    "backend/tests/smoke_test_publishing_review.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Review WordPress",
            "channel_type": "wordpress",
            "target_url": "https://example.com",
            "notes": "Review smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-review-content-asset",
            "source_title": "تست بازبینی انتشار",
            "source_body": "این متن مادر برای تست چرخه بازبینی نسخه انتشار ساخته شده است.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text
    variant = plan_response.json()["items"][0]

    review_response = client.patch(
        f"/publishing/variants/{variant['id']}/review",
        json={
            "status": "approved",
            "variant_title": "عنوان تأییدشده",
            "variant_body": "متن تأییدشده برای انتشار در مرحله بعد.",
            "review_notes": "بازبینی smoke test انجام شد.",
            "reviewed_by": "smoke-test",
        },
    )
    assert review_response.status_code == 200, review_response.text

    reviewed = review_response.json()
    assert reviewed["status"] == "approved"
    assert reviewed["variant_title"] == "عنوان تأییدشده"
    assert reviewed["review_notes"]
    assert isinstance(reviewed["review_history"], list)

    print("Publishing review smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "frontend/src/components/review-publishing-variant-form.tsx",
    r'''
"use client";

import { FormEvent, useState } from "react";

type ReviewPublishingVariantFormProps = {
  apiBaseUrl: string;
  variantId: string;
  initialTitle: string;
  initialBody: string;
  initialStatus: string;
  initialNotes?: string;
};

export function ReviewPublishingVariantForm({
  apiBaseUrl,
  variantId,
  initialTitle,
  initialBody,
  initialStatus,
  initialNotes = ""
}: ReviewPublishingVariantFormProps) {
  const [variantTitle, setVariantTitle] = useState(initialTitle);
  const [variantBody, setVariantBody] = useState(initialBody);
  const [status, setStatus] = useState(initialStatus || "ready_for_review");
  const [reviewNotes, setReviewNotes] = useState(initialNotes);
  const [reviewedBy, setReviewedBy] = useState("اپراتور دامامدیا");
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");

    try {
      const response = await fetch(
        `${apiBaseUrl}/publishing/variants/${variantId}/review`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            variant_title: variantTitle,
            variant_body: variantBody,
            status,
            review_notes: reviewNotes,
            reviewed_by: reviewedBy
          })
        }
      );

      if (!response.ok) {
        setMessage(`خطا در ثبت بازبینی: HTTP ${response.status}`);
        return;
      }

      setMessage("بازبینی ذخیره شد. صفحه را refresh کن تا وضعیت جدید را ببینی.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">بازبینی انسانی</p>
        <h2>نسخه نهایی این کانال را تأیید یا رد کن</h2>
      </div>

      <label>
        عنوان نسخه
        <input
          value={variantTitle}
          onChange={(event) => setVariantTitle(event.target.value)}
        />
      </label>

      <label>
        متن نسخه
        <textarea
          value={variantBody}
          onChange={(event) => setVariantBody(event.target.value)}
          rows={14}
        />
      </label>

      <label>
        وضعیت بازبینی
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="draft">پیشنویس</option>
          <option value="ready_for_review">آماده بازبینی</option>
          <option value="approved">تأیید شده</option>
          <option value="ready_for_publish">آماده انتشار</option>
          <option value="rejected">رد شده</option>
        </select>
      </label>

      <label>
        بازبین
        <input
          value={reviewedBy}
          onChange={(event) => setReviewedBy(event.target.value)}
        />
      </label>

      <label>
        یادداشت بازبینی
        <textarea
          value={reviewNotes}
          onChange={(event) => setReviewNotes(event.target.value)}
          rows={4}
          placeholder="مثلا متن مناسب است اما قبل از انتشار نیاز به تصویر دارد."
        />
      </label>

      <p className="muted-note">
        هنوز انتشار واقعی انجام نمیشود. وضعیت آماده انتشار فقط برای مرحله بعدی صف انتشار استفاده میشود.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving}>
        {isSaving ? "در حال ذخیره..." : "ذخیره بازبینی"}
      </button>
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/variants/[variantId]/page.tsx",
    r'''
import { ErrorPanel } from "../../../../components/error-panel";
import { PageHeader } from "../../../../components/page-header";
import { ReviewPublishingVariantForm } from "../../../../components/review-publishing-variant-form";
import { StatCard } from "../../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type VariantDetailPageProps = {
  params: Promise<{
    variantId: string;
  }>;
};

type PublishingVariant = {
  id: string;
  content_asset_id: string;
  channel_id: string;
  channel_name: string;
  channel_type: string;
  source_title: string;
  source_body: string;
  variant_title: string;
  variant_body: string;
  status: string;
  adaptation_mode?: string;
  adaptation_notes?: string[];
  review_notes?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_history?: Array<Record<string, string>>;
};

async function loadVariant(variantId: string): Promise<PublishingVariant | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/publishing/variants/${variantId}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return null;
    }

    return (await response.json()) as PublishingVariant;
  } catch {
    return null;
  }
}

function channelTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    wordpress: "وردپرس",
    telegram: "تلگرام",
    instagram: "اینستاگرام",
    linkedin: "لینکدین",
    whatsapp: "واتساپ",
    bale: "بله",
    eitaa: "ایتا",
    manual: "دستی"
  };

  return labels[type] ?? type;
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "پیشنویس",
    ready_for_review: "آماده بازبینی",
    approved: "تأیید شده",
    ready_for_publish: "آماده انتشار",
    rejected: "رد شده",
    scheduled: "زمانبندیشده",
    published: "منتشرشده",
    failed: "خطادار"
  };

  return labels[status] ?? status;
}

export default async function PublishingVariantDetailPage({
  params
}: VariantDetailPageProps) {
  const { variantId } = await params;
  const variant = await loadVariant(variantId);

  if (!variant) {
    return (
      <main className="page-shell">
        <ErrorPanel
          eyebrow="نسخه انتشار"
          title="نسخه پیدا نشد"
          message="این نسخه کانالی در بکاند پیدا نشد."
        />
      </main>
    );
  }

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="بازبینی نسخه انتشار"
        title={variant.variant_title || "نسخه بدون عنوان"}
        lead="اینجا متن مخصوص این کانال را با متن مادر مقایسه میکنی و وضعیت بازبینی را ثبت میکنی."
      >
        <div className="actions">
          <a href="/publishing/variants">بازگشت به نسخهسازی</a>
          <a href="/publishing">کانالها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="کانال" value={variant.channel_name || ""} helper={channelTypeLabel(variant.channel_type)} />
        <StatCard label="وضعیت" value={statusLabel(variant.status)} helper="وضعیت بازبینی" />
        <StatCard label="روش آمادهسازی" value={variant.adaptation_mode || "rule_based"} helper="rule-based / AI / dry-run" />
        <StatCard label="بازبین" value={variant.reviewed_by || ""} helper={variant.reviewed_at || "هنوز بازبینی نشده"} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">متن مادر</p>
            <h2>{variant.source_title || "محتوای اصلی"}</h2>
          </div>

          <pre className="generated-output">{variant.source_body || "متن مادر ثبت نشده است."}</pre>
        </section>

        <ReviewPublishingVariantForm
          apiBaseUrl={API_BASE_URL}
          variantId={variant.id}
          initialTitle={variant.variant_title}
          initialBody={variant.variant_body}
          initialStatus={variant.status}
          initialNotes={variant.review_notes}
        />
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">یادداشتها</p>
          <h2>توضیحات آمادهسازی و بازبینی</h2>
        </div>

        <div className="two-column">
          <div>
            <h3>یادداشتهای آمادهسازی</h3>
            {variant.adaptation_notes?.length ? (
              <ul className="note-list">
                {variant.adaptation_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : (
              <p className="muted-note">یادداشتی ثبت نشده است.</p>
            )}
          </div>

          <div>
            <h3>تاریخچه بازبینی</h3>
            {variant.review_history?.length ? (
              <ul className="note-list">
                {variant.review_history.map((item, index) => (
                  <li key={`${item.reviewed_at}-${index}`}>
                    {statusLabel(item.status ?? "")}  {item.reviewed_by ?? "بازبین"}  {item.reviewed_at ?? ""}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted-note">هنوز بازبینی ثبت نشده است.</p>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
    ''',
)


# Patch variants listing to link to detail page.
variants_page = ROOT / "frontend/src/app/publishing/variants/page.tsx"
page = variants_page.read_text(encoding="utf-8")

if "بازبینی</a>" not in page:
    page = page.replace(
        "<th>وضعیت</th>",
        "<th>وضعیت</th>\n                <th>بازبینی</th>",
        1,
    )
    page = page.replace(
        """<td>
                      <span className={`status-badge status-${variant.status}`}>
                        {variant.status}
                      </span>
                    </td>""",
        """<td>
                      <span className={`status-badge status-${variant.status}`}>
                        {variant.status}
                      </span>
                    </td>
                    <td>
                      <a href={`/publishing/variants/${variant.id}`}>بازبینی</a>
                    </td>""",
        1,
    )
    page = page.replace(
        '<td colSpan={5}>هنوز نسخهای ساخته نشده است.</td>',
        '<td colSpan={6}>هنوز نسخهای ساخته نشده است.</td>',
        1,
    )
    page = page.replace(
        '<td colSpan={4}>هنوز نسخهای ساخته نشده است.</td>',
        '<td colSpan={5}>هنوز نسخهای ساخته نشده است.</td>',
        1,
    )

variants_page.write_text(page, encoding="utf-8")
print("Patched variants list page with review link.")


append_once(
    "docs/publishing-foundation.md",
    "## Publishing Review Workflow",
    r'''
## Publishing Review Workflow

Release Pack Z adds human review and approval for publishing variants.

Endpoint:

    PATCH /publishing/variants/{variant_id}/review

Review statuses:

- draft
- ready_for_review
- approved
- ready_for_publish
- rejected

The review workflow allows the operator to:

- compare source content with channel variant
- edit variant title
- edit variant body
- write review notes
- approve or reject a variant
- mark a variant as ready for publish

This still does not perform real publishing.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack Z Completed",
    r'''
## Release Pack Z Completed

Name:

Publishing Review + Approval Workflow

Added files:

- backend/tests/smoke_test_publishing_review.py
- frontend/src/app/publishing/variants/[variantId]/page.tsx
- frontend/src/components/review-publishing-variant-form.tsx

Updated files:

- backend/src/services/publishing_variant_service.py
- backend/src/api/publishing.py
- frontend/src/app/publishing/variants/page.tsx
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- review publishing variant endpoint
- variant detail page
- compare source vs channel variant
- edit variant title/body
- approve/reject variant
- ready_for_publish status
- review notes
- review history

Next recommended Release Pack:

Release Pack AA: WordPress Draft Connector

Suggested scope:

- WordPress channel configuration shape
- no secret in database
- manual environment-based application password support
- create draft post from approved variant
- store publish attempt
- no automatic publish yet
    ''',
)


patch_backend_check()
patch_frontend_check()

print("Release Pack Z applied successfully.")
