# Upload Image Script
# Replace these values:
$API_ENDPOINT = "https://8nrciibxkh.execute-api.us-east-1.amazonaws.com/prod"
$ID_TOKEN = "eyJraWQiOiJ0cVZZNjQ2d2RMMHk5TDRJYnA1dDhUR2lcL0s2amoxUzVuT1MyOVJyMXg0ST0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI0NDk4YzRjOC1kMDIxLTcwMjYtOWVjYy1hMDQ5YTQ1MmRmODQiLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9iSDlOaklPNVciLCJjb2duaXRvOnVzZXJuYW1lIjoiNDQ5OGM0YzgtZDAyMS03MDI2LTllY2MtYTA0OWE0NTJkZjg0Iiwib3JpZ2luX2p0aSI6ImFiNzI3YzIzLTliMzktNDJmNy1hNWZmLWY5MGYxZTJiZGI5YiIsImF1ZCI6IjNvaTFzZnM2N201dGQwMmowdHFja2pmbHY5IiwiZXZlbnRfaWQiOiI4NmEwNzgzNS1kYzMzLTQ0Y2YtOWYwMC1lYWM1YmRlZDM3OGEiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTc2NDI2NTgyNywiZXhwIjoxNzY0MjY5NDI3LCJpYXQiOjE3NjQyNjU4MjcsImp0aSI6IjljMmQ3MGZhLWRiNDQtNGQyMi1iNWNjLWRjZmY3NGUyMGJkYyIsImVtYWlsIjoidGVzdHVzZXJAZXhhbXBsZS5jb20ifQ.MSHMsuyDD_rdOKak3HqxYUVNiTXXfxVrc5lXje7BJWoXBmW8kuCBORYPnkGHLIm_lKGNHIZZ0MOsrxCrEUIuerY89BfGNa7AIQpJk6LWMKgpUcrGRTROw_66qc7tftatrXQt-PcWUKZqdb-tduQnvAkeoWXjB4TorIqBTeh8BvUyl2NUpoLjxgPQnpG1c6PqDkR-fWwCEIkI1pQ2a0oXrV1STC-i6PCtCBFUiOsXmN92hqYg2lrVmt43BS8eiAwZa8PTZkTOzhuVWWV_alEZcHBSk857ySXfG6WcO26NasxSYXOVJib6mgrk3rnPry3yWBwRFCM9Mz5LXJyWqhaMgw"
$IMAGE_PATH = "Gemini_Generated_Image_pkgxzcpkgxzcpkgx.png"  # Put your image path here

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
