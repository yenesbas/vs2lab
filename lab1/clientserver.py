"""
Client and server using classes
"""

import logging
import socket

import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

#pylint: disable=logging-not-lazy, line-too-long

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket " + str(self.sock))

        self.telefonbuch = {
            "Alpha": "0176-12345678",
            "Beta": "0176-23456789", 
            "Gamma": "0176-123123123",
            "Hakim": 13245,
            "Florian": 13245,
            "Yusuf": 13245, 
            "Korn": 13245,
            "Weber": 54321,
            "Hofmann": 15643,
            "Mueller": 49122,
            "Schmidt": 49233,
            "Schneider": 49344,
            "Fischer": 49455,
            "Meyer": 49566,
            "Wagner": 49677,
            "Becker": 49788,
            "Schulz": 49899,
            "Hoffmann": 49910,
            "Koch": 50011,
            "Bauer": 50022,
            "Richter": 50033,
            "Klein": 50044,
            "Wolf": 50055,
            "Neumann": 50066,
            "Schwarz": 50077,
            "Zimmermann": 50088,
            "Braun": 50099,
            "Krueger": 50110,
            "Hartmann": 50132,
            "Lange": 50143,
            "Schmitt": 50154,
            "Werner": 50165,
            "Schmitz": 50176,
            "Krause": 50187,
            "Meier": 50198,
            "Lehmann": 50209,
            "Schmid": 50220,
            "Schaefer": 50231,
            "Maier": 50242,
            "Keller": 50253,
            "Huber": 50264,
            "Mayer": 50275,
            "Kaiser": 50286,
            "Vogel": 50297,
            "Fuchs": 50308,
            "Lang": 50319,
            "Weiss": 50330,
            "Peters": 50341,
            "Scholz": 50352,
            "Jung": 50363,
            "Moeller": 50374,
            "Hahn": 50385,
            "Koenig": 50396,
            "Walter": 50407,
            "Kaiser": 50418
        }



    def handle_request(self, request):
        if request.startswith("GETALL"):
            entries = [f"{name}: {nummer}" for name, nummer in self.telefonbuch.items()]
            return "\n".join(entries)
        elif request.startswith("GET"):
            name_list = request.split(" ")
            name = name_list[1]
            number = self.telefonbuch.get(name)
            return f"{name}: {number}\n"

    def serve(self):
        """ Serve echo """
        self.sock.listen(1)
        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                # pylint: disable=unused-variable
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    if not data:
                        break  # stop if client stopped
                    response = self.handle_request(data.decode('ascii'))
                    connection.send(response.encode('ascii'))  # return sent data plus an "*"
                connection.close()  # close the connection
            except socket.timeout:
                pass  # ignore timeouts
        self.sock.close()
        self._logger.info("Server down.")


class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket " + str(self.sock))

    def call(self, request):
        """ Call server """
        self.sock.send(request.encode('ascii'))  # send encoded string as data
        data = self.sock.recv(1024)  # receive the response
        response = data.decode('ascii')
        self.sock.close()  # close the connection
        self.logger.info("Client down.")
        return response

    def GET(self, name):
        response = self.call(f"GET {name}")
        print(response)
    
    def GETALL(self):
        response = self.call("GETALL")
        print(response)

    def close(self):
        """ Close socket """
        self.sock.close()