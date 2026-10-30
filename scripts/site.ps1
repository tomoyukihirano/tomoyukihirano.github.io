#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('Setup', 'Validate', 'Build', 'Preview')]
    [string]$Task = 'Validate',

    [ValidateRange(1024, 65535)]
    [int]$Port = 4000
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$rubyDir = Join-Path $root '.tools/ruby33'
$ruby = Join-Path $rubyDir 'bin/ruby.exe'
$bundle = Join-Path $rubyDir 'bin/bundle'
$bundlerVersion = '2.5.22'
$savedEnvironment = @{}
$environmentNames = @('PATH', 'RUBYOPT', 'JEKYLL_ENV', 'PAGES_REPO_NWO',
    'BUNDLE_GEMFILE', 'BUNDLE_PATH', 'BUNDLE_APP_CONFIG', 'BUNDLE_USER_HOME', 'BUNDLE_FROZEN')

function Invoke-Ruby {
    param([string[]]$RubyArguments)
    & $ruby @RubyArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Ruby command failed (exit $LASTEXITCODE): $($RubyArguments -join ' ')"
    }
}

function Invoke-Bundle {
    param([string[]]$BundleArguments)
    Invoke-Ruby -RubyArguments (@($bundle, "_${bundlerVersion}_") + $BundleArguments)
}

Push-Location $root
try {
    foreach ($name in $environmentNames) {
        $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }

    if ($Task -eq 'Setup') {
        if (-not (Test-Path -LiteralPath $ruby)) {
            $downloadDir = Join-Path $root '.tools/downloads'
            New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
            $installer = Join-Path $downloadDir 'rubyinstaller-devkit-3.3.13-1-x64.exe'
            $sha256 = 'a37f6b5ac644b691b42d3fef40af7e9661b506b09f5506330271caae69ccbd15'
            if (-not (Test-Path -LiteralPath $installer)) {
                Write-Host 'Downloading official RubyInstaller+Devkit 3.3.13-1 (x64)...'
                Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/oneclick/rubyinstaller2/releases/download/RubyInstaller-3.3.13-1/rubyinstaller-devkit-3.3.13-1-x64.exe' -OutFile $installer
            }
            if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash -ne $sha256) {
                throw "RubyInstaller SHA256 mismatch. Remove $installer and retry Setup."
            }
            $process = Start-Process -FilePath $installer -ArgumentList @(
                '/verysilent', '/currentuser', '/norestart', '/noicons',
                '/components=ruby,msys2', '/tasks=noassocfiles,nomodpath,noridkinstall',
                ('/dir="{0}"' -f $rubyDir)
            ) -WindowStyle Hidden -Wait -PassThru
            if ($process.ExitCode -ne 0) {
                throw "RubyInstaller failed (exit $($process.ExitCode))."
            }
        }
    }

    if (-not (Test-Path -LiteralPath $ruby)) {
        throw 'Run .\scripts\site.ps1 Setup first to install the project Ruby and gems.'
    }

    $env:PATH = (Join-Path $rubyDir 'bin') + ';' + $env:PATH
    $env:RUBYOPT = '-EUTF-8:UTF-8'
    $env:BUNDLE_GEMFILE = Join-Path $root 'Gemfile'
    $env:BUNDLE_PATH = Join-Path $root 'vendor/bundle'
    $env:BUNDLE_APP_CONFIG = Join-Path $root '.bundle'
    $env:BUNDLE_USER_HOME = Join-Path $root '.bundle/user'
    $env:BUNDLE_FROZEN = 'true'
    $env:PAGES_REPO_NWO = 'tomoyukihirano/tomoyukihirano.github.io'

    $expectedRuby = (Get-Content -LiteralPath (Join-Path $root '.ruby-version') -Raw).Trim()
    $actualRuby = & $ruby -e 'print RUBY_VERSION'
    if ($LASTEXITCODE -ne 0 -or $actualRuby -ne $expectedRuby) {
        throw "Expected Ruby $expectedRuby; found $actualRuby. Check .tools/ruby33."
    }

    if ($Task -eq 'Setup') {
        $devkitMarker = Join-Path $rubyDir '.devkit-initialized'
        if (-not (Test-Path -LiteralPath $devkitMarker)) {
            & (Join-Path $rubyDir 'bin/ridk.cmd') install 1
            if ($LASTEXITCODE -ne 0) { throw 'MSYS2 initialization failed.' }
            New-Item -ItemType File -Path $devkitMarker -Force | Out-Null
        }
        # Use the bundled version when present; otherwise install only this version.
        & $ruby $bundle "_${bundlerVersion}_" --version
        if ($LASTEXITCODE -ne 0) {
            Invoke-Ruby -RubyArguments @((Join-Path $rubyDir 'bin/gem'), 'install',
                'bundler', '--version', $bundlerVersion, '--no-document')
        }
        Invoke-Bundle -BundleArguments @('install')
        Write-Host 'Setup complete. Run .\scripts\site.ps1 Validate, then .\scripts\site.ps1 Preview.'
    }
    else {
        Invoke-Bundle -BundleArguments @('check')
        if ($Task -eq 'Preview') {
            $env:JEKYLL_ENV = 'development'
            Write-Host "Preview: http://127.0.0.1:$Port/ (Ctrl+C to stop)"
            # Polling avoids the optional native wdm watcher on Windows.
            Invoke-Bundle -BundleArguments @('exec', 'jekyll', 'serve', '--host', '127.0.0.1',
                '--port', "$Port", '--force_polling', '--source', $root,
                '--destination', (Join-Path $root '_site-preview'))
        }
        else {
            $env:JEKYLL_ENV = 'production'
            # Same build entry point as actions/jekyll-build-pages@v1.
            Invoke-Bundle -BundleArguments @('exec', 'github-pages', 'build',
                '--source', $root, '--destination', (Join-Path $root '_site'))
            Write-Host 'GitHub Pages-compatible Jekyll build succeeded: _site/'
        }
    }
}
finally {
    foreach ($name in $environmentNames) {
        if ($null -eq $savedEnvironment[$name]) {
            Remove-Item -LiteralPath "Env:$name" -ErrorAction SilentlyContinue
        }
        else {
            [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], 'Process')
        }
    }
    Pop-Location
}
