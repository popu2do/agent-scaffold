param(
    [string]$Range,

    [string]$StartRef,

    [string]$EndRef = "HEAD",

    [string]$StartMarker,

    [switch]$IncludeMerges
)

$ErrorActionPreference = "Stop"

$inside = git rev-parse --is-inside-work-tree 2>$null
if (($LASTEXITCODE -ne 0) -or ($inside.Trim() -ne "true")) {
    throw "Current directory is not inside a git repository."
}

$repoRoot = (git rev-parse --show-toplevel).Trim()

function Resolve-Commit {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value,

        [switch]$AllowSubjectMatch
    )

    $oldNativePref = $global:PSNativeCommandUseErrorActionPreference
    $oldErrorPreference = $ErrorActionPreference
    try {
        $global:PSNativeCommandUseErrorActionPreference = $false
        $ErrorActionPreference = "Continue"
        $resolved = git rev-parse --verify "$Value^{commit}" 2>$null
    }
    finally {
        $global:PSNativeCommandUseErrorActionPreference = $oldNativePref
        $ErrorActionPreference = $oldErrorPreference
    }
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
        return $resolved.Trim()
    }

    if ($AllowSubjectMatch) {
        $oldNativePref = $global:PSNativeCommandUseErrorActionPreference
        $oldErrorPreference = $ErrorActionPreference
        try {
            $global:PSNativeCommandUseErrorActionPreference = $false
            $ErrorActionPreference = "Continue"
            $match = git log --all --grep="$Value" --format=%H -n 1
        }
        finally {
            $global:PSNativeCommandUseErrorActionPreference = $oldNativePref
            $ErrorActionPreference = $oldErrorPreference
        }
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($match)) {
            return $match.Trim()
        }
    }

    throw "Unable to resolve commit boundary from '$Value'."
}

function Test-IsAncestor {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ancestor,

        [Parameter(Mandatory = $true)]
        [string]$Descendant
    )

    $oldNativePref = $global:PSNativeCommandUseErrorActionPreference
    $oldErrorPreference = $ErrorActionPreference
    try {
        $global:PSNativeCommandUseErrorActionPreference = $false
        $ErrorActionPreference = "Continue"
        git merge-base --is-ancestor $Ancestor $Descendant 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    }
    finally {
        $global:PSNativeCommandUseErrorActionPreference = $oldNativePref
        $ErrorActionPreference = $oldErrorPreference
    }
}

function Resolve-MarkerCommit {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Marker,

        [Parameter(Mandatory = $true)]
        [string]$EndCommit
    )

    try {
        $directCommit = Resolve-Commit -Value $Marker
        if (Test-IsAncestor -Ancestor $directCommit -Descendant $EndCommit) {
            return $directCommit
        }
    }
    catch {
    }

    $searchPlans = @(
        @("log", "--first-parent", "--grep=$Marker", "--regexp-ignore-case", "--format=%H`t%s", $EndCommit),
        @("log", "--grep=$Marker", "--regexp-ignore-case", "--format=%H`t%s", $EndCommit)
    )

    foreach ($plan in $searchPlans) {
        $oldNativePref = $global:PSNativeCommandUseErrorActionPreference
        $oldErrorPreference = $ErrorActionPreference
        try {
            $global:PSNativeCommandUseErrorActionPreference = $false
            $ErrorActionPreference = "Continue"
            $matches = git @plan
        }
        finally {
            $global:PSNativeCommandUseErrorActionPreference = $oldNativePref
            $ErrorActionPreference = $oldErrorPreference
        }

        foreach ($line in ($matches -split "`r?`n")) {
            if ([string]::IsNullOrWhiteSpace($line)) {
                continue
            }

            $parts = $line -split "`t", 2
            if ($parts.Count -lt 1) {
                continue
            }

            $candidate = $parts[0].Trim()
            if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-IsAncestor -Ancestor $candidate -Descendant $EndCommit)) {
                return $candidate
            }
        }
    }

    throw "Unable to resolve marker '$Marker' on the history leading to '$EndCommit'."
}

if ([string]::IsNullOrWhiteSpace($Range)) {
    $endCommit = Resolve-Commit -Value $EndRef

    if (-not [string]::IsNullOrWhiteSpace($StartRef)) {
        $startCommit = Resolve-Commit -Value $StartRef
    }
    elseif (-not [string]::IsNullOrWhiteSpace($StartMarker)) {
        $startCommit = Resolve-MarkerCommit -Marker $StartMarker -EndCommit $endCommit
    }
    else {
        throw "Provide -Range, or provide -StartRef / -StartMarker together with optional -EndRef."
    }

    if (-not (Test-IsAncestor -Ancestor $startCommit -Descendant $endCommit)) {
        throw "Resolved start boundary '$startCommit' is not an ancestor of '$endCommit'. Provide -Range explicitly for cross-branch comparisons."
    }

    $Range = "$startCommit..$endCommit"
}

$logArgs = @(
    "log",
    "--date=short",
    "--pretty=format:%H`t%h`t%ad`t%s"
)

if (-not $IncludeMerges) {
    $logArgs += "--no-merges"
}

$logArgs += $Range

$rawCommits = git @logArgs
$commits = @()

foreach ($line in ($rawCommits -split "`r?`n")) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $parts = $line -split "`t", 4
    if ($parts.Count -lt 4) {
        continue
    }

    $changedFiles = git show --name-only --format="" $parts[0]
    $statLines = git show --stat --format="" $parts[0]

    $commits += [pscustomobject]@{
        fullHash  = $parts[0]
        shortHash = $parts[1]
        date      = $parts[2]
        subject   = $parts[3]
        changedFiles = @($changedFiles | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        statLines = @($statLines | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    }
}

$diffStat = (git diff --stat $Range) -join "`n"
$files = git diff --name-only $Range

[pscustomobject]@{
    repoRoot    = $repoRoot
    range       = $Range
    commitCount = $commits.Count
    commits     = $commits
    diffStat    = $diffStat
    files       = $files
} | ConvertTo-Json -Depth 6
