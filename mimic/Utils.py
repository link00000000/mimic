import socket


def resolve_host():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect(("8.8.8.8", 80))

    host = sock.getsockname()[0]
    sock.close()

    return host
