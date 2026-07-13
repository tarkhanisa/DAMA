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


write_file(
    "backend/src/services/media_campaign_service.py",
    r'''
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
import json


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"
CAMPAIGNS_PATH = DATA_DIR / "media_campaigns.json"


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


ALLOWED_CAMPAIGN_STATUSES = {
    "draft",
    "ready",
    "variant_planned",
    "queued",
    "published",
    "archived",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not CAMPAIGNS_PATH.exists():
        CAMPAIGNS_PATH.write_text("[]\n", encoding="utf-8")


def read_campaigns() -> list[dict[str, Any]]:
    ensure_store()

    try:
        payload = json.loads(CAMPAIGNS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = []

    return payload if isinstance(payload, list) else []


def write_campaigns(items: list[dict[str, Any]]) -> None:
    ensure_store()
    CAMPAIGNS_PATH.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def infer_media_type(value: str, explicit_type: str = "") -> str:
    media_type = explicit_type.strip().lower()

    if media_type in {"image", "video", "document", "other"}:
        return media_type

    suffix = Path(value.split("?")[0]).suffix.lower()

    if suffix in IMAGE_EXTENSIONS:
        return "image"

    if suffix in VIDEO_EXTENSIONS:
        return "video"

    return "other"


def normalize_media_item(item: Any) -> dict[str, Any] | None:
    if isinstance(item, str):
        value = item.strip()
        explicit_type = ""
        caption = ""
        alt = ""
    elif isinstance(item, dict):
        value = str(item.get("url") or item.get("path") or item.get("source") or "").strip()
        explicit_type = str(item.get("type") or "").strip()
        caption = str(item.get("caption") or "").strip()
        alt = str(item.get("alt") or "").strip()
    else:
        return None

    if not value:
        return None

    source_kind = "url" if value.startswith(("http://", "https://")) else "local_path"

    return {
        "id": str(uuid4()),
        "type": infer_media_type(value, explicit_type),
        "source": value,
        "source_kind": source_kind,
        "caption": caption,
        "alt": alt,
        "status": "attached",
    }


def normalize_media_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    source = payload.get("media_items")

    if not isinstance(source, list):
        source = []

    media_items = [
        normalized
        for item in source
        if (normalized := normalize_media_item(item)) is not None
    ]

    media_urls = payload.get("media_urls")

    if isinstance(media_urls, str):
        media_urls = [line.strip() for line in media_urls.splitlines() if line.strip()]

    if isinstance(media_urls, list):
        for item in media_urls:
            normalized = normalize_media_item(item)
            if normalized:
                media_items.append(normalized)

    return media_items


def normalize_channel_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    channel_ids: list[str] = []

    for item in value:
        text = str(item).strip()

        if text and text not in channel_ids:
            channel_ids.append(text)

    return channel_ids


def campaign_preview_text(source_body: str) -> str:
    text = " ".join(source_body.split())

    if len(text) <= 180:
        return text

    return text[:177] + "..."


def list_media_campaigns(
    status: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    items = read_campaigns()

    if status:
        items = [item for item in items if item.get("status") == status]

    if project_id:
        items = [item for item in items if item.get("project_id") == project_id]

    return {
        "total": len(items),
        "items": items,
    }


def get_media_campaign(campaign_id: str) -> dict[str, Any] | None:
    for item in read_campaigns():
        if item.get("id") == campaign_id:
            return item

    return None


def create_media_campaign(payload: dict[str, Any]) -> dict[str, Any]:
    now = utc_now()

    source_title = str(payload.get("source_title") or payload.get("title") or "").strip()
    source_body = str(payload.get("source_body") or payload.get("body") or "").strip()

    if not source_title:
        source_title = "کمپین بدون عنوان"

    campaign = {
        "id": str(uuid4()),
        "project_id": str(payload.get("project_id") or "").strip(),
        "project_name": str(payload.get("project_name") or "").strip(),
        "source_title": source_title,
        "source_body": source_body,
        "preview": campaign_preview_text(source_body),
        "campaign_goal": str(payload.get("campaign_goal") or "").strip(),
        "language": str(payload.get("language") or "fa").strip() or "fa",
        "status": "draft",
        "channel_ids": normalize_channel_ids(payload.get("channel_ids")),
        "media_items": normalize_media_items(payload),
        "notes": str(payload.get("notes") or "").strip(),
        "created_at": now,
        "updated_at": now,
        "history": [
            {
                "status": "draft",
                "at": now,
                "message": "Media campaign created.",
            }
        ],
    }

    items = read_campaigns()
    items.insert(0, campaign)
    write_campaigns(items)

    return campaign


def update_media_campaign(campaign_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    items = read_campaigns()

    for index, item in enumerate(items):
        if item.get("id") != campaign_id:
            continue

        updated = dict(item)

        for field in [
            "project_id",
            "project_name",
            "source_title",
            "source_body",
            "campaign_goal",
            "language",
            "notes",
        ]:
            if field in payload:
                updated[field] = str(payload.get(field) or "").strip()

        if "status" in payload:
            next_status = str(payload.get("status") or "").strip()

            if next_status in ALLOWED_CAMPAIGN_STATUSES:
                updated["status"] = next_status

        if "channel_ids" in payload:
            updated["channel_ids"] = normalize_channel_ids(payload.get("channel_ids"))

        if "media_items" in payload or "media_urls" in payload:
            updated["media_items"] = normalize_media_items(payload)

        updated["preview"] = campaign_preview_text(str(updated.get("source_body") or ""))
        updated["updated_at"] = utc_now()

        history = updated.get("history")
        if not isinstance(history, list):
            history = []

        history.append(
            {
                "status": updated.get("status", "draft"),
                "at": updated["updated_at"],
                "message": "Media campaign updated.",
            }
        )

        updated["history"] = history

        items[index] = updated
        write_campaigns(items)

        return updated

    return None


def delete_media_campaign(campaign_id: str) -> bool:
    items = read_campaigns()
    next_items = [item for item in items if item.get("id") != campaign_id]

    if len(next_items) == len(items):
        return False

    write_campaigns(next_items)
    return True
    ''',
)


