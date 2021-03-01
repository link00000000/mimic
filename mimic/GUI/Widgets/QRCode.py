import tkinter as tk
import pyqrcode


class QRCodeImage(tk.Label):
    def __init__(self, parent, qr_data, scale=8):
        super().__init__(parent)

        code = pyqrcode.create(qr_data)

        code_bmp = tk.BitmapImage(data=code.xbm(
            scale=scale), foreground="black", background="white")

        # Save a references to the image @NOTE This is important because tkinter
        # does not automatically save a referece itself. If we don't do this,
        # the image will render completely transparent
        self.img = code_bmp
        self.config(image=code_bmp)
