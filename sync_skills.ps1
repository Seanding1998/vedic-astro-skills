# Vedic Skills 三地同步脚本
# 源头: antigravity/skills/ → 同步到 claude-code + gemini运行时 + git push

param(
    [string]$CommitMsg = "sync: update skills"
)

$repo = "d:\0417jhora\vedic-astrology-skills"
$src = "$repo\antigravity\skills"
$cc = "$repo\claude-code\skills"
$gemini = "C:\Users\14361\.gemini\config\skills"

# 要同步的skill列表
$skills = @("vedic-reader", "vedic-core", "vedic-career", "vedic-love", "vedic-rectifier")

Write-Host "=== Vedic Skills 三地同步 ===" -ForegroundColor Cyan

# 1. 同步到 claude-code
Write-Host "`n[1/3] 同步到 claude-code..." -ForegroundColor Yellow
foreach ($skill in $skills) {
    if (Test-Path "$src\$skill") {
        # 先删再整个复制，避免残留
        if (Test-Path "$cc\$skill") { Remove-Item "$cc\$skill" -Recurse -Force }
        Copy-Item "$src\$skill" "$cc\$skill" -Recurse -Force
        Write-Host "  ✓ $skill" -ForegroundColor Green
    }
}

# 2. 同步到 Gemini 运行时
Write-Host "`n[2/3] 同步到 Gemini 运行时..." -ForegroundColor Yellow
foreach ($skill in $skills) {
    if (Test-Path "$src\$skill") {
        if (Test-Path "$gemini\$skill") {
            # 先删再整个复制
            Remove-Item "$gemini\$skill" -Recurse -Force
        }
        Copy-Item "$src\$skill" "$gemini\$skill" -Recurse -Force
        Write-Host "  ✓ $skill" -ForegroundColor Green
    }
}

# 3. Git commit + push
Write-Host "`n[3/3] Git commit + push..." -ForegroundColor Yellow
Set-Location $repo
git add -A
git commit -m $CommitMsg
git push

Write-Host "`n=== 同步完成 ===" -ForegroundColor Cyan
