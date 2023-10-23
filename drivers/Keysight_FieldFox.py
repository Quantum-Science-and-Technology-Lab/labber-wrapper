#!/usr/bin/env python

from VISA_Driver import VISA_Driver
import numpy as np
import os.path


# Experimental FieldFox driver from Keysight's Anushka Shrivastava.

__version__ = "0.0.1"

class Error(Exception):
    pass

class Driver(VISA_Driver):
    """ This class implements the FieldFox VNA driver"""

    def performOpen(self, options={}):
        """Perform the operation of opening the instrument connection"""
        # init meas param dict
        self.dMeasParam = {}
        # calling the generic VISA open to make sure we have a connection
        VISA_Driver.performOpen(self, options=options)

        # Disable local lockout mode (only needed for driver testing)
        self.writeAndLog(':INST:RLOC:DIS 1')

    def performSetValue(self, quant, value, sweepRate=0.0, options={}):
        """Perform the Set Value instrument operation. This function should
        return the actual value set by the instrument"""
        
        ### Reset mode traces when switching between modes ###
        if quant.name in ('Mode'):
            if value == 'Network Analyzer':
                VISA_Driver.performOpen(self, options=options)
                self.writeAndLog(':INST:SEL "NA"')
            if value == 'Signal Analyzer':
                VISA_Driver.performOpen(self, options=options)
                self.writeAndLog(':INST:SEL "SA"')
       

        #update VISA commands for triggers
        elif quant.name in ('S11 - Enabled', 'S21 - Enabled', 'S12 - Enabled',
                          'S22 - Enabled'):
            # new trace handling, use trace numbers, set all at once
            lParam = ['S11', 'S21', 'S12', 'S22']
            dParamValue = dict()
            for param in lParam:
                dParamValue[param] = self.getValue('%s - Enabled' % param)
            dParamValue[quant.name[:3]] = value
            # add parameters, if enabled
            self.dMeasParam = dict()
            for (param, enabled) in dParamValue.items():
                if enabled:
                    nParam = len(self.dMeasParam)+1
                    self.writeAndLog(":CALC:PAR%d:DEF %s" %
                                     (nParam, param))
                    self.dMeasParam[param] = nParam
            # set number of visible traces
            self.writeAndLog(":CALC:PAR:COUN %d" % len(self.dMeasParam))

        elif quant.name in ('Wait for new trace',):
            # do nothing
            pass

        elif quant.name in ('Range type',):
            # change range if single point
            if value == 'Single frequency':
                self.writeAndLog(':SENS:FREQ:SPAN:ZERO')
                self.writeAndLog(':SENS:SWE:POIN 2')
            if value == 'Full' and self.getValue('Mode') == 'Network Analyzer':
                self.writeAndLog('FREQ:STAR 30000')
                self.writeAndLog('FREQ:STOP 26.5E9')
            elif value == 'Full' and self.getValue('Mode') == 'Signal Analyzer':
                self.writeAndLog(':SENS:FREQ:SPAN:FULL')
                # self.writeAndLog('FREQ:STOP 26.6E9')
                # self.writeAndLog('FREQ:STAR 0')

        elif quant.name in ('Trace 1 - Enabled', 'Trace 2 - Enabled', 'Trace 3 - Enabled', 'Trace 4 - Enabled'):
            num = int(quant.name[6])
            if value == True:
                self.writeAndLog(':TRAC%d:TYPE CLRW' % num)
            if value == False:
                self.writeAndLog(':TRAC%d:TYPE BLAN' % num)
                self.writeAndLog(':CALC:MARK%d OFF' % num)

        elif quant.name in ('Marker 1 - Enabled', 'Marker 2 - Enabled', 'Marker 3 - Enabled', 'Marker 4 - Enabled', 'Marker 5 - Enabled', 'Marker 6 - Enabled'):
            num = int(quant.name[7])
            if value == True: 
                self.writeAndLog(':CALC:MARK%d:ACT' % num)
            if value == False:
                self.writeAndLog(':CALC:MARK%d OFF' % num)

        elif quant.name in ('Marker 1: Trace', 'Marker 2: Trace', 'Marker 3: Trace', 'Marker 4: Trace', 'Marker 5: Trace', 'Marker 6: Trace'):
            num = int(quant.name[7])
            #trac = quant.getValue()
            self.writeAndLog('CALC:MARK%d:TRAC %s' %(num,value))


        elif quant.name in ('Marker 1: Function', 'Marker 2: Function', 'Marker 3: Function', 'Marker 4: Function', 'Marker 5: Function', 'Marker 6: Function'):
            num = int(quant.name[7])
            if value == 'Peak':
                self.writeAndLog(':CALC:MARK%d:FUNC:MAX' % num)            
            if value == 'Minimum':
                self.writeAndLog(':CALC:MARK%d:FUNC:MIN' % num)


        elif quant.name in ('Marker 1: Normal Frequency', 'Marker 2: Normal Frequency','Marker 3: Normal Frequency','Marker 4: Normal Frequency','Marker 5: Normal Frequency','Marker 6: Normal Frequency'):
            num = int(quant.name[7])
            self.writeAndLog('CALC:MARK%d:X %d' %(num,value))


        elif quant.name in ('Marker A', 'Marker B'):
            pass

        elif quant.name in ('Autoscale'):
            if value == True:
                self.writeAndLog(':DISP:WIND:TRAC1:Y:AUTO')

        elif quant.name in ('Amplitude Scale'):
            if value == 'Log':
                self.writeAndLog(':AMPL:SCAL LIN')
                if self.getValue('Autoscale') == True:
                    self.writeAndLog(':DISP:WIND:TRAC1:Y:AUTO')
            if value == 'Linear':
                self.writeAndLog(':AMPL:SCAL LOG')
                if self.getValue('Autoscale') == True:
                    self.writeAndLog(':DISP:WIND:TRAC1:Y:AUTO')

        else:
            # run standard VISA case 
            value = VISA_Driver.performSetValue(self, quant, value, sweepRate, options)
        return value


    def performGetValue(self, quant, options={}):
        """Perform the Get Value instrument operation"""
        # check type of quantity

        if quant.name in ('S11 - Enabled', 'S21 - Enabled', 'S12 - Enabled',
                          'S22 - Enabled'):
            # update list of channels in use
            self.getActiveMeasurements()
            # get selected parameter
            param = quant.name[:3]
            value = (param in self.dMeasParam)
        elif quant.name in ('S11 - Value', 'S21 - Value', 'S12 - Value', 'S22 - Value'):
            # read trace, return averaged data
            data = self.readValueFromOther(quant.name[:3])
            return np.mean(data['y'])
        elif quant.name in ('S11', 'S21', 'S12', 'S22'):
            # check if channel is on
            if quant.name not in self.dMeasParam:
                # get active measurements again, in case they changed
                self.getActiveMeasurements()
            if quant.name in self.dMeasParam:
                # new trace handling, use trace numbers to select trace
                self.writeAndLog('CALC:PAR%d:SEL' % self.dMeasParam[quant.name])
                 
                # if not in continous mode, trig from computer
                bWaitTrace = self.getValue('Wait for new trace')
                dAverage = self.getValue('# of averages')

                # wait for trace, either in averaging or normal mod
                if bWaitTrace:

                    self.writeAndLog(':INIT:CONT OFF;*WAI')
                    # Clear averaging
                    self.writeAndLog(':SENS:AVER:CLE')
                    # wait some time before first check
                    self.wait(0.03)
                    bDone = False
                    # Wait for the averaging to finish
                    while (not bDone) and (not self.isStopped()):
                        # check if done
                        if int(dAverage) >= 1:
                            for i in range(int(dAverage)):
                                # if averaging, turn off cont and trigger new aquisition
                                self.writeAndLog(':INIT:IMM;*OPC?')
                                i += 1
                            bDone = True
                        else:
                            #stb = int(self.askAndLog('*ESR?'))
                            self.writeAndLog(':INIT:IMM;*OPC?')
                            bDone = True
                            #bDone = (stb & 1) > 0
                        if not bDone:
                            self.wait(0.1)
                    # if stopped, don't get data
                    if self.isStopped():
                        self.writeAndLog('*CLS;:INIT:CONT ON;')
                        return []
        
                # if stopped, don't get data
                if self.isStopped():
                    self.writeAndLog('*CLS;:INIT:CONT ON;')
                    return []

                # get data as float32, convert to numpy array
                self.writeAndLog(':FORM:DATA REAL,32;:CALC:DATA:SDATA?', bCheckError=False)
                
                #Read data
                sData = self.read(ignore_termination=True)
                # self.log('sData=' + str(sData))
                if bWaitTrace and not int(dAverage) >= 1:
                    self.writeAndLog(':INIT:CONT ON;')
                # strip header to find # of points
                i0 = sData.find(b'#')
                nDig = int(sData[i0+1:i0+2])
                nByte = int(sData[i0+2:i0+2+nDig])
                nData = int(nByte/4)
                nPts = int(nData/2)
                # get data to numpy array
                vData = np.frombuffer(sData[(i0+2+nDig):(i0+2+nDig+nByte)], 
                                      dtype='f', count=nData)
                # data is in I0,Q0,I1,Q1,I2,Q2,.. format, convert to complex
                mC = vData.reshape((nPts,2))
                vComplex = mC[:,0] + 1j*mC[:,1]

                # get start/stop frequencies
                numPoints = self.readValueFromOther('# of points')
                rangeType = self.readValueFromOther('Range type')

                if rangeType == 'Center - Span':
                    # Calculate start and stop frequencies for Center - Span case
                    centerFreq = self.readValueFromOther('Center frequency')
                    span = self.readValueFromOther('Span')
                    startFreq = centerFreq - (span/2)
                    stopFreq = centerFreq + (span/2)
                elif rangeType == 'Start - Stop':
                    startFreq = self.readValueFromOther('Start frequency')
                    stopFreq = self.readValueFromOther('Stop frequency')
                elif rangeType == 'Full':
                    startFreq = 30000
                    stopFreq = 26500000000

                value = quant.getTraceDict(vComplex, x0=startFreq, x1=stopFreq)
                self.writeAndLog(':INIT:CONT ON;')
            else:
                # not enabled, return empty array
                value = quant.getTraceDict([])

        elif quant.name in ('Wait for new trace',):
            # do nothing, return local value
            value = quant.getValue()

        elif quant.name in ('Trace 1', 'Trace 2', 'Trace 3', 'Trace 4'):
            num = int(quant.name[6])
            bWaitTrace = self.getValue('Wait for new trace')
            dAverage = self.getValue('# of averages')

            # wait for trace, either in averaging or normal mod
            if bWaitTrace:

                self.writeAndLog(':INIT:CONT OFF;*WAI')
                # Clear averaging
                #self.writeAndLog(':SENS:AVER:CLE')
                # wait some time before first check
                self.wait(0.03)
                bDone = False
                # Wait for the averaging to finish
                while (not bDone) and (not self.isStopped()):
                    # check if done
                    if int(dAverage) >= 1:
                        for i in range(int(dAverage)):
                            # if averaging, turn off cont and trigger new aquisition
                            self.writeAndLog(':INIT:IMM;*OPC?')
                            i += 1
                        bDone = True
                    else:
                        #stb = int(self.askAndLog('*ESR?'))
                        self.writeAndLog(':INIT:IMM;*OPC?')
                        bDone = True
                        #bDone = (stb & 1) > 0
                    if not bDone:
                        self.wait(0.1)
                # if stopped, don't get data
                if self.isStopped():
                    self.writeAndLog('*CLS;:INIT:CONT ON;')
                    return []
    
            # if stopped, don't get data
            if self.isStopped():
                self.writeAndLog('*CLS;:INIT:CONT ON;')
                return []


            # get data as float32, convert to numpy array
            self.writeAndLog(':FORM:DATA REAL,32;:TRAC%d:DATA?' % num, bCheckError=False)
            
            #Read data
            sData = self.read(ignore_termination=True)
            # self.log('sData=' + str(sData))
            if bWaitTrace and not int(dAverage) >= 1:
                self.writeAndLog(':INIT:CONT ON;')
            # strip header to find # of points
            i0 = sData.find(b'#')
            nDig = int(sData[i0+1:i0+2])
            nByte = int(sData[i0+2:i0+2+nDig])
            nData = int(nByte/4)
            nPts = int(nData)
            # get data to numpy array
            vData = np.frombuffer(sData[(i0+2+nDig):(i0+2+nDig+nByte)], 
                                  dtype='f', count=nData)

            mC = vData.reshape((nPts,1))
            vComplex = mC[:,0] 

            # get start/stop frequencies
            numPoints = self.readValueFromOther('# of points')
            rangeType = self.readValueFromOther('Range type')

            if rangeType == 'Center - Span':
                # Calculate start and stop frequencies for Center - Span case
                centerFreq = self.readValueFromOther('Center frequency')
                span = self.readValueFromOther('Span')
                startFreq = centerFreq - (span/2)
                stopFreq = centerFreq + (span/2)
            elif rangeType == 'Start - Stop':
                startFreq = self.readValueFromOther('Start frequency')
                stopFreq = self.readValueFromOther('Stop frequency')
            elif rangeType == 'Full':
                startFreq = 0
                stopFreq = 39750000000

            value = quant.getTraceDict(vComplex, x0=startFreq, x1=stopFreq)
        
            self.writeAndLog(':INIT:CONT ON;')


        elif quant.name in ('Marker Delta Y'):
            numa = self.readValueFromOther('Marker A')
            numb = self.readValueFromOther('Marker B')
            marka = self.readValueFromOther('Marker %s: Y Value' % numa)
            markb = self.readValueFromOther('Marker %s: Y Value' % numb)
            value = marka - markb
            return value

        elif quant.name in ('Marker Delta X'):
            numa = self.readValueFromOther('Marker A')
            numb = self.readValueFromOther('Marker B')
            marka = self.readValueFromOther('Marker %s: X Value' % numa)
            markb = self.readValueFromOther('Marker %s: X Value' % numb)
            value = marka - markb
            return value

        else:
            # for all other cases, call VISA driver
            value = VISA_Driver.performGetValue(self, quant, options)
        
        return value
        

    def getActiveMeasurements(self):
        """Retrieve and a list of measurement/parameters currently active"""
        # in this case, meas param is just a trace number
        self.dMeasParam = {}
        # get number or traces
        nTrace = int(self.askAndLog(":CALC:PAR:COUN?"))
        # get active trace names, one by one
        for n in range(nTrace):
            sParam = self.askAndLog(":CALC:PAR%d:DEF?" % (n+1))
            self.dMeasParam[sParam] = (n+1)

if __name__ == '__main__':
    pass
