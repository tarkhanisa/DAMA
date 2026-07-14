"use client";

import { useState } from "react";
import { friendlyErrorMessage } from "../lib/persian-copy";

type PlanCampaignVariantsActionProps = {
  apiBaseUrl: string;
  campaignId: string;
  sourceTitle: string;
  sourceBody: string;
  channelIds: string[];
};

export function PlanCampaignVariantsAction({
  apiBaseUrl,
  campaignId,
  sourceTitle,
  sourceBody,
  channelIds
}: PlanCampaignVariantsActionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [message, setMessage] = useState("");

  async function handlePlan() {
    setIsRunning(true);
    setMessage("");

    try {
      const response = await fetch(`${apiBaseUrl}/publishing/variants/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          content_asset_id: campaignId,
          source_title: sourceTitle,
          source_body: sourceBody,
          channel_ids: channelIds
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        setMessage(friendlyErrorMessage(String(payload.detail ?? `HTTP ${response.status}`)));
        return;
      }

      await fetch(`${apiBaseUrl}/publishing/campaigns/${campaignId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          status: "variant_planned",
          notes: "variants planned from campaign detail"
        })
      });

      const count = Array.isArray(payload.items) ? payload.items.length : 0;
      setMessage(`نسخه‌سازی انجام شد. تعداد نسخه‌ها: ${count}.`);
    } catch (error) {
      setMessage(friendlyErrorMessage(error instanceof Error ? error.message : "خطای ناشناخته"));
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="enhance-variant-action">
      <button type="button" onClick={handlePlan} disabled={isRunning || channelIds.length === 0}>
        {isRunning ? "در حال نسخه‌سازی..." : "ساخت نسخه برای کانال‌ها"}
      </button>

      {message ? <p className="form-message">{message}</p> : null}
    </div>
  );
}
