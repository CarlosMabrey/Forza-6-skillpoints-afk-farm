# 📝 Forza Horizon Skill Point Automator - TODO List

This document tracks upcoming features, enhancements, and automation sequences planned for the Forza Horizon Automator.

---

## 🚀 1. Freeplay Start Script
*Automate the menu navigation to load the farm event and select the vehicle starting directly from Freeplay.*

- [ ] **Menu Navigation & Share Code Entry**
  - [ ] Enter Horizon Menu.
  - [ ] Press `RB` 4 times to navigate to the **Creative Hub** tab.
  - [ ] Press `A` to enter **Event Lab**.
  - [ ] Press `A` to select **Play Event**.
  - [ ] Press `BACK` (Left Options/View button) to open Search.
  - [ ] Navigate up 1 slot and press `A` to select **Share Code**.
  - [ ] Input share code: `409 742 297`.
  - [ ] Press `A` to select the map.
  - [ ] Press `A` to choose the race type.
- [ ] **Event Setup & Filters**
  - [ ] Wait a few seconds for the event screen to load.
  - [ ] Press `Y` to open Filters.
  - [ ] Scroll down 8 times and press `A` to enable **S2 Performance Class**.
  - [ ] Scroll down 26 more times and press `A` to select **Retro Rally**.
  - [ ] Scroll down 17 more times and press `A` to select **Legendary** championship status.
  - [ ] Press `B` to apply filters.
- [ ] **Vehicle Selection via CV/OCR**
  - [ ] Press `BACK` (Left Options/View button) to search/filter manufacturer.
  - [ ] Utilize a lightweight Computer Vision/OCR model (e.g., EasyOCR or Tesseract + OpenCV template matching) to find **Subaru** in the manufacturer list.
  - [ ] Calculate and send the required D-pad/Joystick inputs to highlight and select **Subaru** with `A`.
  - [ ] Use CV/OCR to locate and select the **Impreza 22B-STI Version**.
  - [ ] Press `A` to confirm selection.
  - [ ] Wait approximately 10 seconds for the race environment to load, then trigger the core loop script.

---

## 🏎️ 2. Autobuy Car (Skill Point Source)
*Automate purchasing multiple copies of the target car to farm wheelspins.*

- [ ] **Navigate to Car Collection**
  - [ ] Press `BACK` (Select/View button).
  - [ ] Press `DPAD_LEFT` once, then `DPAD_RIGHT` once to highlight the **Discover Japan** playlist.
  - [ ] Press `DPAD_DOWN` once to highlight **Car Collection** and select.
- [ ] **Find & Purchase Target Car**
  - [ ] Press the Select/View button to open the brand selector.
  - [ ] Press `DPAD_UP` 3 times, `DPAD_RIGHT` 3 times to highlight **Subaru**, then select with `A`.
  - [ ] Press `DPAD_DOWN` once to hover over the **Impreza 22B-STI Version** card (no need to press `A`).
- [ ] **Buying Loop (Configurable)**
  - [ ] Create a buying loop sequence:
    1. Press the Select/View button (Buy).
    2. Press `DPAD_DOWN` once to highlight "Yes" (confirm purchase).
    3. Press `A` (confirm purchase).
    4. Press `A` again (skip/confirm color/options).
    5. Press `A` again (finish transaction).
  - [ ] Add a configuration setting in `settings.json` (and UI) for the **number of purchase iterations**.
  - [ ] *Optimization:* Implement UI card detection via OCR/CV to robustly locate and select the correct car card regardless of layout changes.

---

## 💎 3. Car Mastery & Wheelspin Farming Script
*Collect wheelspins from newly purchased cars by spending skill points on their mastery trees.*

- [ ] **Navigate to "My Cars"**
  - [ ] From the Car Collection page, press `B` 3 times to return to the main menu.
  - [ ] Press `RB` to go to the **My Cars** tab and select it with `A`.
- [ ] **Apply Filter Script**
  - [ ] Press `Y` to open the filter menu.
  - [ ] Scroll down 4 times and press `A` to select duplicates.
  - [ ] Scroll down 3 times and press `A` to select **B class**.
  - [ ] Scroll down 27 times and press `A` to select **Retro Rally**.
  - [ ] Scroll down 17 times and press `A` to select **Legendary**.
  - [ ] Press `B` to apply and return.
