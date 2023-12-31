/**
 * @file Battery_Tester.ino
 * @author Maximilian Mönikes
 * @brief A short skript to controll my homebrew battery tester Hardware
 * @version 1.0
 * @date 2023-10-21
 * 
 * @copyright Copyright (c) 2023
 * 
 */

#include <Wire.h>


#define DAC_CHARGE_ADDRESS 0x60     //I2C Address of the Charge Controller
#define DAC_DISCHARGE_ADDRESS 0x61  //I2C Address of the Discharge Controller
#define ADC_ADDRESS 0x48            //I2C Address of the ADS1115 ADC
#define ADC_CURRENT_CONFIG 0x60E3   //
#define ADC_VOLTAGE_CONFIG 0x00E3   //
#define ADC_CONFIG_REG 0x01         // Address of ADC configuration register
#define ADC_CONVERSION_REG 0x00     // Address of ADC result register
#define DAC_REF 5.04                // Reference voltage for the DACs
#define ADC_REF 6.144               // Reference voltage for the ADC (Internal)
#define DAC_DIVIDER 0.152           // Voltage divider ratio at the output of each DAC
#define SHUNT_VAL 0.15              // Value of the electronic load current sense shunt

#define BAT_SWITCH_PIN 4            // Pin for the NMOS Bidirectional switch between electronic loads and batterys
#define BAT_SWITCH_ON LOW           // Pinstate if current is allowed to flow in and out of the battery
#define BAT_SWITCH_OFF HIGH         // Pinstate if current is NOT allowed to flow in and out of the battery

#define CCCV_P 1.0                  // P Part of the CCCV PI regulator
#define CCCV_I 2.0                  // I Part of the CCCV PI regulator

//The Constant Current regulator uses a seperate PI algorithm with its own P and I Part
#define CC_P 0.01                   // P Part of the CC PI regulator
#define CC_I 1.0                    // I Part of the CC PI regulator

#define LOWER_VOLTAGE_LIMIT 0       //Should be regulated by the PC Software and 0V is ok for Sodium batterys
#define UPPER_VOLTAGE_LIMIT 4.5     //Manufacturer states that 4.1 is the charge cut-off voltage
#define CURRENT_LIMIT 5.0           //Maximum continous discharge in datasheet is 3C = 4.5A so 5A as a worst case limit should be reasonable


typedef enum 
{
  IDLE=0,
  CCCV=1,
  CCP=2,
  CCR=3,
  NUMOFSTATES=4
} testState_t;

uint8_t stringbuffer[64];
uint8_t stringpointer = 0;

float current = 0;
float voltage = 0;

float cccv_error_integrator = 0;
float cc_error = 0;

float current_setpoint = 0;
float voltage_setpoint = 3.6;
float cutoff_current = 0.05;

float CURRENT_SENSE_ZERO_VOLTAGE = 2.52;  //This is no constant because the zero current value is recalibrated at startup

uint32_t last_millis;

testState_t teststate;

void setup() {

  teststate = IDLE;                                //The Software always starts in IDLE State

  Wire.begin();                                    //Start I2C Interface
  setDAC_charge(0x0000);                           //Initialize DACs with 0 => No charge and discharge current
  setDAC_discharge(0x0000);

  Serial.begin(115200);                            //Initialize Serial Port

  writeADC(ADC_CONFIG_REG,ADC_CURRENT_CONFIG);     //Initalize the ADC in current Measurement mode for subsequent ADC calibration


  calibrate_current_sensor();                     //Calibrate the current Sensor 

  last_millis = millis();                         //Initialize loop time counter
}

