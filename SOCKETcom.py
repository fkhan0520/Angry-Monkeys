#imports
import socket
import os

#Serial Port
class ComSocket(socket._socketobject):
    #constructor
    def __init__(self, buffsize, comaddr):
        print comaddr
        try:
            os.remove("socks/monkeys_socket")
        except OSError:
            pass

        socket._socketobject.__init__(self, socket.AF_UNIX, socket.SOCK_STREAM, 0)
        self.bind("socks/monkeys_socket")
        self.BUFFSIZE = buffsize
        self.client = None

    def reconnect(self):
        # self.closeConn()
        # self.port = serial.Serial(portname, baudrate, timeout = 1)
        # self.port.flushInput()
        # self.port.flushOutput()

	    self.listen(1)

	    (self.client, addr) = self.accept()

    def closeConn(self):
        try:
            self.client.close()
            self.close()
        except:
            pass

    def sendData(self,data):
	    if self.client:
		    data = data + '\n'
		    self.client.send(data)
	    else:
		    print "Send failed, no client connected..."

    def receiveData(self):
        if self.client:
            data = self.client.recv(self.BUFFSIZE)
            return data
        else:
            print "Recv failed, no client connected..."
        
