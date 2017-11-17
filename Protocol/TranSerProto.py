'''
Created on 20170926

@author: wangweizhou
'''
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER, BOOL
from playground.network.common import StackingProtocol
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingTransport
import asyncio
from .myTransport import *
import playground
import random
import time
from .HandShakePacket import *

'''
    State machine:
    1. state = 0  Inactivate && waiting for Syn packet
    2. state = 1  Syn-ack sent waiting for ack
    3. state = 2  ack received connection made
    4. state = 3  rip received && ack sent!
    5. state = 4  rip sent waiting for ack
    
'''


class TranSerProto(StackingProtocol):
    def __init__(self):
        self.transport = None
        self._deserializer = PEEPPacket.Deserializer()
        self.handshake = False
        self.seq = 0
        self.state = 0
        self.ack_counter = 0
        self.expected_packet = 0
        self.expected_ack = 0
        self.info_list = item_list()
        self.timeout_timer = time.time()
        self.higherTransport = None
        self.lastcorrect = 0
        self.lastAck = 0
        self.close_timer = time.time()

    def transmit(self):
        if time.time() - self.timeout_timer > 0.5:
            if self.info_list.sequenceNumber < self.info_list.init_seq + len(self.info_list.outBuffer):
                if self.lastAck > self.info_list.sequenceNumber:
                    self.info_list.sequenceNumber = self.lastAck
                self.higherTransport.sent_data()
                self.timeout_timer = time.time()
                self.ack_counter = 0
            else:
                if time.time() - self.close_timer > 20:
                    self.info_list.readyToclose = True
                    self.higherTransport.close()
                    return
        txDelay = 1
        asyncio.get_event_loop().call_later(txDelay, self.transmit)

    def connection_made(self, transport):
        self.transport = transport
        

    def resentsynack(self, pkt):
        if self.state == 1:
            self.transport.write(pkt.__serialize__())
            asyncio.get_event_loop().call_later(1, self.resentsynack, pkt)

    def data_received(self, data):
        self.close_timer = time.time()
        self._deserializer.update(data)
        for pkt in self._deserializer.nextPackets():
            if isinstance(pkt, PEEPPacket):
                if pkt.Type == 0 and self.state == 0:
                    if pkt.verifyChecksum():
                        print("Server: received SYN")
                        SYN_ACK = PEEPPacket()
                        SYN_ACK.Type = 1
                        self.seq = self.seq + 1
                        SYN_ACK.updateSeqAcknumber(seq=self.seq, ack=pkt.SequenceNumber + 1)
                        SYN_ACK.Checksum = SYN_ACK.calculateChecksum()
                        print("Server: SYN-ACK sent")
                        self.transport.write(SYN_ACK.__serialize__())
                        self.state = 1
                        self.resentsynack(SYN_ACK)

                elif pkt.Type == 2 and self.state == 1 and not self.handshake:
                    if pkt.verifyChecksum():
                        self.state = 3
                        print("Srver: ACK received!")
                        self.expected_packet = pkt.SequenceNumber
                        self.expected_ack = pkt.SequenceNumber + PACKET_SIZE
                        self.info_list.sequenceNumber = self.seq
                        self.info_list.init_seq = self.seq

                        self.higherTransport = myTransport(self.transport)
                        self.higherTransport.setinfo(self.info_list)
                        self.higherProtocol().connection_made(self.higherTransport)
                        self.handshake = True
                        self.transmit()
                        break
                    
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

                    if pkt.Type == 3:
                        if self.info_list.sequenceNumber >= self.info_list.init_seq + len(self.info_list.outBuffer):
                            RIP_ACK = PEEPPacket()
                            RIP_ACK.Type = 4
                            RIP_ACK.updateSeqAcknumber(seq=self.info_list.sequenceNumber, ack=pkt.Acknowledgement)
                            RIP_ACK.Checksum = RIP_ACK.calculateChecksum()
                            print("Server: RIP-ACK sent!")
                            self.transport.write(RIP_ACK.__serialize__())
                            self.info_list.readyToclose = True
                            self.higherTransport.close()

    def connection_lost(self, exc):
        self.higherProtocol().connection_lost(exc)
    
    def verify_packet(self, packet, expected_packet):
        goodpacket = True
        if packet.verifyChecksum() == False:
            print("Server: Wrong checksum")
            goodpacket = False
        if expected_packet != packet.SequenceNumber:
            print("Server: Wrong packet seq number")
            print("Server: Expected number:" + str(expected_packet))
            print("Server: packet number: " + str(packet.SequenceNumber))
            
            goodpacket = False
        return goodpacket
    
    def verify_ack(self, packet):
        goodpacket = True
        if packet.verifyChecksum() == False:
            print("Server: Wrong checksum")
            goodpacket = False
        return goodpacket
    
    def generate_ACK(self, seq_number, ack_number):
        ACK = PEEPPacket()
        ACK.Type = 2
        ACK.SequenceNumber = seq_number
        ACK.Acknowledgement = ack_number
        ACK.Checksum = ACK.calculateChecksum()
        return ACK









