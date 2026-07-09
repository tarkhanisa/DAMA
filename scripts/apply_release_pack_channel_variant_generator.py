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

    if "smoke_test_publishing_variants.py" in text:
        print("Skipped backend-check patch.")
        return

    if '"./backend/tests/smoke_test_publishing.py"' in text:
        text = text.replace(
            '"./backend/tests/smoke_test_publishing.py"',
            '"./backend/tests/smoke_test_publishing.py",\n    "./backend/tests/smoke_test_publishing_variants.py"',
            1,
        )
    elif '".\\backend\\tests\\smoke_test_publishing.py"' in text:
        text = text.replace(
            '".\\backend\\tests\\smoke_test_publishing.py"',
            '".\\backend\\tests\\smoke_test_publishing.py",\n    ".\\backend\\tests\\smoke_test_publishing_variants.py"',
            1,
        )
    else:
        text = text.rstrip() + r'''

$PublishingVariantSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_publishing_variants.py"
$PublishingVariantPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $PublishingVariantSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_publishing_variants.py..."
    & $PublishingVariantPython $PublishingVariantSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_publishing_variants.py"
    }
}
''' + "\n"

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


def patch_frontend_check() -> None:
    target = ROOT / "scripts/frontend-check.ps1"
    text = target.read_text(encoding="utf-8")

    required = [
        '".\\frontend\\src\\app\\publishing\\variants\\page.tsx",',
        '".\\frontend\\src\\components\\create-publishing-variants-form.tsx",',
    ]

    for line in required:
        if line not in text:
            marker = '".\\frontend\\src\\app\\publishing\\page.tsx",'
            if marker in text:
                text = text.replace(marker, marker + "\n    " + line, 1)
            else:
                marker = '".\\frontend\\src\\app\\generate\\page.tsx",'
                text = text.replace(marker, marker + "\n    " + line, 1)

    if "Publishing variants page does not include variant form." not in text:
        block = r'''
$PublishingVariantsPage = Read-TextFile ".\frontend\src\app\publishing\variants\page.tsx"
$PublishingVariantsForm = Read-TextFile ".\frontend\src\components\create-publishing-variants-form.tsx"

if ($PublishingVariantsPage -notmatch "CreatePublishingVariantsForm") {
    throw "Publishing variants page does not include variant form."
}

if ($PublishingVariantsForm -notmatch "/publishing/variants/plan") {
    throw "Publishing variants form does not call variant plan endpoint."
}
'''.strip()

        text = text.replace(
            'Write-Host "Frontend production readiness check passed."',
            block + '\n\nWrite-Host "Frontend production readiness check passed."'
        )

    target.write_text(text, encoding="utf-8")
    print("Patched scripts/frontend-check.ps1")


