# Upload Image Script v2 - Using Pre-signed URLs
# Replace these values:
$API_ENDPOINT = "https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod"
$ID_TOKEN = "YOUR-ID-TOKEN-HERE"
$IMAGE_PATH = "path\to\your\image.png"  # Put your image path here

$filename = Split-Path $IMAGE_PATH -Leaf
$extension = $filename.Split('.')[-1].ToLower()

# Determine content type
$contentType = switch ($extension) {
    "jpg"  { "image/jpeg" }
    "jpeg" { "image/jpeg" }
    "png"  { "image/png" }
    "gif"  { "image/gif" }
    "webp" { "image/webp" }
    default { "image/png" }
}

Write-Host "=== Upload Image v2 (Pre-signed URL) ===" -ForegroundColor Cyan
Write-Host "File: $filename" -ForegroundColor Yellow
Write-Host "Content-Type: $contentType" -ForegroundColor Yellow

$headers = @{
    "Authorization" = $ID_TOKEN
    "Content-Type" = "application/json"
}

# Step 1: Request pre-signed URL
Write-Host "`nStep 1: Requesting upload URL..." -ForegroundColor Cyan
$requestBody = @{
    filename = $filename
    game_title = "ACME Labs"
    description = "Screenshot from game level 3-2"
    content_type = $contentType
} | ConvertTo-Json

try {
    $urlResponse = Invoke-RestMethod -Uri "$API_ENDPOINT/request-upload" -Method POST -Headers $headers -Body $requestBody
    Write-Host "Success! Screenshot ID: $($urlResponse.screenshot_id)" -ForegroundColor Green
    $screenshotId = $urlResponse.screenshot_id
    $uploadUrl = $urlResponse.upload_url
} catch {
    Write-Host "Error requesting URL: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit
}

# Step 2: Upload file directly to S3
Write-Host "`nStep 2: Uploading file to S3..." -ForegroundColor Cyan
try {
    $imageBytes = [System.IO.File]::ReadAllBytes($IMAGE_PATH)
    Write-Host "File size: $($imageBytes.Length) bytes" -ForegroundColor Yellow
    
    $uploadHeaders = @{
        "Content-Type" = $contentType
    }
    
    Invoke-RestMethod -Uri $uploadUrl -Method PUT -Headers $uploadHeaders -Body $imageBytes -ContentType $contentType
    Write-Host "Success! File uploaded to S3" -ForegroundColor Green
} catch {
    Write-Host "Error uploading to S3: $($_.Exception.Message)" -ForegroundColor Red
    exit
}

# Step 3: Confirm upload and trigger processing
Write-Host "`nStep 3: Confirming upload..." -ForegroundColor Cyan
$confirmBody = @{
    screenshot_id = $screenshotId
} | ConvertTo-Json

try {
    $confirmResponse = Invoke-RestMethod -Uri "$API_ENDPOINT/confirm-upload" -Method POST -Headers $headers -Body $confirmBody
    Write-Host "Success!" -ForegroundColor Green
    Write-Host "Status: $($confirmResponse.status)" -ForegroundColor Green
    Write-Host "Message: $($confirmResponse.message)" -ForegroundColor Green
} catch {
    Write-Host "Error confirming upload: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== Upload Complete ===" -ForegroundColor Cyan
Write-Host "Screenshot ID: $screenshotId" -ForegroundColor Green
