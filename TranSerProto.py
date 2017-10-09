'''
Created on 20170926

@author: teamwork 
'''
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER, BOOL
from playground.network.common import StackingProtocol
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingTransport
from asyncio import *
from HandShakePacket import PEEPPacket
import playground
import random
import time
from myTransport import TranTransport
'''
    Things to do:
    1. Setting SYN-->SYN+ACK time out mechanism 
'''


class TranSerProto(StackingProtocol):
    def __init__(self):
        super().__init__
        self.window = []
        self.windowsize = 10
        self.Status = "InActivated"
        self.RecSeq = 0
        self.SenSeq = 0
        self.deserializer = PacketType.Deserializer()
        self.higherTransport = None

    def connection_made(self, transport):
        print("Server: TranSerProto Connection made!")
        self.transport = transport
        self.higherTransport = TranTransport(self.transport,self)

    def data_received(self, data):
        self.data = data
        self.deserializer.update(data)

        for pkg in self.deserializer.nextPackets():
            if self.Status == "InActivated":
                if pkg.Type == 0:
                    if not pkg.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Server: SYN received!")
                    self.RecSeq = pkg.SequenceNumber
                    tmpkg = PEEPPacket()
                    tmpkg.Type = 1
                    tmpkg.Checksum = 0
                    tmpkg.SequenceNumber = random.randint(0, 99)
                    self.SenSeq = tmpkg.SequenceNumber
                    tmpkg.Acknowledgement = self.RecSeq + 1
                    tmpkg.updateChecksum()
                    self.transport.write(tmpkg.__serialize__())
                    print("Server: Ack+Syn sent!")
                elif pkg.Type == 2:
                    if not pkg.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                        # do something for errors
                    print("Server: ACK received!")
                    if pkg.Acknowledgement == self.SenSeq + 1:
                        self.RecSeq = pkg.SequenceNumber
                        self.Status = "Activated"
                        print("Server: Activated!")
                        self.higherProtocol().connection_made(self.higherTransport)
                    else:
                        self.transport.close()

            elif self.Status == "HalfActivated":
                if pkg.Type == 4 and pkg.Acknowledgement == self.SenSeq + 1:
                    if not pkg.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Server: Rip-Ack received!")
                    self.Status = "InActivated"
                    self.connection_lost("Client request")

            elif self.Status == "Activated":
                
                '''
                    After handshake processing the real transportation start here!
                    We might to do several following things:
                    1. de-packet data from the transporting packet
                    2. send the data to a higher level layer such as SSL then to the application layer
                '''

                ''' Close the connection!'''
                if pkg.Type == 3:
                    if not pkg.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Server: Rip received from Client!")
                    self.RecSeq = pkg.SequenceNumber
                    ServerRipAckPacket = PEEPPacket()
                    ServerRipAckPacket.Type = 4
                    self.RecSeq += 1
                    ServerRipAckPacket.Acknowledgement = self.RecSeq
                    self.SenSeq += 1
                    ServerRipAckPacket.SequenceNumber = self.SenSeq
                    self.Status = "HalfActivated"
                    ServerRipAckPacket.Checksum = 0
                    ServerRipAckPacket.updateChecksum()
                    self.transport.write(ServerRipAckPacket.__serialize__())
                    #time.sleep(2)  # Mock the buffer transport processing!
                    '''
                        Only transfer data in the buffer!
                        Waiting for the transportation complete!
                    '''
                    print("Server: Waiting for the transportation complete!")
                    print("Server: Rip sent to the Client!")
                    ServerRip = PEEPPacket()  # Send Rip package after transport data from buffer
                    ServerRip.Type = 3
                    self.SenSeq += 1
                    ServerRip.SequenceNumber = self.SenSeq
                    ServerRip.Checksum = 0
                    ServerRip.Acknowledgement = 0
                    ServerRip.updateChecksum()
                    self.transport.write(ServerRip.__serialize__())

                elif pkg.Type == 5:
                    #print("Status:activated")
                    print("Server: Transport layer packet received! Sequence Number: {}".format(pkg.SequenceNumber))
                    self.higherProtocol().data_received(pkg.Data)
    
    def receiveAckList(self,acknum):
        self.window.append(acknum)

    def connection_lost(self, exc):
        self.higherProtocol().connection_lost(exc)
        self.transport.close()
        print('Connection stopped because {}'.format(exc))
