'''
@ author 2016024793 김유진
Simple middleware implementation - Format
- definition of topic class and other classes.
'''
import enum
import socket
import threading

class Format:
    def __init__(self, filename, filesize, value):
        self.FILENAME = filename
        self.FILESIZE = filesize
        self.VALUE = value

class Type(enum.Enum):
    PUB = 0
    SUB = 1

class Topic():
    def __init__(self, type, name):
        self.TYPE = type           # Publish or Subscribe
        self.NAME = name           # Instant name

    def __eq__(self, another):
        # a = hasattr(another, 'NAME') 
        return hasattr(another, 'NAME') and self.NAME == another.NAME 
    def __hash__(self):
        return hash(self.NAME)    

class Handler(threading.Thread):
    def __init__(self, client, local_ip, local_port):
        self.client_sock, self.client_addr = client
        self.local_ip = local_ip
        self.local_port = local_port

        threading.Thread.__init__(self)
    
    def run(self):
        try:
            cmd = self.client_sock.recv(1024).decode()
            # print('Client connected: ' + str(self.client_addr)+ ':' + cmd)
            try:
                func = getattr(self, cmd.split(' ')[0].upper())
                func(cmd)
            except AttributeError as e:
                print('ERROR: ' + str(self.client_addr) + ': Invalid command.')
                self.client_sock.send('550 Invalid Command')
        finally:
            self.client_sock.close()

class Sender(threading.Thread):
    def __init__(self, ip, port, msg):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.msg = msg

        threading.Thread.__init__(self)

    def create_connection(self):
        try:
            addr = (self.ip, self.port)
            self.socket.connect(addr)
            # print('Connected to: ', self.ip, ':', self.port)
        except Exception as e:
            print('Connection to: ', self.ip, ':', self.port, 'failed.', str(e))
            self.close_connection()
            return
    
    def close_connection(self):
        # print('Closing socket connection...')
        self.socket.close()
        # print('Sender terminating...')

    def start(self):
        self.create_connection()

        try:
            self.socket.send(self.msg.encode('utf-8'))
        except:
            print('Failed to send to: ', self.ip, ':', self.port)
            self.close_connection()
        
        tmp =''
        try:
            tmp = self.socket.recv(1024).decode('utf-8')
            # print('From', self.ip, ':', self.port, ':', tmp)
        except:
            print('Failed to recv from:', self.ip, ':', self.port)
        finally:
            self.close_connection()
            return tmp
