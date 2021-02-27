from src.GUI import Application
import asyncio
from src.Server import Server
from threading import Thread, Event
from signal import signal, SIGINT, SIGTERM
import tkinter as tk
from src.Pipeable import StringMessage

stop_event = Event()


def stop_handler(signal_number, frame):
    stop_event.set()


def run_server(server: Server):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(server.start())


def run_gui(app: Application):
    app.mainloop()


def main():
    signal(SIGINT, stop_handler)
    signal(SIGTERM, stop_handler)

    server = Server(stop_event=stop_event)
    server_thread = Thread(target=run_server, args=[server])
    server_thread.start()

    gui = Application(master=tk.Tk())

    @gui.on('quit')
    def on_gui_quit():
        print("Stopping...")
        stop_event.set()

    # Main loop
    while True:
        if stop_event.is_set():
            break

        # Get data from web server
        if server.pipe.poll():
            data = server.pipe.recv()

            if data.isType(StringMessage):
                gui.text_area.insert(tk.INSERT, data.payload.rstrip() + '\n')

        # Update GUI
        gui.update_idletasks()
        gui.update()

    server_thread.join()


if __name__ == "__main__":
    main()
