"""
Cross-Virtual-Desktop capture for DX12 windows (Forza Horizon 6).

Uses IVirtualDesktopManager COM interface to:
1. Detect if the target window is on a different virtual desktop
2. Temporarily move it to the current desktop for capture
3. Move it back when done

Usage:
    from cross_desktop_capture import CrossDesktopCapture

    cap = CrossDesktopCapture(target_title="Forza Horizon 6")
    cap.move_to_current_desktop()  # move game to this desktop
    # ... run your WGC/MSS capture loop normally ...
    cap.restore_desktop()          # move game back to original desktop
"""

import ctypes
from ctypes import wintypes, POINTER, byref, c_void_p, c_bool, c_uint32
import win32gui


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]

    def __eq__(self, other):
        if not isinstance(other, GUID):
            return False
        return (
            self.Data1 == other.Data1
            and self.Data2 == other.Data2
            and self.Data3 == other.Data3
            and bytes(self.Data4) == bytes(other.Data4)
        )

    def __repr__(self):
        data4_hex = "".join(f"{b:02X}" for b in bytearray(self.Data4))
        return f"{{{self.Data1:08X}-{self.Data2:04X}-{self.Data3:04X}-{data4_hex[:4]}-{data4_hex[4:]}}}"


# CLSID_VirtualDesktopManager = {AA509086-5CA9-4C25-8F95-589D3C07B48A}
CLSID_VirtualDesktopManager = GUID(
    0xAA509086, 0x5CA9, 0x4C25,
    (0x8F, 0x95, 0x58, 0x9D, 0x3C, 0x07, 0xB4, 0x8A),
)

# IID_IVirtualDesktopManager = {A5CD92FF-29BE-454C-8D04-D82879FB3F1B}
IID_IVirtualDesktopManager = GUID(
    0xA5CD92FF, 0x29BE, 0x454C,
    (0x8D, 0x04, 0xD8, 0x28, 0x79, 0xFB, 0x3F, 0x1B),
)


# IVirtualDesktopManager vtable layout (IUnknown + 3 methods)
class IVirtualDesktopManagerVtbl(ctypes.Structure):
    _fields_ = [
        ("QueryInterface", ctypes.c_void_p),
        ("AddRef", ctypes.c_void_p),
        ("Release", ctypes.c_void_p),
        ("IsWindowOnCurrentVirtualDesktop", ctypes.c_void_p),
        ("GetWindowDesktopId", ctypes.c_void_p),
        ("MoveWindowToDesktop", ctypes.c_void_p),
    ]


# COM method prototypes (HRESULT = LONG)
LONG = wintypes.LONG

IsWindowOnCurrentVirtualDesktopProto = ctypes.WINFUNCTYPE(
    LONG, c_void_p, wintypes.HWND, POINTER(c_bool)
)
GetWindowDesktopIdProto = ctypes.WINFUNCTYPE(
    LONG, c_void_p, wintypes.HWND, POINTER(GUID)
)
MoveWindowToDesktopProto = ctypes.WINFUNCTYPE(
    LONG, c_void_p, wintypes.HWND, POINTER(GUID)
)


def _get_vdm_vtable(vdm_ptr):
    """Return the vtable pointer from a COM interface pointer."""
    ppv = ctypes.cast(vdm_ptr, POINTER(c_void_p))
    vtable = ctypes.cast(ppv.contents, POINTER(IVirtualDesktopManagerVtbl))
    return vtable.contents


def _ensure_com_initialized():
    """Ensure COM is initialized for the current thread (best-effort)."""
    ole32 = ctypes.windll.ole32
    # COINIT_APARTMENTTHREADED = 2; also try 0 (COINIT_MULTITHREADED)
    for flags in (2, 0):
        hr = ole32.CoInitializeEx(None, flags)
        if hr >= 0:
            return
        # 0x80010106 = RPC_E_CHANGED_MODE (already init'd with different mode)
        if (hr & 0xFFFFFFFF) == 0x80010106:
            continue
    # If we get here, COM is in some state; proceed anyway


_ensure_com_initialized()


def _create_virtual_desktop_manager():
    """Create an instance of IVirtualDesktopManager via CoCreateInstance."""
    ole32 = ctypes.windll.ole32

    vdm_ptr = c_void_p()
    hr = ole32.CoCreateInstance(
        byref(CLSID_VirtualDesktopManager),
        None,
        1,  # CLSCTX_INPROC_SERVER
        byref(IID_IVirtualDesktopManager),
        byref(vdm_ptr),
    )
    if hr < 0:
        raise OSError(f"CoCreateInstance failed: 0x{hr & 0xFFFFFFFF:08X}")
    return vdm_ptr


def get_window_hwnd(title_substring):
    """Find a window HWND by title substring (case-insensitive)."""
    result = ctypes.c_void_p()

    def callback(hwnd, _):
        if not win32gui.IsWindow(hwnd):
            return True
        text = win32gui.GetWindowText(hwnd)
        if title_substring.lower() in text.lower():
            ctypes.cast(ctypes.byref(result), POINTER(c_void_p))[0] = hwnd
            return False
        return True

    win32gui.EnumWindows(callback, None)
    return result


def _to_hwnd(hwnd):
    """Normalize to wintypes.HWND, accepting int or c_void_p."""
    if isinstance(hwnd, wintypes.HWND):
        return hwnd
    return wintypes.HWND(hwnd)