api_path = ROOT / "backend/src/api/publishing.py"
api = api_path.read_text(encoding="utf-8")

if "from typing import Any" not in api:
    api = "from typing import Any\n" + api

if "media_campaign_service" not in api:
    api = api.replace(
        "\n\nrouter = APIRouter",
        "\n\nfrom src.services.media_campaign_service import (\n    create_media_campaign,\n    get_media_campaign,\n    list_media_campaigns,\n    update_media_campaign,\n)\n\nrouter = APIRouter",
        1,
    )

if '@router.get("/campaigns")' not in api:
    api += r'''


@router.get("/campaigns")
def api_list_media_campaigns(
    status: str | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    return list_media_campaigns(status=status, project_id=project_id)


@router.post("/campaigns")
def api_create_media_campaign(payload: dict[str, Any]) -> dict[str, Any]:
    return create_media_campaign(payload)


@router.get("/campaigns/{campaign_id}")
def api_get_media_campaign(campaign_id: str) -> dict[str, Any]:
    campaign = get_media_campaign(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Media campaign not found.")

    return campaign


@router.patch("/campaigns/{campaign_id}")
def api_update_media_campaign(campaign_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    campaign = update_media_campaign(campaign_id, payload)

    if not campaign:
        raise HTTPException(status_code=404, detail="Media campaign not found.")

    return campaign
'''

api_path.write_text(api.strip() + "\n", encoding="utf-8")
print("Patched backend/src/api/publishing.py with media campaign endpoints.")


write_file(
    "backend/tests/smoke_test_media_campaigns.py",
    r'''
from fastapi.testclient import TestClient

from src.main import app
from src.services.media_campaign_service import delete_media_campaign


client = TestClient(app)


def main() -> None:
    channel_response = client.post(
        "/publishing/channels",
        json={
            "name": "DAMA Campaign Smoke Telegram",
            "channel_type": "telegram",
            "target_url": "@damamedia_campaign_smoke",
            "notes": "Media campaign smoke channel.",
        },
    )
    assert channel_response.status_code == 200, channel_response.text
    channel = channel_response.json()

    create_response = client.post(
        "/publishing/campaigns",
        json={
            "project_name": "DAMA Smoke Project",
            "source_title": "کمپین تست چندرسانه‌ای",
            "source_body": "این متن مادر برای تست کمپین چندرسانه‌ای DAMA ساخته شده است.",
            "campaign_goal": "تست ساخت کمپین مادر",
            "media_urls": [
                "I:/DAMA/smoke-image.jpg",
                "I:/DAMA/smoke-video.mp4",
            ],
            "channel_ids": [channel["id"]],
            "notes": "smoke-test media campaign",
        },
    )
    assert create_response.status_code == 200, create_response.text
    campaign = create_response.json()

    assert campaign["id"]
    assert campaign["source_title"] == "کمپین تست چندرسانه‌ای"
    assert len(campaign["media_items"]) == 2
    assert campaign["media_items"][0]["type"] == "image"
    assert campaign["media_items"][1]["type"] == "video"
    assert campaign["channel_ids"] == [channel["id"]]

    get_response = client.get(f"/publishing/campaigns/{campaign['id']}")
    assert get_response.status_code == 200, get_response.text

    update_response = client.patch(
        f"/publishing/campaigns/{campaign['id']}",
        json={
            "status": "ready",
            "notes": "smoke-test updated",
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["status"] == "ready"

    list_response = client.get("/publishing/campaigns")
    assert list_response.status_code == 200, list_response.text
    assert list_response.json()["total"] >= 1

    delete_media_campaign(campaign["id"])

    print("Media campaign smoke test passed.")


if __name__ == "__main__":
    main()
    ''',
)


