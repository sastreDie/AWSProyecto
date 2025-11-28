# Get Cognito Token
$USER_POOL_ID = "YOUR-USER-POOL-ID"
$CLIENT_ID = "YOUR-CLIENT-ID"
$USERNAME = "testuser@example.com"
$PASSWORD = "MyPassword123!"

Write-Host "Authenticating..." -ForegroundColor Cyan

$authParams = "USERNAME=$USERNAME,PASSWORD=$PASSWORD"
$response = aws cognito-idp admin-initiate-auth `
    --user-pool-id $USER_POOL_ID `
    --client-id $CLIENT_ID `
    --auth-flow ADMIN_NO_SRP_AUTH `
    --auth-parameters $authParams `
    --output json | ConvertFrom-Json

$idToken = $response.AuthenticationResult.IdToken

Write-Host "`nID Token:" -ForegroundColor Green
Write-Host $idToken

Write-Host "`nCopy this token and use it in your API calls" -ForegroundColor Yellow
