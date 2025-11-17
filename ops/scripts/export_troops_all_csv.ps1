<#
  兵种参数导出为单一 CSV（包含所有部落与兵种）
  适合快速汇总查看或导入到其他系统。
#>
param(
  [string]$JsonPath = "backend_py/data/troops_t4.6_1x.json",
  [string]$OutPath = "backend_py/exports/troops_all.csv"
)
$ErrorActionPreference = 'Stop'
function Read-Json($p) { Get-Content $p -Raw | ConvertFrom-Json }
function Fmt-Time($sec) { if (-not $sec -or $sec -le 0) { return '0:00:00' }; [System.TimeSpan]::FromSeconds([int]$sec).ToString() }
$CN_TRIBES = @{ '1'='罗马'; '2'='条顿'; '3'='高卢'; '4'='自然'; '5'='纳塔'; '6'='埃及'; '7'='匈奴'; '8'='斯巴达'; '9'='维京' }
$CN_UNITS = @{ '1'=@('军团兵','禁卫兵','帝国兵','侦察骑兵','帝国骑兵','凯撒骑兵','攻城槌','投石车','参议员','移民');
                '2'=@('棒兵','矛兵','斧兵','侦察兵','圣骑士','条顿骑士','攻城槌','投石车','酋长','移民');
                '3'=@('方阵','剑士','探路者','雷霆骑兵','德鲁伊骑士','海都安骑士','攻城槌','投石车','首领','移民') }
function Q($s) { '"' + ($s -replace '"','""') + '"' }
$data = Read-Json $JsonPath
New-Item -ItemType Directory -Force -Path (Split-Path $OutPath -Parent) | Out-Null
"Version 版本,Speed 倍速,TribeId 部落ID,Tribe(EN) 部落(英文),部落(中文) Tribe(ZH),UnitId 兵种ID,Name(EN) 英文名称,名称(中文) Name(ZH),Type 类型,Off 攻击,Def_i 防御(步),Def_c 防御(骑),Speed 速度,Cap 负重,Cost 木 Lumber,Cost 泥 Clay,Cost 铁 Iron,Cost 粮 Crop,Upkeep 维护,TrainTime 训练时间(s),TrainTimeFmt 训练时间,ResearchTime 研究时间(s),ResearchTimeFmt 研究时间" | Set-Content -Encoding UTF8 $OutPath
foreach ($tribe in $data.tribes) {
  $tid = [int]$tribe.tribeId
  $enLabel = $tribe.tribeLabel
  $cnLabel = $CN_TRIBES[[string]$tid]
  if (-not $cnLabel) { $cnLabel = $enLabel }
  foreach ($u in $tribe.units) {
    $uid = [int]$u.unitId
    $enName = $u.name
    $cnList = $CN_UNITS[[string]$tid]
    $cnName = if ($cnList -and $uid -le $cnList.Count) { $cnList[$uid-1] } else { $enName }
    $cost = $u.cost
    $line = (
      (Q $data.version) + ',' + (Q $data.speed) + ',' + $tid + ',' + (Q $enLabel) + ',' + (Q $cnLabel) + ',' + $uid + ',' + (Q $enName) + ',' + (Q $cnName) + ',' + (Q $u.type) + ',' + $u.off + ',' + $u.def_i + ',' + $u.def_c + ',' + $u.speed + ',' + $u.cap + ',' + $cost[0] + ',' + $cost[1] + ',' + $cost[2] + ',' + $cost[3] + ',' + $u.cu + ',' + $u.time + ',' + (Q (Fmt-Time $u.time)) + ',' + $u.rs_time + ',' + (Q (Fmt-Time $u.rs_time))
    )
    $line | Add-Content -Encoding UTF8 $OutPath
  }
}
Write-Output (Resolve-Path $OutPath)