backend_check = ROOT / "scripts/backend-check.ps1"
backend_text = backend_check.read_text(encoding="utf-8")

if "smoke_test_media_campaigns.py" not in backend_text:
    backend_text = backend_text.rstrip() + r'''

$MediaCampaignSmokeTest = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\tests\smoke_test_media_campaigns.py"
$MediaCampaignPython = Join-Path (Split-Path -Parent $PSScriptRoot) "backend\.venv\Scripts\python.exe"

if (Test-Path $MediaCampaignSmokeTest) {
    Write-Host ""
    Write-Host "Running .\backend\tests\smoke_test_media_campaigns.py..."
    & $MediaCampaignPython $MediaCampaignSmokeTest
    if ($LASTEXITCODE -ne 0) {
        throw "Smoke test failed: .\backend\tests\smoke_test_media_campaigns.py"
    }
}
''' + "\n"

    backend_check.write_text(backend_text, encoding="utf-8")
    print("Patched scripts/backend-check.ps1")


write_file(
    "frontend/src/components/create-media-campaign-form.tsx",
    r'''
"use client";

import { FormEvent, useMemo, useState } from "react";
import { friendlyErrorMessage, labelConnector } from "../lib/persian-copy";

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
};

type CreateMediaCampaignFormProps = {
  apiBaseUrl: string;
  channels: ChannelOption[];
};

export function CreateMediaCampaignForm({
  apiBaseUrl,
  channels
}: CreateMediaCampaignFormProps) {
  const defaultChannelIds = useMemo(
    () => channels.filter((channel) => ["wordpress", "telegram"].includes(channel.channel_type)).map((channel) => channel.id),
    [channels]
  );

  const [projectName, setProjectName] = useState("");
  const [sourceTitle, setSourceTitle] = useState("");
  const [sourceBody, setSourceBody] = useState("");
  const [campaignGoal, setCampaignGoal] = useState("");
  const [mediaUrls, setMediaUrls] = useState("");
  const [selectedChannelIds, setSelectedChannelIds] = useState<string[]>(defaultChannelIds);
  const [message, setMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  function toggleChannel(channelId: string) {
    setSelectedChannelIds((current) =>
      current.includes(channelId)
        ? current.filter((item) => item !== channelId)
        : [...current, channelId]
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/campaigns`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          project_name: projectName,
          source_title: sourceTitle,
          source_body: sourceBody,
          campaign_goal: campaignGoal,
          media_urls: mediaUrls,
          channel_ids: selectedChannelIds,
          notes: "created from media campaign composer"
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      setMessage("کمپین چندرسانه‌ای ساخته شد. صفحه را تازه‌سازی کن یا وارد جزئیات کمپین شو.");
      setProjectName("");
      setSourceTitle("");
      setSourceBody("");
      setCampaignGoal("");
      setMediaUrls("");
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="panel generation-form" onSubmit={handleSubmit}>
      <div className="panel-heading">
        <p className="eyebrow">کمپین مادر</p>
        <h2>ساخت کمپین چندرسانه‌ای</h2>
      </div>

      <label>
        نام پروژه
        <input
          value={projectName}
          onChange={(event) => setProjectName(event.target.value)}
          placeholder="مثلاً دامامدیا، گرگران، اورماشاپ..."
        />
      </label>

      <label>
        عنوان کمپین
        <input
          value={sourceTitle}
          onChange={(event) => setSourceTitle(event.target.value)}
          placeholder="عنوانی که بعداً برای نسخه‌های کانالی استفاده می‌شود"
          required
        />
      </label>

      <label>
        متن مادر
        <textarea
          value={sourceBody}
          onChange={(event) => setSourceBody(event.target.value)}
          placeholder="توضیح اصلی کمپین را اینجا بنویس. DAMA بعداً از این متن نسخه مخصوص هر شبکه را می‌سازد."
          rows={8}
          required
        />
      </label>

      <label>
        هدف کمپین
        <input
          value={campaignGoal}
          onChange={(event) => setCampaignGoal(event.target.value)}
          placeholder="مثلاً معرفی پروژه، جذب مخاطب، اطلاع‌رسانی، فروش..."
        />
      </label>

      <label>
        عکس‌ها یا ویدیوها
        <textarea
          value={mediaUrls}
          onChange={(event) => setMediaUrls(event.target.value)}
          placeholder="هر مسیر فایل یا لینک را در یک خط بگذار. مثال: I:\DAMA\media\poster.jpg"
          rows={5}
        />
      </label>

      <div className="field-group">
        <span>کانال‌های مقصد</span>

        <div className="channel-checkbox-grid">
          {channels.length > 0 ? (
            channels.map((channel) => (
              <label className="checkbox-card" key={channel.id}>
                <input
                  type="checkbox"
                  checked={selectedChannelIds.includes(channel.id)}
                  onChange={() => toggleChannel(channel.id)}
                />
                <strong>{channel.name || labelConnector(channel.channel_type)}</strong>
                <small>{labelConnector(channel.channel_type)}</small>
              </label>
            ))
          ) : (
            <p className="muted-note">هنوز کانالی ثبت نشده است. از بخش انتشار، کانال‌ها را بساز.</p>
          )}
        </div>
      </div>

      <p className="muted-note">
        این مرحله هنوز چیزی را منتشر نمی‌کند. فقط کمپین مادر را برای نسخه‌سازی و صف انتشار آماده می‌کند.
      </p>

      {message ? <p className="form-message">{message}</p> : null}

      <button type="submit" disabled={isSaving || !sourceTitle || !sourceBody}>
        {isSaving ? "در حال ساخت..." : "ساخت کمپین"}
      </button>
    </form>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/campaigns/page.tsx",
    r'''
import { CreateMediaCampaignForm } from "../../../components/create-media-campaign-form";
import { PageHeader } from "../../../components/page-header";
import { StatCard } from "../../../components/stat-card";
import { formatPersianDate, labelConnector } from "../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
  status: string;
};

