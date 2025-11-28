# Test Upload with Real Image
$API_ENDPOINT = "https://8nrciibxkh.execute-api.us-east-1.amazonaws.com/prod"
$ID_TOKEN = "eyJraWQiOiJ0cVZZNjQ2d2RMMHk5TDRJYnA1dDhUR2lcL0s2amoxUzVuT1MyOVJyMXg0ST0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI0NDk4YzRjOC1kMDIxLTcwMjYtOWVjYy1hMDQ5YTQ1MmRmODQiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9iSDlOaklPNVciLCJjb2duaXRvOnVzZXJuYW1lIjoiNDQ5OGM0YzgtZDAyMS03MDI2LTllY2MtYTA0OWE0NTJkZjg0Iiwib3JpZ2luX2p0aSI6IjE2MGIzZDdkLWEzNGYtNGQyMi04NDMzLTg5NGYyNTFjZTk4ZCIsImF1ZCI6IjNvaTFzZnM2N201dGQwMmowdHFja2pmbHY5IiwiZXZlbnRfaWQiOiJlZWI1OTcwZS0xOWM2LTQ5ZDctYmExMC1kMjRmZjA1OTI2N2YiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTc2NDI5NTkzMywiZXhwIjoxNzY0Mjk5NTMzLCJpYXQiOjE3NjQyOTU5MzMsImp0aSI6Ijg1Y2E0YzFlLWZkZWYtNDZiOC04ZmVhLWQxOTM3NGY2MjZkYiIsImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20ifQ.PM8cProGBLx9EprgBcjynA1u6FSewZiuJ4xjIpF4T1mO2poQGSzFAIB1cYjABuN-TuK6m254958U08hONuhwjbX83btUzTihlVsB6thc9Vx1InzfzzYwxyXSgQjHevYTmMILWh8vwhiDWAO9-inuSTICmDmLUa6BL6GM3cKTwK77k9alw72pBaa5nEEYBDtaBtn2emqJ-gVzAfGbEWR07at_44oYi89bX1a01J2WIM5FduxfL4pgJxztAkSKCTuS_XNQprG-Cb2cmT_83gud8F5Tr-bwr2XVZADyMivss5Yw3gEBrv2bbqoCqaB_O02s1zk71uC3XucFbTUpyNTiMg"
$IMAGE_PATH = "WhatsApp Image 2025-11-27 at 8.50.50 PM.jpeg"

$headers = @{
    "Authorization" = $ID_TOKEN
    "Content-Type" = "application/json"
}

Write-Host "=== Testing Upload with Gemini Image ===" -ForegroundColor Cyan

# Convert image to base64
Write-Host "Converting image to base64..." -ForegroundColor Yellow
$imageBytes = [System.IO.File]::ReadAllBytes($IMAGE_PATH)
$base64Image = [System.Convert]::ToBase64String($imageBytes)
Write-Host "Image size: $($imageBytes.Length) bytes ($([math]::Round($imageBytes.Length/1MB, 2)) MB)" -ForegroundColor Yellow

$uploadBody = @{
    image = $base64Image
    filename = "gemini-test.png"
    game_title = "Gemini Generated"
    description = "Testing with Gemini generated image"
} | ConvertTo-Json

Write-Host "Uploading..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API_ENDPOINT/upload" -Method POST -Headers $headers -Body $uploadBody -TimeoutSec 30
    Write-Host "SUCCESS!" -ForegroundColor Green
    Write-Host "Screenshot ID: $($response.screenshot_id)" -ForegroundColor Green
    $response | ConvertTo-Json
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}