def is_window_on_current_desktop(hwnd):
    """Check if the given window is on the currently active virtual desktop."""
    hwnd = _to_hwnd(hwnd)
    vdm_ptr = _create_virtual_desktop_manager()
    vtable = _get_vdm_vtable(vdm_ptr)
    func = IsWindowOnCurrentVirtualDesktopProto(vtable.IsWindowOnCurrentVirtualDesktop)

    on_current = c_bool()
    hr = func(vdm_ptr, hwnd, byref(on_current))
    if hr < 0:
        raise OSError(f"IsWindowOnCurrentVirtualDesktop failed: 0x{hr & 0xFFFFFFFF:08X}")
    return on_current.value


def get_window_desktop_id(hwnd):
    """Get the virtual desktop GUID for the window."""
    hwnd = _to_hwnd(hwnd)
    vdm_ptr = _create_virtual_desktop_manager()
    vtable = _get_vdm_vtable(vdm_ptr)
    func = GetWindowDesktopIdProto(vtable.GetWindowDesktopId)

    desktop_id = GUID()
    hr = func(vdm_ptr, hwnd, byref(desktop_id))
    if hr < 0:
        raise OSError(f"GetWindowDesktopId failed: 0x{hr & 0xFFFFFFFF:08X}")
    return desktop_id


def move_window_to_desktop(hwnd, desktop_id):
    """Move a window to the specified virtual desktop."""
    hwnd = _to_hwnd(hwnd)
    vdm_ptr = _create_virtual_desktop_manager()
    vtable = _get_vdm_vtable(vdm_ptr)
    func = MoveWindowToDesktopProto(vtable.MoveWindowToDesktop)

    hr = func(vdm_ptr, hwnd, byref(desktop_id))
    if hr < 0:
        raise OSError(f"MoveWindowToDesktop failed: 0x{hr & 0xFFFFFFFF:08X}")


def is_window_cloaked(hwnd):
    """Check if a window is cloaked by DWM (DWMWA_CLOAKED = 14)."""
    cloaked = ctypes.c_int(0)
    ctypes.windll.dwmapi.DwmGetWindowAttribute(
        hwnd, 14, byref(cloaked), ctypes.sizeof(cloaked),
    )
    return bool(cloaked.value)


def get_current_desktop_id():
    """Get the GUID of the currently active virtual desktop.

    Uses the foreground window (which is always on the current desktop)."""
    hwnd = win32gui.GetForegroundWindow()
    if hwnd:
        return get_window_desktop_id(hwnd)
    # Last-resort fallback: create a hidden message-only window
    return _get_desktop_id_via_message_window()


def _get_desktop_id_via_message_window():
    """Create a temporary message window to get current desktop ID."""
    import atexit

    wc = wintypes.WNDCLASSEXW()
    wc.cbSize = ctypes.sizeof(wc)
    wc.lpfnWndProc = ctypes.WINFUNCTYPE(
        wintypes.LPARAM, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    )(lambda h, m, w, l: ctypes.windll.user32.DefWindowProcW(h, m, w, l))
    wc.hInstance = ctypes.windll.kernel32.GetModuleHandleW(None)
    wc.lpszClassName = "CrossDesktopCaptureTemp"

    ctypes.windll.user32.RegisterClassExW(byref(wc))
    hwnd = ctypes.windll.user32.CreateWindowExW(
        0, wc.lpszClassName, "", 0, 0, 0, 0, 0, None, None, wc.hInstance, None,
    )
    atexit.register(lambda: ctypes.windll.user32.DestroyWindow(hwnd))
    return get_window_desktop_id(hwnd)


class CrossDesktopCapture:
    """Manage cross-virtual-desktop window capture.

    Moves the target window to the current virtual desktop so that
    WGC / BitBlt / MSS can capture it, and optionally moves it back.
    """

    def __init__(self, target_title=None, hwnd=None):
        self._vdm_ptr = None
        self._original_desktop_id = None
        self._moved = False

        if hwnd is not None:
            self.hwnd = wintypes.HWND(hwnd)
        elif target_title is not None:
            self.hwnd = get_window_hwnd(target_title)
            if self.hwnd is None or self.hwnd.value is None:
                raise ValueError(f"No window found matching: {target_title}")
        else:
            raise ValueError("Must provide target_title or hwnd")

    @property
    def is_on_current_desktop(self):
        return is_window_on_current_desktop(self.hwnd)

    @property
    def is_cloaked(self):
        return is_window_cloaked(self.hwnd)

    @property
    def original_desktop_id(self):
        if self._original_desktop_id is None:
            self._original_desktop_id = get_window_desktop_id(self.hwnd)
        return self._original_desktop_id

    def move_to_current_desktop(self):
        """Move the target window to the current virtual desktop."""
        if self._moved:
            return

        if is_window_on_current_desktop(self.hwnd):
            self._moved = True
            return

        self._original_desktop_id = get_window_desktop_id(self.hwnd)
        current_id = get_current_desktop_id()

        if self._original_desktop_id == current_id:
            self._moved = True
            return

        move_window_to_desktop(self.hwnd, current_id)
        self._moved = True

    def restore_desktop(self):
        """Move the target window back to its original virtual desktop."""
        if not self._moved or self._original_desktop_id is None:
            return

        current_id = get_current_desktop_id()
        if self._original_desktop_id != current_id:
            move_window_to_desktop(self.hwnd, self._original_desktop_id)

        self._moved = False

    def __enter__(self):
        self.move_to_current_desktop()
        return self

    def __exit__(self, *args):
        self.restore_desktop()
