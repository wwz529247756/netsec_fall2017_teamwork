'''
Created on 2017年10月5日

@author: wangweizhou
'''
from playground.network.common import StackingTransport
from HandShakePacket import PEEPPacket
import random
import time

class TranTransport(StackingTransport):
    def __init__(self, lowerTransport, protocol):
        super().__init__(lowerTransport, extra=None)
        self._lowerTransport = lowerTransport
        self.protocol = protocol

        self.buffer = []            #Packet buffer

        self.Size = 10
        self.windowSize = 10 * self.Size
        self.window = []  # Sliding window: recording the sequence number of the packets that has been sent
        self.pktStore = []  # To store bytes that have been transmitted
        self.seqStore = []
        self.winSeq = 0
        self.lastSeq = 0

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
                Pkt.SequenceNumber = self.lastSeq + len(unit)
                self.lastSeq = Pkt.SequenceNumber
                self.protocol.SenSeq += 1
                Pkt.Acknowledgement = 0
                Pkt.Data = unit
                Pkt.Checksum = 0
                Pkt.updateChecksum()
                self.lowerTransport().write(Pkt.__serialize__())
                

                

                #self.pktStore.append(unit)
                #self.seqStore.append(Pkt.SequenceNumber)
                #self.count += 1

            #time.sleep(1)
            #self.checkAck()
                
    def checkAck(self): # compare acks with seqs
        self.window.sort()
        self.protocol.window.sort()
        for recvnum,sentnum in self.protocol.window,self.window:
            if(recvnum!=sentnum):
                self.resent(sentnum)
                break
    
    def resent(self, PktSeq):
        if(len(self.buffer != 0)):
            for pkt in self.buffer:
                if pkt.SequenceNumber < PktSeq:
                    self.buffer.pop(0) # delete the packet whose sequence is smaller than the resent packet number
                elif pkt.SequenceNumber ==PktSeq:
                    break
                else:
                    print("Packet storage error! Do not have this Packet!")
        i = 0
        self.clearance(self) # clear window record
        for pkt in self.buffer:
            self.lowerTransport().write(pkt.__serialize__())#resent
            self.window.append(pkt.SequenceNumber) # record the new sequence number from the resent packet
            i = i + 1
            if(i == self.windowsize):
                break
            
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
    
    