write_file(
    "backend/src/services/publishing_variant_service.py",
    r'''
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
import json
import re

from src.services.publishing_channel_service import get_channel


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
VARIANTS_PATH = DATA_DIR / "publishing_variants.json"


ALLOWED_VARIANT_STATUSES = {
    "draft",
    "ready_for_review",
    "approved",
    "rejected",
    "scheduled",
    "published",
    "failed",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not VARIANTS_PATH.exists():
        VARIANTS_PATH.write_text("[]\n", encoding="utf-8")


def read_variants() -> list[dict[str, Any]]:
    ensure_store()

    try:
        payload = json.loads(VARIANTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = []

    return payload if isinstance(payload, list) else []


def write_variants(variants: list[dict[str, Any]]) -> None:
    ensure_store()
    VARIANTS_PATH.write_text(
        json.dumps(variants, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_status(status: str | None) -> str:
    value = (status or "draft").strip().lower()

    if value not in ALLOWED_VARIANT_STATUSES:
        return "draft"

    return value


def clean_text(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def limit_text(text: str, max_chars: int) -> str:
    value = clean_text(text)

    if len(value) <= max_chars:
        return value

    return value[: max_chars - 1].rstrip() + ""


def paragraphize(text: str, max_paragraph_chars: int = 360) -> str:
    value = clean_text(text)
    chunks: list[str] = []

    for paragraph in value.split("\n"):
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        if len(paragraph) <= max_paragraph_chars:
            chunks.append(paragraph)
            continue

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        current = ""

        for sentence in sentences:
            candidate = (current + " " + sentence).strip()

            if len(candidate) > max_paragraph_chars and current:
                chunks.append(current)
                current = sentence
            else:
                current = candidate

        if current:
            chunks.append(current)

    return "\n\n".join(chunks)


def make_short_hook(title: str, body: str) -> str:
    title = clean_text(title)

    if title:
        return title

    first_line = clean_text(body).split("\n")[0]
    return limit_text(first_line, 80) if first_line else "محتوای تازه"


def make_variant_body(channel_type: str, title: str, body: str) -> tuple[str, str, list[str]]:
    source_title = make_short_hook(title, body)
    source_body = clean_text(body)

    notes: list[str] = []

    if channel_type == "wordpress":
        variant_title = source_title
        variant_body = f"{source_title}\n\n{paragraphize(source_body, 520)}"
        notes = [
            "مناسب پیشنویس وردپرس",
            "قابل استفاده برای توسعه بعدی SEO title و meta description",
            "در این مرحله انتشار واقعی انجام نمیشود",
        ]
        return variant_title, variant_body, notes

    if channel_type == "telegram":
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{paragraphize(source_body, 300)}",
            3500,
        )
        notes = [
            "پاراگرافها کوتاهتر شدهاند",
            "برای پیامرسان مناسبتر است",
            "لینک و CTA در مرحله بعد اضافه میشود",
        ]
        return variant_title, variant_body, notes

    if channel_type == "instagram":
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{paragraphize(source_body, 240)}\n\n#دامامدیا",
            1800,
        )
        notes = [
            "نسخه کپشن است نه مقاله کامل",
            "هشتگ پایه اضافه شده است",
            "تصویر/کاور در مرحله بعدی باید وصل شود",
        ]
        return variant_title, variant_body, notes

    if channel_type == "linkedin":
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{paragraphize(source_body, 420)}",
            2200,
        )
        notes = [
            "لحن برای پست حرفهای مناسبتر شده است",
            "جزئیات اجرایی و رسمی در مرحله AI enhancement بهتر میشود",
        ]
        return variant_title, variant_body, notes

    if channel_type == "whatsapp":
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{source_body}",
            700,
        )
        notes = [
            "نسخه کوتاه برای ارسال محدود یا پیام مستقیم",
            "برای ارسال انبوه باید قوانین WhatsApp Business بررسی شود",
        ]
        return variant_title, variant_body, notes

    if channel_type in {"bale", "eitaa"}:
        variant_title = source_title
        variant_body = limit_text(
            f"{source_title}\n\n{paragraphize(source_body, 300)}",
            2500,
        )
        notes = [
            "نسخه پیامرسان داخلی",
            "اتصال واقعی به API در مرحله بعد بررسی میشود",
        ]
        return variant_title, variant_body, notes

    variant_title = source_title
    variant_body = source_body
    notes = [
        "نسخه دستی برای بازبینی",
        "بدون انتشار خودکار",
    ]

    return variant_title, variant_body, notes


def list_variants(
    content_asset_id: str | None = None,
    channel_id: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    variants = read_variants()

    if content_asset_id:
        variants = [
            variant
            for variant in variants
            if variant.get("content_asset_id") == content_asset_id
        ]

    if channel_id:
        variants = [
            variant
            for variant in variants
            if variant.get("channel_id") == channel_id
        ]

    if status:
        variants = [
            variant
            for variant in variants
            if variant.get("status") == status
        ]

    return {
        "total": len(variants),
        "items": variants,
    }


def get_variant(variant_id: str) -> dict[str, Any] | None:
    for variant in read_variants():
        if variant.get("id") == variant_id:
            return variant

    return None


def create_variants_plan(payload: dict[str, Any]) -> dict[str, Any]:
    content_asset_id = str(payload.get("content_asset_id") or "").strip()
    source_title = clean_text(str(payload.get("source_title") or payload.get("title") or ""))
    source_body = clean_text(str(payload.get("source_body") or payload.get("body") or ""))
    channel_ids = payload.get("channel_ids")

    if not isinstance(channel_ids, list):
        channel_ids = []

    if not source_body:
        source_body = "متن منبع وارد نشده است. این نسخه فقط برای تست ساختار variant ساخته شده است."

    variants = read_variants()
    created: list[dict[str, Any]] = []
    now = utc_now()

    for raw_channel_id in channel_ids:
        channel_id = str(raw_channel_id or "").strip()
        channel = get_channel(channel_id)

        if not channel:
            continue

        channel_type = str(channel.get("channel_type") or "manual")
        variant_title, variant_body, notes = make_variant_body(
            channel_type=channel_type,
            title=source_title,
            body=source_body,
        )

        variant = {
            "id": str(uuid4()),
            "content_asset_id": content_asset_id,
            "channel_id": channel_id,
            "channel_name": channel.get("name", ""),
            "channel_type": channel_type,
            "source_title": source_title,
            "source_body": source_body,
            "variant_title": variant_title,
            "variant_body": variant_body,
            "status": "draft",
            "adaptation_mode": "rule_based",
            "adaptation_notes": notes,
            "created_at": now,
            "updated_at": now,
        }

        variants.insert(0, variant)
        created.append(variant)

    write_variants(variants)

    return {
        "created": len(created),
        "items": created,
    }


def update_variant_status(variant_id: str, status: str) -> dict[str, Any] | None:
    variants = read_variants()
    normalized_status = normalize_status(status)

    for index, variant in enumerate(variants):
        if variant.get("id") != variant_id:
            continue

        updated = dict(variant)
        updated["status"] = normalized_status
        updated["updated_at"] = utc_now()
        variants[index] = updated
        write_variants(variants)
        return updated

    return None
    ''',
)


