import serial as Serial
import hppc_tester
import time

############# Experiment Parameters ################
CHARGE_CURRENT = 0.75   #CC Phase current of CCCV charge in Ampere
CUTOFF_CURRENT = 0.075  #Cutoff current of CCCV charge in Ampere
CHARGE_VOLTAGE = 4.1    #Charge Voltage in V
CHARGE_TIMEOUT = 10000  #Maximum charging time if cutoff current is not reacher earlier in seconds

DISCHARGE_CUTOFF_VOLTAGE = 1.5  #Cutoff voltage for the constant current discharge in V
DISCHARGE_CURRENT = -0.75       #Discharge current in Ampere (must be negative)
DISCHARGE_TIMEOUT = 10000       #Maximum discharge time in seconds
#####################################################

comport = Serial.Serial(port="COM5",baudrate=115200)
logfile = "./static_test.csv" #Path of the logfile for the experiment

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
    
    if(instructionpointer == 0):
        instructionpointer = instructionpointer + 1
        bat_tester.set_voltage_limits(CHARGE_VOLTAGE + 0.1 , DISCHARGE_CUTOFF_VOLTAGE - 0.1)
        bat_tester.start_cccv(CHARGE_VOLTAGE,CHARGE_CURRENT,CUTOFF_CURRENT,CHARGE_TIMEOUT)
    
    elif(bat_tester.check_operation_complete()):

        if(instructionpointer == 1):
            bat_tester.set_voltage_limits(CHARGE_VOLTAGE + 0.1, DISCHARGE_CUTOFF_VOLTAGE)
            bat_tester.start_cc_regulated(DISCHARGE_CURRENT,DISCHARGE_TIMEOUT)
        if(instructionpointer == 2):
            bat_tester.set_voltage_limits(CHARGE_VOLTAGE + 0.1 , DISCHARGE_CUTOFF_VOLTAGE - 0.1)
            bat_tester.start_cccv(CHARGE_VOLTAGE,CHARGE_CURRENT,CUTOFF_CURRENT,CHARGE_TIMEOUT)
        if(instructionpointer == 3):
            bat_tester.start_idle_time(10)
            running = False
        instructionpointer = instructionpointer + 1
        print(instructionpointer)


comport.close()