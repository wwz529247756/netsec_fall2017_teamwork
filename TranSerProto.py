'''
Created on 2017年9月26日

@author: wangweizhou
'''
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER,BOOL
from playground.network.common import StackingProtocol
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingTransport
import playground
from asyncio import *
from packet import HsPkt
import random

class TranSerProto(Protocol):
    def __init__(self):
        self.Status="InActivated"
        self.RecSeq=0
        self.SenSeq=0
        self.transport = None
        self.deserializer = PacketType.Deserializer()
    def connection_made(self, transport):
        print("TranSerProto connection made!")
        self.transport=transport
        
    def data_received(self,data):
        print("Received!")
        self.deserializer.update(data)
        if self.Status=="InActivated":
            for pkg in self.deserializer.nextPackets():
                if pkg.PType==0:
                    print("SYN received!")
                    self.RecSeq=pkg.Seq
                    tmpkg = HsPkt()
                    tmpkg.PType = 1
                    tmpkg.Seq = random.randint(0,99)
                    self.SenSeq = tmpkg.Seq
                    tmpkg.Ack = self.RecSeq+1
                    data = tmpkg.__serialize__()
                    self.transport.write(data)
                elif pkg.PType==2:
                    print("ACK received!")
                    if pkg.Seq==self.SenSeq+1:
                        self.RecSeq=pkg.Seq
                        self.Status="Activated"
                    else:
                        self.transport.close()
                    
        else:
            print("Start transportation!")
            #depackage
            #self.higherProtocol().dataR
    def connection_lost(self,exc):
        print('Connection stopped because {}'.format(exc))
if __name__=='__main__':
    loop = get_event_loop()
    coro = playground.getConnector().create_playground_server(lambda:TranSerProto(),8999)
    myserver= loop.run_until_complete(coro)
    loop.run_forever()
    myserver.close()
    loop.close()