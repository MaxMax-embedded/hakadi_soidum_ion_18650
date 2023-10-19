# Measurements with Hakadi 18650 Sodium Ion Cells

## Project Overview

The Goal of this project is to provide an overview about what a commercially available Sodium Ion cell is capable of in the end of 2023. As far as I know, Hakadi is the only battery brand selling Sodium based cells to the general Public. For experimental purposes I bought 4 cells in a 18650 package with a claimed capacity of 1500mAh. The datasheet provides the following general specifications:

| Parameter | Value |
| ----- | ----- |
| Nominal Capacity at 0.5C | 1500mAh |
| Typical Capacity at 0.5C | 1530mAh |
| Charge Voltage |  4.1V |
| Cutoff Voltage | 1.5V |
| Weight | 37.5g |
| Charge Temperature Range | -10-45°C |
| Discharge Temperature Range | -30-60°C|
| Internal Resistance | <20mOhm |

Notable are the wide voltage range as well as the large temperature range, which supports the claim of Hakadi that this is in fact a real Sodium based battery and not a rebranded Lithium based one. On a first glance, 1500mAh is also on the lower to mid end of available LiFePo based 18650 and not an unrealistic claim as sometimes done by chinese manufacturers.

The research in this reposetory is done by me as a Student with my own, in part self developed, measurement equipment so my capabillity for longer term aging tests, as well as test at temperatures other then room temperature are limited at the moment. I also do research at my University and may link to papers in the future. 

## Testplan

I am currently waiting for the cells from China so no tests are in progress for the moment. Heres the test plan as well as the current status:

| Test | Progress |
| ---- | ---- |
| Capacity with 0.5C Discharge | <span style="color:grey"> waiting for cells </span> |
| HPPC test with 5% steps | <span style="color:grey"> not in progress </span> |
| incremental charge and discharge OCV | <span style="color:grey"> not in progress </span> |
| Discharge Capacity at various C rates | <span style="color:grey"> not in progress </span> |
| 0V Discharge behaviour | <span style="color:grey"> not in progress </span> |

All tests are carried out at room temperature. A overview about the testing equipment and its associated limits are provided in the next chapter. Hakadi claims that the cells can safely be dicharged and recharged to 0V which is a possibility for Sodium Cells with certain electrolytes and therefore needs to be tested 😉

## Measurement Equipment

To perform the various tests listed above it is necessary to charge and discharge the cells with a controlled current. To performed the controlled discharge, a self developed electronic load is used. The charge is a bit more tricky, because the charge current needs to be controlled arbitrary so no standard charging IC can be used. Because of the fast change between charge and Discharge pulses for the HPPC, a Lab Bench Power Supply is also no solution for the charge cycle. To solve this problem, a electronic load can be used for the charge cycle as well but with the ground reference "shifted" to the positive terminal voltage of the battery. The "upper" load therefore acts as a voltage controlled current source while the "lower" load acts as a voltage controlled current sink. 

With the loads beeing made from non precise components it is necessary to measure the current going in and out of the battery independently. This is done by using a ACS712-05 Current sense Module which uses the ACS712 Hall based current sensor IC configured to a range of +-5A. The uuput of the current sensor, as well as the voltage of the battery is measured by a ADS1115 16-bit ADC sensor. While the voltage of the current sensor is measured single ended, the battery voltage is measured differentially to provide better accuracy. The sample rate of all values is approx 100ms and the delay between current and voltage measurements is approx 20ms. To mitigate the influence of wiring on impedance measurements, the cell holder provides the option to perform 4-wire measurements of the cell under test.

