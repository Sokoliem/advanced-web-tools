"""Installation script for computer interaction dependencies."""

import subprocess
import sys
import platform

def install_package(package):
    """Install a package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"Successfully installed {package}")
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to install {package}")
        return False

def main():
    """Install all required dependencies for computer interaction."""
    print("Installing computer interaction dependencies...")
    
    # Core dependencies
    core_packages = [
        "pyautogui>=0.9.53",
        "Pillow>=9.0.0",
        "pygetwindow>=0.0.9",
        "psutil>=5.8.0",
        "pyperclip>=1.8.2",
        "keyboard>=0.13.5",
        "mouse>=0.7.1",
        "numpy>=1.21.0"
    ]
    
    # Platform-specific dependencies
    if platform.system() == "Windows":
        core_packages.append("pywin32>=301")
    
    # Optional dependencies for advanced features
    optional_packages = [
        "opencv-python>=4.5.0",  # For computer vision
        "pytesseract>=0.3.0",    # For OCR
        "scikit-image>=0.18.0"   # For image comparison
    ]
    
    # Install core packages
    print("\nInstalling core packages...")
    for package in core_packages:
        install_package(package)
    
    # Ask about optional packages
    print("\nOptional packages provide advanced features:")
    print("- opencv-python: Advanced computer vision capabilities")
    print("- pytesseract: OCR for text recognition")
    print("- scikit-image: Advanced image analysis")
    
    response = input("\nInstall optional packages? (y/n): ").lower()
    if response == 'y':
        print("\nInstalling optional packages...")
        for package in optional_packages:
            install_package(package)
        
        # Note about Tesseract OCR
        if "pytesseract" in optional_packages:
            print("\n" + "="*50)
            print("IMPORTANT: pytesseract requires Tesseract OCR to be installed separately.")
            print("Download from: https://github.com/UB-Mannheim/tesseract/wiki")
            print("After installation, add it to your system PATH.")
            print("="*50)
    
    print("\nInstallation complete!")
    print("\nTo use computer interaction tools, make sure to:")
    print("1. Restart your Python environment")
    print("2. If you installed OCR, install Tesseract OCR separately")
    print("3. On some systems, you may need to run as administrator for full functionality")

if __name__ == "__main__":
    main()
