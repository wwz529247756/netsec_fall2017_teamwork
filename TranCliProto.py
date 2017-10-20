import asyncio
import playground
from HandShakePacket import PEEPPacket
from playground.network.packet import PacketType
from playground.network.common import PlaygroundAddress
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingProtocol
from playground.network.common import StackingTransport
from myTransport import TranTransport
import random
import time
#from asyncio.windows_events import NULL


'''
State machine definition:
Client:
    state = 0 Inactivated 
    state = 1 Waiting for SYN-Ack
    state = 2 Ack sent && Connection made 
    state = 3 Rip sent waiting for ack
    state = 4 ack receive waiting for Rip
'''



class TranCliProto(StackingProtocol):
    def __init__(self,loop):
        '''
            Init TranCliProto: 
            self.RecSeq is to record sequential number from Server
            self.Status is to record protocol status Activated or InActivated 
            checking for the handshake processing
            
        '''
        self.data = None
        self.loop = loop
        self.transport = None
        self.Status = 0
        self.RecSeq = 0
        self.SenSeq = 0
        self.higherTransport = None
        self.window = []
        self.deserializer = PacketType.Deserializer()
        self.RecAck = 0
    def connection_made(self, transport):
        print("Client: TranCliProto Connection made")
        self.transport = transport
        self.higherTransport = TranTransport(self.transport,self)
        
        self.connection_request()
        self.Status = 1

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if self.Status == 1:
                if pkt.Type == 1 and pkt.Acknowledgement == (self.SenSeq + 1):
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Client: Ack+Syn received! Sequence Number:{0} Acknowledgement Number:{1}",pkt.SequenceNumber,pkt.Acknowledgement)
                    self.RecSeq = pkt.SequenceNumber
                    AckPkt = PEEPPacket()
                    AckPkt.Type = 2
                    AckPkt.Checksum = 0
                    AckPkt.SequenceNumber = self.SenSeq
                    self.SenSeq+=1
                    AckPkt.Acknowledgement = self.RecSeq + 1
                    AckPkt.updateChecksum()
                    self.transport.write(AckPkt.__serialize__())
                    print("Client: Ack sent! Acknowledgement Number: {0}", AckPkt.Acknowledgement)
                    self.Status = 2
                    #time.sleep(3)  # test area!!
                    #self.close_request()
                    self.higherProtocol().connection_made(self.higherTransport)


                else:
                    self.transport.close()
            elif self.Status == 2:
                
                if self.RecAck == 0:
                    self.RecAck = self.SenSeq
                '''
                    Protocol Activated Transport data HERE!
                '''
                #Add from this line
                if pkt.Type == 2:
                    print("Client: receive ack!: ", pkt.Acknowledgement)
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    
                    if len(pkt.Data) != 0:
                        self.higherProtocol().data_received(pkt.Data)                                                                                                                                                     
                        self.RecSeq+=1
                        dataAck = PEEPPacket()
                        dataAck.Type = 2
                        dataAck.Checksum = 0
                        dataAck.SequenceNumber =0
                        dataAck.Acknowledgement = pkt.SequenceNumber + len(pkt.Data)
                        dataAck.updateChecksum()
                        self.transport.write(dataAck.__serialize__())
                    
                    self.window.append(pkt.Acknowledgement)
                    
                    #self.RecAck = pkt.Acknowledgement

                #End at this line
                if pkt.Type == 5:
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    self.higherProtocol().data_received(pkt.Data)                                                                                                                                                     
                    self.RecSeq += len(pkt.Data)
                    dataAck = PEEPPacket()
                    dataAck.Type = 2
                    dataAck.Checksum = 0
                    dataAck.SequenceNumber = 0
                    dataAck.Acknowledgement = self.SequenceNumber
                    dataAck.updateChecksum()
                    self.transport.write(dataAck.__serialize__())
                '''
                if pkt.Type == 5:
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    self.higherProtocol().data_received(pkt.Data)
                    self.RecSeq+=1
                '''

            elif self.Status == 3:
                if pkt.Type == 4 and pkt.Acknowledgement == self.SenSeq + 1:  # RIP-ACK
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    '''
                        Stop sendind data and WAIT!
                    '''
                    self.Status = 4
                    print("Client: Waiting for Server close the transport!")
            elif self.Status == 4:
                if pkt.Type == 3:
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Client: Rip from server received!")
                    self.RecSeq = pkt.SequenceNumber
                    clientRip = PEEPPacket()
                    clientRip.Type = 4
                    clientRip.Checksum = 0
                    clientRip.SequenceNumber = 0
                    self.RecSeq += 1
                    clientRip.Acknowledgement = self.RecSeq
                    clientRip.updateChecksum()
                    self.transport.write(clientRip.__serialize__())
                    self.Status=0
                    self.connection_lost("End")
                

    def connection_request(self):
        handshakeRequest = PEEPPacket()
        handshakeRequest.Type = 0
        handshakeRequest.Acknowledgement = 0
        handshakeRequest.SequenceNumber = random.randint(0, 1000)  # currently the range is [0,99]
        handshakeRequest.Checksum = 0  # have to be improved in the future
        handshakeRequest.updateChecksum()
        self.SenSeq = handshakeRequest.SequenceNumber
        print("Client: Connection Request sent! Sequence Number:{0}", handshakeRequest.SequenceNumber)
        self.transport.write(handshakeRequest.__serialize__())
    
    def sentpackets(self,data):
        if len(data)!=0:
            self.data = data
            self.higherTransport.sent(data)
            self.loop.call_later(2,self.sentpackets, self.data)

    
    def close_request(self):
        '''
            Close higher level transportation!
        '''
        print("Client: Rip request sent!")
        closePacket = PEEPPacket()
        closePacket.Type = 3
        self.SenSeq += 1
        closePacket.SequenceNumber = self.SenSeq
        closePacket.Acknowledgement = 0
        closePacket.Checksum = 0
        self.Status = "HalfActivated"
        closePacket.updateChecksum()
        self.transport.write(closePacket.__serialize__())

    def connection_lost(self, exc):
        self.transport.close()
        self.higherProtocol().connection_lost(exc)
        print("Connection stop because {}".format(exc))
