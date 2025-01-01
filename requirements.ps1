# Define variables
$mediaInfoUrl = "https://mediaarea.net/download/binary/mediainfo/23.09/MediaInfo_CLI_23.09_Windows_x64.zip"
$mediaInfoTempPath = "$env:TEMP\mediainfo-cli.zip"
$mediaInfoExtractPath = "$env:TEMP\mediainfo-cli"
$mediaInfoInstallPath = "C:\bin\mediainfo-cli"

$pythonUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
$pythonInstallerPath = "$env:TEMP\python-3.12.0-amd64.exe"

$ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$ffmpegTempPath = "$env:TEMP\ffmpeg.zip"
$ffmpegExtractPath = "$env:TEMP\ffmpeg"
$ffmpegInstallPath = "C:\bin\ffmpeg"

# Get the directory of the current script
$currentScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementsFilePath = "$currentScriptPath\requirements.txt"

# Function to download a file
function Download-File {
    param (
        [string]$url,
        [string]$destination
    )
    Write-Host "Downloading $url to $destination..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $url -OutFile $destination
}

# Function to extract a ZIP file
function Extract-Zip {
    param (
        [string]$zipPath,
        [string]$destination
    )
    Write-Host "Extracting $zipPath to $destination..." -ForegroundColor Cyan
    Expand-Archive -Path $zipPath -DestinationPath $destination -Force
}

# Function to add a directory to PATH
function Add-To-Path {
    param (
        [string]$directory
    )
    Write-Host "Adding $directory to PATH..." -ForegroundColor Cyan
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$directory", [EnvironmentVariableTarget]::Machine)
}

# Step 1: Install MediaInfo CLI
Write-Host "Installing MediaInfo CLI..." -ForegroundColor Yellow
Download-File -url $mediaInfoUrl -destination $mediaInfoTempPath
Expand-Archive -Path $mediaInfoTempPath -DestinationPath $mediaInfoExtractPath -Force
New-Item -ItemType Directory -Path $mediaInfoInstallPath -Force | Out-Null
Move-Item -Path "$mediaInfoExtractPath\*" -Destination $mediaInfoInstallPath -Force
Add-To-Path -directory $mediaInfoInstallPath
Remove-Item -Path $mediaInfoTempPath, $mediaInfoExtractPath -Recurse -Force

# Verify MediaInfo CLI installation
Write-Host "Verifying MediaInfo CLI installation..." -ForegroundColor Cyan
try {
    $result = & mediainfo --version
    Write-Host "MediaInfo CLI is successfully installed and available in PATH!" -ForegroundColor Green
    Write-Host $result
} catch {
    Write-Host "MediaInfo CLI installation failed or is not in PATH. Please check the steps." -ForegroundColor Red
}

# Step 2: Install Python 3.12
Write-Host "Installing Python 3.12..." -ForegroundColor Yellow
Download-File -url $pythonUrl -destination $pythonInstallerPath
Write-Host "Running Python installer..." -ForegroundColor Cyan
Start-Process -FilePath $pythonInstallerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
Remove-Item -Path $pythonInstallerPath -Force

# Verify Python installation
Write-Host "Verifying Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = & python --version
    Write-Host "Python is successfully installed!" -ForegroundColor Green
    Write-Host $pythonVersion
} catch {
    Write-Host "Python installation failed or is not in PATH. Please check the steps." -ForegroundColor Red
}

# Step 3: Install FFmpeg
Write-Host "Installing FFmpeg..." -ForegroundColor Yellow

try {
    # Download FFmpeg
    Download-File -url $ffmpegUrl -destination $ffmpegTempPath

    # Extract FFmpeg
    Write-Host "Extracting FFmpeg..." -ForegroundColor Cyan
    Extract-Zip -zipPath $ffmpegTempPath -destination $ffmpegExtractPath

    # Ensure we locate the correct extracted folder
    $ffmpegExtractedFolder = Get-ChildItem -Path $ffmpegExtractPath | Where-Object { $_.PSIsContainer -and $_.Name -match "ffmpeg" } | Select-Object -First 1

    if ($null -eq $ffmpegExtractedFolder) {
        Write-Host "Failed to find the extracted FFmpeg folder." -ForegroundColor Red
        throw "FFmpeg extraction failed."
    }

    # Move FFmpeg files to the install directory
    Write-Host "Moving FFmpeg files to $ffmpegInstallPath..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $ffmpegInstallPath -Force | Out-Null
    Move-Item -Path "$($ffmpegExtractedFolder.FullName)\*" -Destination $ffmpegInstallPath -Force

    # Add to PATH
    Add-To-Path -directory $ffmpegInstallPath

    # Cleanup
    Write-Host "Cleaning up temporary files..." -ForegroundColor Cyan
    Remove-Item -Path $ffmpegTempPath, $ffmpegExtractPath -Recurse -Force

    # Verify installation
    Write-Host "Verifying FFmpeg installation..." -ForegroundColor Cyan
    $ffmpegVersion = & ffmpeg -version
    Write-Host "FFmpeg is successfully installed and available in PATH!" -ForegroundColor Green
    Write-Host $ffmpegVersion
} catch {
    Write-Host "An error occurred during FFmpeg installation: $($_.Exception.Message)" -ForegroundColor Red
}

# Step 4: Install requirements from requirements.txt
Write-Host "Installing requirements from requirements.txt..." -ForegroundColor Yellow
if (Test-Path $requirementsFilePath) {
    try {
        & python -m pip install --upgrade pip
        & python -m pip install -r $requirementsFilePath
        Write-Host "Requirements installed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install requirements. Please check the requirements.txt file." -ForegroundColor Red
    }
} else {
    Write-Host "requirements.txt not found in the script directory. Skipping this step." -ForegroundColor Red
}