type MediaCampaign = {
  id: string;
  project_name: string;
  source_title: string;
  preview: string;
  status: string;
  channel_ids: string[];
  media_items: Array<{ id: string; type: string; source: string }>;
  created_at: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function getItems(payload: unknown): Record<string, unknown>[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : Array.isArray(payload) ? payload : [];
  return source.map(asRecord);
}

function normalizeChannels(payload: unknown): ChannelOption[] {
  return getItems(payload)
    .map((item) => ({
      id: String(item.id ?? ""),
      name: String(item.name ?? ""),
      channel_type: String(item.channel_type ?? ""),
      status: String(item.status ?? "")
    }))
    .filter((item) => item.id)
    .filter((item) => item.status !== "inactive");
}

function normalizeCampaigns(payload: unknown): MediaCampaign[] {
  return getItems(payload)
    .map((item) => ({
      id: String(item.id ?? ""),
      project_name: String(item.project_name ?? ""),
      source_title: String(item.source_title ?? ""),
      preview: String(item.preview ?? ""),
      status: String(item.status ?? ""),
      channel_ids: Array.isArray(item.channel_ids) ? item.channel_ids.map(String) : [],
      media_items: Array.isArray(item.media_items)
        ? item.media_items.map((media) => {
            const value = asRecord(media);
            return {
              id: String(value.id ?? ""),
              type: String(value.type ?? ""),
              source: String(value.source ?? "")
            };
          })
        : [],
      created_at: String(item.created_at ?? "")
    }))
    .filter((item) => item.id);
}

async function loadJson(path: string): Promise<unknown> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return await response.json();
  } catch {
    return {};
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "پیش‌نویس",
    ready: "آماده نسخه‌سازی",
    variant_planned: "نسخه‌سازی شده",
    queued: "وارد صف شده",
    published: "منتشر شده",
    archived: "آرشیو شده"
  };

  return labels[status] ?? "پیش‌نویس";
}

