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
        super().__init__(lowerTransport,extra=None)
        self._lowerTransport = lowerTransport
        self.protocol = protocol
        self.windowsize = 10
        self.buffer = []            #Packet buffer
        self.window = []            #Sliding window: recording the sequence number of the packets that has been sent
        if self.get_extra_info("sockname", None) == None:
            self._extra["sockname"] = lowerTransport.get_extra_info("sockname", None)
        if self.get_extra_info("peername", None) == None:
            self._extra["peername"] = lowerTransport.get_extra_info("peername", None)
        
    
    def write(self, data):
        self.Size = 20
        Slices = [data[i:(i+self.Size)] for i in range(0, len(data), self.Size)]
        count = 0
        for SingleSlice in Slices:
            
            Pkt = PEEPPacket()
            Pkt.Type = 5
            Pkt.SequenceNumber = self.protocol.SenSeq
            self.protocol.SenSeq+=1
            Pkt.Acknowledgement = 0
            Pkt.Data = SingleSlice
            Pkt.Checksum = 0
            Pkt.updateChecksum()
            self.lowerTransport().write(Pkt.__serialize__())
            print("Client: Transport packet sent! Sequence Number: ",Pkt.SequenceNumber)
            
            self.buffer.append(Pkt) #put the packet into buffer
            self.window.append(Pkt.SequenceNumber) # record the sequence number
            count = count + 1
            if(count%10 == 0 and count != 0): #check every 10 packet
                count = 0
                time.sleep(1)
                self.checkAck()
                
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
        self.lowerTransport().write(closePacket.__serialize__())
    
    
