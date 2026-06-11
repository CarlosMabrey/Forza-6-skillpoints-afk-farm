import time
import threading
import sys
import json
import os
import argparse
import cv2
import numpy as np
import mss
import win32gui
import win32con
import win32ui
from PyQt5.QtWidgets import (QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QTableWidgetItem, QComboBox, 
                             QDoubleSpinBox, QCheckBox, QLabel, QHeaderView, QAbstractItemView, QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QBrush, QFontMetrics, QRadialGradient, QLinearGradient, QPainterPath, QImage, QPixmap
import vgamepad as vg
import ctypes
from ctypes import wintypes
try:
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl
except ImportError:
    WindowsCapture = None

def is_window_cloaked(hwnd):
    try:
        # DWMWA_CLOAKED = 14
        cloaked = ctypes.c_int(0)
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)
        )
        return bool(cloaked.value)
    except Exception:
        return False

def get_window_rect_correct(hwnd):
    try:
        rect = wintypes.RECT()
        # DWMWA_EXTENDED_FRAME_BOUNDS = 9
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)
        )
        return (rect.left, rect.top, rect.right, rect.bottom)
    except Exception:
        return win32gui.GetWindowRect(hwnd)

def get_target_window(target_title=None):
    def callback(hwnd, hwnds):
        title = win32gui.GetWindowText(hwnd)
        if title:
            hwnds.append((hwnd, title))
        return True
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    if not hwnds:
        return None
    if target_title:
        for hwnd, title in hwnds:
            if title == target_title:
                return hwnd
    for hwnd, title in hwnds:
        if "forza" in title.lower():
            return hwnd
    return None

# Try to import OCR, but allow graceful failure
try:
    import easyocr
    reader = easyocr.Reader(['en'])
except ImportError:
    reader = None

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULT_PRESETS = {
    "Custom Loop": [
        {
            "type": "hold_rt"
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 30.0
        },
        {
            "type": "press",
            "button": "X",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.2
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 7.0
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        }
    ],
    "Freeplay Start": [
        {
            "type": "press",
            "button": "START",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "RB",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "RB",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "RB",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "RB",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "BACK",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "DPAD_UP",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 2.0
        },
        {
            "type": "type_text",
            "text": "409 742 297"
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 2.0
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 5.0
        },
        {
            "type": "press",
            "button": "Y",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "B",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 2.0
        },
        {
            "type": "find_and_select_text",
            "text": "Subaru"
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 10.0
        }
    ],
    "Autobuy Car": [
        {
            "type": "press",
            "button": "START",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "press",
            "button": "DPAD_LEFT",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.1
        },
        {
            "type": "press",
            "button": "DPAD_RIGHT",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "press",
            "button": "DPAD_RIGHT",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "press",
            "button": "DPAD_DOWN",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 2.0
        },
        {
            "type": "press",
            "button": "BACK",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "DPAD_UP",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.2
        },
        {
            "type": "press",
            "button": "DPAD_UP",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.2
        },
        {
            "type": "press",
            "button": "DPAD_UP",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.2
        },
        {
            "type": "press",
            "button": "DPAD_RIGHT",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.2
        },
        {
            "type": "press",
            "button": "DPAD_RIGHT",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.2
        },
        {
            "type": "press",
            "button": "DPAD_RIGHT",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.2
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "DPAD_DOWN",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "BACK",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "DPAD_DOWN",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1,
            "count": 1
        },
        {
            "type": "wait",
            "seconds": 5.0
        }
    ],
    "Car Mastery Farm": [
        {
            "type": "find_and_select_text",
            "text": "NEW"
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 5.0
        },
        {
            "type": "press",
            "button": "B",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "RB",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "RB",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "DPAD_DOWN",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "DPAD_RIGHT",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 3.0
        },
        {
            "type": "press",
            "button": "DPAD_UP",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 3.0
        },
        {
            "type": "press",
            "button": "DPAD_UP",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 3.0
        },
        {
            "type": "press",
            "button": "DPAD_UP",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 3.0
        },
        {
            "type": "press",
            "button": "DPAD_LEFT",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 3.0
        },
        {
            "type": "press",
            "button": "B",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "B",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 2.0
        },
        {
            "type": "press",
            "button": "DPAD_UP",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 2.0
        }
    ],
    "Auction Sell": [
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 5.0
        },
        {
            "type": "press",
            "button": "LB",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "DPAD_DOWN",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 2.0
        },
        {
            "type": "press",
            "button": "DPAD_DOWN",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 0.5
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 2.0
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 1.0
        },
        {
            "type": "press",
            "button": "A",
            "hold": 0.1
        },
        {
            "type": "wait",
            "seconds": 5.0
        }
    ]
}


