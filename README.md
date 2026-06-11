# 🎮 Forza Horizon Skill Point Automator

A visually interactive, virtual-controller-based automator for **Forza Horizon**. Designed to run seamlessly in the background using Windows Virtual Desktops so you can farm skill points while continuing to use your PC.

It displays a beautiful, real-time Xbox controller HUD overlay showing active buttons and countdown timers, alongside an OBS-friendly preview window.

---

## ✨ Key Features

*   **📺 Translucent HUD Overlay:** A floating, frameless, and translucent UI built with PyQt5 that stays on top of your screen or game capture.
*   **💡 Live Input Visualization:** Watch buttons, D-pad, triggers, and thumbsticks light up dynamically as the script executes.
*   **⏯️ Interactive Control:** Toggle the automation on or off directly from the HUD using the built-in Play/Pause button.
*   **🎮 Virtual Controller Emulation:** Utilizes `vgamepad` to emulate a hardware Xbox 360 controller, registering as native controller input to bypass anti-cheat keyboard/mouse detection.
*   **💻 Multitasking-Friendly:** Designed to run on a separate Windows Virtual Desktop. Custom Win32 background capture APIs fetch frames even when the game window is "cloaked" on another desktop.
*   **🎯 Right-Click Window Targeting:** Right-click inside the **OBS Game Preview** window to select any running application window (e.g., Forza) for capture, including applications running on different virtual desktops.
*   **⚙️ Interactive Settings & Sequential Presets:**
    *   Add, edit, remove, and reorder steps (`Move Up`/`Move Down`) sequentially.
    *   Configure type (`press`, `hold_rt`, `release_rt`, `wait`, `wait_for_text`, `find_and_select_text`, `type_text`).
    *   Set button, wait delay, hold delay, and **input count** (allowing a button to be pressed multiple times sequentially).
    *   **Test Run:** Execute and test your modified sequence parameters immediately before saving them.
*   **🎙️ Controller Macro Recording:** Toggle **Record Macro** in the settings dialog, press buttons on your physical Xbox controller, and let the tool automatically record and translate your inputs into sequence steps using `xinput-python`.

---

## 🚀 Setup & Installation

