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
                break   #menghentikan perulangan
            for sock in readable:   #melakukan perulangan pada list readable
                if sock == self.server:     #mengecek apakah sock == server
                    client, address = self.server.accept()  #server menerima koneksi dan mengassign nilainya ke client dan address
                    print("Chat server: got connection %d from %s" %(client.fileno(), address)) #menampilkan pesan saat server menerima koneksi
                    cname = receive(client).split('NAME: ')[1]  #assign nilai cname dengan menerima return dari method receive
                    self.clients += 1   #menambah nilai pada self.clients dengan 1
                    send(client, 'CLIENT: ' + str(address[0]))  #menjaankan method send
                    inputs.append(client)   #menambahkan client pada list inputs
                    self.clientmap[client] = (address,cname)    #assign nilai self.clientmap[client] dengan 
                    msg = "\n(Connected: New client (%d) from %s)" %\
                    (self.clients, self.get_client_name(client))    #assign  nilai msg
                    for output in self.outputs:     #looping pada list output
                        send(output,msg)        #memanggil method send 
                    self.outputs.append(client) #menambahkan isi list outputs dengan client
                elif sock == sys.stdin:         #jika sock = sys.stdin
                    junk = sys.stdin.readline() #membuat variabel junk
                    running = False             #reassign variabel running dengan false
                else:                           #saat kondisi if tidak ada yang terpenuhi
                    try:       #membuka blok try untuk scanning exeption                 
                        data = receive(sock) #assign nilai data dengan method receive   
                        if data:    #mengecekek jika data tidak kosong
                            msg = '\n#[' + self.get_client_name(sock) + ']>>' + data    #assign nilai dari variabel msg
                            for output in self.outputs: #looping terhadap list outpusts
                                if output != sock:  #mengecek jika output = sock
                                    send(output, msg)   #memanggil method send()
                        else:   #bila data ksoong
                            print("Chat server: %d hung up" % sock.fileno()) #menampilkan pessan
                            self.clients -= 1   #mengurangi jumlah clients
                            sock.close()    #menutup sock
                            inputs.remove(sock) #menghapus sock dari inputs
                            self.outputs.remove(sock)   #menghapus sock dari outputs
                            msg = "\n(Now hung up: Client from %s)" %self.get_client_name(sock) #assign nilai msg
                            for output in self.outputs: #looping pada outputs
                                send(output, msg)   #memanggil method send
                    except socket.error:    #menagkap error socket.error
                        inputs.remove(sock)     #menghapus sock dari list inputs
                        self.outputs.remove(sock)   #menghapus sock dari outputs
        self.server.close() #menutup server

"""
Mendefenisikan class Chat Client untuk client dalam aplikasi
"""
class ChatClient(object):
    def __init__(self, name, port, host=SERVER_HOST):   #constructor dari class Chat client
        self.name = name
        self.connected = False
        self.host = host
        self.port = port
        self.prompt='[' + '@'.join((name, socket.gethostname().split('.')[0])) + ']> '  #assign nilai dari prompt
        try:    #scanning error
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #membuat socket dengan parameter ipv4 dan tcp
            self.sock.connect((host, self.port))    #melakukan koneksi ke host pada port tertentu
            print("Now connected to chat server@ port %d" % self.port)  #menampilkan pesan saat telah konek ke server
            self.connected = True   #assign connected dengan true
            send(self.sock, 'NAME: '+self.name) #memanggil method send
            data = receive(self.sock)   #assign nilai data dengan return value dari receive(self.sock)
            addr = data.split('CLIENT: ')[1]    #assign nilai addr dari data
            self.prompt = '[' + '@'.join((self.name, addr)) + ']> ' #assgin prompt
        except socket.error:    #menangkap socket.error
            print("Failed to connect to chat server @ port %d" % self.
port)   #menampilakan pesan saat gagal terhubung ke server
            sys.exit(1) #keluar dari program

    def run(self):      #method run untuk menjalankan class ChatClient
        while self.connected:   #looping saat client connect ke server
            try:    #scanning error
                sys.stdout.write(self.prompt)   #digunakan dalam menampilkan pesan
                sys.stdout.flush()  #membersihkan internal buffer pada file
                readable, writeable, exceptional = select.select([0,self.sock], [], []) #assign nilai readable, writable, exceptional dengan select.select()
                for sock in readable:   #looping pada list readable
                    if sock == 0:   #jika sock = 0
                        data = sys.stdin.readline().strip() #menghapus trailing character pada awal dan akhir 
                        if data: send(self.sock, data)  #jika data ada maka memanggil method send
                    elif sock == self.sock: #jika sock = self.sock
                        data = receive(self.sock)   #assign nilai data dengan return value dari recevive
                        if not data:    #jika data kosong
                            print('Client shutting down.')  #menampilkan pesan shutting down
                            self.connected = False  #reassign connected dengan False
                            break
                        else:
                            sys.stdout.write(data + '\n')   #writing pada sys.stdout
                            sys.stdout.flush()  ##membersihkan internal buffer pada file
            
            except KeyboardInterrupt:   #menangkap exception saat terjadi interupsi dari keyboar
                print(" Client interrupted. ")  #menampilkan pesan interupsi
                self.sock.close()   #menutup self.sock
                break   #menghentikan looping

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