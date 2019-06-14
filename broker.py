'''
@ author 2016024793 김유진
Simple middleware implementation - Broker
'''
from format import *
import socket
import threading
import time
import enum

class MessageBrokerManager:
    def __init__(self):
        self.pub = {}     # topic:['ip:port', ...] 
        self.sub = {}     # topic:['ip,port', ...] 토픽을 구독한 구독자들의 리스트.
    
    def registerTopic(self, topic, addr):
        if topic.TYPE == Type.PUB:
            if topic not in self.pub:
                self.pub[topic] = []

            if addr not in self.pub[topic]:
                self.pub[topic].append(addr)
                return True
            else:
                # 이미 등록되어 있는 경우
                return False

        elif topic.TYPE == Type.SUB:
            if topic not in self.sub:
                self.sub[topic] = []
            
            if addr not in self.sub[topic]:
                self.sub[topic].append(addr)
                return True
            else:
                return False
    
    def removeUnused(self):
        for t in self.pub.keys():
            if len(self.pub[t]) == 0:
                del self.pub[t]
        for t in self.sub.keys():
            if len(self.sub[t]) == 0:
                del self.sub[t]

    def getMatched(self, topic):
        if topic.TYPE == Type.PUB:
            if topic in self.sub:
                return self.sub[topic]
            else: 
                return None
        if topic.TYPE == Type.SUB:
            if topic in self.pub:
                return self.pub[topic]
            else:
                return None

    def getMatchingPub(self, subscriber):
        '''
        get matching publishers using subscriber address and
        delete subscriber in the sub list
        '''
        topiclist = []
        for topic, subs in self.sub.items():
            if subscriber in subs:
                topiclist.append(topic)
                self.sub[topic].remove(subscriber)
        publishers = []
        for topic in topiclist:
            publishers += self.pub[topic]
        publishers = list(set(publishers))
        return publishers
    
    def getMatchingSub(self, publisher):
        '''
        get matching subscribers using publisher address and
        delete publisher in the pub list
        '''
        topiclist = []
        for topic, pubs in self.pub.items():
            if publisher in pubs:
                topiclist.append(topic)
                self.pub[topic].remove(publisher)
        subscribers = []
        for topic in topiclist:
            subscribers += self.sub[topic]
        subscribers = list(set(subscribers))
        return subscribers

    def printStatus(self):
        print("======Message Broker Status======")
        print(self.pub)
        print(self.sub)

broker = MessageBrokerManager()
lock = threading.Lock()

class MessageBrokerHandler(Handler):
    def __init__(self, client, local_ip, local_port):
        Handler.__init__(self, client, local_ip, local_port)
    
    def check_matched(self):
        '''
        function for checking matched pairs. 
        If a match is found, send a REPORT message to the subscribers.
        '''
        global broker
        tmp = {}
        for topic in broker.sub:
            subcribers = broker.sub[topic]
            publishers = broker.getMatched(topic)
            
            if publishers:
                if len(publishers) > 0:
                    msg = 'REPORT {} '.format(topic.NAME) + ' '.join(publishers)
                    for sub in subcribers:
                        ip, port = sub.split(':')
                        thread = Sender(ip, int(port), msg)
                        thread.start()
        print('\n match check done!')

    def REQ(self, cmd):
        '''
        Topic request
            REQ SUB [topicname] [ip:port]
        '''
        global broker, lock
        _, topictype, topicname, addr = cmd.split(' ')

        if topictype=='PUB':
            type = Type.PUB
        elif topictype=='SUB':
            type = Type.SUB
        topic = Topic(type, topicname)
        
        # lock.acquire()
        result = broker.registerTopic(topic, addr)
        # lock.release()

        broker.printStatus()
        if result:
            msg = '200 Topic Register Request OK.'
        else:
            msg = '400 Already registered. Topic Register failed.'
        self.client_sock.send(msg.encode('utf-8'))

        thread = threading.Thread(target=self.check_matched)
        thread.start()    
        
    def QUIT(self, cmd):
        '''
        Terminate program. Before terminating, send quit message to broker
            QUIT {type} {ip:port}
        ''' 
        _, type, addr = cmd.split(' ')
        
        if type=='SUB':     # if a subscriber logged out, report its publishers
            sendlist = broker.getMatchingPub(addr)
        elif type=='PUB':   # if a publisher logged out, report its subscribers
            sendlist = broker.getMatchingSub(addr)
        print('Broker Updated...')
        # broker.removeUnused()
        broker.printStatus()
        
        msg =  'DEL {}'.format(addr)
        for s in sendlist:
            ip, port = s.split(':')
            thread = Sender(ip, int(port), msg)
            thread.start()

        self.client_sock.send('Good Bye.'.encode('utf-8'))

class MessageBroker:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def start_sock(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        addr = (self.ip, self.port)

        try:
            self.sock.bind(addr)
            self.sock.listen(5)
        except Exception as e:
            print('Failed to create server on ', self.ip, ':', self.port,' because of ', str(e))
            quit()

    def start(self):
        self.start_sock()
        try:
            while True:
                thread = MessageBrokerHandler(self.sock.accept(), self.ip, self.port)
                thread.start()
        except KeyboardInterrupt:
            print('Closing socket connection')
            self.sock.close()
            quit()


ip = '127.0.0.1'
port = 10020

messagebroker = MessageBroker(ip, port)
messagebroker.start()
