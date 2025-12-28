import os
import shutil

# 1. Define the new healthy structure
NEW_STRUCTURE = {
    'src': [
        'model/app.py',
        'model/database.py',
        'model/waste_predictor.py',
        'generation/anomaly_detector.py',
        'generation/feature_engineering.py',
        'src/data_generator.py'
    ]
}

def clean_and_fix():
    print("🔧 Fixing project structure...")
    
    # Create new 'src' if it doesn't exist
    if not os.path.exists('src'):
        os.makedirs('src')

    # Move files to 'src'
    for dest_folder, source_files in NEW_STRUCTURE.items():
        for source in source_files:
            if os.path.exists(source):
                file_name = os.path.basename(source)
                dest_path = os.path.join(dest_folder, file_name)
                
                # Check if we are overwriting a file that's already there
                if os.path.exists(dest_path):
                    print(f"  ⚠️  {file_name} already exists in {dest_folder}. Skipping...")
                    continue
                
                print(f"  -> Moving {source} to {dest_path}")
                shutil.move(source, dest_path)
            else:
                print(f"  ❌ Could not find {source} (It might already be moved)")

    # Create an empty __init__.py in src to make it a package
    init_file = os.path.join('src', '__init__.py')
    if not os.path.exists(init_file):
        open(init_file, 'a').close()
        print("  -> Created src/__init__.py")

    # Delete old folders if empty
    for old_folder in ['model', 'generation']:
        if os.path.exists(old_folder) and not os.listdir(old_folder):
            os.rmdir(old_folder)
            print(f"  -> Removed empty folder: {old_folder}")

    # Delete all __pycache__ folders and .pyc files
    print("🧹 Cleaning up cache files...")
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))
                print(f"  -> Deleted {os.path.join(root, d)}")
        for f in files:
            if f.endswith(".pyc"):
                os.remove(os.path.join(root, f))

    print("\n✅ Project structure fixed! You can now run the app.")

if __name__ == "__main__":
    clean_and_fix()