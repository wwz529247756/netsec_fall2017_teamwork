from asyncio import *
import playground
from HandShakePacket import HsPkt
from playground.network.packet import PacketType
from playground.network.common import PlaygroundAddress
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingProtocol
from playground.network.common import StackingTransport
import random

class TranCliProto(Protocol):
    def __init__(self):
        '''
            Init TranCliProto: 
            self.RecSeq is to record sequential number from Server
            self.Status is to record protocol status Activated or InActivated 
            checking for the handshake processing
            
        '''
        self.transport = None
        self.Status = "InActivated"
        self.RecSeq = 0
        self.SenSeq = 0
        self.deserializer = PacketType.Deserializer()

    def connection_made(self, transport):
        self.transport = transport
        

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if pkt.PType==1 and pkt.Ack == (self.SenSeq + 1):
                print("Client: Ack+Syn received!")
                self.RecSeq = pkt.Seq
                self.SenSeq = pkt.Seq + 1
                AckPkt = HsPkt()
                AckPkt.PType = 2
                AckPkt.Seq = pkt.Ack
                AckPkt.Ack = self.SenSeq
                self.transport.write(AckPkt.__serialize__())
                print("Client: Ack sent!")
            else:
                self.transport.close()

    def connection_request(self):
        print("Client: Request sent!")
        handshakeRequest = HsPkt()
        handshakeRequest.PType = 0
        handshakeRequest.Ack = 0
        handshakeRequest.Seq = random.randint(0,99)   #currently the range is [0,99]
        self.SenSeq = handshakeRequest.Seq
        self.transport.write(handshakeRequest.__serialize__())
    
    
    def connection_lost(self, exc):
        self.transport = None
        print("The Server stopped and the loop stopped")



if __name__ == "__main__":
    loop = get_event_loop()
    coro = playground.getConnector().create_playground_connection(lambda: TranCliProto(), '20174.1.1.1', 8999)
    mytransport,myprotocol = loop.run_until_complete(coro)
    myprotocol.connection_request()
    loop.run_forever()
    loop.close()
