"""
Simple tcp client
"""

import socket
import const_cs

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((const_cs.HOST, const_cs.PORT))  # connect to server (block until accepted)

s.send("Hello, world".encode('utf-8'))  # send encoded string as data
data = s.recv(1024)  # receive the response

print(data.decode('utf-8'))  # print the result

s.close()  # close the connection
