$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

Write-Host "Usando Python: $Python"

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

& $Python -m py_compile `
    desktop_app.py `
    desktop/main_window.py `
    desktop/theme.py `
    desktop/widgets.py `
    desktop/views/gestion_gastos_view.py `
    desktop/views/aprendizaje_historico_view.py `
    desktop/views/analisis_agente_view.py `
    desktop/views/caja_blanca_view.py `
    desktop/controllers/gastos_controller.py `
    desktop/controllers/historico_controller.py `
    desktop/controllers/analisis_controller.py `
    desktop/controllers/caja_blanca_controller.py

& $Python -m unittest discover -s tests -v

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --windowed `
    --name AntCluster `
    --specpath build `
    --add-data "desktop;desktop" `
    --add-data "src;src" `
    --add-data "data;data" `
    --collect-submodules sklearn `
    --collect-submodules scipy `
    --collect-data matplotlib `
    desktop_app.py

$DistRoot = Join-Path $ProjectRoot "dist\AntCluster"
$DistData = Join-Path $DistRoot "data"
$SourceData = Join-Path $ProjectRoot "data"
$ReadmeSource = Join-Path $ProjectRoot "README_EJECUCION.txt"
$ReadmeTarget = Join-Path $DistRoot "README_EJECUCION.txt"

if (!(Test-Path $DistRoot)) {
    throw "No se encontro la carpeta esperada: $DistRoot"
}

$ResolvedDistRoot = (Resolve-Path $DistRoot).Path
if (Test-Path $DistData) {
    $ResolvedDistData = (Resolve-Path $DistData).Path
    if (!$ResolvedDistData.StartsWith($ResolvedDistRoot)) {
        throw "Ruta data fuera de dist: $ResolvedDistData"
    }
    Remove-Item -LiteralPath $ResolvedDistData -Recurse -Force
}

Copy-Item -LiteralPath $SourceData -Destination $DistData -Recurse
Copy-Item -LiteralPath $ReadmeSource -Destination $ReadmeTarget -Force

Write-Host "Build completado: dist\AntCluster\AntCluster.exe"
Write-Host "Para entregar en CD, copie la carpeta dist\AntCluster completa."