void loop() {
  
   //The loop is only executed every 100 milliseconds
   if((millis() - last_millis) > 100U)
   {

     //Update Timing
     last_millis = millis();

     //Read Current and Voltage Values
     writeADC(ADC_CONFIG_REG,ADC_CURRENT_CONFIG);
     delay(15);
     current = convertCurrent(readADC(ADC_CONVERSION_REG));
     writeADC(ADC_CONFIG_REG,ADC_VOLTAGE_CONFIG);
     delay(15);
     voltage = convertVoltage(readADC(ADC_CONVERSION_REG));

     //Print to screen
     Serial.print(teststate);
     Serial.print(',');
     Serial.print(last_millis);
     Serial.print(',');
     Serial.print(voltage,4);
     Serial.print(',');
     Serial.println(current,4);

     //Check Limits and revert to IDLE if limits are Broken
     if(voltage < LOWER_VOLTAGE_LIMIT)
      teststate = IDLE;

     if(voltage > UPPER_VOLTAGE_LIMIT)
      teststate = IDLE;

     if(current > CURRENT_LIMIT)
      teststate = IDLE;

     if(current < (-CURRENT_LIMIT))
      teststate = IDLE;

     //Execute function for current 
     SerialRead(); 
     switch(teststate)
     {
       case IDLE:
        batSwitchOff();
        //current_regulator(0.0);

        cccv_error_integrator = 0;
        cc_error = 0;
        break;
       case CCCV:
        batSwitchOn();
        cccv_regulator(voltage_setpoint,current_setpoint);

        cc_error = 0;
        break;
       case CCP:
        batSwitchOn();
        setCurrent(current_setpoint);

        cccv_error_integrator = 0;
        cc_error = 0;
        break;
       case CCR:
        batSwitchOn();
        current_regulator(current_setpoint);

        cccv_error_integrator = 0;
        break;
       default:
        teststate = IDLE;
        current_regulator(0.0);
     }

   }

   
}

/**
 * @brief Compensate for the offset Voltage of the current sensor
 * 
 * The current sensor is bidirectional with the voltage representing 0 ampere beeing at VCC/2. Because VCC is generated by a LM317 voltage regulator
 * configured with a voltage divider, VCC might be suspect to some variation. The calibration routine
 * disconnects the battery via the NMOS switch so that no current can flow through the sensor and the 
 * output voltage is therefore representive of VCC/2
 */
void calibrate_current_sensor()
{
  batSwitchOff();
  delay(50);
  writeADC(ADC_CONFIG_REG,ADC_CURRENT_CONFIG);
  delay(50);
  uint16_t adcval = readADC(ADC_CONVERSION_REG);
  CURRENT_SENSE_ZERO_VOLTAGE = (((float) adcval)/32768 * ADC_REF);
  batSwitchOn(); 
}

/**
 * @brief Turn on (close) the NMOS based switch
 * 
 */
void batSwitchOn()
{
  digitalWrite(BAT_SWITCH_PIN, BAT_SWITCH_ON);
  pinMode(BAT_SWITCH_PIN, OUTPUT);
}

/**
 * @brief Turn off (open) the NMOS based switch
 * 
 */

void batSwitchOff()
{
  pinMode(BAT_SWITCH_PIN, INPUT);
}

/**
 * @brief Set the output value of a DAC connected to the I2C bus
 * 
 * @param val 12 bit output value of the DAC
 * @param address I2C address of the DAC
 */
void setDAC(uint16_t val, uint8_t address)
{
  Wire.beginTransmission(address);
  uint8_t uval = (0x3F & (val>>8));
  uint8_t lval = (uint8_t) (0xFF & (val));
  Wire.write(uval);
  Wire.write(lval);

  Wire.endTransmission();
 
}

/**
 * @brief Set the value of the charge DAC
 * 
 * @param val 12 bit DAC output
 */
void setDAC_charge(uint16_t val)
{
  setDAC(val,DAC_CHARGE_ADDRESS);
}

/**
 * @brief Set the value of the discharge DAC
 * 
 * @param val 12 bit DAC output
 */
void setDAC_discharge(uint16_t val)
{
  setDAC(val,DAC_DISCHARGE_ADDRESS);
}

/**
 * @brief Read a register of the ADS1115 ADC
 * 
 * @param reg Address of the register that should be reed from
 * @retval 16 bit value of the requested register
 */
uint16_t readADC(uint8_t reg)
{

  uint16_t retval = 0;
  
  Wire.beginTransmission(ADC_ADDRESS);
  Wire.write(reg);
  Wire.endTransmission();

  Wire.requestFrom(ADC_ADDRESS,2);

  while(Wire.available())
  {
    retval |= Wire.read()<<8;
    retval |= Wire.read(); 
  }
  
  return retval;
  
}

/**
 * @brief Write to the ADC register file
 * 
 * @param reg register address 
 * @param val new register value
 */
void writeADC(uint8_t reg, uint16_t val)
{
  Wire.beginTransmission(ADC_ADDRESS);
  Wire.write(reg);
  Wire.write((uint8_t) ((val>>8) & 0xFF));
  Wire.write((uint8_t) ((val) & 0xFF));
  Wire.endTransmission();
}

