<#
  抓取 Kirilloid 兵种参数（PowerShell 版）
  从网页与 JS 提取 1.46 版本 1x 兵种数据并写入 JSON。
#>
param()
$ErrorActionPreference = 'Stop'
$baseUrl = 'http://travian.kirilloid.ru'
$troopsUrl = "$baseUrl/troops.php#s=1.46&tribe=1&s_lvl=1&t_lvl=1&unit=1"
$unitsJsUrl = "$baseUrl/js/units.js?d"
$outDir = Join-Path (Split-Path $PSScriptRoot -Parent) '..\backend_py\data'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outPath = Join-Path $outDir 'troops_t4.6_1x.json'

function Fetch($url) { (Invoke-WebRequest -UseBasicParsing $url).Content }
function Jsonize($text) {
  $t = $text
  $t = [regex]::Replace($t, "'(.*?)'", { param($m) ($m.Groups[1].Value | ConvertTo-Json -Compress) })
  $t = [regex]::Replace($t, "([\{,\s,])(\w+):", '$1"$2":')
  $t = [regex]::Replace($t, ",\s*\]", ']')
  $t = [regex]::Replace($t, ",\s*\}", '}')
  $t
}

$html = Fetch $troopsUrl
$namesBlock = [regex]::Match($html, 'names:\s*\[(.*?)\]\s*;', 'Singleline').Groups[1].Value
$names = @()
foreach ($arr in [regex]::Matches($namesBlock, '\[(.*?)\]', 'Singleline')) {
  $items = @()
  foreach ($m in [regex]::Matches($arr.Groups[1].Value, '"(.*?)"')) { $items += $m.Groups[1].Value }
  $names += ,$items
}

$tribeSel = [regex]::Match($html, '<select id=\"tribe\"[\s\S]*?</select>').Value
$tribeLabels = @()
foreach ($m in [regex]::Matches($tribeSel, '<option[^>]*>([^<]+)</option>')) { $tribeLabels += $m.Groups[1].Value }

$js = Fetch $unitsJsUrl
$baseRaw = [regex]::Match($js, 'var\s+units\s*=\s*\[(.*?)]\s*;', 'Singleline').Groups[1].Value
$baseJson = Jsonize("[$baseRaw]") | ConvertFrom-Json
$t4raw = [regex]::Match($js, 'var\s+t4\s*=\s*extend\(units,\s*\[(.*?)]\s*\)\s*;', 'Singleline').Groups[1].Value
$t4mix = $null
if ($t4raw) { $t4mix = (Jsonize("[$t4raw]") | ConvertFrom-Json) }

function DeepExtend($proto, $mixin) {
  $out = @()
  for ($i=0; $i -lt $proto.Count; $i++) {
    $tribe = $proto[$i]
    $tOverride = if ($mixin -and $i -lt $mixin.Count) { $mixin[$i] } else { $null }
    $tribeOut = @()
    for ($u=0; $u -lt $tribe.Count; $u++) {
      $unit = $tribe[$u] | ConvertTo-Json -Compress | ConvertFrom-Json
      if ($tOverride -and $u -lt $tOverride.Count -and ($tOverride[$u] -is [hashtable] -or $tOverride[$u].psobject.Properties.Count -gt 0)) {
        foreach ($p in $tOverride[$u].psobject.Properties) { $unit | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value -Force }
      }
      $tribeOut += ,$unit
    }
    $out += ,$tribeOut
  }
  $out
}

$t4 = DeepExtend $baseJson $t4mix
for ($r=0; $r -lt $t4.Count; $r++) {
  for ($u=0; $u -lt $t4[$r].Count; $u++) {
    $unit = $t4[$r][$u] | ConvertTo-Json -Compress | ConvertFrom-Json
    $unit | Add-Member -NotePropertyName tribeId -NotePropertyValue ($r + 1) -Force
    $unit | Add-Member -NotePropertyName unitId -NotePropertyValue ($u + 1) -Force
    $nm = if ($r -lt $names.Count -and $u -lt $names[$r].Count) { $names[$r][$u] } else { '' }
    $unit | Add-Member -NotePropertyName name -NotePropertyValue $nm -Force
    $t4[$r][$u] = $unit
  }
}

$data = [ordered]@{
  version = '1.46'
  speed = '1x'
  tribes = @()
}
for ($r=0; $r -lt $t4.Count; $r++) {
  $label = if ($r -lt $tribeLabels.Count) { $tribeLabels[$r] } else { "tribe_$($r+1)" }
  $data.tribes += ,([ordered]@{ tribeId = $r + 1; tribeLabel = $label; units = $t4[$r] })
}

($data | ConvertTo-Json -Depth 6 -Compress) | Set-Content -Encoding UTF8 $outPath
Write-Output $outPath