BUTTON_MAP = {
    "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "GUIDE": vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    "LSTICK": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    "RSTICK": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    "DPAD_UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "DPAD_DOWN": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "DPAD_LEFT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "DPAD_RIGHT": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                presets = data.get("presets", DEFAULT_PRESETS)
                active = data.get("active_preset", "Custom Loop")
                bg = data.get("show_background", True)
                if active not in presets:
                    active = list(presets.keys())[0]
                return presets, active, bg
        except Exception as e:
            print("Error loading settings:", e)
    return DEFAULT_PRESETS.copy(), "Custom Loop", True

def save_settings(presets, active, show_background):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump({
                "active_preset": active,
                "presets": presets,
                "show_background": show_background
            }, f, indent=4)
    except Exception as e:
        print("Error saving settings:", e)


class SettingsDialog(QDialog):
    def __init__(self, presets, active_preset, show_background, overlay_state=None, parent=None):
        super().__init__(parent)
        self.overlay_state = overlay_state
        self.presets = presets.copy()
        self.active_preset = active_preset
        self.setWindowTitle("Overlay Settings")
        self.resize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QLabel {
                color: #e0e0e0;
                font-weight: 500;
            }
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #3a3a3a;
                background-color: #1e1e1e;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #007acc;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border: 1px solid #007acc;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border: 1px solid #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QPushButton#btnSave {
                background-color: #007acc;
                border: 1px solid #005f9e;
            }
            QPushButton#btnSave:hover {
                background-color: #0098ff;
            }
            QTableWidget {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
                gridline-color: transparent;
                selection-background-color: #264f78;
                outline: 0;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #252525;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #888888;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #2d2d2d;
                font-weight: bold;
            }
            QComboBox, QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 10px;
            }
            QComboBox:hover, QLineEdit:hover {
                border: 1px solid #007acc;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                selection-background-color: #007acc;
                outline: 0px;
            }
            QDoubleSpinBox, QSpinBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px;
            }
            QDoubleSpinBox:hover, QDoubleSpinBox:focus, QSpinBox:hover, QSpinBox:focus {
                border: 1px solid #007acc;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button, QSpinBox::up-button, QSpinBox::down-button {
                background-color: transparent;
                border: none;
                width: 16px;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #3d3d3d;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #1a1a1a;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6a6a6a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(16, 16, 16, 16)

        # Preset Top Bar
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Active Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(self.presets.keys())
        self.preset_combo.setCurrentText(self.active_preset)
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        
        btn_new_preset = QPushButton("New Preset")
        btn_new_preset.clicked.connect(self.new_preset)
        preset_layout.addWidget(btn_new_preset)
        self.layout.addLayout(preset_layout)

        self.bg_checkbox = QCheckBox("Show Dark Background Overlay")
        self.bg_checkbox.setChecked(show_background)
        self.layout.addWidget(self.bg_checkbox)
        
        # Environment Check
        btn_env = QPushButton("Check Environment Setup")
        btn_env.clicked.connect(lambda: show_env_helper(self))
        self.layout.addWidget(btn_env)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Type", "Button", "Wait (s)", "Hold (s)", "Count", "Text (CV)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.layout.addWidget(self.table)
        
        if self.active_preset in self.presets:
            self.load_sequence(self.presets[self.active_preset])
            
        # Update timer for highlighting active test run step
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_highlight)
        self.update_timer.start(100)
            
        ctrl_layout = QHBoxLayout()
        btn_add = QPushButton("Add Step")
        btn_add.clicked.connect(lambda: self.add_row({"type": "press", "button": "A", "hold": 0.1}))
        btn_del = QPushButton("Remove Step")
        btn_del.clicked.connect(self.remove_row)
        btn_up = QPushButton("Move Up")
        btn_up.clicked.connect(self.move_up)
        btn_down = QPushButton("Move Down")
        btn_down.clicked.connect(self.move_down)
        
        ctrl_layout.addWidget(btn_add)
        ctrl_layout.addWidget(btn_del)
        ctrl_layout.addWidget(btn_up)
        ctrl_layout.addWidget(btn_down)
        self.layout.addLayout(ctrl_layout)
        
        btm_layout = QHBoxLayout()
        btn_restore = QPushButton("Restore Defaults")
        btn_restore.clicked.connect(self.restore_defaults)
        
        self.btn_record = QPushButton("Record Macro")
        self.btn_record.setCheckable(True)
        self.btn_record.toggled.connect(self.toggle_record)
        
        self.btn_test = QPushButton("Test Run")
        self.btn_test.clicked.connect(self.test_run)
        
        btn_save = QPushButton("Save")
        btn_save.setObjectName("btnSave")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btm_layout.addWidget(btn_restore)
        btm_layout.addWidget(self.btn_record)
        btm_layout.addWidget(self.btn_test)
        btm_layout.addStretch()
        btm_layout.addWidget(btn_save)
        btm_layout.addWidget(btn_cancel)
        self.layout.addLayout(btm_layout)

    def load_sequence(self, sequence):
        self.table.setRowCount(0)
        for step in sequence:
            self.add_row(step)

    def on_preset_changed(self, text):
        if self.active_preset in self.presets:
            self.presets[self.active_preset] = self.get_sequence()
        self.active_preset = text
        if text in self.presets:
            self.load_sequence(self.presets[text])

    def new_preset(self):
        base_name = "New Preset"
        name = base_name
        i = 1
        while name in self.presets:
            name = f"{base_name} {i}"
            i += 1
        self.presets[name] = [{"type": "wait", "seconds": 1.0}]
        self.preset_combo.addItem(name)
        self.preset_combo.setCurrentText(name)

    def add_row(self, step):
        r = self.table.rowCount()
        self.table.insertRow(r)
        
        type_combo = QComboBox()
        type_combo.addItems(["press", "hold_rt", "release_rt", "wait", "wait_for_text", "find_and_select_text", "type_text"])
        type_combo.setCurrentText(step.get("type", "press"))
        self.table.setCellWidget(r, 0, type_combo)
        
        btn_combo = QComboBox()
        btn_combo.addItems(["A", "B", "X", "Y", "LB", "RB", "START", "BACK", "GUIDE", "LSTICK", "RSTICK", "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT"])
        if "button" in step:
            btn_combo.setCurrentText(step["button"])
        self.table.setCellWidget(r, 1, btn_combo)
        
        wait_spin = QDoubleSpinBox()
        wait_spin.setMaximum(9999.0)
        wait_spin.setValue(float(step.get("seconds", 0.0)))
        self.table.setCellWidget(r, 2, wait_spin)
        
        hold_spin = QDoubleSpinBox()
        hold_spin.setMaximum(10.0)
        hold_spin.setSingleStep(0.1)
        hold_spin.setValue(float(step.get("hold", 0.1)))
        self.table.setCellWidget(r, 3, hold_spin)

        from PyQt5.QtWidgets import QSpinBox
        count_spin = QSpinBox()
        count_spin.setMinimum(1)
        count_spin.setMaximum(9999)
        count_spin.setValue(int(step.get("count", 1)))
        self.table.setCellWidget(r, 4, count_spin)

        text_edit = QLineEdit()
        text_edit.setText(step.get("text", ""))
        self.table.setCellWidget(r, 5, text_edit)

    def remove_row(self):
        selected_indices = self.table.selectionModel().selectedRows()
        if not selected_indices:
            row = self.table.currentRow()
            if row >= 0:
                self.table.removeRow(row)
            return

        rows_to_delete = sorted([idx.row() for idx in selected_indices], reverse=True)
        for r in rows_to_delete:
            self.table.removeRow(r)

    def move_up(self):
        row = self.table.currentRow()
        if row > 0:
            self.swap_rows(row, row - 1)
            self.table.selectRow(row - 1)

    def move_down(self):
        row = self.table.currentRow()
        if row >= 0 and row < self.table.rowCount() - 1:
            self.swap_rows(row, row + 1)
            self.table.selectRow(row + 1)

    def swap_rows(self, r1, r2):
        for col in range(6):
            w1 = self.table.cellWidget(r1, col)
            w2 = self.table.cellWidget(r2, col)
            self.table.removeCellWidget(r1, col)
            self.table.removeCellWidget(r2, col)
            self.table.setCellWidget(r1, col, w2)
            self.table.setCellWidget(r2, col, w1)

    def test_run(self):
        if not self.overlay_state:
            return
        with self.overlay_state.lock:
            currently_running = self.overlay_state.running
        if currently_running:
            with self.overlay_state.lock:
                self.overlay_state.running = False
                self.overlay_state.pause_event.clear()
        else:
            seq = self.get_sequence()
            with self.overlay_state.lock:
                self.overlay_state.presets[self.overlay_state.active_preset] = seq
                self.overlay_state.running = True
                self.overlay_state.pause_event.set()

    def toggle_record(self, checked):
        if checked:
            self.btn_record.setText("Stop Recording")
            self.is_recording = True
            self.recorded_steps = []
            self.record_thread = threading.Thread(target=self._record_macro_loop, daemon=True)
            self.record_thread.start()
        else:
            self.btn_record.setText("Record Macro")
            self.is_recording = False
            time.sleep(0.1)
            for step in self.recorded_steps:
                self.add_row(step)
                
    def _record_macro_loop(self):
        try:
            import XInput
            last_time = time.time()
            
            BTN_MAP = {
                "DPAD_UP": "DPAD_UP", "DPAD_DOWN": "DPAD_DOWN", 
                "DPAD_LEFT": "DPAD_LEFT", "DPAD_RIGHT": "DPAD_RIGHT",
                "A": "A", "B": "B", "X": "X", "Y": "Y",
                "LEFT_SHOULDER": "LB", "RIGHT_SHOULDER": "RB",
                "START": "START", "BACK": "BACK"
            }
            
            while self.is_recording:
                events = XInput.get_events()
                for event in events:
                    if not self.is_recording:
                        break
                    
                    if event.type == XInput.EVENT_BUTTON_PRESSED:
                        # event.button in XInput_Python returns the string representation like "DPAD_UP" or "A"
                        # wait, earlier task-259 showed the raw _button_dict: {1: 'DPAD_UP', ...}
                        # event.button_id is the integer, event.button is the string.
                        btn_name = BTN_MAP.get(event.button)
                        if btn_name:
                            current_time = time.time()
                            wait_time = current_time - last_time
                            if wait_time > 0.1:
                                self.recorded_steps.append({"type": "wait", "seconds": round(wait_time, 1)})
                            self.recorded_steps.append({"type": "press", "button": btn_name, "hold": 0.1, "count": 1})
                            last_time = current_time
                time.sleep(0.01)
        except Exception as e:
            print("Error recording macro:", e)

    def restore_defaults(self):
        self.presets = DEFAULT_PRESETS.copy()
        self.preset_combo.clear()
        self.preset_combo.addItems(self.presets.keys())
        self.preset_combo.setCurrentText("Custom Loop")
        self.bg_checkbox.setChecked(True)

    def get_sequence(self):
        seq = []
        for r in range(self.table.rowCount()):
            t = self.table.cellWidget(r, 0).currentText()
            step = {"type": t}
            if t == "press":
                step["button"] = self.table.cellWidget(r, 1).currentText()
                step["hold"] = self.table.cellWidget(r, 3).value()
                step["count"] = self.table.cellWidget(r, 4).value()
            elif t == "wait":
                step["seconds"] = self.table.cellWidget(r, 2).value()
            elif t in ["wait_for_text", "find_and_select_text", "type_text"]:
                step["text"] = self.table.cellWidget(r, 5).text()
            seq.append(step)
        return seq

    def update_highlight(self):
        if not self.overlay_state:
            return
        with self.overlay_state.lock:
            active_idx = self.overlay_state.current_step_idx
            is_running = self.overlay_state.running
        
        if is_running:
            self.btn_test.setText("Stop Test")
        else:
            self.btn_test.setText("Test Run")
        
        # If not running or active_idx is out of range, clear highlights
        if not is_running or active_idx < 0 or active_idx >= self.table.rowCount():
            for r in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    w = self.table.cellWidget(r, col)
                    if w:
                        w.setStyleSheet("")
            return

        # Highlight the active row and reset others
        for r in range(self.table.rowCount()):
            is_active = (r == active_idx)
            for col in range(self.table.columnCount()):
                w = self.table.cellWidget(r, col)
                if w:
                    if is_active:
                        w.setStyleSheet("background-color: #1a4f76; color: #ffffff; border: 1px solid #007acc; border-radius: 4px;")
                    else:
                        w.setStyleSheet("")
                        
        # Auto-scroll to the active row
        self.table.scrollTo(self.table.model().index(active_idx, 0))


