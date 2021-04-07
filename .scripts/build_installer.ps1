$url = "https://github.com/CatxFish/obs-virtual-cam/releases/download/2.0.4/OBS-VirtualCam2.0.4.zip"
$filename = Split-Path $url -leaf
$filename_no_ext = Split-Path $url -leafbase
$out_dir = ".\build"
$dll_name = "obs-virtualsource.dll"

Write-Host "Creating build directory if it does not already exist"
$null = New-Item $out_dir -ItemType Directory -Force

Write-Host "Downloading $filename_no_ext from $url"
$ProgressPreference = 'SilentlyContinue' # Hide download progress bar
Invoke-WebRequest $url -OutFile "$out_dir\$filename"
$ProgressPreference = 'Continue' # Restore download progress bar

Write-Host "Extracting archive $out_dir\$filename"
7z.exe x -r -aoa -o"$out_dir" "$out_dir\$filename"

iscc.exe "setup.iss" @args
