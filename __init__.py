'''
Created on 2017年10月4日

@author: wangweizhou
'''

from playground.network.common import StackingProtocolFactory
import playground
import HandShakePacket
from TranSerProto import *
from TranCliProto import *
from ServerPassThrough import *
from ClientPassThrough import *

ClientFactory = StackingProtocolFactory(lambda: ClientPassThrough(), lambda: TranCliProto())
ServerFactory = StackingProtocolFactory(lambda: ServerPassThrough(), lambda: TranSerProto())
myConnector = playground.Connector(protocolStack=(ClientFactory, ServerFactory))
playground.setConnector("myprotocol", myConnector)