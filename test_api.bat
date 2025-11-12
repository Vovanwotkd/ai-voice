@echo off
REM AI Voice Hostess Bot - API Integration Test Script (Windows)
REM Usage: test_api.bat [backend_url]
REM Example: test_api.bat http://localhost:8000

setlocal enabledelayedexpansion

set BACKEND_URL=%1
if "%BACKEND_URL%"=="" set BACKEND_URL=http://localhost:8000

echo ===========================================
echo AI Voice Hostess Bot - API Tests
echo ===========================================
echo Backend URL: %BACKEND_URL%
echo.

set TESTS_PASSED=0
set TESTS_FAILED=0

REM Test 1: Health check
echo [TEST 1] Testing: Health check...
curl -s -o response.json -w "%%{http_code}" %BACKEND_URL%/api/health > status.txt
set /p STATUS=<status.txt
if !STATUS! GEQ 200 if !STATUS! LSS 300 (
    echo [PASS] Health check - HTTP !STATUS!
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Health check - HTTP !STATUS!
    set /a TESTS_FAILED+=1
)
echo.

REM Test 2: Database health check
echo [TEST 2] Testing: Database health check...
curl -s -o response.json -w "%%{http_code}" %BACKEND_URL%/api/health/db > status.txt
set /p STATUS=<status.txt
if !STATUS! GEQ 200 if !STATUS! LSS 300 (
    echo [PASS] Database health check - HTTP !STATUS!
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Database health check - HTTP !STATUS!
    set /a TESTS_FAILED+=1
)
echo.

REM Test 3: Get all prompts
echo [TEST 3] Testing: Get all prompts...
curl -s -o response.json -w "%%{http_code}" %BACKEND_URL%/api/prompts/ > status.txt
set /p STATUS=<status.txt
if !STATUS! GEQ 200 if !STATUS! LSS 300 (
    echo [PASS] Get all prompts - HTTP !STATUS!
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Get all prompts - HTTP !STATUS!
    set /a TESTS_FAILED+=1
)
echo.

REM Test 4: Get active prompt
echo [TEST 4] Testing: Get active prompt...
curl -s -o response.json -w "%%{http_code}" %BACKEND_URL%/api/prompts/active > status.txt
set /p STATUS=<status.txt
if !STATUS! GEQ 200 if !STATUS! LSS 300 (
    echo [PASS] Get active prompt - HTTP !STATUS!
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Get active prompt - HTTP !STATUS!
    set /a TESTS_FAILED+=1
)
echo.

REM Test 5: Send chat message
echo [TEST 5] Testing: Send chat message (may take a few seconds)...
curl -s -X POST -H "Content-Type: application/json" -d "{\"message\":\"Здравствуйте\",\"conversation_id\":null,\"generate_audio\":false}" -o response.json -w "%%{http_code}" %BACKEND_URL%/api/chat/message > status.txt
set /p STATUS=<status.txt
if !STATUS! GEQ 200 if !STATUS! LSS 300 (
    echo [PASS] Send chat message - HTTP !STATUS!
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Send chat message - HTTP !STATUS!
    set /a TESTS_FAILED+=1
)
echo.

REM Test 6: Get chat history
echo [TEST 6] Testing: Get chat history...
curl -s -o response.json -w "%%{http_code}" "%BACKEND_URL%/api/chat/history?limit=10&offset=0" > status.txt
set /p STATUS=<status.txt
if !STATUS! GEQ 200 if !STATUS! LSS 300 (
    echo [PASS] Get chat history - HTTP !STATUS!
    set /a TESTS_PASSED+=1
) else (
    echo [FAIL] Get chat history - HTTP !STATUS!
    set /a TESTS_FAILED+=1
)
echo.

REM Cleanup
del response.json status.txt 2>nul

REM Summary
echo ===========================================
echo Test Summary
echo ===========================================
echo Passed: !TESTS_PASSED!
echo Failed: !TESTS_FAILED!
echo.

if !TESTS_FAILED! EQU 0 (
    echo All tests passed!
    exit /b 0
) else (
    echo Some tests failed.
    exit /b 1
)
