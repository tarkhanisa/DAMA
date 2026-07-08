"use client";

import { damaApi } from "../lib/api-client";
import { SafeActionButton } from "./safe-action-button";

type ExportContentAssetActionProps = {
  assetId: string;
};

export function ExportContentAssetAction({ assetId }: ExportContentAssetActionProps) {
  return (
    <SafeActionButton
      label="Export asset markdown"
      confirmLabel="Confirm export"
      successMessage="Content asset exported."
      action={() => damaApi.exportContentAssetMarkdown(assetId)}
    />
  );
}
