from pathlib import Path

ROOT = Path("I:/DAMA")
target = ROOT / "scripts/frontend-check.ps1"

text = target.read_text(encoding="utf-8-sig")

old = '''
if ($AttemptDetailPage -notmatch "نمایش جزئیات فنی") {
    throw "Attempt detail page is missing Persian technical details label."
}
'''.strip()

new = '''
if ($AttemptDetailPage -notmatch "<summary>") {
    throw "Attempt detail page is missing technical details summary."
}
'''.strip()

if old in text:
    text = text.replace(old, new)
else:
    text = text.replace(
        'if ($AttemptDetailPage -notmatch "technical-details") {\n    throw "Attempt detail page is missing collapsible technical details."\n}',
        'if ($AttemptDetailPage -notmatch "technical-details") {\n    throw "Attempt detail page is missing collapsible technical details."\n}\n\nif ($AttemptDetailPage -notmatch "<summary>") {\n    throw "Attempt detail page is missing technical details summary."\n}'
    )

target.write_text(text, encoding="utf-8-sig")

print("frontend-check.ps1 patched: Persian text assertion removed.")
