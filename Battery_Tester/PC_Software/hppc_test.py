import serial as Serial
import hppc_tester
import time

############# Experiment Parameters ################
CCCV_CHARGE_CURRENT = 0.75       #CC Phase current of CCCV charge in Ampere
CCCV_CUTOFF_CURRENT = 0.075      #Cutoff current of CCCV charge in Ampere
CCCV_CHARGE_VOLTAGE = 4.1        #Charge Voltage in V
CCCV_CHARGE_TIMEOUT = 10000      #Maximum charging time if cutoff current is not reacher earlier in seconds
CUTOFF_VOLTAGE = 1.5             #Minimum Voltage of the Battery Cell according to Datasheet

IDLE_BEFORE_HPPC_START = 3600    #Rest Time after CCCV charge and before first HPPC Pulses

HPPC_DISCHARGE_PULSE_CURRENT = -3.0 #Current of the HPPC Discharge Pulse in Ampere (must be negative)
HPPC_DISCHARGE_PULSE_DURATION = 10  #Duration of the HPPC discharge pulse in seconds
HPPC_DISCHARGE_PULSE_PAUSE = 40     #Pause between Discharge and subsequent charge pulse in seconds
HPPC_CHARGE_PULSE_CURRENT = 3.0     #Current of the HPPC charge Pulse in Ampere (must be positive)
HPPC_CHARGE_PULSE_DURATION = 10     #Duration of the HPPC charge pulse in seconds
HPPC_CHARGE_PULSE_PAUSE = 40        #Pause between charge pulse and step discharge in seconds
HPPC_STEP_DISCHARGE_CURRENT = -0.1  #Discharge current during the step discharge in ampere (must be negative)
HPPC_STEP_DISCHARGE_TIME = 1000     #Discharge time for step discharge in seconds
HPPC_REST_AFTER_STEP = 3600         #Rest time after a discharge step in seconds

#####################################################

comport = Serial.Serial(port="COM6",baudrate=115200)
logfile = "./hppc_test.csv" #Path of logfile for the experiment

running = True
bat_tester = hppc_tester.tester(comport)

instructionpointer = 0

def hppcsubcycle(startoffset):
        if((instructionpointer-startoffset) == 1):
            bat_tester.set_voltage_limits(4.5,0.5)
            bat_tester.start_cc_pulse(HPPC_DISCHARGE_PULSE_CURRENT,4.5,0.5,HPPC_DISCHARGE_PULSE_DURATION)
        if((instructionpointer-startoffset) == 2):
            bat_tester.start_idle_time(HPPC_DISCHARGE_PULSE_PAUSE)
        if((instructionpointer-startoffset) == 3):
            bat_tester.set_voltage_limits(4.5,0.5)
            bat_tester.start_cc_pulse(HPPC_CHARGE_PULSE_CURRENT,4.5,0.5,HPPC_CHARGE_PULSE_DURATION)
        if((instructionpointer-startoffset) == 4):
            bat_tester.start_idle_time(HPPC_CHARGE_PULSE_PAUSE)
        if((instructionpointer-startoffset) == 5):
            bat_tester.set_voltage_limits(4.2,CUTOFF_VOLTAGE)
            bat_tester.start_cc_regulated(HPPC_STEP_DISCHARGE_CURRENT,HPPC_STEP_DISCHARGE_TIME)
        if((instructionpointer-startoffset) == 6):
            bat_tester.set_voltage_limits(4.4,CUTOFF_VOLTAGE - 0.1)
            bat_tester.start_idle_time(HPPC_REST_AFTER_STEP)
        
        

with open(logfile, 'a') as f:
    f.write("step,mode,time,voltage,current\n")

while running:
    #Wait for new logdata -> advance in testing scheduel
    logdata = bat_tester.get_data()
    
    with open(logfile, 'a') as f:
        f.write(str(instructionpointer) + "," + str(logdata,'utf-8').replace('\r', ""))
    print(logdata)
    
    if(instructionpointer == 0):
        instructionpointer = instructionpointer + 1
        bat_tester.set_voltage_limits(CCCV_CHARGE_VOLTAGE+0.1,CUTOFF_VOLTAGE-0.1)
        bat_tester.start_cccv(CCCV_CHARGE_VOLTAGE,CCCV_CHARGE_CURRENT,CCCV_CUTOFF_CURRENT,CCCV_CHARGE_TIMEOUT)
       
    
    elif(bat_tester.check_operation_complete()):
        if(instructionpointer == 1):
            bat_tester.start_idle_time(IDLE_BEFORE_HPPC_START)

        #Is this code pretty? No but it works for now
        hppcsubcycle(1)
        hppcsubcycle(7)
        hppcsubcycle(13)
        hppcsubcycle(19)
        hppcsubcycle(25)
        hppcsubcycle(31)
        hppcsubcycle(37)
        hppcsubcycle(43)
        hppcsubcycle(49)
        hppcsubcycle(55)

        if(instructionpointer == 62):
            bat_tester.set_voltage_limits(CCCV_CHARGE_VOLTAGE+0.1,CUTOFF_VOLTAGE-0.1)
            bat_tester.start_cccv(CCCV_CHARGE_VOLTAGE,CCCV_CHARGE_CURRENT,CCCV_CUTOFF_CURRENT,CCCV_CHARGE_TIMEOUT)
        if(instructionpointer == 63):
            bat_tester.start_idle_time(10)
            running = False
        instructionpointer = instructionpointer + 1
        print(instructionpointer)


comport.close()