write_file(
    "backend/src/api/publishing.py",
    r'''
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.services.publishing_channel_service import (
    create_channel,
    get_channel,
    list_channels,
    test_channel,
    update_channel,
)
from src.services.publishing_variant_service import (
    create_variants_plan,
    get_variant,
    list_variants,
    update_variant_status,
)


router = APIRouter(prefix="/publishing", tags=["publishing"])


@router.get("/channels")
def api_list_channels() -> dict[str, Any]:
    return list_channels()


@router.post("/channels")
def api_create_channel(payload: dict[str, Any]) -> dict[str, Any]:
    return create_channel(payload)


@router.get("/channels/{channel_id}")
def api_get_channel(channel_id: str) -> dict[str, Any]:
    channel = get_channel(channel_id)

    if not channel:
        raise HTTPException(status_code=404, detail="Publishing channel not found.")

    return channel


@router.patch("/channels/{channel_id}")
def api_update_channel(channel_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    channel = update_channel(channel_id, payload)

    if not channel:
        raise HTTPException(status_code=404, detail="Publishing channel not found.")

    return channel


@router.post("/channels/{channel_id}/test")
def api_test_channel(channel_id: str) -> dict[str, Any]:
    result = test_channel(channel_id)

    if not result:
        raise HTTPException(status_code=404, detail="Publishing channel not found.")

    return result


@router.get("/variants")
def api_list_variants(
    content_asset_id: str | None = Query(default=None),
    channel_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> dict[str, Any]:
    return list_variants(
        content_asset_id=content_asset_id,
        channel_id=channel_id,
        status=status,
    )


@router.post("/variants/plan")
def api_create_variants_plan(payload: dict[str, Any]) -> dict[str, Any]:
    return create_variants_plan(payload)


@router.get("/variants/{variant_id}")
def api_get_variant(variant_id: str) -> dict[str, Any]:
    variant = get_variant(variant_id)

    if not variant:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return variant


@router.patch("/variants/{variant_id}/status")
def api_update_variant_status(variant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    variant = update_variant_status(variant_id, str(payload.get("status") or "draft"))

    if not variant:
        raise HTTPException(status_code=404, detail="Publishing variant not found.")

    return variant
    ''',
)


