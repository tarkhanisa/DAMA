type AssetBodyPreviewProps = {
  body?: string;
};

export function AssetBodyPreview({ body }: AssetBodyPreviewProps) {
  const normalized = String(body ?? "").trim();

  if (!normalized) {
    return <p className="empty-state">No body content.</p>;
  }

  return <pre className="asset-body-preview">{normalized}</pre>;
}
