from easyEBB import easyEBB

e = easyEBB()
e.enableMotors()
e.centerWorm(100,200,300)
e.disableMotors()
e.closeSerial()
