'''
각 구독자 마다 데이터 리더 라이터 관리.
'''
import threading
import socket
import socketserver
import format

class PublisherManager:
    def __init__(self):
        self.topic = {}         # topic list. topic:data
        self.subscribers = {}   # subscriber list. topic:[(ip, port), ...]

    def publish(self, topic, data):
        self.topic[topic] = data
        try:
            subscribers = self.subscribers[topic]
        except:
            self.subscribers[topic] = []
            subscribers = []
        return data, subscribers
    
    def updateData(self, topic, data):
        self.topic[topic] = data
    
    def getSubscribers(self, topic):
        return self.subscribers[topic]

    def findNewSubscribers(self, topic, matched):
        tmp = []
        if topic in self.subscribers:
            for m in matched:
                if m not in self.subscribers[topic]:
                    tmp.append(m)
        else:
            tmp = matched
        return tmp

    def updateSubscribers(self, topic, matched):
        for m in matched:
            self.subscribers[topic].append(m)     

    def addSubscriber(self, topic, subscriber):
        try:
            if topic not in self.subscribers:
                self.subscribers[topic] = []

            if subscriber not in self.subscribers[topic]:
                self.subscribers[topic].append(subscriber)
                return subscriber
        except:
            return None

    def printStatus(self):
        print('- Topics and Data')
        print(' ', self.topic)
        print('- Subscribers')
        print(' ', self.subscribers)

class PubTcpHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            cmd = self.request.recv(1024).decode()
            # print('Connection from: ' + str(self.client_address)+ ':' + cmd)
            try:
                func = getattr(self, cmd.split(' ')[0].upper())
                func(cmd)
            except AttributeError as e:
                print('ERROR: ' + str(self.client_address) + ': Invalid command.')
                self.request.send('550 Invalid Command')
        finally:
            self.request.close()
    
    def sendData(self, topic, subscriber):
        global pub
        data = pub.topic[topic]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # create connection
        try:
            sock.connect(subscriber)
        except:
            print('Connection to ', subscriber, 'failed. Publish failure.')
            sock.close()
        msg = 'DATA {}'.format(data)
        # send data
        sock.send(msg.encode('utf-8'))        
        sock.close()

    def REPORT(self, cmd):
        '''
        GET report of matched topics from broker
        cmd would look be something like this: 
            REPORT [topicname] ip:port ip:port ...
        '''
        topicname = cmd.split(' ')[1]
        tmp = cmd.split(' ')[2:]
        self.request.close()

    def SUBREQ(self, cmd):
        '''
        Subscribe request from a subscriber
            SUBREQ [topicname] [subscriber-ip:subscriber-port]
        '''
        global pub

        topicname = cmd.split(' ')[1]
        ip, port = cmd.split(' ')[2:]
        subscriber = (ip, int(port))

        result = pub.addSubscriber(topicname, subscriber)
        if result:
            msg = '200 Subscribe request OK.'
            
            # Send corresponding data to this subscriber.
            thread = threading.Thread(target=self.sendData, args=(topicname, subscriber,))
            thread.setDaemon(True)
            thread.start()
        else:
            msg = '400 Subscribe rejected.'
        
        # pub.printStatus()
        self.request.send(msg.encode('utf-8'))
        self.request.close()
    
    def DEL(self, cmd):
        '''
        DEL [ip:port]
        '''
        global pub
        ip, port = cmd.split(' ')[-1].split(':')
        addr = (ip, int(port))
        for t in pub.topic.keys():
            if addr in pub.subscribers[t]:
                pub.subscribers[t].remove(addr)
        # pub.printStatus()

class PubServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class Publisher:
    def __init__(self, ip, port, broker_ip, broker_port):
        self.ip = ip
        self.port = port
        self.broker_ip = broker_ip
        self.broker_port = broker_port
    
    def run_server(self):
        try:
            server = PubServer((self.ip, self.port), PubTcpHandler)
            server.serve_forever()
        except KeyboardInterrupt:
            print('Shutting down...')
            server.shutdown()
            server.server_close()
    
    def start(self):
        try:
            thread = threading.Thread(target=self.run_server)
            thread.setDaemon(True)
            thread.start()

            while True:
                command = input('>>> ')
                if not command:
                    print('Need a command')
                    continue
                
                cmd = command.split(' ')[0].upper()
            
                if cmd=='QUIT' or cmd=='PUB' or cmd=='LIST':
                    func = getattr(self, cmd)
                    func(command)
                else:
                    print('list, quit, pub')

        except KeyboardInterrupt:
            self.QUIT('')
            print('Bye.')

        except Exception as e:
            print('Failed to create listener on ', self.ip, ':', self.port, 'because of ', str(e))
            quit()
    
    def LIST(self, command):
        '''
        show current topics and subscribers
        '''
        global pub
        pub.printStatus()

    def QUIT(self, command):
        '''
        send quitting message to broker to update subsciber list
            QUIT PUB {ip:port}
        '''
        msg = 'QUIT PUB {}:{}'.format(self.ip, self.port)
        thread = format.Sender(self.broker_ip, self.broker_port, msg)
        thread.start()
        quit()

    def PUB(self, command):
        '''
        command: PUB [topicname]
        send topic register request to the broker
            REQ PUB [topicname] [ip] [port]
        '''
        topicname = command.split(' ')[-1]
        # topicname = input('> topic name: ')
        # topicperiod = input('> period(in sec): ')
        # data = input('> file name: ')
        data = input('> corresponding message: ')
        # TODO: requst file to publish

        msg = 'REQ PUB {} {}:{}'.format(topicname, self.ip, self.port)
        thread = format.Sender(self.broker_ip, self.broker_port, msg)
        response = thread.start()

        if response.split(' ')[0] == '200':
            pub.publish(topicname, data)
            # pub.printStatus()
        elif response.split(' ')[0] == '400':
            pub.updateData(topicname, data)
            print('Starting sending messages to subscribers...')
            subscribers = pub.getSubscribers(topicname)
            msg = 'DATA {} '.format(data)

            for s in subscribers:
                ip,port = s
                thread = format.Sender(ip, port, msg)
                thread.start()
        '''
        TODO: pub하면 기존 subscriber 에게 새로 메시지 뿌리기...
        '''

pub = PublisherManager()
lock = threading.Lock()

IP = '127.0.0.1'
# PORT = 46007
PORT = int(input('> port number: '))

BROKER_IP = '127.0.0.1'
BROKER_PORT = 10020

publisher = Publisher(IP, PORT, BROKER_IP, BROKER_PORT)
publisher.start()