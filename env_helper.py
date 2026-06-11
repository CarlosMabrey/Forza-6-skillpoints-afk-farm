import os
import winreg
from PyQt5.QtWidgets import QMessageBox

def check_steam_and_forza():
    steam_path = None
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
    except Exception as e:
        pass

    results = []
    if steam_path:
        results.append(f"✅ Steam found at: {steam_path}")
        
        # Check standard library folder for Forza Horizon 5 or similar
        # Since this is "Forza-6" in path name, let's just do a generic check
        common_apps = os.path.join(steam_path, "steamapps", "common")
        if os.path.exists(common_apps):
            forza_dirs = [d for d in os.listdir(common_apps) if "forza" in d.lower()]
            if forza_dirs:
                results.append(f"✅ Forza installation found: {', '.join(forza_dirs)}")
            else:
                results.append("❌ Forza installation not found in primary Steam library.")
    else:
        results.append("❌ Steam not found in Registry.")

    # Check Windows DPI settings and Scaling
    results.append("⚠️ Ensure Windows Display Scaling is set to 100% for CV/OCR accuracy.")
    results.append("⚠️ Ensure you are running the game in Windowed or Borderless mode.")

    return "\n".join(results)

def show_env_helper(parent_widget=None):
    results = check_steam_and_forza()
    msg = QMessageBox(parent_widget)
    msg.setWindowTitle("Environment Checker")
    msg.setText("Environment Setup Checks:\n\n" + results)
    msg.setStyleSheet("background-color: #2d2d2d; color: #ffffff; font-size: 14px;")
    msg.exec_()

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    show_env_helper()
