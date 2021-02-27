from mimic.EventEmitter import EventEmitter
import tkinter as tk


class Application(tk.Frame, EventEmitter):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.hi_there = tk.Button(self)
        self.hi_there["text"] = "Hello, world!\n(Click me)"
        self.hi_there["command"] = self.say_hi
        self.hi_there.pack(side="top")

        self.text_area = tk.Text(self)
        self.text_area.pack()

        self.close_btn = tk.Button(self, text="QUIT", fg="red",
                                   command=self.quit)
        self.close_btn.pack(side="bottom")

    def quit(self):
        self.master.destroy()
        self._emit("quit")

    def say_hi(self):
        print("Hi there! 👋")
