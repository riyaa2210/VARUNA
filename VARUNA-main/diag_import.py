import os, sys, traceback, importlib
print('CWD=', os.getcwd())
print('PYTHONEXE=', sys.executable)
print('SYSPATH entries:')
for p in sys.path:
    print(' -', p)
print('\nFILES:')
for f in os.listdir('.'):
    print(' -', f)

importlib.invalidate_caches()
try:
    import main
    print('\nIMPORT: OK')
except Exception:
    print('\nIMPORT: FAILED')
    traceback.print_exc()