export default async function MediaCampaignsPage() {
  const [campaignsPayload, channelsPayload] = await Promise.all([
    loadJson("/publishing/campaigns"),
    loadJson("/publishing/channels")
  ]);

  const campaigns = normalizeCampaigns(campaignsPayload);
  const channels = normalizeChannels(channelsPayload);

  const mediaCount = campaigns.reduce((total, campaign) => total + campaign.media_items.length, 0);
  const selectedChannelCount = campaigns.reduce((total, campaign) => total + campaign.channel_ids.length, 0);

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="کمپین چندرسانه‌ای"
        title="کمپین‌های انتشار"
        lead="اینجا متن مادر، عکس‌ها یا ویدیوها و کانال‌های مقصد را در قالب یک کمپین ذخیره می‌کنی."
      >
        <div className="actions">
          <a href="/publishing">مرکز انتشار</a>
          <a href="/publishing/variants">نسخه‌ها</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="کمپین‌ها" value={campaigns.length} helper="کمپین‌های ثبت‌شده" />
        <StatCard label="رسانه‌ها" value={mediaCount} helper="عکس/ویدیو/فایل" />
        <StatCard label="کانال‌های انتخابی" value={selectedChannelCount} helper="مقصدهای کمپین‌ها" />
        <StatCard label="کانال‌های فعال" value={channels.length} helper="قابل انتخاب" />
      </section>

      <section className="two-column">
        <CreateMediaCampaignForm apiBaseUrl={API_BASE_URL} channels={channels} />

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">راهنما</p>
            <h2>این صفحه چه کار می‌کند؟</h2>
          </div>

          <ol className="simple-steps">
            <li>یک متن مادر برای کمپین می‌نویسی.</li>
            <li>عکس‌ها یا ویدیوهای مربوط را معرفی می‌کنی.</li>
            <li>کانال‌های مقصد را انتخاب می‌کنی.</li>
            <li>در مرحله بعد، DAMA از همین کمپین نسخه‌های کانالی می‌سازد.</li>
          </ol>
        </section>
      </section>

      <section className="panel">
        <div className="panel-heading">
          <p className="eyebrow">لیست کمپین‌ها</p>
          <h2>کمپین‌های اخیر</h2>
        </div>

        <div className="campaign-grid">
          {campaigns.length > 0 ? (
            campaigns.map((campaign) => (
              <a className="campaign-card" href={`/publishing/campaigns/${campaign.id}`} key={campaign.id}>
                <div>
                  <span className={`status-badge status-${campaign.status}`}>
                    {statusLabel(campaign.status)}
                  </span>
                  <strong>{campaign.source_title}</strong>
                  <p>{campaign.preview || "بدون توضیح کوتاه"}</p>
                </div>

                <dl>
                  <div>
                    <dt>پروژه</dt>
                    <dd>{campaign.project_name || ""}</dd>
                  </div>
                  <div>
                    <dt>رسانه</dt>
                    <dd>{campaign.media_items.length}</dd>
                  </div>
                  <div>
                    <dt>کانال</dt>
                    <dd>{campaign.channel_ids.length}</dd>
                  </div>
                  <div>
                    <dt>زمان</dt>
                    <dd>{formatPersianDate(campaign.created_at)}</dd>
                  </div>
                </dl>
              </a>
            ))
          ) : (
            <p className="muted-note">هنوز کمپینی ساخته نشده است.</p>
          )}
        </div>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/campaigns/[campaignId]/page.tsx",
    r'''
import { PageHeader } from "../../../../components/page-header";
import { StatCard } from "../../../../components/stat-card";
import { formatPersianDate, labelConnector, shortId } from "../../../../lib/persian-copy";

export const dynamic = "force-dynamic";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

type Props = {
  params: Promise<{
    campaignId: string;
  }>;
};

type ChannelOption = {
  id: string;
  name: string;
  channel_type: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function getItems(payload: unknown): Record<string, unknown>[] {
  const record = asRecord(payload);
  const source = Array.isArray(record.items) ? record.items : Array.isArray(payload) ? payload : [];
  return source.map(asRecord);
}

async function loadJson(path: string): Promise<unknown> {
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      return {};
    }

    return await response.json();
  } catch {
    return {};
  }
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: "پیش‌نویس",
    ready: "آماده نسخه‌سازی",
    variant_planned: "نسخه‌سازی شده",
    queued: "وارد صف شده",
    published: "منتشر شده",
    archived: "آرشیو شده"
  };

  return labels[status] ?? "پیش‌نویس";
}

function mediaTypeLabel(type: string): string {
  if (type === "image") {
    return "تصویر";
  }

  if (type === "video") {
    return "ویدیو";
  }

  if (type === "document") {
    return "فایل";
  }

  return "رسانه";
}

export default async function MediaCampaignDetailPage({ params }: Props) {
  const { campaignId } = await params;

  const [campaignPayload, channelsPayload] = await Promise.all([
    loadJson(`/publishing/campaigns/${campaignId}`),
    loadJson("/publishing/channels")
  ]);

  const campaign = asRecord(campaignPayload);
  const mediaItems = Array.isArray(campaign.media_items)
    ? campaign.media_items.map(asRecord)
    : [];
  const channelIds = Array.isArray(campaign.channel_ids)
    ? campaign.channel_ids.map(String)
    : [];

  const channels: ChannelOption[] = getItems(channelsPayload)
    .map((item) => ({
      id: String(item.id ?? ""),
      name: String(item.name ?? ""),
      channel_type: String(item.channel_type ?? "")
    }))
    .filter((item) => item.id);

  const selectedChannels = channels.filter((channel) => channelIds.includes(channel.id));

  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="جزئیات کمپین"
        title={String(campaign.source_title ?? "کمپین")}
        lead={String(campaign.preview ?? "کمپین چندرسانه‌ای برای نسخه‌سازی و انتشار چندکاناله.")}
      >
        <div className="actions">
          <a href="/publishing/campaigns">بازگشت به کمپین‌ها</a>
          <a href="/publishing/variants">نسخه‌سازی</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="وضعیت" value={statusLabel(String(campaign.status ?? ""))} helper={`شناسه: ${shortId(campaignId)}`} />
        <StatCard label="رسانه‌ها" value={mediaItems.length} helper="عکس، ویدیو یا فایل" />
        <StatCard label="کانال‌های مقصد" value={selectedChannels.length} helper="برای نسخه‌سازی بعدی" />
        <StatCard label="زمان ساخت" value={formatPersianDate(String(campaign.created_at ?? ""))} helper={String(campaign.project_name ?? "")} />
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">متن مادر</p>
            <h2>محتوای اصلی کمپین</h2>
          </div>

          <div className="generated-output">
            <h3>{String(campaign.source_title ?? "بدون عنوان")}</h3>
            <p>{String(campaign.source_body ?? "بدون متن")}</p>
          </div>
        </section>

        <section className="panel quiet-panel">
          <div className="panel-heading">
            <p className="eyebrow">قدم بعدی</p>
            <h2>بعد از ساخت کمپین</h2>
          </div>

          <ol className="simple-steps">
            <li>در مرحله بعد، برای کانال‌های انتخاب‌شده نسخه مخصوص ساخته می‌شود.</li>
            <li>هر نسخه را بازبینی و تأیید می‌کنی.</li>
            <li>بعد نسخه‌ها وارد صف انتشار می‌شوند.</li>
            <li>انتشار واقعی همچنان دستی و کنترل‌شده خواهد بود.</li>
          </ol>
        </section>
      </section>

      <section className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">رسانه‌ها</p>
            <h2>عکس‌ها و ویدیوهای کمپین</h2>
          </div>

          <div className="media-list">
            {mediaItems.length > 0 ? (
              mediaItems.map((item) => (
                <div className="media-row" key={String(item.id ?? item.source)}>
                  <span>{mediaTypeLabel(String(item.type ?? ""))}</span>
                  <code>{String(item.source ?? "")}</code>
                </div>
              ))
            ) : (
              <p className="muted-note">برای این کمپین هنوز رسانه‌ای ثبت نشده است.</p>
            )}
          </div>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <p className="eyebrow">مقصدها</p>
            <h2>کانال‌های انتخاب‌شده</h2>
          </div>

          <div className="channel-chip-list">
            {selectedChannels.length > 0 ? (
              selectedChannels.map((channel) => (
                <span className="channel-chip" key={channel.id}>
                  {channel.name || labelConnector(channel.channel_type)}
                  <small>{labelConnector(channel.channel_type)}</small>
                </span>
              ))
            ) : (
              <p className="muted-note">هنوز کانالی برای این کمپین انتخاب نشده است.</p>
            )}
          </div>
        </section>
      </section>

      <section className="panel">
        <details className="technical-details">
          <summary>نمایش جزئیات فنی کمپین</summary>
          <pre className="json-block">{JSON.stringify(campaign, null, 2)}</pre>
        </details>
      </section>
    </main>
  );
}
    ''',
)