write_file(
    "backend/tests/smoke_test_publishing_variants.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Variant WordPress",
            "channel_type": "wordpress",
            "target_url": "https://example.com",
            "notes": "Variant smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    plan_response = client.post(
        "/publishing/variants/plan",
        json={
            "content_asset_id": "smoke-content-asset",
            "source_title": "عنوان تست انتشار",
            "source_body": "این یک متن مادر برای تست نسخهسازی کانالهای انتشار است. متن باید برای کانالهای مختلف قابل تبدیل باشد.",
            "channel_ids": [channel["id"]],
        },
    )
    assert plan_response.status_code == 200, plan_response.text

    plan = plan_response.json()
    assert plan["created"] == 1
    assert len(plan["items"]) == 1

    variant = plan["items"][0]
    assert variant["channel_type"] == "wordpress"
    assert variant["variant_body"]

    list_response = client.get("/publishing/variants")
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] >= 1

    status_response = client.patch(
        f"/publishing/variants/{variant['id']}/status",
        json={"status": "ready_for_review"},
    )
    assert status_response.status_code == 200, status_response.text
    assert status_response.json()["status"] == "ready_for_review"

    print("Publishing variants smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


write_file(
    "frontend/src/components/create-publishing-variants-form.tsx",
    r'''
"use client";

import { FormEvent, useMemo, useState } from "react";

type ContentAsset = {
  id: string;
  title: string;
  body: string;
  content_type?: string;
  status?: string;
};

type PublishingChannel = {
  id: string;
  name: string;
  channel_type: string;
  status: string;
};

type PublishingVariant = {
  id: string;
  content_asset_id: string;
  channel_id: string;
  channel_name: string;
  channel_type: string;
  variant_title: string;
  variant_body: string;
  status: string;
  adaptation_mode: string;
  adaptation_notes: string[];
};

type CreatePublishingVariantsFormProps = {
  apiBaseUrl: string;
  assets: ContentAsset[];
  channels: PublishingChannel[];
};

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

export function CreatePublishingVariantsForm({
  apiBaseUrl,
  assets,
  channels
}: CreatePublishingVariantsFormProps) {
  const [assetId, setAssetId] = useState(assets[0]?.id ?? "");
  const [selectedChannelIds, setSelectedChannelIds] = useState<string[]>(
    channels.slice(0, 3).map((channel) => channel.id)
  );
  const [isCreating, setIsCreating] = useState(false);
  const [message, setMessage] = useState("");
  const [createdVariants, setCreatedVariants] = useState<PublishingVariant[]>([]);

  const selectedAsset = useMemo(
    () => assets.find((asset) => asset.id === assetId),
    [assetId, assets]
  );

  function toggleChannel(channelId: string) {
    setSelectedChannelIds((current) =>
      current.includes(channelId)
        ? current.filter((item) => item !== channelId)
        : [...current, channelId]
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedAsset) {
      setMessage("اول یک محتوای مادر انتخاب کن.");
      return;
    }

    if (selectedChannelIds.length === 0) {
      setMessage("حداقل یک کانال انتشار انتخاب کن.");
      return;
    }

    setIsCreating(true);
    setMessage("");
    setCreatedVariants([]);

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/variants/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          content_asset_id: selectedAsset.id,
          source_title: selectedAsset.title,
          source_body: selectedAsset.body,
          channel_ids: selectedChannelIds
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(`خطا در ساخت نسخهها: HTTP ${response.status}`);
        return;
      }

      setCreatedVariants(Array.isArray(payload.items) ? payload.items : []);
      setMessage(`${payload.created ?? 0} نسخه کانالی ساخته شد.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "خطای ناشناخته");
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <div className="generation-grid">
      <form className="panel generation-form" onSubmit={handleSubmit}>
        <div className="panel-heading">
          <p className="eyebrow">نسخهسازی کانالی</p>
          <h2>محتوا را برای کانالها آماده کن</h2>
        </div>

        <label>
          محتوای مادر
          <select value={assetId} onChange={(event) => setAssetId(event.target.value)}>
            {assets.length > 0 ? (
              assets.map((asset) => (
                <option key={asset.id} value={asset.id}>
                  {asset.title}
                </option>
              ))
            ) : (
              <option value="">محتوایی پیدا نشد</option>
            )}
          </select>
        </label>

        <div className="channel-checkbox-list">
          <strong>کانالهای مقصد</strong>

          {channels.length > 0 ? (
            channels.map((channel) => (
              <label key={channel.id} className="checkbox-row">
                <input
                  type="checkbox"
                  checked={selectedChannelIds.includes(channel.id)}
                  onChange={() => toggleChannel(channel.id)}
                />
                <span>
                  {channel.name}  {channelTypeLabel(channel.channel_type)}
                </span>
              </label>
            ))
          ) : (
            <p className="muted-note">
              هنوز کانالی تعریف نشده. اول از صفحه انتشار کانال بساز.
            </p>
          )}
        </div>

        <p className="muted-note">
          این مرحله هنوز منتشر نمیکند فقط نسخههای مخصوص هر کانال را برای بازبینی میسازد.
        </p>

        {message ? <p className="form-message">{message}</p> : null}

        <button type="submit" disabled={isCreating || assets.length === 0 || channels.length === 0}>
          {isCreating ? "در حال ساخت نسخهها..." : "ساخت نسخههای کانالی"}
        </button>
      </form>

      <section className="panel generation-output">
        <div className="panel-heading">
          <p className="eyebrow">پیشنمایش</p>
          <h2>نسخههای ساختهشده</h2>
        </div>

        {createdVariants.length > 0 ? (
          <div className="variant-preview-list">
            {createdVariants.map((variant) => (
              <article key={variant.id} className="variant-preview-card">
                <div className="variant-preview-header">
                  <strong>
                    {variant.channel_name}  {channelTypeLabel(variant.channel_type)}
                  </strong>
                  <span className={`status-badge status-${variant.status}`}>
                    {variant.status}
                  </span>
                </div>

                <h3>{variant.variant_title}</h3>
                <pre className="generated-output">{variant.variant_body}</pre>

                {variant.adaptation_notes?.length > 0 ? (
                  <ul className="note-list">
                    {variant.adaptation_notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ))}
          </div>
        ) : (
          <div className="quality-help">
            <h3>این مرحله چه میکند</h3>
            <p>
              یک محتوای مادر را انتخاب میکنی و سیستم برای هر کانال یک نسخه جدا میسازد.
            </p>
            <ul>
              <li>وردپرس: متن کاملتر و مناسب پیشنویس سایت</li>
              <li>تلگرام: پاراگرافهای کوتاهتر</li>
              <li>اینستاگرام: کپشن کوتاهتر</li>
              <li>لینکدین: نسخه رسمیتر</li>
              <li>واتساپ: نسخه کوتاه و مستقیم</li>
            </ul>
          </div>
        )}
      </section>
    </div>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/variants/page.tsx",
    r'''
import { CreatePublishingVariantsForm } from "../../../components/create-publishing-variants-form";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type ContentAsset = {
  id: string;
  title: string;
  body: string;
  content_type?: string;
  status?: string;
};

type PublishingChannel = {
  id: string;
  name: string;
  channel_type: string;
  status: string;
};

type PublishingVariant = {
  id: string;
  content_asset_id: string;
  channel_id: string;
  channel_name: string;
  channel_type: string;
  variant_title: string;
  variant_body: string;
  status: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

async function getJson(endpoint: string): Promise<unknown> {
  const response = await fetch(endpoint, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

function normalizeAssets(payload: unknown): ContentAsset[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload)
    ? payload
    : asArray(record.items ?? record.assets ?? record.content_assets ?? record.data);

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        title: String(value.title ?? value.name ?? "محتوای بدون عنوان"),
        body: String(value.body ?? value.content ?? value.response ?? value.text ?? ""),
        content_type:
          typeof value.content_type === "string" ? value.content_type : undefined,
        status: typeof value.status === "string" ? value.status : undefined
      };
    })
    .filter((asset) => asset.id && asset.body);
}

function normalizeChannels(payload: unknown): PublishingChannel[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload) ? payload : asArray(record.items);

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        name: String(value.name ?? "کانال بدون نام"),
        channel_type: String(value.channel_type ?? "manual"),
        status: String(value.status ?? "not_configured")
      };
    })
    .filter((channel) => channel.id);
}

