import socket
s = socket.socket()
s.settimeout(3)
try:
    s.connect(("127.0.0.1", 8080))
    print("Burp UP")
except Exception as e:
    print("Burp DOWN:", e)
