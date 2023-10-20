#include <Wire.h>
#include "Test_Control.hpp"

#define DAC_CHARGE_ADDRESS 0x60
#define DAC_DISCHARGE_ADDRESS 0x61
#define ADC_ADDRESS 0x48
#define ADC_CURRENT_CONFIG 0x60E3
#define ADC_VOLTAGE_CONFIG 0x00E3
#define ADC_CONFIG_REG 0x01
#define ADC_CONVERSION_REG 0x00
#define DAC_REF 5.04
#define ADC_REF 6.144
#define DAC_DIVIDER 0.152
#define SHUNT_VAL 0.15

#define BAT_SWITCH_PIN 4
#define BAT_SWITCH_ON LOW
#define BAT_SWITCH_OFF HIGH

#define CCCV_P 1.0
#define CCCV_I 2.0

#define CC_P 0.01
#define CC_I 1.0

#define LOWER_VOLTAGE_LIMIT 2.3
#define UPPER_VOLTAGE_LIMIT 4.3
#define CURRENT_LIMIT 5.0

uint8_t stringbuffer[64];
uint8_t stringpointer = 0;


float current = 0;
float voltage = 0;

float cccv_error_integrator = 0;
float cc_error = 0;

float current_setpoint = 0;
float voltage_setpoint = 3.6;
float cutoff_current = 0.05;

float CURRENT_SENSE_ZERO_VOLTAGE = 2.52;

uint32_t last_millis;

testState_t teststate;

void setup() {
  // put your setup code here, to run once:

  
  Wire.begin();
  setDAC_charge(0x0000);
  setDAC_discharge(0x0000);
  Serial.begin(115200);
  writeADC(ADC_CONFIG_REG,ADC_CURRENT_CONFIG);
  last_millis = millis();
  teststate = IDLE;
  calibrate_current_sensor();
}

void loop() {
  // put your main code here, to run repeatedly:
   //idle_regulator(current);
   //setCurrent(-0.3);
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

void batSwitchOn()
{
  digitalWrite(BAT_SWITCH_PIN, BAT_SWITCH_ON);
  pinMode(BAT_SWITCH_PIN, OUTPUT);
}

void batSwitchOff()
{
  pinMode(BAT_SWITCH_PIN, INPUT);
}

void setDAC(uint16_t val, uint8_t address)
{
  Wire.beginTransmission(address);
  uint8_t uval = (0x3F & (val>>8));
  uint8_t lval = (uint8_t) (0xFF & (val));
  Wire.write(uval);
  Wire.write(lval);

  Wire.endTransmission();
 
}

void setDAC_charge(uint16_t val)
{
  setDAC(val,DAC_CHARGE_ADDRESS);
}

void setDAC_discharge(uint16_t val)
{
  setDAC(val,DAC_DISCHARGE_ADDRESS);
}

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

void writeADC(uint8_t reg, uint16_t val)
{
  Wire.beginTransmission(ADC_ADDRESS);
  Wire.write(reg);
  Wire.write((uint8_t) ((val>>8) & 0xFF));
  Wire.write((uint8_t) ((val) & 0xFF));
  Wire.endTransmission();
}

float convertCurrent(uint16_t adcval)
{
  return (((float) adcval)/32768 * ADC_REF - CURRENT_SENSE_ZERO_VOLTAGE) / 0.185; 
}

float convertVoltage(int16_t adcval)
{
  return (((float) adcval)/32768 * ADC_REF);
}

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
