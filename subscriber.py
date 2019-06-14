'''
@ author 2016024793 김유진
Simple middleware implementation - Subscriber
'''
import threading
import socket
import socketserver
import format

class SubscriberManager:
    def __init__(self):
        self.topic = []         # topic list
        self.publishers = {}    # topic:[(ip, port)]
        
    def subscribe(self, topic):
        if topic not in self.topic:
            self.topic.append(topic)
        return self.topic

    def findNewPublishers(self, topic, matched):
        tmp = []
        if topic in self.publishers:
            for m in matched:
                if m not in self.publishers[topic]:
                    tmp.append(m)
        else: 
            tmp = matched
        return tmp

    def addPublisher(self, topic, publisher):
        if topic not in self.publishers:
            self.publishers[topic] = []
        self.publishers[topic].append(publisher)

    def updatePublishers(self, topic, matched):
        tmp = []
        if topic not in self.publishers:
            self.publishers[topic] = []
        for m in matched:
            if m not in self.publishers[topic]:
                tmp.append(m)
                self.publishers[topic].append(m)
        return tmp

    def printStatus(self):
        # print('Topics: ')
        # for t in self.topic:
        #     print(t.NAME)
        print('- Topics')
        print(' ', self.topic)
        print('- Publishers')
        print(' ',self.publishers)

class SubTcpHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            cmd = self.request.recv(1024).decode()
            # print('Connection from: ' + str(self.client_address)+ ':' + cmd)
            try:
                func = getattr(self, cmd.split(' ')[0].upper())
                func(cmd)
            except AttributeError as e:
                print('ERROR: ' + str(self.client_address) + ': Invalid command.')
                self.request.send('550 Invalid Command'.encode('utf-8'))
        finally:
            self.request.close()
    
    def REPORT(self, cmd):
        '''
        Get report of matched topics from broker
        then send subscribe request to publishers.

        cmd would look be something like this: 
            REPORT [topicname] ip:port ip:port ...
        '''
        global sub, IP, PORT
        topicname = cmd.split(' ')[1]
        tmp = cmd.split(' ')[2:]

        matched = []
        for t in tmp:
            ip, port = t.split(':')
            matched.append((ip, int(port)))

        new_matched = sub.findNewPublishers(topicname, matched)

        # If there are some new publishers matched, 
        # send subscribe request to them.
        if len(new_matched) > 0:
            msg = 'SUBREQ {} {} {}'.format(topicname, IP, PORT)
            
            for p in new_matched:
                ip, port = p
                thread = format.Sender(ip, port, msg)
                response = thread.start()
                
                if response.split(' ')[0] == '200':
                    sub.addPublisher(topicname, p)
                # sub.printStatus()

        self.request.close()
    
    def DATA(self, cmd):
        '''
        Receive data from a publisher.
        DATA [actual message]
        '''
        msg = cmd.split(' ')[1:]
        msg = ' '.join(msg)
        print('\n >>> Publisher {}: {}\n'.format(self.client_address, msg))
        self.request.close()
    
    def DEL(self, cmd):
        '''
        Delete request from broker.
        delete corresponding address form pub list.
        DEL [ip:port]
        '''
        global sub
        ip, port = cmd.split(' ')[-1].split(':')
        addr = (ip,int(port))
        for t in sub.topic:
            if addr in sub.publishers[t]:
                sub.publishers[t].remove(addr)
        # sub.printStatus()

class SubServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class Subscriber:
    def __init__(self, ip, port, broker_ip, broker_port):
        self.ip = ip
        self.port = port
        self.broker_ip = broker_ip
        self.broker_port = broker_port

    def run_server(self):
        try:
            server = SubServer((self.ip, self.port), SubTcpHandler)
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
            
                if cmd=='QUIT' or cmd=='SUB' or cmd=='LIST':
                    func = getattr(self, cmd)
                    func(command)
                else:
                    print('quit, list, sub')

        except KeyboardInterrupt:
            self.QUIT('')
            print('Bye.')

        except Exception as e:
            print('Failed to create listener on ', self.ip, ':', self.port, 'because of ', str(e))
            quit()
    def LIST(self, command):
        '''
        show currently subscribed topics and matched publishers
        '''
        global sub
        sub.printStatus()

    def QUIT(self, command):
        '''
        send quitting message to broker to update subsciber list
            QUIT SUB {ip:port}
        '''
        msg = 'QUIT SUB {}:{}'.format(self.ip, self.port)
        thread = format.Sender(self.broker_ip, self.broker_port, msg)
        thread.start()
        quit()
    
    def SUB(self, command):
        '''
        command: SUB [topicname]
        send topic register request to the broker
            REQ SUB [topicname] [ip] [port]
        '''
        global sub
        topicname = command.split(' ')[-1].upper()
        
        msg = 'REQ SUB {} {}:{}'.format(topicname, self.ip, self.port)
        thread = format.Sender(self.broker_ip, self.broker_port, msg)
        response = thread.start()

        if response.split(' ')[0] == '200':
            sub.subscribe(topicname)
        elif response.split(' ')[0] == '400':
            print('Already subscribed.')

sub = SubscriberManager()
lock = threading.Lock()

BROKER_IP = '127.0.0.1'
BROKER_PORT = 10020

IP = '127.0.0.1'
PORT = input('> port number: ')

subscriber = Subscriber(IP, int(PORT), BROKER_IP, BROKER_PORT)
subscriber.start()
        