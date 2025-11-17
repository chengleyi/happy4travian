<#
  兵种参数导出（PowerShell 版）
  读取 JSON 并构造最小 xlsx（多工作表），无需第三方依赖。
#>
param(
  [string]$JsonPath = "backend_py/data/troops_t4.6_1x.json",
  [string]$OutPath = "backend_py/exports/troops_t4.6_1x.xlsx"
)
$ErrorActionPreference = 'Stop' # 出错即停止
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.IO.Compression
function Read-Json($p) { Get-Content $p -Raw -Encoding UTF8 | ConvertFrom-Json }
function Fmt-Time($sec) {
  if (-not $sec -or $sec -le 0) { return '0:00:00' }
  [System.TimeSpan]::FromSeconds([int]$sec).ToString()
}
$CN_TRIBES = @{}
$CN_UNITS = @{}
$CN_TYPE = @{ 'i'='Infantry'; 'c'='Cavalry' } # 类型中文映射可按需替换

function ColLetter($idx) {
  $s=''; $i=$idx
  while ($i -gt 0) { $i=$i-1; $r=$i % 26; $s=[char](65+$r) + $s; $i=[math]::Floor($i/26) }
  return $s
}
function CellXml($col,$row,$value,$isStr) {
  $addr = "$col$row"
  if ($isStr) {
    $safe = [System.Security.SecurityElement]::Escape([string]$value)
    return "<c r=`"$addr`" t=`"inlineStr`"><is><t>$safe</t></is></c>"
  }
  if ($null -eq $value) { return "<c r=`"$addr`"/>" }
  return "<c r=`"$addr`"><v>$value</v></c>"
}

$data = Read-Json $JsonPath
$cn = Read-Json (Join-Path (Split-Path $JsonPath -Parent) 'cn_map.json')
$headers = @(
  'Version 版本','Speed 倍速','TribeId 部落ID','Tribe(EN) 部落(英文)','部落(中文) Tribe(ZH)',
  'UnitId 兵种ID','Name(EN) 英文名称','名称(中文) Name(ZH)','Type 类型',
  'Off 攻击','Def_i 防御(步)','Def_c 防御(骑)','Speed 速度','Cap 负重',
  'Cost 木 Lumber','Cost 泥 Clay','Cost 铁 Iron','Cost 粮 Crop','Upkeep 维护',
  'TrainTime 训练时间(s)','TrainTimeFmt 训练时间','ResearchTime 研究时间(s)','ResearchTimeFmt 研究时间'
)
$speeds = @(1,2,3,5,10)
$spdMap = @{ '1' = 1; '2' = 2; '3' = 2; '5' = 2; '10' = 4 }
$sheetXmls = @()
forEach ($k in $speeds) {
  $rows = @()
  $cells = @()
  for ($i=1; $i -le $headers.Count; $i++) { $cells += (CellXml (ColLetter $i) 1 $headers[$i-1] $true) }
  $rows += "<row r=`"1`">$($cells -join '')</row>"
  $r = 2
  foreach ($tribe in $data.tribes) {
    $tid = [int]$tribe.tribeId
    $enLabel = $tribe.tribeLabel; if (-not $enLabel) { $enLabel = "tribe_$tid" }
    $cnLabel = $cn.tribes[[string]$tid]; if (-not $cnLabel) { $cnLabel = $enLabel }
    foreach ($u in $tribe.units) {
      $uid = [int]$u.unitId
      $enName = $u.name
      $cnUnits = $cn.units[[string]$tid]
      if ($cnUnits -and $uid -le $cnUnits.Count) { $cnName = $cnUnits[$uid-1] } else { $cnName = $enName }
      $cost = $u.cost
      $typeVal = if ([string]$u.type -eq 'c') { '骑兵' } else { '步兵' }
      $spdFactor = $spdMap[[string]$k]
      $speedAdj = [int]([math]::Round([double]$u.speed * [double]$spdFactor))
      $timeAdj = [int]([math]::Round([double]$u.time / [double]$k))
      $rsAdj = [int]([math]::Round([double]$u.rs_time / [double]$k))
      $vals = @($data.version,"$k`x",$tid,$enLabel,$cnLabel,$uid,$enName,$cnName,$typeVal,
                $u.off,$u.def_i,$u.def_c,$speedAdj,$u.cap,
                ($cost[0]),($cost[1]),($cost[2]),($cost[3]),
                $u.cu,$timeAdj,(Fmt-Time $timeAdj),$rsAdj,(Fmt-Time $rsAdj))
      $cells = @()
      for ($i=1; $i -le $vals.Count; $i++) {
        $v = $vals[$i-1]
        $cells += (CellXml (ColLetter $i) $r $v ($v -is [string]))
      }
      $rows += "<row r=`"$r`">$($cells -join '')</row>"
      $r++
    }
  }
  $sheetXmls += ("<?xml version=`"1.0`" encoding=`"UTF-8`"?><worksheet xmlns=`"http://schemas.openxmlformats.org/spreadsheetml/2006/main`" xmlns:r=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships`"><sheetData>$(($rows -join ''))</sheetData></worksheet>")
}

