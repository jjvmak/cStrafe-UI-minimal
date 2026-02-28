$ErrorActionPreference = 'Stop'

Write-Host "Starting Windows build script"

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

$addData = "images;images"
pyinstaller --noconfirm --onedir --noconsole --name "cStrafe_UI" --add-data $addData main.py

Write-Host "Build finished. Expected exe: dist\cStrafe_UI\cStrafe_UI.exe"
