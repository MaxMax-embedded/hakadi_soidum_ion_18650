import serial as Serial
import hppc_tester
import time

############# Experiment Parameters ################
CCCV_CHARGE_CURRENT = 0.75    #CC Phase current of CCCV charge in Ampere
CCCV_CUTOFF_CURRENT = 0.075   #Cutoff current of CCCV charge in Ampere
CCCV_CHARGE_VOLTAGE = 4.1     #Charge Voltage in V
CCCV_CHARGE_TIMEOUT = 10000   #Maximum charging time if cutoff current is not reacher earlier in seconds

IDLE_BEFORE_OCV_START = 3600  #Rest Time between CCCV charge and start of the pseudo OCV test in seconds

OCV_DISCHARGE_CUTOFF_VOLTAGE = 1.5  #Cutoff voltage for the low C-rate discharge in V
OCV_DISCHARGE_CURRENT = -0.075      #Discharge current for the pseudo OCV test in Ampere (must be negative and low in regards to the battery capacity)
OCV_DISCHARGE_TIMEOUT = 80000       #Maximum discharge time if cutoff voltage is not reached before in seconds

OCV_CHARGE_CUTOFF_VOLTAGE = 4.1     #Final charge voltage for the charge part of the pseudo OCV test in V
OCV_CHARGE_CURRENT = 0.075          #Charge current for the pseudo OCV test in Ampere (must be positive and low in regards to the battery capacity)
OCV_CHARGE_TIMEOUT = 80000          #Maximum charge time if charge voltage is not reached in seconds
#####################################################

comport = Serial.Serial(port="COM6",baudrate=115200)
logfile = "./ocv_test.csv"  #Path of the logfile for the experiment

running = True
bat_tester = hppc_tester.tester(comport)

instructionpointer = 0

        

with open(logfile, 'a') as f:
    f.write("step,mode,time,voltage,current\n")

while running:
    #Wait for new logdata -> advance in testing scheduel
    logdata = bat_tester.get_data()
    with open(logfile, 'a') as f:
        f.write(str(instructionpointer) + "," + str(logdata,'utf-8').replace('\r', ""))
    print(logdata)
    print(logdata)
    print(instructionpointer)
    if(instructionpointer == 0):
        instructionpointer = instructionpointer + 1
        bat_tester.set_voltage_limits(CCCV_CHARGE_VOLTAGE+0.1,OCV_DISCHARGE_CUTOFF_VOLTAGE-0.1)
        bat_tester.start_cccv(CCCV_CHARGE_VOLTAGE,CCCV_CHARGE_CURRENT,CCCV_CUTOFF_CURRENT,CCCV_CHARGE_TIMEOUT)
       
    
    elif(bat_tester.check_operation_complete()):
        if(instructionpointer == 1):
            bat_tester.start_idle_time(IDLE_BEFORE_OCV_START)

        if(instructionpointer == 2):
            bat_tester.set_voltage_limits(CCCV_CHARGE_VOLTAGE+0.1,OCV_DISCHARGE_CUTOFF_VOLTAGE)
            bat_tester.start_cc_regulated(OCV_DISCHARGE_CURRENT,OCV_DISCHARGE_TIMEOUT)
        if(instructionpointer == 3):
            bat_tester.set_voltage_limits(OCV_CHARGE_CUTOFF_VOLTAGE,OCV_DISCHARGE_CUTOFF_VOLTAGE-0.1)
            bat_tester.start_cc_regulated(OCV_CHARGE_CURRENT,OCV_CHARGE_TIMEOUT)
        if(instructionpointer == 4):
            bat_tester.start_idle_time(10)
            running = False
        instructionpointer = instructionpointer + 1
        print(instructionpointer)


comport.close()