The automator requires Python 3. All dependencies are managed in [requirements.txt](file:///C:/Users/carlo/Documents/scripts/Forza/requirements.txt).

### Option A: The Click-to-Run Script (Recommended)
Simply double-click or run [run.bat](file:///C:/Users/carlo/Documents/scripts/Forza/run.bat) from the command line:
```cmd
run.bat
```
*   **What this does:**
    1. Checks if a local Python virtual environment (`venv`) exists. If not, it creates it.
    2. Installs all required packages automatically (`pip install -r requirements.txt`).
    3. Activates the environment and launches the automator script.

### Option B: Manual Virtual Environment Setup
If you prefer to manage the environment manually:

1. **Create the Virtual Environment:**
   ```cmd
   python -m venv venv
   ```

2. **Activate the Environment:**
   * **In Command Prompt (`cmd.exe`):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   * **In PowerShell:**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
     *(Note: If PowerShell blocks the script with an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` first to allow it in your current terminal session).*

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Script:**
   ```bash
   python auto_forza_skill_points.py
   ```

> [!WARNING]
> **Virtual Gamepad Driver Required**  
> `vgamepad` relies on the **ViGEmBus** system driver to emulate hardware controllers. If the script fails to run or complains about missing drivers, download and install it from the official [ViGEmBus Releases](https://github.com/ViGEm/ViGEmBus/releases).

---

## 🛠️ Environment Configuration

To run the automator successfully in the background, configure your game and compatibility settings as detailed below.

### 1. Steam Launch Options
To allow background controller input and visual captures, configure the game to run in borderless windowed mode.

> [!IMPORTANT]
> 1. Right-click your **Forza** game in Steam -> Select **Properties...**
> 2. In the **Launch Options** field under the **General** tab, paste:
>    ```text
>    -windowed -noborder -fullscreen=false
>    ```

### 2. Windows Executable Compatibility Settings
Adjust the compatibility settings of your Forza executable (e.g., `forzahorizon6.exe`).

| Feature / Setting | Instructions | Visual Guide |
| :--- | :--- | :--- |
| **Disable Fullscreen Optimizations** | Right-click the game `.exe` -> **Properties** -> **Compatibility** -> Check **Disable fullscreen optimizations**. | ![Disable Fullscreen Optimizations](image.png) |
| **Override High DPI Scaling** | Click **Change high DPI settings** -> Check **Override high DPI scaling behavior** -> Set **Scaling performed by:** to `Application`. | ![DPI Settings Override](image-2.png) |

---

## 🚀 Step-by-Step Farming Guide

Follow this sequence to set up background farming:

1. **Launch the Game:** Open Forza.
2. **Configure Virtual Desktops:**
   * Press `Win + Tab` to open the Windows Task View.
   * Create a new virtual desktop.
   * Drag the Forza window into this new virtual desktop.
   * Switch to the new virtual desktop using `Ctrl + Win + Left/Right Arrow`.
3. **Run the Script:**
   * Start it using `run.bat` or by activating the `venv` and running `python auto_forza_skill_points.py`.
4. **Choose Target Window:**
   * In the **OBS Game Preview** window, right-click and select the Forza window title from the list.
5. **Load the Farm Event:**
   * Go to the event browser in Forza and search using **Share Code:** `409 742 297`.
   * Start the event.
6. **Begin Automation:**
   * Click the Play button (▶) on the floating Xbox controller overlay to start farming.
7. **Minimize/Switch Desktop:**
   * Switch back to your primary virtual desktop (`Ctrl + Win + Left/Right Arrow`) to work or play other games. 
   * *Optional:* You can capture or monitor the automator desktop using **OBS Studio** (Window Capture mode).

---

## ⚙️ Settings Dialog & Sequencer

Click the gear icon (**⚙**) on the overlay controller to open the interactive **Settings Dialog**.

### Sequencer Actions Configuration Matrix

Use the following action types inside your presets:

| Action Type | Description | Configurable Fields |
| :--- | :--- | :--- |
| `hold_rt` | Holds the accelerator (RT) trigger down. | None |
| `release_rt` | Releases the accelerator (RT) trigger. | None |
| `wait` | Pauses sequence execution. | `Wait (s)` |
| `press` | Presses and releases a specific gamepad button. | `Button`, `Hold (s)`, `Count` (sequential presses) |
| `wait_for_text` | Screen-captures and pauses until specific text is found. | `Text (CV)` |
| `find_and_select_text` | Searches for text on screen and clicks it. | `Text (CV)` |
| `type_text` | Types keyboard text directly into the game window. | `Text (CV)` |

> [!TIP]
> **Supported Buttons for the `press` Action:**  
> `A` • `B` • `X` • `Y` • `LB` • `RB` • `START` • `BACK` • `GUIDE` • `LSTICK` • `RSTICK` • `DPAD_UP` • `DPAD_DOWN` • `DPAD_LEFT` • `DPAD_RIGHT`

---

## 📈 Commercialization & Distribution Strategy (Internal Note)

If you plan to package, market, and sell this automator, use the following framework.

### 1. Monetization Models
*   **One-Time License ($5 – $15):** Best for a simple, plug-and-play `.exe` file sold on platforms like Gumroad or Itch.io.
*   **Freemium/Subscription ($3/mo):** Keep this baseline script open-source, and charge a small subscription fee for premium features (e.g., custom preset loop sequences, automatic game-update updates, multi-instance managers).

### 2. Marketing & Promotion Channels
*   **Short-Form Video (TikTok & YouTube Shorts):** Create videos showing a split-screen layout—one half displaying Forza farming, the other half showing your virtual controller overlay lighting up in real-time. Emphasize the multitasking aspect (*"Farming credits on desktop 2 while working on desktop 1"*).
*   **Community Building:** Establish a Discord server to handle support requests, allow users to trade custom `LOOP_SEQUENCE` configurations, and push direct updates.
*   **Targeted Modding Forums:** Advertise/showcase the script on game-modification forums (e.g., Se7enSins, ElitePvPers) and automation subreddits.

### 3. Release & Packaging Checklist
*   [ ] **Compile to Executable:** Package the python script into a standalone `.exe` using `PyInstaller` so customers do not have to install Python or depend on terminal interfaces.
*   [ ] **Simplify ViGEmBus Setup:** Bundle the ViGEmBus driver installer with your package, or include a clear, single-click setup guide for the virtual gamepad driver.
*   [ ] **Safety & Disclaimer Note:** Provide a terms-of-service warning advising users to use reasonable timeouts to prevent anomalies that might attract anti-cheat flags.