'''
Created on 2017年10月5日

@author: wangweizhou
'''
from playground.network.common import StackingTransport
from .HandShakePacket import PEEPPacket
import random
import asyncio

class TranTransport(StackingTransport):
    def __init__(self, lowerTransport, protocol):
        super().__init__(lowerTransport, extra=None)
        self._lowerTransport = lowerTransport
        self.protocol = protocol
        self.buffer = []        #Packet buffer
        self.Size = 1000
        self.windowSize = 10 * self.Size
        self.protocol.packetsize = self.Size
        self.window = []  # Sliding window: recording the sequence number of the packets that has been sent
        self.pktseqStore = []  # To store bytes that have been transmitted
        self.seqStore = []
        self.baselen = 0
        self.currentlen =0
        self.lastsize=0
        

    def write(self, data):
        
        self.currentlen =0
        self.baselen = 0
        self.protocol.sentpackets(data)
        
    def sent(self,data):
        if len(data)!=0:
            if len(self.protocol.window)!=0:
                self.checkAck()
            self.baselen = self.protocol.SenSeq
            self.buffer = data
            self.buffer = self.buffer[self.currentlen:len(self.buffer)]
            self.protocol.data = self.buffer
            self.window = self.buffer[0:self.windowSize]
            for i in range(0, len(self.window), self.Size):
                unit = self.buffer[i:(i+self.Size)]
                Pkt = PEEPPacket()
                Pkt.Type = 5
                Pkt.SequenceNumber = self.protocol.SenSeq
                self.protocol.SenSeq = Pkt.SequenceNumber+ len(unit)
                Pkt.Acknowledgement = 0
                Pkt.Data = unit
                #Pkt.Checksum = 0
                Pkt.updateChecksum()
                self.lowerTransport().write(Pkt.__serialize__())
                self.seqStore.append(self.protocol.SenSeq)
         
    def checkAck(self): # compare acks with seqs
        self.seqStore.sort()
        self.protocol.window.sort()
        self.maxAck = self.protocol.window[len(self.protocol.window)-1]
        self.protocol.SenSeq = self.maxAck
        self.currentlen = self.maxAck-self.baselen
        self.seqStore=[]
        self.protocol.window=[]
        print("Acknowledgement Checked!")
    
            
    def clearance(self):
        while len(self.window)!=0 :
            self.window.pop()
    
    
    
    def close(self):
        print("Client: Rip request sent!")
        closePacket = PEEPPacket()
        closePacket.Type = 3
        closePacket.SequenceNumber = self.protocol.SenSeq
        closePacket.Acknowledgement = 0
        closePacket.Checksum = 0
        closePacket.updateChecksum()
        self.protocol.Status=3
        self.lowerTransport().write(closePacket.__serialize__())
        print("waiting for rip ack packet")
        self.lowerTransport().close()
    