write_file(
    "frontend/src/app/publishing/page.tsx",
    r'''
import { PageHeader } from "../../components/page-header";
import { StatCard } from "../../components/stat-card";

export const dynamic = "force-dynamic";

export default function PublishingHomePage() {
  return (
    <main className="page-shell">
      <PageHeader
        eyebrow="انتشار"
        title="مرکز ساده انتشار"
        lead="از اینجا کمپین مادر می‌سازی، نسخه کانالی آماده می‌کنی، وارد صف می‌کنی و نتیجه را می‌بینی."
      >
        <div className="actions">
          <a href="/publishing/campaigns">کمپین‌ها</a>
          <a href="/publishing/queue">صف انتشار</a>
        </div>
      </PageHeader>

      <section className="stats-grid">
        <StatCard label="کمپین‌ها" value="جدید" helper="متن + رسانه + مقصدها" />
        <StatCard label="نسخه‌ها" value="کانالی" helper="متناسب با هر شبکه" />
        <StatCard label="صف انتشار" value="دستی" helper="امن و کنترل‌شده" />
        <StatCard label="گزارش‌ها" value="ثبت کامل" helper="هر اجرا یک گزارش" />
      </section>

      <section className="operator-grid">
        <a className="operator-card primary-operator-card" href="/publishing/campaigns">
          <span></span>
          <strong>کمپین چندرسانه‌ای</strong>
          <p>متن مادر، عکس/ویدیو و کانال‌های مقصد را یکجا تعریف کن.</p>
        </a>

        <a className="operator-card" href="/publishing/variants">
          <span></span>
          <strong>نسخه‌ها</strong>
          <p>برای وردپرس، تلگرام و کانال‌های دیگر نسخه جدا بساز.</p>
        </a>

        <a className="operator-card" href="/publishing/queue">
          <span></span>
          <strong>صف انتشار</strong>
          <p>نسخه آماده را وارد صف کن و دستی اجرا کن.</p>
        </a>

        <a className="operator-card" href="/publishing/attempts">
          <span></span>
          <strong>گزارش انتشار</strong>
          <p>نتیجه اجرای وردپرس، تلگرام و خطاها را بررسی کن.</p>
        </a>
      </section>
    </main>
  );
}
    ''',
)


