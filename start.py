# start.py
"""
Bank Statement to Tally Integrator
Startup script with dependency checking.
"""

import subprocess
import sys
import os


def check_dependencies():
    """Check if required packages are installed"""
    required = {
        'customtkinter': 'customtkinter',
        'pandas': 'pandas',
        'thefuzz': 'thefuzz',
        'openpyxl': 'openpyxl'
    }
    
    missing = []
    
    for import_name, package_name in required.items():
        try:
            __import__(import_name)
            print(f"  ✓ {package_name}")
        except ImportError:
            missing.append(package_name)
            print(f"  ✗ {package_name} - MISSING")
    
    return missing


def install_dependencies(packages):
    """Install missing packages"""
    print(f"\nInstalling missing packages: {', '.join(packages)}")
    
    for package in packages:
        print(f"  Installing {package}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
            print(f"    ✓ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"    ✗ Failed to install {package}: {e}")
            return False
    
    return True


def main():
    print("=" * 60)
    print("  Bank Statement to Tally Integrator")
    print("  Version 1.0 - Tally.ERP 9")
    print("=" * 60)
    print()
    
    print("Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"\n{len(missing)} package(s) missing: {', '.join(missing)}")
        choice = input("\nInstall now? (y/n): ").strip().lower()
        
        if choice == 'y':
            if not install_dependencies(missing):
                print("\nFailed to install some packages. Please install manually:")
                print(f"pip install {' '.join(missing)}")
                input("\nPress Enter to exit...")
                return
        else:
            print("\nCannot start without required packages.")
            print(f"Install with: pip install {' '.join(missing)}")
            input("\nPress Enter to exit...")
            return
    
    print("\n✓ All dependencies satisfied!")
    print("\nStarting application...\n")
    
    try:
        import main as main_module
        main_module.main()
    except Exception as e:
        print(f"\nError starting application: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()