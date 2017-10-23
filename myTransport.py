'''
Created on 2017年10月5日

@author: wangweizhou
'''
from playground.network.common import StackingTransport
from HandShakePacket import PEEPPacket
import random
import asyncio

class TranTransport(StackingTransport):
    def __init__(self, lowerTransport, protocol):
        super().__init__(lowerTransport, extra=None)
        self._lowerTransport = lowerTransport
        self.protocol = protocol
        self.buffer = []        #Packet buffer
        self.Size = 10
        self.windowSize = 5 * self.Size
        self.protocol.packetsize = self.Size
        self.window = []  # Sliding window: recording the sequence number of the packets that has been sent
        self.pktseqStore = []  # To store bytes that have been transmitted
        self.seqStore = []
        self.baselen = 0
        self.currentlen =0
        self.lastsize=0
        

    def write(self, data):
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
                Pkt.Checksum = 0
                Pkt.updateChecksum()
                self.lowerTransport().write(Pkt.__serialize__())
                self.seqStore.append(self.protocol.SenSeq)
         
    def checkAck(self): # compare acks with seqs
        self.seqStore.sort()
        self.protocol.window.sort()
        if len(self.seqStore)>len(self.protocol.window):
            if self.seqStore[0] < self.protocol.window[0]:
                self.protocol.SenSeq = self.protocol.window[0]
                self.currentlen = self.protocol.window[0]-self.baselen
            else:
                for i in range(0,len(self.protocol.window),1):
                    if self.seqStore[i]!=self.protocol.window[i]:
                        if i==len(self.seqStore)-1 :
                            self.protocol.SenSeq = self.seqStore[i]-self.lastsize
                            self.currentlen = self.seqStore[i]-self.lastsize-self.baselen
                        else:
                            self.protocol.SenSeq = self.seqStore[i]-self.Size
                            self.currentlen = self.seqStore[i]-self.Size-self.baselen
                        self.seqStore=[]
                        self.protocol.window=[]
                        print("Acknowledgement Checked!")
                        return
                self.protocol.SenSeq = self.seqStore[len(self.protocol.window)]-self.Size
                self.currentlen = self.seqStore[len(self.protocol.window)]-self.Size-self.baselen
        else:
            if self.seqStore[0] < self.protocol.window[0]:
                self.protocol.SenSeq = self.protocol.window[0]
                self.currentlen = self.protocol.window[0]-self.baselen
            
            else:
                for i in range(0,len(self.seqStore),1):
                    
                    if self.seqStore[i]!=self.protocol.window[i]:
                        if i==len(self.seqStore)-1 :
                            self.protocol.SenSeq = self.seqStore[i]-self.lastsize
                            self.currentlen = self.seqStore[i]-self.lastsize-self.baselen
                        else:
                            self.protocol.SenSeq = self.seqStore[i]-self.Size
                            self.currentlen = self.seqStore[i]-self.Size-self.baselen
                        break
                    elif i==len(self.seqStore)-1:
                        self.protocol.SenSeq = self.seqStore[i]
                        self.currentlen = self.seqStore[i]-self.baselen
                        break
        
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
    
    
