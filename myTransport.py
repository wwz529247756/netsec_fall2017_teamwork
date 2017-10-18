'''
Created on 2017年10月5日

@author: wangweizhou
'''
from playground.network.common import StackingTransport
from HandShakePacket import PEEPPacket
import random
import time
from matplotlib.transforms import interval_contains
import asyncio

class TranTransport(StackingTransport):
    def __init__(self, lowerTransport, protocol):
        super().__init__(lowerTransport, extra=None)
        self._lowerTransport = lowerTransport
        self.protocol = protocol

        self.buffer = []            #Packet buffer

        self.Size = 20
        self.windowSize = 2 * self.Size
        self.protocol.packetsize = self.Size
        self.window = []  # Sliding window: recording the sequence number of the packets that has been sent
        self.pktseqStore = []  # To store bytes that have been transmitted
        self.seqStore = []
        self.winSeq = 0
        self.lastSeq = self.protocol.SenSeq
        self.currentlen =0
        self.lastsize=0

        if self.get_extra_info("sockname", None) == None:
            self._extra["sockname"] = lowerTransport.get_extra_info("sockname", None)
        if self.get_extra_info("peername", None) == None:
            self._extra["peername"] = lowerTransport.get_extra_info("peername", None)

    def write(self, data):
        self.buffer = data
        print("A packet unit has been sent.")
        for j in range(0, len(self.buffer), self.windowSize):
            self.window = self.buffer[j:(j+self.windowSize)]
            self.winSeq = self.protocol.SenSeq
            self.lastSeq = self.winSeq
            
            for i in range(0, len(self.window), self.Size):
                unit = self.buffer[i:(i+self.Size)]
                Pkt = PEEPPacket()
                Pkt.Type = 5
                Pkt.SequenceNumber = self.lastSeq 
                self.lastSeq = Pkt.SequenceNumber+ len(unit)
                self.protocol.SenSeq += 1
                Pkt.Acknowledgement = 0
                Pkt.Data = unit
                Pkt.Checksum = 0
                Pkt.updateChecksum()
                self.lowerTransport().write(Pkt.__serialize__())
            
        
        

         
    def checkAck(self): # compare acks with seqs
        self.seqStore.sort()
        self.protocol.window.sort()
        
        for i in range(0,len(self.seqStore),1):
            print("test")
            if self.seqStore[i]!=self.protocol.window[i]:
                if i==len(self.seqStore)-1 :
                    self.currentlen = self.seqStore[i]-self.lastsize
                else:
                    self.currentlen = self.seqStore[i]-self.Size
                break
            elif i==len(self.seqStore)-1:
                self.currentlen = self.seqStore[i]
                break
        
    
    
    
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
    
    
