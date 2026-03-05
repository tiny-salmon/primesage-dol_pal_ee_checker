@echo off
chcp 65001 >nul
title 프라임세이지 돌팔이체커 — EXE 빌드

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   프라임세이지 돌팔이체커  EXE 빌드      ║
echo  ╚══════════════════════════════════════════╝
echo.

:: ── Python 확인 ──────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [오류] Python이 설치되지 않았습니다.
    echo         https://python.org 에서 설치 후 "Add to PATH" 를 체크하세요.
    pause & exit /b 1
)

:: ── PyInstaller 설치 확인 ────────────────────
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  PyInstaller 설치 중...
    pip install pyinstaller --quiet
)

:: ── 빌드 실행 ────────────────────────────────
echo  빌드 시작합니다. 1~3분 정도 소요됩니다...
echo.

if exist ico.ico (
    set ICON_OPT=--icon=ico.ico
    pyinstaller --onefile --windowed --name "프라임세이지_돌팔이체커" --icon=ico.ico --add-data "ico.ico;." pc_price_checker.py
) else (
    echo  [주의] ico.ico 파일이 없어 기본 아이콘으로 빌드합니다.
    pyinstaller --onefile --windowed --name "프라임세이지_돌팔이체커" pc_price_checker.py
)

if errorlevel 1 (
    echo.
    echo  [오류] 빌드 실패. 위 오류 메시지를 확인하세요.
    pause & exit /b 1
)

:: ── 바탕화면에 복사 ──────────────────────────
echo.
echo  바탕화면에 복사 중...

set DESKTOP=%USERPROFILE%\Desktop
set EXE_SRC=dist\프라임세이지_돌팔이체커.exe
set EXE_DST=%DESKTOP%\프라임세이지_돌팔이체커.exe

if exist "%EXE_SRC%" (
    copy /y "%EXE_SRC%" "%EXE_DST%" >nul
    echo  [완료] 바탕화면에 복사됐습니다!
    echo         위치: %EXE_DST%
) else (
    echo  [주의] dist 폴더에서 exe를 찾지 못했습니다.
)

:: ── dist 폴더 탐색기로 열기 ──────────────────
echo.
echo  빌드 완료! dist 폴더를 엽니다...
timeout /t 2 /nobreak >nul
explorer dist

echo.
echo  ※ 배포 시 이 파일 하나만 전달하면 됩니다:
echo     프라임세이지_돌팔이체커.exe
echo.
pause