"""
QRCode images for Tkinter.

>>> root = tk.Tk()
>>> qr_code = QRCodeImage(root, "We are the knights who say ni!")
>>> qr_code.pack()
"""
import tkinter as tk

import pyqrcode


class QRCodeImage(tk.Label):
    """Tkinter widget that renders a black and white QR code image."""

    def __init__(self, parent, qr_data, scale=8):
        """
        Tkinter widget that renders a black and white QR code image.

        Args:
            parent (tk.Frame): Tkinter parent frame
            qr_data (str): Data to store in the QR code
            scale (int, optional): Number of pixels per cell of the QR code image. Defaults to 8.
        """
        super().__init__(parent)

        code = pyqrcode.create(qr_data)

        code_bmp = tk.BitmapImage(data=code.xbm(
            scale=scale), foreground="black", background="white")

        # Save a references to the image
        #
        # @NOTE This is important because tkinter
        # does not automatically save a referece itself. If we don't do this,
        # the image will render completely transparent
        self.img = code_bmp
        self.config(image=code_bmp)
