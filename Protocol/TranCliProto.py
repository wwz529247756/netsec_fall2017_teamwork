'''
Created on 20170926

@author: wangweizhou
'''
import asyncio
import playground
from .HandShakePacket import *
from playground.network.packet import PacketType
from playground.network.common import PlaygroundAddress
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingProtocol
from playground.network.common import StackingTransport
from .myTransport import *
import random
import time
import logging



'''
State machine definition:
Client:
    state = 0 Inactivated 
    state = 1 Waiting for SYN-Ack
    state = 2 Ack sent && Connection made 
    state = 3 Rip sent waiting for ack
    state = 4 ack receive waiting for Rip
'''
logging.getLogger().setLevel(logging.NOTSET)  
logging.getLogger().addHandler(logging.StreamHandler())  


class TranCliProto(StackingProtocol):
    def __init__(self):
        self.transport = None
        self._deserializer = PEEPPacket.Deserializer()
        self.handshake = False
        self.seq = 0
        self.state = 0
        self.ack_counter = 0
        self.expected_packet = 0
        self.expected_ack = 0
        self.databuffer = ''
        self.timeout_timer = time.time()
        self.info_list = item_list()
        self.higherTransport = None
        self.lastcorrect = 0
        self.lastAck = 0
        self.close_timer = time.time()
        self.forceclose = 0

    

    def connection_made(self, transport):
        self.transport = transport
        SYN = PEEPPacket()
        SYN.SequenceNumber = self.seq
        self.seq = self.seq + 1
        SYN.Type = 0  
        SYN.Checksum = SYN.calculateChecksum()
        print("client: SYN sent")
        SYNbyte = SYN.__serialize__()
        self.transport.write(SYNbyte)
        self.resentsyn(SYN)

    def data_received(self, data):
        self.close_timer = time.time()
        self._deserializer.update(data)
        for pkt in self._deserializer.nextPackets():
            if isinstance(pkt, PEEPPacket):
                if pkt.Type == 1 and self.state == 0 and not self.handshake:
                    print("Client: Syn-Ack received")
                    if pkt.verifyChecksum():
                        ACK = PEEPPacket()
                        ACK.Type = 2  
                        self.seq = self.seq + 1
                        ACK.updateSeqAcknumber(seq=self.seq, ack=pkt.SequenceNumber + 1)
                        print("Client: ACK sent")
                        ACK.Checksum = ACK.calculateChecksum()
                        self.transport.write(ACK.__serialize__())
                        self.state = 1
                        print("Client: ACK sent")
                        self.expected_packet = pkt.SequenceNumber
                        self.expected_ack = pkt.SequenceNumber + PACKET_SIZE
                        self.info_list.sequenceNumber = self.seq
                        self.info_list.init_seq = self.seq
                        self.higherTransport = myTransport(self.transport)
                        self.higherTransport.setinfo(self.info_list)
                        self.higherProtocol().connection_made(self.higherTransport)
                        self.handshake = True
                        self.transmit()


                elif self.handshake:
                    if pkt.Type == 5:
                        if self.verify_packet(pkt, self.expected_packet):
                            self.lastcorrect = pkt.SequenceNumber + len(pkt.Data)
                            self.expected_packet = self.expected_packet + len(pkt.Data)
                            Ackpacket = self.generate_ACK(self.seq, pkt.SequenceNumber + len(pkt.Data))
                            self.transport.write(Ackpacket.__serialize__())
                            self.higherProtocol().data_received(pkt.Data)
                        else:

                            Ackpacket = self.generate_ACK(self.seq, self.lastcorrect)
                            
                            self.transport.write(Ackpacket.__serialize__())

                    if pkt.Type == 2:
                        if self.verify_ack(pkt):
                            self.ack_counter = self.ack_counter + 1
                            

                            if self.info_list.sequenceNumber < pkt.Acknowledgement:
                                self.info_list.sequenceNumber = pkt.Acknowledgement
                                self.lastAck = pkt.Acknowledgement

                            if self.ack_counter == WINDOW_SIZE and pkt.Acknowledgement < len(
                                    self.info_list.outBuffer) + self.seq:
                                self.timeout_timer = time.time()
                                
                                self.ack_counter = 0

                                if pkt.Acknowledgement < self.info_list.init_seq + len(self.info_list.outBuffer):
                                    self.higherTransport.sent_data()

                            elif pkt.Acknowledgement == len(self.info_list.outBuffer) + self.seq:
                                self.seq = pkt.Acknowledgement
                                self.ack_counter = 0
                                self.higherTransport.setinfo(self.info_list)
            
                    if pkt.Type == 4:
                        print("Client: Receive Rip-Ack!")
                        self.info_list.readyToclose = True
                        self.higherTransport.close()

    def connection_lost(self, exc):
        self.higherProtocol().connection_lost(exc)
        
    def transmit(self):
        if time.time() - self.timeout_timer > 0.5:
            if self.info_list.sequenceNumber < self.info_list.init_seq + len(self.info_list.outBuffer):
                if self.lastAck > self.info_list.sequenceNumber:
                    self.info_list.sequenceNumber = self.lastAck
                self.ack_counter = 0
                self.timeout_timer = time.time()
                self.higherTransport.sent_data()
            else:
                print("Client: Ending....")

        if time.time() - self.close_timer > 5:
            self.forceclose += 1
            self.close_timer = time.time()
            Rip = PEEPPacket()
            Rip.Type = 3
            Rip.updateSeqAcknumber(self.info_list.sequenceNumber, ack=1)
            print("Client: Rip sent")
            Rip.Checksum = Rip.calculateChecksum()
            self.transport.write(Rip.__serialize__())

            if self.forceclose > 5:
                self.info_list.readyToclose = True
                self.higherTransport.close()
                return

        txDelay = 1
        asyncio.get_event_loop().call_later(txDelay, self.transmit)

    def resentsyn(self, pkt):
        if self.state == 0:
            self.transport.write(pkt.__serialize__())
            asyncio.get_event_loop().call_later(1, self.resentsyn, pkt)
    
    def verify_packet(self, packet, expected_packet):
        goodpacket = True
        if packet.verifyChecksum() == False:
            print("wrong checksum")
            goodpacket = False
        if expected_packet != packet.SequenceNumber:
            print("Client: Wrong packet seq number")
            print("Client: Expected number:" + str(expected_packet))
            print("Client: Received seq number: " + str(packet.SequenceNumber))
            
            goodpacket = False
        return goodpacket
    def verify_ack(self, packet):
        goodpacket = True
        if packet.verifyChecksum() == False:
            print("Client: Wrong checksum")
            goodpacket = False
        return goodpacket
    def generate_ACK(self, seq_number, ack_number):
        ACK = PEEPPacket()
        ACK.Type = 2
        ACK.SequenceNumber = seq_number
        ACK.Acknowledgement = ack_number
        ACK.Checksum = ACK.calculateChecksum()
        return ACK
        








