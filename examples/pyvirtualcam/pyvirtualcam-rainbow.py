from colorsys import hsv_to_rgb

import numpy as np
import pyvirtualcam

with pyvirtualcam.Camera(width=1280, height=720, fps=30) as cam:
    while True:
        frame = np.zeros((cam.height, cam.width, 4), np.uint8)  # RGBA
        # Convert HSV to RGB
        color = [
            x * 255 for x in hsv_to_rgb((cam.frames_sent % 255) / 255, 1, 1)]

        frame[:, :, 0] = color[0]
        frame[:, :, 1] = color[1]
        frame[:, :, 2] = color[2]
        frame[:, :, 3] = 255

        cam.send(frame)
        cam.sleep_until_next_frame()