class OverlayState:
    _UNSET = object()

    def __init__(self, presets, active_preset, show_background):
        self.lock = threading.Lock()
        self.phase_label = ""
        self.countdown = 0
        self.active_button = None
        self.highlight_buttons = set()
        self.holding_rt = False
        self.running = True
        self.pause_event = threading.Event()
        self.presets = presets
        self.active_preset = active_preset
        self.show_background = show_background
        self.latest_frame = None
        self.target_window_title = None
        self.current_step_idx = -1

    def update(self, phase_label=_UNSET, countdown=_UNSET, active_button=_UNSET, highlight_buttons=_UNSET, holding_rt=_UNSET, latest_frame=_UNSET, current_step_idx=_UNSET):
        with self.lock:
            if phase_label is not self._UNSET:
                self.phase_label = phase_label
            if countdown is not self._UNSET:
                self.countdown = countdown
            if active_button is not self._UNSET:
                self.active_button = active_button
            if highlight_buttons is not self._UNSET:
                self.highlight_buttons = highlight_buttons or set()
            if holding_rt is not self._UNSET:
                self.holding_rt = holding_rt
            if latest_frame is not self._UNSET:
                self.latest_frame = latest_frame
            if current_step_idx is not self._UNSET:
                self.current_step_idx = current_step_idx

    def snapshot(self):
        with self.lock:
            return (self.phase_label, self.countdown, self.active_button,
                    self.highlight_buttons.copy(), self.holding_rt, self.running,
                    self.show_background, self.latest_frame)

    def toggle_running(self):
        with self.lock:
            self.running = not self.running
            if self.running:
                self.pause_event.set()
            else:
                self.pause_event.clear()


