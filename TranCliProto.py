from asyncio import *
from packet import HsPkt
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER, BOOL
from playground.network.common import PlaygroundAddress
import playground
from playground.asyncio_lib.testing import TestLoopEx
from playground.network.testing import MockTransportToStorageStream
from playground.network.testing import MockTransportToProtocol
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingProtocol
from playground.network.common import StackingTransport
import logging
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
        self.handshake = HsPkt()
        self.handshake.PType = 0
        self.rdm = random.randint(0,99)
        self.handshake.Seq = self.rdm
        self.handshake.Ack = 0
        self.deserializer = PacketType.Deserializer()

    def connection_made(self, transport):
        # higherTransport = StackingTransport(self.transport)
        # self.higherProtocol().connection_made(higherTransport)
        self.transport = transport
        print("Client: Activated.")
        self.transport.write(self.handshake.__serialize__())

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if pkt.Seq and pkt.Ack == (self.handshake.Seq + 1):
                print("Client: write Ack")
                self.handshake.Ack = pkt.Seq + 1

                self.RecSeq = pkt.Seq
                self.SenSeq = pkt.Seq + 1

                AckPkt = HsPkt()
                AckPkt.PType = 2
                AckPkt.Seq = pkt.Ack
                AckPkt.Ack = self.SenSeq
                self.transport.write(AckPkt.__serialize__())
            else:
                self.transport.close()


    def connection_lost(self, exc):
        self.transport = None
        print("The Server stopped and the loop stopped")



if __name__ == "__main__":
    loop = get_event_loop()
    coro = playground.getConnector().create_playground_connection(lambda: TranCliProto(), '20174.1.1.1', 8999)
    loop.run_until_complete(coro)

    loop.run_forever()
    loop.close()