$workbookXml = "<?xml version=`"1.0`" encoding=`"UTF-8`"?><workbook xmlns=`"http://schemas.openxmlformats.org/spreadsheetml/2006/main`" xmlns:r=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships`"><sheets><sheet name=`"1x`" sheetId=`"1`" r:id=`"rId1`"/><sheet name=`"2x`" sheetId=`"2`" r:id=`"rId2`"/><sheet name=`"3x`" sheetId=`"3`" r:id=`"rId3`"/><sheet name=`"5x`" sheetId=`"4`" r:id=`"rId4`"/><sheet name=`"10x`" sheetId=`"5`" r:id=`"rId5`"/></sheets></workbook>"
$workbookRels = "<?xml version=`"1.0`" encoding=`"UTF-8`"?><Relationships xmlns=`"http://schemas.openxmlformats.org/package/2006/relationships`"><Relationship Id=`"rId1`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet`" Target=`"worksheets/sheet1.xml`"/><Relationship Id=`"rId2`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet`" Target=`"worksheets/sheet2.xml`"/><Relationship Id=`"rId3`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet`" Target=`"worksheets/sheet3.xml`"/><Relationship Id=`"rId4`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet`" Target=`"worksheets/sheet4.xml`"/><Relationship Id=`"rId5`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet`" Target=`"worksheets/sheet5.xml`"/></Relationships>"
$rootRels = "<?xml version=`"1.0`" encoding=`"UTF-8`"?><Relationships xmlns=`"http://schemas.openxmlformats.org/package/2006/relationships`"><Relationship Id=`"rId1`" Type=`"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument`" Target=`"xl/workbook.xml`"/></Relationships>"
$stylesXml = "<?xml version=`"1.0`" encoding=`"UTF-8`"?><styleSheet xmlns=`"http://schemas.openxmlformats.org/spreadsheetml/2006/main`"></styleSheet>"
$contentTypes = "<?xml version=`"1.0`" encoding=`"UTF-8`"?><Types xmlns=`"http://schemas.openxmlformats.org/package/2006/content-types`"><Default Extension=`"rels`" ContentType=`"application/vnd.openxmlformats-package.relationships+xml`"/><Default Extension=`"xml`" ContentType=`"application/xml`"/><Override PartName=`"/xl/workbook.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml`"/><Override PartName=`"/xl/worksheets/sheet1.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml`"/><Override PartName=`"/xl/worksheets/sheet2.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml`"/><Override PartName=`"/xl/worksheets/sheet3.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml`"/><Override PartName=`"/xl/worksheets/sheet4.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml`"/><Override PartName=`"/xl/worksheets/sheet5.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml`"/><Override PartName=`"/xl/styles.xml`" ContentType=`"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml`"/></Types>"

New-Item -ItemType Directory -Force -Path (Split-Path $OutPath -Parent) | Out-Null
$tmp = [System.IO.Path]::GetTempFileName()
Remove-Item $tmp -Force
[System.IO.Compression.ZipFile]::Open($tmp, [System.IO.Compression.ZipArchiveMode]::Create) | ForEach-Object {
  $zip = $_
  ($zip.CreateEntry("[Content_Types].xml").Open()) | ForEach-Object { $w = New-Object IO.StreamWriter($_); $w.Write($contentTypes); $w.Dispose() }
  ($zip.CreateEntry("_rels/.rels").Open()) | ForEach-Object { $w = New-Object IO.StreamWriter($_); $w.Write($rootRels); $w.Dispose() }
  ($zip.CreateEntry("xl/workbook.xml").Open()) | ForEach-Object { $w = New-Object IO.StreamWriter($_); $w.Write($workbookXml); $w.Dispose() }
  ($zip.CreateEntry("xl/_rels/workbook.xml.rels").Open()) | ForEach-Object { $w = New-Object IO.StreamWriter($_); $w.Write($workbookRels); $w.Dispose() }
  ($zip.CreateEntry("xl/styles.xml").Open()) | ForEach-Object { $w = New-Object IO.StreamWriter($_); $w.Write($stylesXml); $w.Dispose() }
  for ($si=0; $si -lt $sheetXmls.Count; $si++) {
    ($zip.CreateEntry("xl/worksheets/sheet$($si+1).xml").Open()) | ForEach-Object { $w = New-Object IO.StreamWriter($_); $w.Write($sheetXmls[$si]); $w.Dispose() }
  }
  $zip.Dispose()
}
Copy-Item $tmp $OutPath -Force
Write-Output (Resolve-Path $OutPath)