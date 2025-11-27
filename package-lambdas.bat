@echo off
REM Script to package Lambda functions

echo Packaging Lambda functions...

REM Create output directory
if not exist dist\lambda mkdir dist\lambda

REM Package Image Uploader
echo Packaging image_uploader...
powershell Compress-Archive -Path src\lambda\image_uploader.py -DestinationPath dist\lambda\image_uploader.zip -Force

REM Package Profanity Filter
echo Packaging profanity_filter...
powershell Compress-Archive -Path src\lambda\profanity_filter.py -DestinationPath dist\lambda\profanity_filter.zip -Force

REM Package Image Retrieval
echo Packaging image_retrieval...
powershell Compress-Archive -Path src\lambda\image_retrieval.py -DestinationPath dist\lambda\image_retrieval.zip -Force

echo.
echo Packaging complete! Files in dist\lambda\
dir dist\lambda

echo.
echo To upload to S3, run:
echo aws s3 cp dist\lambda\ s3://YOUR-BUCKET/lambda/ --recursive