class XboxControllerWidget(QWidget):
    def __init__(self, overlay_state):
        super().__init__()
        self.state = overlay_state
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_Hover)

        screen = QApplication.primaryScreen().geometry()
        self.cw, self.ch = 480, 370
        self.setGeometry(
            screen.width() - self.cw - 20,
            screen.height() - self.ch - 20,
            self.cw, self.ch
        )
        
        self.btn_rect = QRect(self.cw - 82, 14, 68, 28)
        self.settings_rect = QRect(14, 14, 28, 28)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

        self.flash = 0.0
        self.drag_pos = None
        self.is_hovered = False

    def enterEvent(self, event):
        self.is_hovered = True
        self.update()

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.btn_rect.contains(event.pos()):
                self.state.toggle_running()
                return
            if self.settings_rect.contains(event.pos()):
                show_bg = self.state.snapshot()[6]
                if show_bg or self.is_hovered:
                    self.open_settings()
                    return
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(event.globalPos() - self.drag_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = None

    def open_settings(self):
        if hasattr(self, 'settings_dialog') and self.settings_dialog.isVisible():
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return

        with self.state.lock:
            presets_copy = {k: [step.copy() for step in v] for k, v in self.state.presets.items()}
            active = self.state.active_preset
            show_bg = self.state.show_background
            
        self.settings_dialog = SettingsDialog(presets_copy, active, show_bg, self.state)
        self.settings_dialog.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.settings_dialog.accepted.connect(self._on_settings_saved)
        self.settings_dialog.show()

    def _on_settings_saved(self):
        if self.settings_dialog.active_preset in self.settings_dialog.presets:
            self.settings_dialog.presets[self.settings_dialog.active_preset] = self.settings_dialog.get_sequence()
        new_presets = self.settings_dialog.presets
        new_active = self.settings_dialog.active_preset
        new_bg = self.settings_dialog.bg_checkbox.isChecked()
        with self.state.lock:
            self.state.presets = new_presets
            self.state.active_preset = new_active
            self.state.show_background = new_bg
        save_settings(new_presets, new_active, new_bg)

    def tick(self):
        self.flash = (self.flash + 0.05) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        phase, countdown, active_button, highlights, holding_rt, running, show_bg, _ = self.state.snapshot()

        cx, cy = self.cw // 2, self.ch // 2 - 10

        self.draw_background(painter, cx, cy, running, phase, active_button, highlights, show_bg)
        self.draw_controller_body(painter, cx, cy)
        self.draw_triggers(painter, cx, cy, highlights, holding_rt)
        self.draw_bumpers(painter, cx, cy, highlights)
        self.draw_dpad(painter, cx, cy, highlights)
        self.draw_left_stick(painter, cx, cy, highlights)
        self.draw_right_stick(painter, cx, cy, highlights)
        self.draw_face_buttons(painter, cx, cy, highlights)
        self.draw_center_cluster(painter, cx, cy, highlights)
        self.draw_countdown(painter, cx, countdown, phase, active_button)

    def draw_background(self, painter, cx, cy, running, phase, active_button, highlights, show_bg):
        if show_bg:
            painter.setBrush(QColor(8, 8, 12, 200))
            painter.setPen(QPen(QColor(50, 50, 70, 80), 1))
            painter.drawRoundedRect(4, 4, self.cw - 8, self.ch - 8, 14, 14)
        else:
            # Draw a 1-opacity background so the mouse events still hit the entire bounding box
            painter.setBrush(QColor(0, 0, 0, 1))
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, self.cw, self.ch)

        if show_bg or self.is_hovered:
            s_rect = self.settings_rect
            painter.setBrush(QColor(50, 50, 70, 150))
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
            painter.drawRoundedRect(s_rect, 6, 6)
            painter.setPen(QColor(255, 255, 255, 220))
            painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
            painter.drawText(s_rect, Qt.AlignCenter, "⚙")

        # Start/Stop button
        if show_bg or self.is_hovered:
            bx, by, bw, bh = self.btn_rect.getRect()
            if running:
                bg = QColor(200, 50, 50, 200)
                icon = "\u25A0 Stop" 
                icon_color = QColor(255, 200, 200)
            else:
                bg = QColor(50, 200, 80, 200)
                icon = "\u25B6 Start"
                icon_color = QColor(200, 255, 200)

            btn_grad = QLinearGradient(bx, by, bx, by + bh)
            btn_grad.setColorAt(0, bg.lighter(120))
            btn_grad.setColorAt(1, bg.darker(110))
            
            painter.setBrush(QBrush(btn_grad))
            painter.setPen(QPen(QColor(255, 255, 255, 100), 1.5))
            painter.drawRoundedRect(bx, by, bw, bh, bh // 2, bh // 2)
            
            painter.setPen(icon_color)
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(self.btn_rect, Qt.AlignCenter, icon)

    def draw_controller_body(self, painter, cx, cy):
        w, h = 340, 220
        x, y = cx - w // 2, cy - h // 2 + 10

        shadow = QPainterPath()
        shadow.moveTo(x + 70, y + 35)
        shadow.cubicTo(x + w * 0.3, y + 25, x + w * 0.7, y + 25, x + w - 70, y + 35)
        shadow.cubicTo(x + w - 10, y + 40, x + w + 15, y + 70, x + w + 20, y + 110)
        shadow.cubicTo(x + w + 25, y + 170, x + w - 10, y + h + 10, x + w - 40, y + h + 10)
        shadow.cubicTo(x + w - 60, y + h + 10, x + w - 70, y + h - 20, cx + 40, y + h - 30)
        shadow.cubicTo(cx + 20, y + h - 35, cx - 20, y + h - 35, cx - 40, y + h - 30)
        shadow.cubicTo(x + 70, y + h - 20, x + 60, y + h + 10, x + 40, y + h + 10)
        shadow.cubicTo(x + 10, y + h + 10, x - 25, y + 170, x - 20, y + 110)
        shadow.cubicTo(x - 15, y + 70, x + 10, y + 40, x + 70, y + 35)
        shadow.closeSubpath()
        painter.setBrush(QColor(0, 0, 0, 100))
        painter.setPen(Qt.NoPen)
        painter.drawPath(shadow)

        body = QPainterPath()
        body.moveTo(x + 70, y + 25)
        body.cubicTo(x + w * 0.3, y + 15, x + w * 0.7, y + 15, x + w - 70, y + 25)
        body.cubicTo(x + w - 10, y + 30, x + w + 15, y + 60, x + w + 20, y + 100)
        body.cubicTo(x + w + 25, y + 160, x + w - 10, y + h, x + w - 40, y + h)
        body.cubicTo(x + w - 60, y + h, x + w - 70, y + h - 30, cx + 40, y + h - 40)
        body.cubicTo(cx + 20, y + h - 45, cx - 20, y + h - 45, cx - 40, y + h - 40)
        body.cubicTo(x + 70, y + h - 30, x + 60, y + h, x + 40, y + h)
        body.cubicTo(x + 10, y + h, x - 25, y + 160, x - 20, y + 100)
        body.cubicTo(x - 15, y + 60, x + 10, y + 30, x + 70, y + 25)
        body.closeSubpath()

        grad = QRadialGradient(cx, cy - 40, w * 0.8)
        grad.setColorAt(0, QColor(65, 65, 65))
        grad.setColorAt(0.6, QColor(40, 40, 40))
        grad.setColorAt(1, QColor(20, 20, 20))
        
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawPath(body)

        bump = QPainterPath()
        bump.moveTo(cx - 50, y + 18)
        bump.cubicTo(cx - 20, y + 5, cx + 20, y + 5, cx + 50, y + 18)
        painter.setPen(QPen(QColor(20, 20, 20, 150), 2))
        painter.drawPath(bump)

        seam = QPainterPath()
        seam.moveTo(x + 60, y + 28)
        seam.cubicTo(x + w * 0.3, y + 18, x + w * 0.7, y + 18, x + w - 60, y + 28)
        painter.setPen(QPen(QColor(20, 20, 20, 80), 2))
        painter.drawPath(seam)

    def draw_triggers(self, painter, cx, cy, highlights, holding_rt):
        tw, th = 60, 25
        lt_x, lt_y = cx - 120, cy - 100
        rt_x, rt_y = cx + 60, cy - 100

        for label, tx, ty in [("LT", lt_x, lt_y), ("RT", rt_x, rt_y)]:
            activated = (label == "RT" and holding_rt) or label in highlights
            path = QPainterPath()
            path.addRoundedRect(tx, ty, tw, th, 6, 6)

            if activated:
                grad = QLinearGradient(tx, ty, tx, ty + th)
                a = int(180 + 75 * self.flash)
                grad.setColorAt(0, QColor(0, 255, 150, a))
                grad.setColorAt(1, QColor(0, 180, 100, a))
                painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
            else:
                grad = QLinearGradient(tx, ty, tx, ty + th)
                grad.setColorAt(0, QColor(50, 50, 50))
                grad.setColorAt(1, QColor(15, 15, 15))
                painter.setPen(QPen(QColor(80, 80, 80), 1))

            painter.setBrush(QBrush(grad))
            painter.drawPath(path)

            painter.setPen(QColor(255, 255, 255) if activated else QColor(150, 150, 150))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            fm = QFontMetrics(painter.font())
            t_w = fm.horizontalAdvance(label)
            painter.drawText(tx + tw//2 - t_w//2, ty + 16, label)

    def draw_bumpers(self, painter, cx, cy, highlights):
        bw, bh = 80, 20
        lb_x, lb_y = cx - 145, cy - 75
        rb_x, rb_y = cx + 65, cy - 75

        for label, bx, by in [("LB", lb_x, lb_y), ("RB", rb_x, rb_y)]:
            activated = label in highlights
            path = QPainterPath()
            if label == "LB":
                path.moveTo(bx + bw, by + bh)
                path.lineTo(bx + 10, by + bh)
                path.cubicTo(bx, by + bh, bx - 10, by + 10, bx + 10, by)
                path.cubicTo(bx + 30, by - 5, bx + bw, by + 5, bx + bw, by + bh)
            else:
                path.moveTo(bx, by + bh)
                path.lineTo(bx + bw - 10, by + bh)
                path.cubicTo(bx + bw, by + bh, bx + bw + 10, by + 10, bx + bw - 10, by)
                path.cubicTo(bx + bw - 30, by - 5, bx, by + 5, bx, by + bh)

            if activated:
                grad = QLinearGradient(bx, by, bx, by + bh)
                a = int(180 + 75 * self.flash)
                grad.setColorAt(0, QColor(0, 220, 255, a))
                grad.setColorAt(1, QColor(0, 150, 200, a))
                painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
            else:
                grad = QLinearGradient(bx, by, bx, by + bh)
                grad.setColorAt(0, QColor(80, 80, 80))
                grad.setColorAt(1, QColor(30, 30, 30))
                painter.setPen(QPen(QColor(100, 100, 100), 1.5))

            painter.setBrush(QBrush(grad))
            painter.drawPath(path)

            painter.setPen(QColor(255, 255, 255) if activated else QColor(180, 180, 180))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            fm = QFontMetrics(painter.font())
            tw = fm.horizontalAdvance(label)
            painter.drawText(bx + bw//2 - tw//2, by + bh - 6, label)

    def _draw_stick(self, painter, sx, sy, r, activated, is_left):
        painter.setBrush(QColor(0, 0, 0, 150))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(sx - r - 2, sy - r + 4, r * 2, r * 2)

        outer = QRadialGradient(sx, sy, r)
        outer.setColorAt(0, QColor(50, 50, 50))
        outer.setColorAt(0.8, QColor(60, 60, 60))
        outer.setColorAt(1, QColor(30, 30, 30))
        painter.setBrush(QBrush(outer))
        painter.setPen(QPen(QColor(20, 20, 20), 1))
        painter.drawEllipse(sx - r, sy - r, r * 2, r * 2)

        ir = int(r * 0.75)
        inner = QRadialGradient(sx, sy + 5, ir)
        inner.setColorAt(0, QColor(25, 25, 25))
        inner.setColorAt(1, QColor(45, 45, 45))
        painter.setBrush(QBrush(inner))
        painter.setPen(QPen(QColor(70, 70, 70), 1.5))
        painter.drawEllipse(sx - ir, sy - ir, ir * 2, ir * 2)

        if activated:
            gp = QRadialGradient(sx, sy, r + 15)
            a = int(100 + 80 * self.flash)
            gp.setColorAt(0, QColor(0, 200, 255, a))
            gp.setColorAt(0.4, QColor(0, 200, 255, int(a * 0.5)))
            gp.setColorAt(1, QColor(0, 200, 255, 0))
            painter.setBrush(QBrush(gp))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(sx - r - 15, sy - r - 15, (r + 15) * 2, (r + 15) * 2)

    def draw_left_stick(self, painter, cx, cy, highlights):
        self._draw_stick(painter, cx - 85, cy - 20, 26, "LSTICK" in highlights, True)

    def draw_right_stick(self, painter, cx, cy, highlights):
        self._draw_stick(painter, cx + 50, cy + 30, 26, "RSTICK" in highlights, False)

    def draw_dpad(self, painter, cx, cy, highlights):
        dx, dy = cx - 50, cy + 30
        r = 28
        dish = QRadialGradient(dx, dy, r)
        dish.setColorAt(0, QColor(25, 25, 25))
        dish.setColorAt(0.8, QColor(40, 40, 40))
        dish.setColorAt(1, QColor(15, 15, 15))
        painter.setBrush(QBrush(dish))
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.drawEllipse(dx - r, dy - r, r * 2, r * 2)

        cw, cl = 16, 20
        up = "DPAD_UP" in highlights
        down = "DPAD_DOWN" in highlights
        left = "DPAD_LEFT" in highlights
        right = "DPAD_RIGHT" in highlights

        def get_grad(activated, is_vert):
            g = QLinearGradient()
            if is_vert:
                g.setStart(dx - cw/2, dy)
                g.setFinalStop(dx + cw/2, dy)
            else:
                g.setStart(dx, dy - cw/2)
                g.setFinalStop(dx, dy + cw/2)
            if activated:
                a = int(120 + 80 * self.flash)
                g.setColorAt(0, QColor(0, 200, 255, a))
                g.setColorAt(1, QColor(0, 150, 255, a))
            else:
                g.setColorAt(0, QColor(50, 50, 50))
                g.setColorAt(0.5, QColor(65, 65, 65))
                g.setColorAt(1, QColor(40, 40, 40))
            return g

        from PyQt5.QtGui import QLinearGradient
        painter.setPen(Qt.NoPen)
        painter.setBrush(get_grad(up, True))
        painter.drawRoundedRect(int(dx - cw/2), int(dy - cl), int(cw), int(cl), 2, 2)
        painter.setBrush(get_grad(down, True))
        painter.drawRoundedRect(int(dx - cw/2), int(dy), int(cw), int(cl), 2, 2)
        painter.setBrush(get_grad(left, False))
        painter.drawRoundedRect(int(dx - cl), int(dy - cw/2), int(cl), int(cw), 2, 2)
        painter.setBrush(get_grad(right, False))
        painter.drawRoundedRect(int(dx), int(dy - cw/2), int(cl), int(cw), 2, 2)

        painter.setBrush(QColor(30, 30, 30))
        painter.drawEllipse(int(dx - cw/2), int(dy - cw/2), int(cw), int(cw))

    def draw_face_buttons(self, painter, cx, cy, highlights):
        r = 13
        gap = 26
        fx, fy = cx + 105, cy - 35

        bg_r = gap + r + 4
        cavity = QRadialGradient(fx, fy, bg_r)
        cavity.setColorAt(0, QColor(40, 40, 40))
        cavity.setColorAt(1, QColor(50, 50, 50, 0))
        painter.setBrush(QBrush(cavity))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(fx - bg_r, fy - bg_r, bg_r * 2, bg_r * 2)

        btns = [
            ("Y", fx, fy - gap, QColor(255, 200, 0)),
            ("A", fx, fy + gap, QColor(0, 200, 50)),
            ("X", fx - gap, fy, QColor(0, 100, 255)),
            ("B", fx + gap, fy, QColor(255, 50, 50)),
        ]

        from PyQt5.QtGui import QLinearGradient
        for label, bx, by, color in btns:
            activated = label in highlights
            
            painter.setBrush(QColor(0, 0, 0, 150))
            painter.drawEllipse(bx - r - 1, by - r + 2, r * 2, r * 2)

            body_grad = QRadialGradient(bx, by - r//2, r * 1.5)
            if activated:
                body_grad.setColorAt(0, QColor(color.red(), color.green(), color.blue()))
                body_grad.setColorAt(1, QColor(color.red()//2, color.green()//2, color.blue()//2))
            else:
                body_grad.setColorAt(0, QColor(60, 60, 60))
                body_grad.setColorAt(1, QColor(10, 10, 10))
            
            painter.setBrush(QBrush(body_grad))
            painter.setPen(QPen(QColor(30, 30, 30), 1))
            painter.drawEllipse(bx - r, by - r, r * 2, r * 2)

            gloss = QPainterPath()
            gloss.addEllipse(bx - r + 2, by - r + 1, r * 2 - 4, r - 2)
            painter.setBrush(QColor(255, 255, 255, 40))
            painter.setPen(Qt.NoPen)
            painter.drawPath(gloss)

            letter_color = QColor(255, 255, 255) if activated else color
            painter.setPen(letter_color)
            painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
            fm = QFontMetrics(painter.font())
            tw = fm.horizontalAdvance(label)
            painter.drawText(bx - tw // 2, by + 5, label)

            if activated:
                gp = QRadialGradient(bx, by, r + 15)
                a = int(100 + 80 * self.flash)
                gp.setColorAt(0, QColor(color.red(), color.green(), color.blue(), a))
                gp.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
                painter.setBrush(QBrush(gp))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(bx - r - 15, by - r - 15, (r + 15) * 2, (r + 15) * 2)

    def draw_center_cluster(self, painter, cx, cy, highlights):
        guide_x, guide_y = cx + 5, cy - 35
        gs = 28

        g_grad = QRadialGradient(guide_x, guide_y, gs // 2)
        g_grad.setColorAt(0, QColor(240, 240, 240))
        g_grad.setColorAt(0.8, QColor(180, 180, 180))
        g_grad.setColorAt(1, QColor(100, 100, 100))
        
        painter.setBrush(QColor(0, 0, 0, 150))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(guide_x - gs // 2, guide_y - gs // 2 + 2, gs, gs)

        painter.setBrush(QBrush(g_grad))
        painter.setPen(QPen(QColor(60, 60, 60), 1.5))
        painter.drawEllipse(guide_x - gs // 2, guide_y - gs // 2, gs, gs)

        painter.setPen(QPen(QColor(40, 40, 40), 2))
        painter.drawLine(guide_x - 4, guide_y - 4, guide_x + 4, guide_y + 4)
        painter.drawLine(guide_x - 4, guide_y + 4, guide_x + 4, guide_y - 4)

        if "GUIDE" in highlights:
            gp = QRadialGradient(guide_x, guide_y, gs)
            a = int(150 + 80 * self.flash)
            gp.setColorAt(0, QColor(255, 255, 255, a))
            gp.setColorAt(1, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(gp))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(guide_x - gs, guide_y - gs, gs * 2, gs * 2)

        sz = 10
        for label, bx, by, is_menu in [
            ("BACK", cx - 30, cy - 10, False),
            ("START", cx + 40, cy - 10, True),
        ]:
            is_hl = label in highlights
            
            painter.setBrush(QColor(0, 0, 0, 150))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(bx - sz // 2, by - sz // 2 + 1, sz, sz)

            c = QColor(0, 200, 255) if is_hl else QColor(40, 40, 40)
            if is_hl:
                gp = QRadialGradient(bx, by, sz)
                a = int(140 + 80 * self.flash)
                gp.setColorAt(0, QColor(0, 200, 255, a))
                gp.setColorAt(1, QColor(0, 200, 255, 0))
                painter.setBrush(QBrush(gp))
            else:
                b_grad = QRadialGradient(bx, by, sz)
                b_grad.setColorAt(0, QColor(60, 60, 60))
                b_grad.setColorAt(1, QColor(20, 20, 20))
                painter.setBrush(QBrush(b_grad))
                
            painter.setPen(QPen(QColor(80, 80, 80) if not is_hl else QColor(255,255,255), 1))
            painter.drawEllipse(bx - sz // 2, by - sz // 2, sz, sz)

            painter.setPen(QColor(180, 180, 180) if not is_hl else QColor(255, 255, 255))
            if is_menu:
                painter.drawLine(bx - 3, by - 2, bx + 3, by - 2)
                painter.drawLine(bx - 3, by, bx + 3, by)
                painter.drawLine(bx - 3, by + 2, bx + 3, by + 2)
            else:
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(bx - 3, by - 2, 3, 3)
                painter.drawRect(bx, by, 3, 3)

        share_x, share_y = cx + 5, cy + 15
        sz_share = 8
        painter.setBrush(QColor(40, 40, 40))
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawEllipse(share_x - sz_share//2, share_y - sz_share//2, sz_share, sz_share)
        painter.setPen(QColor(180, 180, 180))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(share_x - 2, share_y - 1, 3, 2)
        painter.drawLine(share_x, share_y - 1, share_x, share_y - 3)

    def draw_countdown(self, painter, cx, countdown, phase_label, active_button):
        painter.setFont(QFont("Segoe UI", 16, QFont.Bold))

        show_bg = self.state.snapshot()[6]
        if not show_bg and not self.is_hovered:
            return

        if active_button:
            text = f"Press {active_button}"
        elif phase_label:
            text = phase_label
        elif countdown > 0:
            text = f"{countdown:.0f}s" if countdown >= 10 else f"{countdown:.1f}s"
        else:
            text = ""

        if text and countdown > 0:
            cnt = f"{countdown:.0f}s" if countdown >= 10 else f"{countdown:.1f}s"
            text = f"{text}  {cnt}"

        painter.setPen(QColor(255, 255, 255, 255))

        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text)
        tx = cx - tw // 2
        ty = 32

        painter.setBrush(QColor(0, 0, 0, 160))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(tx - 12, ty - 24, tw + 24, 34, 8, 8)
        painter.setPen(QColor(255, 255, 255, 255))
        painter.drawText(tx, ty, text)


def gamepad_loop(state):
    gamepad = vg.VX360Gamepad()
    hold_rt = False

    def press(btn_name, hold=0.1):
        vg_btn = BUTTON_MAP.get(btn_name)
        if vg_btn is None:
            return
        highlights = {"RT", btn_name} if hold_rt else {btn_name}
        state.update(active_button=btn_name, highlight_buttons=highlights)
        time.sleep(0.05)
        
        if state.running:
            gamepad.press_button(button=vg_btn)
            gamepad.update()
        
        iters = max(1, int(hold * 10))
        for _ in range(iters):
            if not state.running:
                break
            time.sleep(0.1)
            
        gamepad.release_button(button=vg_btn)
        gamepad.update()

    def find_text_on_screen(target_text):
        if not reader:
            return None
        frame = state.snapshot()[7] # latest_frame
        if frame is None:
            return None
        # Convert frame to something easyocr can use
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        results = reader.readtext(gray)
        for bbox, text, prob in results:
            if target_text.lower() in text.lower():
                return bbox
        return None

    state.update(phase_label="Starting..." if state.running else "Paused")
    if state.running:
        state.pause_event.set()

    while True:
        state.pause_event.wait()
        if not state.running:
            state.pause_event.clear()
            continue

        with state.lock:
            current_sequence = state.presets.get(state.active_preset, []).copy()

        for idx, phase in enumerate(current_sequence):
            if not state.running:
                break
            state.update(current_step_idx=idx)

            t = phase["type"]
            if t == "hold_rt":
                gamepad.right_trigger(value=255)
                gamepad.update()
                hold_rt = True
                state.update(phase_label="Holding RT...", highlight_buttons={"RT"}, holding_rt=True)
                time.sleep(0.5)

            elif t == "release_rt":
                gamepad.right_trigger(value=0)
                gamepad.update()
                hold_rt = False
                state.update(phase_label="RT released", highlight_buttons=set(), holding_rt=False)

            elif t == "wait":
                secs = float(phase.get("seconds", 0.0))
                label = "Holding RT..." if hold_rt else "Waiting..."
                state.update(phase_label=label)
                for tick in range(int(secs * 10), 0, -1):
                    if not state.running:
                        break
                    state.update(countdown=tick / 10.0)
                    time.sleep(0.1)

            elif t == "press":
                btn = phase["button"]
                hold = float(phase.get("hold", 0.1))
                count = int(phase.get("count", 1))
                for _ in range(count):
                    if not state.running:
                        break
                    press(btn, hold)
                    state.update(active_button=None, countdown=0, highlight_buttons={"RT"} if hold_rt else set())
                    time.sleep(0.1)
            
            elif t == "wait_for_text":
                target = phase.get("text", "")
                state.update(phase_label=f"Waiting for '{target}'...")
                while state.running:
                    if find_text_on_screen(target):
                        break
                    time.sleep(1.0)
                state.update(phase_label="")
                
            elif t == "find_and_select_text":
                target = phase.get("text", "")
                state.update(phase_label=f"Finding '{target}'...")
                bbox = None
                for _ in range(10): # try 10 times
                    if not state.running:
                        break
                    bbox = find_text_on_screen(target)
                    if bbox:
                        break
                    time.sleep(1.0)
                if bbox:
                    # Found it. We assume simple press A to select it.
                    press("A", 0.1)
                state.update(phase_label="")
                
            elif t == "type_text":
                target = phase.get("text", "")
                state.update(phase_label=f"Typing '{target}'...")
                target_title = None
                with state.lock:
                    target_title = state.target_window_title
                hwnd = get_target_window(target_title)
                if hwnd:
                    try:
                        import pyautogui
                        pyautogui.press('alt') # Wake up shell
                        win32gui.SetForegroundWindow(hwnd)
                        time.sleep(0.5)
                        pyautogui.write(target, interval=0.05)
                        time.sleep(0.5)
                        pyautogui.press('enter')
                    except Exception as e:
                        print("Error typing text:", e)
                state.update(phase_label="")

        if hold_rt and not state.running:
            gamepad.right_trigger(value=0)
            gamepad.update()
            hold_rt = False

        if state.running:
            state.update(phase_label="Restarting...", countdown=0, current_step_idx=-1)
            time.sleep(1)
            state.update(phase_label="")
        else:
            state.update(active_button=None, highlight_buttons=set(), holding_rt=False, phase_label="Stopped", countdown=0, current_step_idx=-1)


def wgc_capture_loop(state, window_name):
    if not WindowsCapture:
        return
    
    try:
        capture = WindowsCapture(
            window_name=window_name,
            cursor_capture=False,
            draw_border=False,
        )

        @capture.event
        def on_frame_arrived(frame, control):
            # Check if target window title has changed
            with state.lock:
                if state.target_window_title != window_name:
                    control.stop()
                    return

            # frame.as_numpy() returns BGRA
            img_bgra = frame.as_numpy()
            img_bgr = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
            
            # Dead frame filter: Ignore solid black or solid gray (204) frames
            avg = np.mean(img_bgr)
            if avg > 2 and abs(avg - 204) > 1:
                state.update(latest_frame=img_bgr)

        @capture.event
        def on_closed():
            print(f"[INFO] WGC Capture session closed for '{window_name}'")

        capture.start()
    except Exception as e:
        print(f"WGC Capture Error for '{window_name}':", e)

def capture_loop(state):
    current_title = None
    with mss.mss() as sct:
        while True:
            target_title = None
            with state.lock:
                target_title = state.target_window_title
            
            # If target changed and we have WGC available, start WGC session
            if WindowsCapture and target_title and target_title != current_title:
                current_title = target_title
                threading.Thread(target=wgc_capture_loop, args=(state, target_title), daemon=True).start()
            
            # Fallback: If no window is selected, capture the primary monitor
            if not target_title:
                try:
                    sct_img = sct.grab(sct.monitors[1])
                    img = np.array(sct_img)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    state.update(latest_frame=img)
                    current_title = None # Reset so selecting a window later works
                except Exception:
                    pass
            
            # The WGC capture runs in its own thread and updates state.latest_frame.
            # We sleep here to keep the monitoring loop alive and handle title changes.
            time.sleep(0.5)


class OBSPreviewWindow(QWidget):
    def __init__(self, overlay_state):
        super().__init__()
        self.state = overlay_state
        self.setWindowTitle("OBS Game Preview")
        self.resize(640, 360)
        self.setStyleSheet("background-color: black;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33) # 30 FPS
        self.current_pixmap = None

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.show_context_menu(event.globalPos())

    def show_context_menu(self, pos):
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2d2d2d; color: white; border: 1px solid #3a3a3a; padding: 4px; } QMenu::item:selected { background-color: #007acc; }")
        
        def callback(hwnd, hwnds):
            if not win32gui.IsWindow(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd)
            if not title:
                return True
            
            # Filter for visible or cloaked (virtual desktop) windows
            # and ignore very small/empty titles or system windows
            is_visible = win32gui.IsWindowVisible(hwnd)
            is_cloaked = is_window_cloaked(hwnd)
            
            if (is_visible or is_cloaked) and len(title) > 2:
                hwnds.append(title)
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)
        windows = sorted(list(set(windows)))
        
        for w in windows:
            if w.strip():
                action = menu.addAction(w)
                action.triggered.connect(lambda checked, title=w: self.set_target_window(title))
                
        menu.exec_(pos)
        
    def set_target_window(self, title):
        with self.state.lock:
            self.state.target_window_title = title

    def update_frame(self):
        frame = self.state.snapshot()[7]
        if frame is not None:
            # convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            q_img = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.current_pixmap = QPixmap.fromImage(q_img)
            self.update()

    def paintEvent(self, event):
        if self.current_pixmap:
            painter = QPainter(self)
            # scale pixmap to fit window while keeping aspect ratio
            scaled_pix = self.current_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled_pix.width()) // 2
            y = (self.height() - scaled_pix.height()) // 2
            painter.drawPixmap(x, y, scaled_pix)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forza Auto Skill Points")
    parser.add_argument("-pause", action="store_true", help="Start paused (no script runs on init)")
    parser.add_argument("-script", type=str, help="Run only the specified script by name")
    parser.add_argument("-controller", type=str, choices=["on", "off"], default="on", help="Show the controller overlay (default: on)")
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    
    initial_presets, initial_active, initial_bg = load_settings()
    
    if args.script:
        if args.script in initial_presets:
            initial_presets = {args.script: initial_presets[args.script]}
            initial_active = args.script
        else:
            print(f"Script '{args.script}' not found. Available: {list(initial_presets.keys())}")
            sys.exit(1)
    
    overlay_state = OverlayState(initial_presets, initial_active, initial_bg)
    
    if args.pause:
        overlay_state.running = False
    
    if args.controller == "on":
        widget = XboxControllerWidget(overlay_state)
        widget.show()
    
    preview = OBSPreviewWindow(overlay_state)
    preview.show()

    t_gamepad = threading.Thread(target=gamepad_loop, args=(overlay_state,), daemon=True)
    t_gamepad.start()
    
    t_capture = threading.Thread(target=capture_loop, args=(overlay_state,), daemon=True)
    t_capture.start()

    sys.exit(app.exec_())
