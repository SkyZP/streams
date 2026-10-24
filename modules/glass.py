import ctypes
import platform
from ctypes.wintypes import HWND, DWORD

def apply_glass_effect(window):
    if platform.system() == "Windows":
        hwnd = window.winId()
        if hasattr(hwnd, 'value'):
            hwnd = hwnd.value
        else:
            hwnd = int(hwnd)

        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState", DWORD),
                ("AccentFlags", DWORD),
                ("GradientColor", DWORD),
                ("AnimationId", DWORD)
            ]

        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", DWORD),
                ("Data", ctypes.POINTER(ACCENT_POLICY)),
                ("SizeOfData", ctypes.c_int)
            ]

        accent = ACCENT_POLICY()
        accent.AccentState = 3 
        accent.AccentFlags = 2
        accent.GradientColor = 0x01000000 

        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19
        data.SizeOfData = ctypes.sizeof(accent)
        data.Data = ctypes.pointer(accent)

        set_window_composition_attribute = ctypes.windll.user32.SetWindowCompositionAttribute
        set_window_composition_attribute(HWND(hwnd), ctypes.byref(data))