append_once(
    "frontend/src/app/globals.css",
    "/* Media campaign composer */",
    r'''
/* Media campaign composer */
.channel-checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  margin-top: 0.6rem;
}

.checkbox-card {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 0.7rem;
  align-items: start;
  padding: 0.8rem;
  border: 1px solid var(--border);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.62);
}

.checkbox-card input {
  margin-top: 0.25rem;
}

.checkbox-card strong,
.checkbox-card small {
  display: block;
}

.checkbox-card small {
  color: var(--muted);
}

.campaign-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1rem;
}

.campaign-card {
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid var(--border);
  border-radius: 1.25rem;
  background: rgba(255, 255, 255, 0.72);
  color: var(--text);
  text-decoration: none;
  box-shadow: var(--shadow);
}

.campaign-card strong {
  display: block;
  margin-top: 0.75rem;
  font-size: 1.05rem;
}

.campaign-card p {
  color: var(--muted);
  line-height: 1.85;
}

.campaign-card dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
  margin: 0;
}

.campaign-card dt {
  color: var(--muted);
  font-size: 0.82rem;
}

.campaign-card dd {
  margin: 0.15rem 0 0;
  font-weight: 800;
}

.media-list {
  display: grid;
  gap: 0.65rem;
}

.media-row {
  display: grid;
  grid-template-columns: 90px minmax(0, 1fr);
  gap: 0.75rem;
  align-items: center;
  padding: 0.8rem;
  border: 1px solid var(--border);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.55);
}

.media-row span {
  font-weight: 900;
}

.media-row code {
  direction: ltr;
  overflow-wrap: anywhere;
}

.channel-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.channel-chip {
  display: inline-grid;
  gap: 0.15rem;
  padding: 0.65rem 0.85rem;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  font-weight: 900;
}

.channel-chip small {
  color: var(--muted);
  font-weight: 700;
}
    ''',
)


