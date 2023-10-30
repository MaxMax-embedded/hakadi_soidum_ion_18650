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
OCV_DISCHARGE_CURRENT = -1.0      #Discharge current for the pseudo OCV test in Ampere (must be negative and low in regards to the battery capacity)
OCV_DISCHARGE_STEP_WAIT = 1200       #Wait time after the SoC was reduced in seconds
OCV_DISCHARGE_STEP_DURATION = 270 #Duration of the discharge step in seconds

OCV_CHARGE_CUTOFF_VOLTAGE = 4.1     #Final charge voltage for the charge part of the pseudo OCV test in V
OCV_CHARGE_CURRENT = 1.0          #Charge current for the pseudo OCV test in Ampere (must be positive and low in regards to the battery capacity)
OCV_CHARGE_STEP_WAIT = 1200          #Wait time after the SoC was increased in seconds
OCV_CHARGE_STEP_DURATION = 270   #Duration of the charge step in seconds
#####################################################

comport = Serial.Serial(port="COM6",baudrate=115200)
logfile = "./ocv_test_inc_1.csv"  #Path of the logfile for the experiment

running = True
bat_tester = hppc_tester.tester(comport)

instructionpointer = 0
dischargesteps = 0
operatingmode = 0
chargesteps = 0

lower_limit_reached = 0
upper_limit_reached = 0

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

    
    if(bat_tester.voltage > OCV_CHARGE_CUTOFF_VOLTAGE):
        upper_limit_reached = 1
    
    if(bat_tester.voltage < OCV_DISCHARGE_CUTOFF_VOLTAGE):
        lower_limit_reached = 1

    if(instructionpointer == 0):
        instructionpointer = instructionpointer + 1
        bat_tester.set_voltage_limits(CCCV_CHARGE_VOLTAGE+0.1,OCV_DISCHARGE_CUTOFF_VOLTAGE-0.1)
        bat_tester.start_cccv(CCCV_CHARGE_VOLTAGE,CCCV_CHARGE_CURRENT,CCCV_CUTOFF_CURRENT,CCCV_CHARGE_TIMEOUT)
       
    
    elif(bat_tester.check_operation_complete()):

        if(instructionpointer == 1):
            bat_tester.start_idle_time(IDLE_BEFORE_OCV_START)
            operatingmode = 1

        if(lower_limit_reached == 0):
            if(operatingmode == 1):
                    dischargesteps = dischargesteps + 1
                    bat_tester.start_cc_regulated(OCV_DISCHARGE_CURRENT,OCV_DISCHARGE_STEP_DURATION)
                    operatingmode = 2

            elif(operatingmode == 2):
                bat_tester.start_idle_time(OCV_DISCHARGE_STEP_WAIT)
                operatingmode = 1
        else:
            operatingmode = 3

        if(lower_limit_reached == 1):
            if(operatingmode == 3):
                    bat_tester.set_voltage_limits(CCCV_CHARGE_VOLTAGE+0.05,OCV_DISCHARGE_CUTOFF_VOLTAGE-0.1)
                    chargesteps = chargesteps + 1
                    bat_tester.start_cc_regulated(OCV_CHARGE_CURRENT,OCV_CHARGE_STEP_DURATION)
                    operatingmode = 4

            elif(operatingmode == 4):
                bat_tester.start_idle_time(OCV_CHARGE_STEP_WAIT)
                operatingmode = 3

            if(upper_limit_reached == 1):
                operatingmode = 5


        if(operatingmode == 5):
            bat_tester.start_idle_time(10)
            running = False

        instructionpointer = instructionpointer + 1
        print(instructionpointer)

print(chargesteps)
print(dischargesteps)
comport.close()