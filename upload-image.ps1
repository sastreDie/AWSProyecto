# Upload Image Script
# Replace these values:
$API_ENDPOINT = "https://8nrciibxkh.execute-api.us-east-1.amazonaws.com/prod"
$ID_TOKEN = "eyJraWQiOiJ0cVZZNjQ2d2RMMHk5TDRJYnA1dDhUR2lcL0s2amoxUzVuT1MyOVJyMXg0ST0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI0NDk4YzRjOC1kMDIxLTcwMjYtOWVjYy1hMDQ5YTQ1MmRmODQiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9iSDlOaklPNVciLCJjb2duaXRvOnVzZXJuYW1lIjoiNDQ5OGM0YzgtZDAyMS03MDI2LTllY2MtYTA0OWE0NTJkZjg0Iiwib3JpZ2luX2p0aSI6ImUzYWY1MTZjLTRiOTUtNDZiYS05NTI5LWQ4NzQxMDI2ZWYxNCIsImF1ZCI6IjNvaTFzZnM2N201dGQwMmowdHFja2pmbHY5IiwiZXZlbnRfaWQiOiJjODFiOGNlOS0xZDkzLTRiOGQtYWY1YS04MTE2Y2U4NmQ3NWQiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTc2NDIxMDIzMywiZXhwIjoxNzY0MjEzODMzLCJpYXQiOjE3NjQyMTAyMzMsImp0aSI6IjhjMzRlYmEzLWUzNmQtNGE2Zi1hNDU3LTQ2ZTIzNWNkYzVkYiIsImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20ifQ.U4y38b_rA612Z-C-0sdPciDgyK9ExxRZTEP5Hd8Z8hMcyIqpJ2-h1ep2Hd3TqScDjr-t1QdVQeJxLrXAgPtigAYe7qbRF-4dedDrrxd-p4WzS__r2mcMV8TjOPirdbbqUu--839O_Ql70R0ztqT3LdhT0xFH3Hko5KnsjsWmopR8CUC2Q3YZIfhKqSRQAxTmZGb-bLqKh1W1-mp-TQp-VL3tAb3UFhLaqTQfLT7nNm7gqg4FTMJcxSs1DYog2CVpDEjVGF0JecEvBBASAx-72Qp5tmOZoUfKF5LuxpDJQOJAjJVKku0ng-khzAeklp2-wfNERqqriC7sqLrT1RwjBQ"
$IMAGE_PATH = "Gemini_Generated_Image_uinx1euinx1euinx.png"  # Put your image path here

# Convert image to base64
Write-Host "Converting image to base64..." -ForegroundColor Cyan
$imageBytes = [System.IO.File]::ReadAllBytes($IMAGE_PATH)
$base64Image = [System.Convert]::ToBase64String($imageBytes)
$filename = Split-Path $IMAGE_PATH -Leaf

Write-Host "Image size: $($imageBytes.Length) bytes" -ForegroundColor Yellow
Write-Host "Filename: $filename" -ForegroundColor Yellow

# Prepare request
$headers = @{
    "Authorization" = $ID_TOKEN
    "Content-Type" = "application/json"
}

$uploadBody = @{
    image = $base64Image
    filename = $filename
    game_title = "ACME Labs"
    description = "Screenshot from game level 3-2"
} | ConvertTo-Json

# Upload
Write-Host "`nUploading to API..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$API_ENDPOINT/upload" -Method POST -Headers $headers -Body $uploadBody
    Write-Host "Success!" -ForegroundColor Green
    Write-Host "Screenshot ID: $($response.screenshot_id)" -ForegroundColor Green
    Write-Host "Status: $($response.status)" -ForegroundColor Green
    $response | ConvertTo-Json
} catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}
