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
    buffer = cPickle.dumps(args)                            #mendefenisikan buffer yang menyimpan hasil serialisasi dari args
    value = socket.htonl(len(buffer))                       #melakukan konvert 32 bit dari host byte ke network byte
    size = struct.pack("L", value)                          #mengembalika objek byte
    channel.send(size)                                      #mengirim data size ke socket yang lain
    channel.send(buffer)                                    #mengirim data buffer ke socket yang lain

def receive(channel):
    size = struct.calcsize("L")                             #mengembalikan ukuran dari struct
    size = channel.recv(size)                               #mengembalikab data yang diterima sebagai objek byte
    try:
        size = socket.ntohl(struct.unpack("L", size)[0])    #konversi 32 bit integer dari network order ke host order.
    except struct.error:                                       #menangkap error
        return ''
    buf = ""
    while len(buf) < size:                                  #perulangan saat panjang dari buf kurang dari size        
        buf = channel.recv(size-len(buf))                   #menerima data dari socket
    return cPickle.loads(buf)[0]    #mengembalikan hierarki objek yang disusun kembali dari representasi data dari suatu objek.

"""
class server yang akan digunakan untuk mendefenisikan fungsi fungsi yang digunakan dalam server
"""
class ChatServer(object):
    def __init__(self, port, backlog=5):
        self.clients = 0    
        self.clientmap = {}
        self.outputs = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     #membuat soket dengan parameter ipv4 dan tcp
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   #mengatur nilai dari pilihan soket
        self.server.bind((SERVER_HOST,port))    #membinding soket dengan server host pada port tertentu
        print('Server listening to port: %s ...' %port) #menampilkan pesan saat server berjalan pada port tertentu
        self.server.listen(backlog) #membuat server dapat menerima koneksi dengan maksimal client sesuai dengan backlog
        signal.signal(signal.SIGINT, self.sighandler)   #mengatur handler untuk signal dengan method sighandler

    def sighandler(self, signum, frame):    #method untuk mengatur signal
        print('Shutting down server...')    #menampilkan pesan
        for output in self.outputs:         #melakukan perulangan 
            output.close()     #menutup socket
        self.server.close()     #menutup socket
    
    def get_client_name(self, client):  #method untuk mendapatkan nama client
        info = self.clientmap[client]       #assign nilai info dengan self.clientmap[client]
        host, name = info[0][0], info[1]    #assign nilai variabel host dan name dengan array info
        return '@'.join((name,host))    #mengembalikan string dengan format @....

    def run(self):  #amengeksekusi class ChatServer
        inputs = [self.server, sys.stdin]   #membuat array inputs
        self.outputs = []
        running = True
        while running:
            try:    #melakukan scanning error
                readable, writeable, exceptional = \
                select.select(inputs, self.outputs,[])
            except select.error:    #handling exception
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
    parser = argparse.ArgumentParser(description='Socket Server Example with Select')   #membuat objek ArgumentParser
    parser.add_argument('--name', action="store", dest="name", required=True)   #menambahkan argumen yang diambil dari terminal
    parser.add_argument('--port', action="store", dest="port", type=int, required=True) #menambahkan argumen yang diambil dari terminal
    given_args = parser.parse_args()    #Mengurai argumen yang ditambahkan sebelumnya  
    port = given_args.port  #Assign nilai given_args.port ke port
    name = given_args.name  #Assign nilai given_args.name ke name
    if name == CHAT_SERVER_NAME:    #mengecek apakah name = CHAT_SERVER_NAME
        server = ChatServer(port)   #membuat objek ChatServer dengan argumen port
        server.run()    #memanggil function run dari objek server
    else:
        client = ChatClient(name=name, port=port)   #membuat objek ChatClient
        client.run()    #memanggil function run dari objek client