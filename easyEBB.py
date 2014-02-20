"""
Class containing methods to open, close and test serial connection
to EiBotBoard as well as methods to send commands to the motors


"""

import serial
import time
import eggbot_scanlinux

class easyEBB:
    def __init__( self ):
        self.actualSerialPort = ''
        self.openSerial()

    def openSerial( self ):
        """
        Opens a serial connection to the EiBotBoard
        """
        self.serialPort = self.getSerialPort()
        if self.serialPort == None:
            print "Unable to find serial port"

    def closeSerial( self ):
        """
        Closes the serial connection to the EiBotBoard
        """
        try: 
            if self.serialPort:
                self.serialPort.flush()
                self.serialPort.close()
        finally:
            self.serialPort = None
            return

    def getSerialPort( self ):
        """
        Returns details of the serial connection
        """
        #try to connect to EBB devices
        for strComPort in eggbot_scanlinux.findEiBotBoards():
            serialPort = self.testSerialPort( strComPort )
            if serialPort:
                self.actualSerialPort = strComPort
                return serialPort
        
        #if that fails, try any likely ports
        for strComPort in eggbot_scanlinux.findPorts():
            serialPort = self.testSerialPort( strComPort )
            if serialPort:
                self.actualSerialPort = strComPort
                return serialPort

    def testSerialPort( self, strComPort ):
        """
        Return a serial connection to the EiBotBoard
        Note: Need to close serial connection
        """
        try:
            serialPort = serial.Serial( strComPort, timeout = 1 )
        
            serialPort.setRTS()
            serialPort.setDTR()
            serialPort.flushInput()
            serialPort.flushOutput()

            time.sleep( 0.1 ) 
        
            serialPort.write( 'v\r' )
            strVersion = serialPort.readline()

            if strVersion and strVersion.startswith( 'EBB' ):
                return serialPort
            serialPort.close()
        
        except serial.SerialException:
            pass

        return None

    def doCommand(self, cmd):
        """
        Sends a string command to EiBotBoard
        """
        try:
            self.serialPort.write( cmd ) 
            response = self.serialPort.readlines()
            for line in response:
                print line
        except:
            print "fail"
            pass



    def disableMotors(self):
        """
        Disables both motors on EiBotBoard
        """
        self.doCommand('EM,0,0\r')
    
    def enableMotors(self):
        """
        Disables both motors on EiBotBoard
        """
        self.doCommand('EM,1,1\r')
        
    def stepM(self, duration, x, y):
        """
        Sends command to motor control board
        Enables motors before sending and disables after 
        
        arguments
        duration -- time to complete movement (in ms)
        x -- number of steps for movement in x direction (+ or -)
        y -- number of steps for movement in y direction (+ or -)
        """
        self.enableMotors()
        self.doCommand('SM,%d,%d,%d\r' %(duration, x, y))
        self.disableMotors()
