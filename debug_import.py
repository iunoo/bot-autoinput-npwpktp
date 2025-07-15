try:
    print("Testing import handlers.callbacks...")
    import handlers.callbacks as cb
    print("✅ Import successful")
    
    print("Available classes:")
    for name in dir(cb):
        if not name.startswith('_'):
            obj = getattr(cb, name)
            if isinstance(obj, type):
                print(f"  - Class: {name}")
            elif callable(obj):
                print(f"  - Function: {name}")
                
except ImportError as e:
    print(f"❌ Import error: {e}")
except SyntaxError as e:
    print(f"❌ Syntax error in file: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")