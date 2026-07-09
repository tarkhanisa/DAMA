from pathlib import Path

target = Path("I:/DAMA/scripts/frontend-real-build.ps1")
text = target.read_text(encoding="utf-8")

text = text.replace("Get-Command npm", "Get-Command npm.cmd")
text = text.replace("npm install", "npm.cmd install")
text = text.replace("npm run typecheck", "npm.cmd run typecheck")
text = text.replace("npm run build", "npm.cmd run build")

target.write_text(text, encoding="utf-8")
print("frontend-real-build.ps1 now uses npm.cmd.")
