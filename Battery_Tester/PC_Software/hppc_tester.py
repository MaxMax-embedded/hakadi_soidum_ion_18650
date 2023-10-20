import serial as Serial
import time as tim


"""
The Purpose of this Class is to handle all communication with the Arduino based Hardware. The Hardware itself contains a State Machine with
four different states (see the operatingmodes dict). These are the following:

IDLE: The MOSFET-Switch is opend so no current can flow in and out of the battery
CCCV: Implements a CCCV charge algorithm based of an PI regulator
CCP: unregulated current pulse to allow for fast rise times in pulse test scenarios
CCR: regulated current charge or discharge

All functions to control the battery tester are contained inside the tester class. The constructor of the class takes a Serial object as argument
which represents the COM port of the Arduino.
"""


operatingmodes = {
    "IDLE" : "0",
    "CCCV" : "1",
    "CCP" : "2",
    "CCR" : "3"
}

class tester:

    """
    Set Functions are used to send commands to the arduino. Might be changed to private functions in the future

    Start Functions are used as an interface between the test programm and the Hardware
    Starting a process will lead to instr_cmplt becoming False.
    To check the current state of the operation call check_operation_complete()
    If at least one termination condition is meet, it will return True and set instr_cmplt to True as well
    """

    _comport = []
    operatingmode = 0
    last_millis = 0
    current = 0
    voltage = 0
    upper_voltage_limit = 0
    lower_voltage_limit = 0
    cutoff_current = 0
    instr_cmplt = True

    instruction_start_time = 0
    instruction_stop_time = 0
    target_operating_mode = 0


    def __init__(self, comport:Serial):
        self._comport = comport
        return
    
    def get_data(self):
        """
        Reads Data from the Arduino based Frontend via Serial
        """
        data = self._comport.readline()
        values = str(data,'utf-8').split(',')
        self.operatingmode = int(values[0])
        self.time_millis = int(values[1])
        self.voltage = float(values[2])
        self.current = float(values[3])
        return data
    


    def set_idle(self):
        """
        Set Arduino State Machine in IDLE State. Might change to private function in further versions
        """
        command = operatingmodes["IDLE"] + " 0.0 0.0 0.0\n"
        self._comport.write(bytes(command,"ascii"))

        return
    
    def set_cccv(self, target_voltage, current_limit, cutoff_current):
        """
        Set Arduino State Machine in CCCV State. Might change to private function in further versions
        """
        command = operatingmodes["CCCV"] + " " + str(target_voltage) + " " + str(current_limit) + " " + str(cutoff_current) + "\n"
        self._comport.write(bytes(command,"ascii"))
        return
    
    def set_cc_pulse(self, current):
        """
        Set Arduino State Machine in CCP State. Might change to private function in further versions
        """
        command = operatingmodes["CCP"] + " 0.0 " + str(current) + " 0.0" + "\n"
        self._comport.write(bytes(command,"ascii"))
        return
    
    def set_cc_regulated(self,current):
        """
        Set Arduino State Machine in CCR State. Might change to private function in further versions
        """
        command = operatingmodes["CCR"] + " 0.0 " + str(current) + " 0.0" + "\n"
        self._comport.write(bytes(command,"ascii"))
        return



    def start_cc_regulated(self,current,time):
        """Start a regulated charge or discharge

        Keyword arguments:
        current -- charge current (positive) or discharge current (negative) in ampere
        time -- Time for the charge/discharge operation in seconds. check_operation_complete() returns True after this time has passed

        """
        if(current == 0.0):
            self.target_operating_mode = int(operatingmodes["IDLE"])
            self.set_idle()
        else:
            self.target_operating_mode = int(operatingmodes["CCR"])
            self.set_cc_regulated(current)
        self.instruction_start_time = tim.time()
        self.instruction_stop_time = tim.time() + time
        self.instr_cmplt = False
        

    def start_idle_time(self,time):
        """Start a time without charge or discharge
        
        Keyword arguments:
        time -- Idle time in seconds
        """
        self.start_cc_regulated(0.0,time)
        self.target_operating_mode = int(operatingmodes["IDLE"])

    

    def start_cc_pulse(self, current, upper_voltage_limit ,lower_voltage_limit, time):
        """Start a unregulated charge or discharge pulse
        
        Keyword arguments:
        current -- charge current (positive) or discharge current (negative) in ampere
        upper_voltage_limit -- Maximum voltage in V
        lower_voltage_limit -- Minimum voltage in V
        time -- Maximum time for the operation in seconds. Timeout leads to check_operation_complete() to return True
        """
        self.set_voltage_limits(upper_voltage_limit,lower_voltage_limit)
        self.set_cc_pulse(current)
        self.instruction_start_time = tim.time()
        self.instruction_stop_time = tim.time() + time
        self.instr_cmplt = False
        self.target_operating_mode = int(operatingmodes["CCP"])


    

    def start_cccv(self, target_voltage, current_limit, cutoff_current, time):
        """Start a CCCV charge.

        Keyword arguments:
        target_voltage -- Final charge voltage in V
        current_limit -- Maximum charge current in A
        cutoff_current -- A current (in Ampere) lower then this value during the charging process will cause check_operation_complete() to return True
        time -- Maximum time for the Operation in seconds. Timeout leads to check_operation_complete() to return True
        """
        self.set_cccv(target_voltage,current_limit,cutoff_current)
        self.cutoff_current = cutoff_current
        self.instruction_start_time = tim.time()
        self.instruction_stop_time = tim.time() + time
        self.instr_cmplt = False
        self.target_operating_mode = int(operatingmodes["CCCV"])

    
    def set_voltage_limits(self, upper_limit:float, lower_limit:float):
        """Set global limits for all operations. Meeting the condition will cause check_operation_complete() to return True

        Keyword arguments:
        upper_limit -- Maximum voltage in V
        lower_limit -- Minimum voltage in V
        """
        self.upper_voltage_limit = upper_limit
        self.lower_voltage_limit = lower_limit

    
    def check_operation_complete(self):
        """Returns true if the current operation is completed"""
        if(self.instr_cmplt == True):
            return False
        
        if(self.target_operating_mode != self.operatingmode):
            return False
        
        if(tim.time() > self.instruction_stop_time):
            self.instr_cmplt = True
            return True
        
        if(self.operatingmode == int(operatingmodes["CCCV"])):
            if(self.current < self.cutoff_current):
                self.instr_cmplt = True
                print("cutoff")
                return True
            
        if(self.voltage > self.upper_voltage_limit):
            self.instr_cmplt = True
            print("ov")
            return True
        
        if(self.voltage < self.lower_voltage_limit):
            self.instr_cmplt = True
            print("uv")
            return True
        
        return False