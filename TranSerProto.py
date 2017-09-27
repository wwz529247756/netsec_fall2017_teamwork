'''
Created on 20170926

@author: teamwork 
'''
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER,BOOL
from playground.network.common import StackingProtocol
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingTransport
from asyncio import *
from HandShakePacket import HsPkt
import playground
import random

'''
    Things to do:
    1. Setting SYN-->SYN+ACK time out mechanism 
'''

class TranSerProto(Protocol):
    def __init__(self):
        self.Status="InActivated"
        self.RecSeq=0
        self.SenSeq=0
        self.transport = None
        self.deserializer = PacketType.Deserializer()
    def connection_made(self, transport):
        self.transport=transport
        
    def data_received(self,data):
        self.deserializer.update(data)
        if self.Status=="InActivated":
            for pkg in self.deserializer.nextPackets():
                if pkg.PType==0:
                    print("Server: SYN received!")
                    self.RecSeq=pkg.Seq
                    tmpkg = HsPkt()
                    tmpkg.PType = 1
                    tmpkg.Seq = random.randint(0,99)
                    self.SenSeq = tmpkg.Seq
                    tmpkg.Ack = self.RecSeq+1
                    data = tmpkg.__serialize__()
                    self.transport.write(data)
                    print("Server: Ack+Syn sent!")
                elif pkg.PType==2:
                    print("Server: ACK received!")
                    if pkg.Seq==self.SenSeq+1:
                        self.RecSeq=pkg.Seq
                        self.Status="Activated"
                        print("Server: Activated!")
                    else:
                        self.transport.close()
                    
        else:
            '''
                After handshake processing the real transportation start here!
                We might to do several following things:
                1. de-packet data from the transporting packet
                2. send the data to a higher level layer such as SSL then to the application layer
            '''
            
    def connection_lost(self,exc):
        print('Connection stopped because {}'.format(exc))
        
if __name__=='__main__':     #Unitest
    loop = get_event_loop()
    coro = playground.getConnector().create_playground_server(lambda:TranSerProto(),8999)
    myserver= loop.run_until_complete(coro)
    loop.run_forever()
    myserver.close()
    loop.close()