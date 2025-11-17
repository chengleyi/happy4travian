<#
  兵种参数导出为 CSV（每部落一份）
  读取静态 JSON，生成若干 CSV 文件便于数据查看与处理。
#>
param(
  [string]$JsonPath = "backend_py/data/troops_t4.6_1x.json",
  [string]$OutDir = "backend_py/exports"
)
$ErrorActionPreference = 'Stop'
function Read-Json($p) { Get-Content $p -Raw | ConvertFrom-Json }
function Fmt-Time($sec) { if (-not $sec -or $sec -le 0) { return '0:00:00' }; [System.TimeSpan]::FromSeconds([int]$sec).ToString() }
$data = Read-Json $JsonPath
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$summary = Join-Path $OutDir 'summary.csv'
"version,speed,tribes" | Set-Content -Encoding UTF8 $summary
"$($data.version),$($data.speed),$($data.tribes.Count)" | Add-Content -Encoding UTF8 $summary
forEach ($tribe in $data.tribes) {
  $tid = [int]$tribe.tribeId
  $en = $tribe.tribeLabel
  $csv = Join-Path $OutDir ("tribe_${tid}_" + ($en -replace '[^A-Za-z0-9_-]', '_') + '.csv')
  "TribeId,Tribe(EN),Tribe(ZH),UnitId,Name(EN),Name(ZH),Type,Off,Def_i,Def_c,Speed,Cap,Cost_Lumber,Cost_Clay,Cost_Iron,Cost_Crop,Upkeep,TrainTime_s,TrainTime,ResearchTime_s,ResearchTime" | Set-Content -Encoding UTF8 $csv
  foreach ($u in $tribe.units) {
    $cost = $u.cost
    $line = (
      "$tid,$en,$en,$($u.unitId),$($u.name),$($u.name),$($u.type),$($u.off),$($u.def_i),$($u.def_c),$($u.speed),$($u.cap),$($cost[0]),$($cost[1]),$($cost[2]),$($cost[3]),$($u.cu),$($u.time),$([string](Fmt-Time $u.time)),$($u.rs_time),$([string](Fmt-Time $u.rs_time))"
    )
    $line | Add-Content -Encoding UTF8 $csv
  }
}
Write-Output (Resolve-Path $OutDir)