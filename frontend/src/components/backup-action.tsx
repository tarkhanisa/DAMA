"use client";

import { damaApi } from "../lib/api-client";
import { SafeActionButton } from "./safe-action-button";

export function BackupAction() {
  return (
    <SafeActionButton
      label="Create database backup"
      confirmLabel="Confirm backup"
      successMessage="Database backup created."
      action={() => damaApi.backupDatabase()}
    />
  );
}
