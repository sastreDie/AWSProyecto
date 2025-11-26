"""
Script para ejecutar todos los tests locales
"""
import subprocess
import sys

tests = [
    'tests/test_image_uploader.py',
    'tests/test_profanity_filter.py',
    'tests/test_image_retrieval.py'
]

print("="*60)
print("🧪 EJECUTANDO TODOS LOS TESTS")
print("="*60)

failed = []
passed = []

for test in tests:
    print(f"\n{'='*60}")
    print(f"Ejecutando: {test}")
    print('='*60)
    
    result = subprocess.run([sys.executable, test], capture_output=False)
    
    if result.returncode == 0:
        passed.append(test)
    else:
        failed.append(test)

print("\n" + "="*60)
print("📊 RESUMEN DE TESTS")
print("="*60)
print(f"✅ Pasados: {len(passed)}/{len(tests)}")
print(f"❌ Fallidos: {len(failed)}/{len(tests)}")

if passed:
    print("\n✅ Tests que pasaron:")
    for test in passed:
        print(f"  - {test}")

if failed:
    print("\n❌ Tests que fallaron:")
    for test in failed:
        print(f"  - {test}")
    sys.exit(1)
else:
    print("\n🎉 TODOS LOS TESTS PASARON!")
    sys.exit(0)