function normalizeVariants(payload: unknown): PublishingVariant[] {
  const record = asRecord(payload);
  const source = Array.isArray(payload) ? payload : asArray(record.items);

  return source
    .map((item) => {
      const value = asRecord(item);

      return {
        id: String(value.id ?? ""),
        content_asset_id: String(value.content_asset_id ?? ""),
        channel_id: String(value.channel_id ?? ""),
        channel_name: String(value.channel_name ?? ""),
        channel_type: String(value.channel_type ?? "manual"),
        variant_title: String(value.variant_title ?? ""),
        variant_body: String(value.variant_body ?? ""),
        status: String(value.status ?? "draft")
      };
    })
    .filter((variant) => variant.id);
}

async function loadAssets(): Promise<ContentAsset[]> {
  try {
    return normalizeAssets(await getJson(`${API_BASE_URL}/content-assets`));
  } catch {
    return [];
  }
}

async function loadChannels(): Promise<PublishingChannel[]> {
  try {
    return normalizeChannels(await getJson(`${API_BASE_URL}/publishing/channels`));
  } catch {
    return [];
  }
}

async function loadVariants(): Promise<PublishingVariant[]> {
  try {
    return normalizeVariants(await getJson(`${API_BASE_URL}/publishing/variants`));
  } catch {
    return [];
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

export default async function PublishingVariantsPage() {
  const [assets, channels, variants] = await Promise.all([
    loadAssets(),
    loadChannels(),
    loadVariants()
  ]);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="نسخهسازی انتشار"
        title="تبدیل محتوای مادر به نسخههای کانالی"
        lead="یک محتوای ذخیرهشده را انتخاب کن و برای کانالهای مختلف نسخه مناسب همان کانال بساز."
      >
        <div className="actions">
          <a href="/publishing">کانالهای انتشار</a>
          <a href="/generate">تولید محتوا</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="محتواهای قابل استفاده" value={assets.length} helper="Content Assets دارای متن" />
        <StatCard label="کانالها" value={channels.length} helper="مقصدهای تعریفشده" />
        <StatCard label="نسخههای ساختهشده" value={variants.length} helper="Publishing Variants" />
        <StatCard label="انتشار واقعی" value="بعدا" helper="فعلا فقط پیشنویس کانالی" />
      </section>

      <CreatePublishingVariantsForm
        apiBaseUrl={API_BASE_URL}
        assets={assets}
        channels={channels}
      />

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">آرشیو نسخهها</p>
          <h2>آخرین نسخههای کانالی</h2>
        </div>

        <div className="responsive-table">
          <table>
            <thead>
              <tr>
                <th>عنوان</th>
                <th>کانال</th>
                <th>نوع</th>
                <th>وضعیت</th>
              </tr>
            </thead>
            <tbody>
              {variants.length > 0 ? (
                variants.slice(0, 20).map((variant) => (
                  <tr key={variant.id}>
                    <td>{variant.variant_title}</td>
                    <td>{variant.channel_name}</td>
                    <td>{channelTypeLabel(variant.channel_type)}</td>
                    <td>
                      <span className={`status-badge status-${variant.status}`}>
                        {variant.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4}>هنوز نسخهای ساخته نشده است.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/components/app-nav.tsx",
    r'''
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "داشبورد" },
  { href: "/projects", label: "پروژهها" },
  { href: "/content-assets", label: "محتواها" },
  { href: "/generate", label: "تولید محتوا" },
  { href: "/publishing", label: "انتشار" },
  { href: "/publishing/variants", label: "نسخهسازی" },
  { href: "/workflows", label: "جریان کار" },
  { href: "/search", label: "جستجو" },
  { href: "/runtime", label: "سلامت سیستم" },
  { href: "/operations", label: "عملیات" },
  { href: "/exports", label: "خروجیها" },
  { href: "/maintenance", label: "نگهداری" }
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="app-nav" aria-label="ناوبری دامامدیا">
      {navItems.map((item) => {
        const isActive =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={isActive ? "active" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Publishing variants */",
    r'''
/* Publishing variants */
.channel-checkbox-list {
  display: grid;
  gap: 0.75rem;
  border: 1px solid var(--border);
  border-radius: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.52);
}

.variant-preview-list {
  display: grid;
  gap: 1rem;
}

.variant-preview-card {
  display: grid;
  gap: 0.75rem;
  border: 1px solid var(--border);
  border-radius: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.58);
}

.variant-preview-header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
}

.variant-preview-card h3 {
  margin: 0;
}
    ''',
)


append_once(
    "docs/publishing-foundation.md",
    "## Channel Variants",
    r'''
## Channel Variants

Release Pack X adds publishing variants.

A single content asset can now be adapted into channel-specific variants.

Endpoint:

    POST /publishing/variants/plan

Input:

- content_asset_id
- source_title
- source_body
- channel_ids

Output:

- one draft variant per selected channel

Current adaptation mode:

    rule_based

Future adaptation mode:

    ai_enhanced

No real publishing happens in this step.
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack X Completed",
    r'''
## Release Pack X Completed

Name:

Channel Variant Generator

Added files:

- backend/src/services/publishing_variant_service.py
- backend/tests/smoke_test_publishing_variants.py
- frontend/src/app/publishing/variants/page.tsx
- frontend/src/components/create-publishing-variants-form.tsx

Updated files:

- backend/src/api/publishing.py
- frontend/src/components/app-nav.tsx
- frontend/src/app/globals.css
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- docs/publishing-foundation.md
- docs/project-status.md

Added behavior:

- list publishing variants
- create channel-specific variant plan
- update variant status
- Persian variant-generation UI
- one content asset to many channel variants
- no real publishing yet

Next recommended Release Pack:

Release Pack Y: AI Variant Enhancer

Suggested scope:

- use local AI to improve each channel variant
- channel-specific prompt templates
- WordPress SEO draft fields
- Telegram message polish
- Instagram caption polish
- LinkedIn professional rewrite
- still no automatic publishing
    ''',
)


patch_backend_check()
patch_frontend_check()

print("Release Pack X applied successfully.")