- [ ] **Farming Loop (Find New & Spend)**
  - [ ] **Find New Script (CV/OCR):** Scan screen to locate car cells containing the **"NEW"** tag.
  - [ ] Navigate the selector to the nearest "NEW" car cell.
  - [ ] Press `A` twice to select and enter the car.
  - [ ] Wait 5 seconds, then press `B` to close any transition screens.
  - [ ] **Navigate to Car Mastery:**
    - [ ] Press `RB` twice to navigate to the **Cars** tab.
    - [ ] Scroll down 1 time to highlight **Upgrades and Tuning** and select with `A`.
    - [ ] Scroll down 7 times to select **Car Mastery**.
  - [ ] **Unlock "Spinball Wizard" (Wheelspin Node):**
    - [ ] Execute path: `A` (base node) -> `DPAD_RIGHT` -> `A` -> `DPAD_UP` -> `A` -> `DPAD_UP` -> `A` -> `DPAD_UP` -> `A` -> `DPAD_LEFT` -> `A`.
    - [ ] Wait 3 seconds for node unlock animation.
  - [ ] **Exit and Loop:**
    - [ ] Press `B` twice to return to the garage.
    - [ ] Press `DPAD_UP` and then `A` to open the car selection menu.
    - [ ] Re-run the **Filter Script**.
    - [ ] Repeat until no cars with the **"NEW"** tag are detected.
  - [ ] Display a visual completion message on the overlay once all new cars are processed.

---

## 🔨 4. Sell to Auction House
*Automatically clean up used/non-new farm cars by selling them on the Auction House.*

- [ ] **Identify Non-New Vehicles**
  - [ ] Run the **Filter Script** to list all target vehicles.
  - [ ] Use OCR/CV to identify car cards that **do not** have the "NEW" tag.
- [ ] **Auction Sequence**
  - [ ] Select a non-new Impreza 22B-STI by pressing `A` twice.
  - [ ] Wait 5 seconds.
  - [ ] Press `LB` to switch to the **Buy and Sell** tab.
  - [ ] Scroll down 1 time to **Auction House** and select with `A`.
  - [ ] Scroll down 1 time to **Start Auction** and select with `A`.
  - [ ] Run the **Filter Script** to find the vehicle list.
  - [ ] Select the target vehicle with `A`.
  - [ ] Press `A` to auction the car.
  - [ ] Press `A` to confirm.
  - [ ] Repeat the loop until all filtered, non-new Impreza 22B-STI cars have been listed.

---

## 🤖 5. Auto Auction Ability
*Specifically target and sell stock Impreza 22B-STI Versions that do not have the "NEW" tag.*

- [ ] Add a dedicated routine to sell only stock, non-new cars to the Auction House automatically.
- [ ] Ensure safety checks so modified or marked cars are not auctioned by mistake.

---

## 📺 6. OBS Preview / Popout Game Mirror
*Render a copy of the game screen directly inside the python overlay UI.*

- [ ] **Windows Screen/Window Capture**
  - [ ] Capture the game window (even when running on a separate Windows Virtual Desktop) using Win32 API (`win32gui`, `win32ui`, `win32con`).
- [ ] **GUI Integration**
  - [ ] Embed a video preview panel in the PyQt5 interface.
  - [ ] Render the captured frames in real-time, functioning similarly to an OBS Window/Source Preview.
  - [ ] Allow minimizing or scaling the preview window.

---

## ⚙️ 7. Environment Configuration Helper Script
*Streamline the initial configuration steps listed in the README.*

- [ ] **Automate Setup Checks**
  - [ ] Detect if Steam is installed and locate the Forza Horizon executable path.
  - [ ] Verify launch options (or output a guide if Steam configuration cannot be programmatically edited).
  - [ ] Check/modify Windows compatibility settings for `forzahorizon6.exe` (DPI override, Disable fullscreen optimizations).
  - [ ] Verify system resolution and scaling to ensure CV/OCR functions correctly.
