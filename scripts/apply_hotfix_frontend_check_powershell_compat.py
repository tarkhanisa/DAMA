from pathlib import Path

ROOT = Path("I:/DAMA")

target = ROOT / "scripts/frontend-check.ps1"
text = target.read_text(encoding="utf-8")

# Replace Get-Content "...file..." -Raw with a PowerShell 2-compatible helper.
helper = r'''
function Read-TextFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Path
    )

    return [string]::Join("`n", (Get-Content -LiteralPath $Path))
}

'''

if "function Read-TextFile" not in text:
    text = text.replace('$ErrorActionPreference = "Stop"\n', '$ErrorActionPreference = "Stop"\n\n' + helper)

text = text.replace('Get-Content ".\\frontend\\src\\lib\\api-client.ts" -Raw', 'Read-TextFile ".\\frontend\\src\\lib\\api-client.ts"')
text = text.replace('Get-Content ".\\frontend\\src\\components\\app-nav.tsx" -Raw', 'Read-TextFile ".\\frontend\\src\\components\\app-nav.tsx"')
text = text.replace('Get-Content ".\\frontend\\src\\components\\safe-action-button.tsx" -Raw', 'Read-TextFile ".\\frontend\\src\\components\\safe-action-button.tsx"')
text = text.replace('Get-Content ".\\frontend\\src\\app\\operations\\page.tsx" -Raw', 'Read-TextFile ".\\frontend\\src\\app\\operations\\page.tsx"')
text = text.replace('Get-Content ".\\frontend\\src\\app\\projects\\[projectId]\\page.tsx" -Raw', 'Read-TextFile ".\\frontend\\src\\app\\projects\\[projectId]\\page.tsx"')
text = text.replace('Get-Content ".\\frontend\\src\\app\\content-assets\\[assetId]\\page.tsx" -Raw', 'Read-TextFile ".\\frontend\\src\\app\\content-assets\\[assetId]\\page.tsx"')

# Generic cleanup for any remaining -Raw usage.
text = text.replace(" -Raw", "")

target.write_text(text, encoding="utf-8")
print("frontend-check.ps1 patched for older PowerShell compatibility.")
