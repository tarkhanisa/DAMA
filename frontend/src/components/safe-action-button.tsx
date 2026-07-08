"use client";

import { useState } from "react";

import { FormStatus } from "./form-status";
import { OperationResult } from "./operation-result";

type SafeActionButtonProps = {
  label: string;
  confirmLabel: string;
  successMessage: string;
  action: () => Promise<unknown>;
};

export function SafeActionButton({
  label,
  confirmLabel,
  successMessage,
  action
}: SafeActionButtonProps) {
  const [isConfirming, setIsConfirming] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const [status, setStatus] = useState<{
    type: "idle" | "success" | "error";
    message?: string;
  }>({ type: "idle" });

  async function runAction() {
    setIsRunning(true);
    setStatus({ type: "idle" });
    setResult(null);

    try {
      const response = await action();
      setResult(response);
      setStatus({
        type: "success",
        message: successMessage
      });
      setIsConfirming(false);
    } catch (error) {
      setStatus({
        type: "error",
        message: error instanceof Error ? error.message : "Operation failed."
      });
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <div className="safe-action">
      {!isConfirming ? (
        <button type="button" onClick={() => setIsConfirming(true)}>
          {label}
        </button>
      ) : (
        <div className="confirm-row">
          <button type="button" disabled={isRunning} onClick={runAction}>
            {isRunning ? "Running..." : confirmLabel}
          </button>
          <button
            type="button"
            className="secondary-button"
            disabled={isRunning}
            onClick={() => setIsConfirming(false)}
          >
            Cancel
          </button>
        </div>
      )}

      <FormStatus type={status.type} message={status.message} />
      <OperationResult title="Operation result" result={result} />
    </div>
  );
}