write_file(
    "scripts/frontend-check.ps1",
    r'''
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required frontend file is missing: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

Write-Host "Checking frontend..."

if (-not (Test-Path -LiteralPath ".\frontend\node_modules")) {
    throw "frontend/node_modules not found. Run npm install in frontend first."
}

Write-Host "node_modules found. Running frontend typecheck..."

Push-Location ".\frontend"
npm.cmd run typecheck
if ($LASTEXITCODE -ne 0) {
    Pop-Location
    throw "Frontend typecheck failed."
}
Pop-Location

$RequiredFiles = @(
    ".\frontend\src\lib\persian-copy.ts",
    ".\frontend\src\lib\operator-workflow.ts",
    ".\frontend\src\components\operator-checklist.tsx",
    ".\frontend\src\components\create-media-campaign-form.tsx",
    ".\frontend\src\components\cleanup-test-data-action.tsx",
    ".\frontend\src\components\create-publishing-queue-item-form.tsx",
    ".\frontend\src\components\run-publishing-queue-item-action.tsx",
    ".\frontend\src\app\page.tsx",
    ".\frontend\src\app\publishing\page.tsx",
    ".\frontend\src\app\publishing\campaigns\page.tsx",
    ".\frontend\src\app\publishing\campaigns\[campaignId]\page.tsx",
    ".\frontend\src\app\publishing\queue\page.tsx",
    ".\frontend\src\app\publishing\attempts\page.tsx",
    ".\frontend\src\app\publishing\attempts\[attemptId]\page.tsx",
    ".\frontend\src\app\advanced\cleanup\page.tsx",
    ".\frontend\src\app\globals.css"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -LiteralPath $File)) {
        throw "Required frontend file is missing: $File"
    }
}

$PublishingPage = Read-TextFile ".\frontend\src\app\publishing\page.tsx"
$CampaignsPage = Read-TextFile ".\frontend\src\app\publishing\campaigns\page.tsx"
$CampaignDetailPage = Read-TextFile ".\frontend\src\app\publishing\campaigns\[campaignId]\page.tsx"
$CampaignForm = Read-TextFile ".\frontend\src\components\create-media-campaign-form.tsx"
$Styles = Read-TextFile ".\frontend\src\app\globals.css"

if ($PublishingPage -notmatch "/publishing/campaigns") {
    throw "Publishing page does not link to media campaigns."
}

if ($CampaignsPage -notmatch "/publishing/campaigns") {
    throw "Campaigns page does not call campaigns endpoint."
}

if ($CampaignsPage -notmatch "CreateMediaCampaignForm") {
    throw "Campaigns page is missing campaign form."
}

if ($CampaignDetailPage -notmatch "media_items") {
    throw "Campaign detail page does not show media items."
}

if ($CampaignForm -notmatch "channel_ids") {
    throw "Campaign form does not submit selected channels."
}

if ($Styles -notmatch "Media campaign composer") {
    throw "Global styles are missing media campaign composer marker."
}

Write-Host "Frontend production readiness check passed."
    ''',
)


append_once(
    "docs/project-status.md",
    "## Release Pack AI-5 Completed",
    r'''
## Release Pack AI-5 Completed

Name:

Media Campaign Composer

Added files:

- backend/src/services/media_campaign_service.py
- backend/tests/smoke_test_media_campaigns.py
- frontend/src/components/create-media-campaign-form.tsx
- frontend/src/app/publishing/campaigns/page.tsx
- frontend/src/app/publishing/campaigns/[campaignId]/page.tsx

Updated files:

- backend/src/api/publishing.py
- scripts/backend-check.ps1
- scripts/frontend-check.ps1
- frontend/src/app/publishing/page.tsx
- frontend/src/app/globals.css
- docs/project-status.md

Added behavior:

- create media campaign with project name
- write master caption/body
- add image/video paths or URLs
- select destination channels
- list campaigns
- view campaign detail
- store campaign runtime data locally

Next recommended step:

Release Pack AI-6: Campaign-to-Variants Planner

Goal:

- select a campaign
- generate variants for all selected channels
- link variants back to campaign
- prepare the bridge toward multi-channel queue publishing
    ''',
)


print("Release Pack AI-5 applied successfully.")
