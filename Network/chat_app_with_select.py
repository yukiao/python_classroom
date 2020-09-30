"""
Mengimport module yang akan digunakan dalam program
"""
import select
import socket
import sys
import signal
import _pickle as cPickle 
import struct
import argparse

SERVER_HOST = 'localhost' # mendefenisikan host dengan 'localhost'
CHAT_SERVER_NAME = 'server' # nama untuk server yang akan dilempar sebaga argumen

def send(channel, *args):
    buffer = cPickle.dumps(args)        #mendefenisikan buffer yang menyimpan hasil serialisasi dari args
    value = socket.htonl(len(buffer))   #melakukan konvert 32 bit dari host byte ke network byte
    size = struct.pack("L", value)      #mengembalika objek byte
    channel.send(size)                  #mengirim data size ke socket yang lain
    channel.send(buffer)                #mengirim data buffer ke socket yang lain

def receive(channel):
    size = struct.calcsize("L")         #mengembalikan ukuran dari struct
    size = channel.recv(size)           #mengembalikab data yang diterima sebagai objek byte
    try:
        size = socket.ntohl(struct.unpack("L", size)[0])
    except struct.error:
        return ''
    buf = ""
    while len(buf) < size:
        buf = channel.recv(size-len(buf))
    return cPickle.loads(buf)[0]

"""
class server yang akan digunakan untuk mendefenisikan fungsi fungsi yang digunakan dalam server
"""
class ChatServer(object):
    def __init__(self, port, backlog=5):
        self.clients = 0
        self.clientmap = {}
        self.outputs = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((SERVER_HOST,port))
        print('Server listening to port: %s ...' %port)
        self.server.listen(backlog)
        signal.signal(signal.SIGINT, self.sighandler)

    def sighandler(self, signum, frame):
        print('Shutting down server...')
        for output in self.outputs:
            output.close()
        self.server.close()
    
    def get_client_name(self, client):
        info = self.clientmap[client]
        host, name = info[0][0], info[1]
        return '@'.join((name,host))

    def run(self):
        inputs = [self.server, sys.stdin]
        self.outputs = []
        running = True
        while running:
            try:
                readable, writeable, exceptional = \
                select.select(inputs, self.outputs,[])
            except select.error:
                break
            for sock in readable:
                if sock == self.server:
                    client, address = self.server.accept()
                    print("Chat server: got connection %d from %s" %(client.fileno(), address))
                    cname = receive(client).split('NAME: ')[1]
                    self.clients += 1
                    send(client, 'CLIENT: ' + str(address[0]))
                    inputs.append(client)
                    self.clientmap[client] = (address,cname)
                    msg = "\n(Connected: New client (%d) from %s)" %\
                    (self.clients, self.get_client_name(client))
                    for output in self.outputs:
                        send(output,msg)
                    self.outputs.append(client)
                elif sock == sys.stdin:
                    junk = sys.stdin.readline()
                    running = False
                else:
                    try:
                        data = receive(sock)
                        if data:
                            msg = '\n#[' + self.get_client_name(sock) + ']>>' + data
                            for output in self.outputs:
                                if output != sock:
                                    send(output, msg)
                        else:
                            print("Chat server: %d hung up" % sock.fileno())
                            self.clients -= 1
                            sock.close()
                            inputs.remove(sock)
                            self.outputs.remove(sock)
                            msg = "\n(Now hung up: Client from %s)" %self.get_client_name(sock)
                            for output in self.outputs:
                                send(output, msg)
                    except socket.error:
                        inputs.remove(sock)
                        self.outputs.remove(sock)
        self.server.close()

"""
Mendefenisikan class Chat Client untuk client dalam aplikasi
"""
class ChatClient(object):
    def __init__(self, name, port, host=SERVER_HOST):
        self.name = name
        self.connected = False
        self.host = host
        self.port = port
        self.prompt='[' + '@'.join((name, socket.gethostname().split('.')[0])) + ']> '
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, self.port))
            print("Now connected to chat server@ port %d" % self.port)
            self.connected = True
            send(self.sock, 'NAME: '+self.name)
            data = receive(self.sock)
            addr = data.split('CLIENT: ')[1]
            self.prompt = '[' + '@'.join((self.name, addr)) + ']> '
        except socket.error:
            print("Failed to connect to chat server @ port %d" % self.
port)
            sys.exit(1)

    def run(self):
        while self.connected:
            try:
                sys.stdout.write(self.prompt)
                sys.stdout.flush()
                readable, writeable, exceptional = select.select([0,self.sock], [], [])
                for sock in readable:
                    if sock == 0:
                        data = sys.stdin.readline().strip()
                        if data: send(self.sock, data)
                    elif sock == self.sock:
                        data = receive(self.sock)
                        if not data:
                            print('Client shutting down.')
                            self.connected = False
                            break
                        else:
                            sys.stdout.write(data + '\n')
                            sys.stdout.flush()
            
            except KeyboardInterrupt:
                print(" Client interrupted. ")
                self.sock.close()
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Socket Server Example with Select')
    parser.add_argument('--name', action="store", dest="name", required=True)
    parser.add_argument('--port', action="store", dest="port", type=int, required=True)
    given_args = parser.parse_args()
    port = given_args.port
    name = given_args.name
    if name == CHAT_SERVER_NAME:    #mengecek apakah name = CHAT_SERVER_NAME
        server = ChatServer(port)   #membuat objek ChatServer dengan argumen port
        server.run()    #memanggil function run dari objek server
    else:
        client = ChatClient(name=name, port=port)   #membuat objek ChatClient
        client.run()    #memanggil function run dari objek client