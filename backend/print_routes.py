from asess.main import app

print('ROUTES:')
for r in app.routes:
    print(f"{r.path} -> {sorted(r.methods)}")