/**
 * @brief convert an ADC value of the current Sensor to the voltage it represents
 * 
 * @param adcval 16 bit raw value of an ADC current measurement 
 * @return float measured current in Ampere (current flowing out of the battery has a negative sign)
 */
float convertCurrent(uint16_t adcval)
{
  return (((float) adcval)/32768 * ADC_REF - CURRENT_SENSE_ZERO_VOLTAGE) / 0.185; 
}

/**
 * @brief convert an ADC value of the battery voltage to the actual voltage
 * 
 * @param adcval 16 bit raw value of the ADC measurement
 * @return float measured voltage in Volt
 */
float convertVoltage(int16_t adcval)
{
  return (((float) adcval)/32768 * ADC_REF);
}

/**
 * @brief Loop function of the PI based current regulator
 * 
 * @param target_current target charge or discharge current in Ampere
 */
void current_regulator(float target_current)
{
 
  cc_error += CC_I*(target_current-current);
  if(cc_error > 5.0)
  cc_error = 5.0;

  if(cc_error < -5.0)
  cc_error = -5.0;

  float error = cc_error + (CC_P * (target_current - current));

  if(error > 5.0)
  error = 5.0;

  if(error < -5.0)
  error = -5.0;
  
  setCurrent(error);
}

/**
 * @brief Set the DACs to the specified current (might be unprecise)
 * 
 * @param current desired current in Ampere
 */
void setCurrent(float current)
{
  
  if(current > 0)
  {
    
    setDAC_discharge(0);
    uint16_t dacval = (uint16_t) (4096*SHUNT_VAL/(DAC_DIVIDER*DAC_REF) * current);
    if(dacval >= 81)
      dacval -= 81;
    setDAC_charge(dacval);
  }
  if(current < 0)
  {
    setDAC_charge(0);
    uint16_t dacval = (uint16_t) (4096*SHUNT_VAL/(DAC_DIVIDER*DAC_REF) * current * (-1));
    if(dacval <= 3950)
      dacval += 81;
    setDAC_discharge(dacval);
  }
  if(current == 0)
  {
    setDAC_discharge(0);
    setDAC_charge(0);
  }

  
}

/**
 * @brief Loop function for the Serial communication
 * 
 * All received bytes are interpreted in this function
 * 
 */
void SerialRead()
{
  uint8_t incoming_len = Serial.available();
  if(incoming_len > 0)
  {
    if((incoming_len + stringpointer) > 64)
    {
      stringpointer = 0;
    }
    
    Serial.readBytes(&stringbuffer[stringpointer],incoming_len);
    stringpointer += incoming_len;
    uint8_t terminated = 0;
    for(uint8_t i = 0; i < 64; i++)
    {
      if(stringbuffer[i] == '\n')
      {
        terminated = 1;
      }
    }

    if(terminated)
    {
      char vset[10];
      char cset[10];
      char cutset[10];
      sscanf(stringbuffer,"%d %s %s %s",&teststate, vset,  cset, cutset);
      voltage_setpoint = (float) atof(vset);
      current_setpoint = (float) atof(cset);
      cutoff_current = (float) atof(cutset);
      for(uint8_t i = 0; i < 64; i++) stringbuffer[i] = 0;
      terminated = 0;
      stringpointer = 0;
    }
    
  }
}

/**
 * @brief Loop function of the CCCV algorithm
 * 
 * @param target_voltage Maximum charge voltage in Volt
 * @param current_limit  Current Limit for the CC Phase in Ampere
 */
void cccv_regulator(float target_voltage, float current_limit)
{
  float voltage_error = target_voltage - voltage; 
  cccv_error_integrator += voltage_error * CCCV_I;

  if(cccv_error_integrator > 3.0)
    cccv_error_integrator = 3.0;

  if(cccv_error_integrator < (-3.0))
    cccv_error_integrator = -3.0;

  float current_setpoint = cccv_error_integrator + (voltage_error * CCCV_P);
  
  if((current_setpoint > 0) && (current_setpoint > current_limit))
    current_setpoint = current_limit;

  if((current_setpoint < 0) && (current_setpoint < (-current_limit)))
    current_setpoint = -current_limit;
    
  setCurrent(current_setpoint);
}
