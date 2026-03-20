param(
    [string]$Config = "distractor",
    [string]$Split = "train",
    [int]$MaxRows = 3,
    [switch]$ShowContextText,
    [string]$OutputJsonPath
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$dataset = "hotpotqa/hotpot_qa"
$baseUrl = "https://datasets-server.huggingface.co"

function Get-Json([string]$url) {
    return Invoke-RestMethod -Uri $url -Method Get
}

function Join-SentenceList($sentences) {
    if ($null -eq $sentences) {
        return ""
    }

    return ($sentences | ForEach-Object { $_.ToString().Trim() }) -join " "
}

function Print-Example($row, [int]$index, [switch]$ShowContextText) {
    $example = $row.row
    $supporting = $example.supporting_facts
    $context = $example.context

    Write-Host ""
    Write-Host ("=" * 80)
    Write-Host ("Example #{0}" -f ($index + 1))
    Write-Host ("id: {0}" -f $example.id)
    Write-Host ("type: {0}" -f $example.type)
    Write-Host ("level: {0}" -f $example.level)
    Write-Host ""
    Write-Host ("Question: {0}" -f $example.question)
    Write-Host ("Answer:   {0}" -f $example.answer)
    Write-Host ""

    $supportPairs = @()
    if ($supporting -and $supporting.title -and $supporting.sent_id) {
        for ($i = 0; $i -lt $supporting.title.Count; $i++) {
            $supportPairs += ("- {0} (sentence {1})" -f $supporting.title[$i], $supporting.sent_id[$i])
        }
    }

    Write-Host "Supporting Facts:"
    if ($supportPairs.Count -eq 0) {
        Write-Host "- none"
    } else {
        $supportPairs | ForEach-Object { Write-Host $_ }
    }

    $titles = @()
    if ($context -and $context.title) {
        $titles = @($context.title)
    }

    Write-Host ""
    Write-Host ("Context Paragraphs: {0}" -f $titles.Count)

    if ($titles.Count -gt 0) {
        for ($i = 0; $i -lt $titles.Count; $i++) {
            $sentenceList = @()
            if ($context.sentences -and $context.sentences.Count -gt $i) {
                $sentenceList = @($context.sentences[$i])
            }

            Write-Host ("- [{0}] {1} ({2} sentences)" -f $i, $titles[$i], $sentenceList.Count)

            if ($ShowContextText) {
                $paragraph = Join-SentenceList $sentenceList
                Write-Host ("  {0}" -f $paragraph)
            }
        }
    }
}

$splitsUrl = "$baseUrl/splits?dataset=$([uri]::EscapeDataString($dataset))"
$splitsResponse = Get-Json $splitsUrl

Write-Host ("Dataset: {0}" -f $dataset)
Write-Host "Available configs/splits:"
$splitsResponse.splits |
    Sort-Object config, split |
    ForEach-Object {
        $rowCount = if ($null -ne $_.num_rows -and $_.num_rows -ne "") { $_.num_rows } else { "n/a" }
        Write-Host ("- {0} / {1} ({2} rows)" -f $_.config, $_.split, $rowCount)
    }

$rowsUrl = "$baseUrl/first-rows?dataset=$([uri]::EscapeDataString($dataset))&config=$([uri]::EscapeDataString($Config))&split=$([uri]::EscapeDataString($Split))"
$rowsResponse = Get-Json $rowsUrl

Write-Host ""
Write-Host ("Features for {0}/{1}:" -f $Config, $Split)
$rowsResponse.features | ForEach-Object {
    $typeName = if ($_.type._type) { $_.type._type } elseif ($_.type.dtype) { $_.type.dtype } else { ($_.type | ConvertTo-Json -Compress) }
    Write-Host ("- {0}: {1}" -f $_.name, $typeName)
}

$rows = @($rowsResponse.rows | Select-Object -First $MaxRows)
for ($i = 0; $i -lt $rows.Count; $i++) {
    Print-Example -row $rows[$i] -index $i -ShowContextText:$ShowContextText
}

if ($OutputJsonPath) {
    $rowsResponse | ConvertTo-Json -Depth 20 | Set-Content -Path $OutputJsonPath -Encoding UTF8
    Write-Host ""
    Write-Host ("Saved raw API response to {0}" -f $OutputJsonPath)
}
