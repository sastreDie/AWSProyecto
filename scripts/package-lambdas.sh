#!/bin/bash
# Script para empaquetar funciones Lambda

set -e

echo "Empaquetando funciones Lambda..."

# Crear directorio de salida
mkdir -p dist/lambda

# Empaquetar Image Uploader
echo "Empaquetando image_uploader..."
cd src/lambda
zip -r ../../dist/lambda/image_uploader.zip image_uploader.py
cd ../..

# Empaquetar Profanity Filter
echo "Empaquetando profanity_filter..."
cd src/lambda
zip -r ../../dist/lambda/profanity_filter.zip profanity_filter.py
cd ../..

# Empaquetar Image Retrieval
echo "Empaquetando image_retrieval..."
cd src/lambda
zip -r ../../dist/lambda/image_retrieval.zip image_retrieval.py
cd ../..

echo "✓ Empaquetado completo. Archivos en dist/lambda/"
echo ""
echo "Archivos generados:"
ls -lh dist/lambda/

echo ""
echo "Para subir a S3, ejecuta:"
echo "aws s3 cp dist/lambda/ s3://YOUR-BUCKET/lambda/ --recursive"
