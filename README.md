# Measurements with Hakadi 18650 Sodium Ion Cells

## Project Overview

The Goal of this project is to provide an overview about what a commercially available Sodium Ion cell is capable of in the end of 2023. As far as I know, Hakadi is the only battery brand selling Sodium based cells to the general Public. For experimental purposes I bought 4 cells in a 18650 package with a claimed capacity of 1500mAh. The datasheet provides the following general specifications:

| Parameter | Value |
| ----- | ----- |
| Nominal Capacity at 0.5C | 1500mAh |
| Typical Capacity at 0.5C | 1530mAh |
| Charge Voltage |  4.1V |
| Cutoff Voltage | 1.5V |
| Continuous Charge Rate at 0-45°C | 1C |
| Continuous Discharge Rate at 0-45°C | 3C |
| Weight | 37.5g |
| Charge Temperature Range | -10-45°C |
| Discharge Temperature Range | -30-60°C|
| Internal Resistance | <20mOhm |

Notable are the wide voltage range as well as the large temperature range, which supports the claim of Hakadi that this is in fact a real Sodium based battery and not a rebranded Lithium based one. On a first glance, 1500mAh is also on the lower to mid end of available LiFePo based 18650 and not an unrealistic claim as sometimes done by chinese manufacturers.

The research in this repository is done by me as a student with my own, in part self developed, measurement equipment so my capabillity for longer term aging tests, as well as test at temperatures other then room temperature are limited at the moment. I also do research at my University and may link to papers in the future. 

## Testplan

In the following table, you can see what kind of test I've planned with the cells. 

| Test | Progress |
| ---- | ---- |
| Capacity with 1C Discharge | <span style="color:grey"> Done </span> |
| Discharge Capacity at various C rates | <span style="color:grey"> Done for 0.25C - 2C </span> |
| HPPC test with 10% steps | <span style="color:grey"> Done </span> |
| incremental charge and discharge OCV | <span style="color:grey"> Done </span> |
| 0V Discharge behaviour | <span style="color:grey"> not in progress </span> |

All tests are carried out at room temperature. A overview about the testing equipment and its associated limits are provided in the next chapter. Hakadi claims that the cells can safely be dicharged and recharged to 0V which is a possibility for Sodium Cells with certain electrolytes and therefore needs to be tested 😉

## Measurement Equipment

To perform the various tests listed above it is necessary to charge and discharge the cells with a controlled current. To performed the controlled discharge, a self developed electronic load is used. The charge is a bit more tricky, because the charge current needs to be controlled arbitrary so no standard charging IC can be used. Because of the fast change between charge and Discharge pulses for the HPPC, a Lab Bench Power Supply is also no solution for the charge cycle. To solve this problem, a electronic load can be used for the charge cycle as well but with the ground reference "shifted" to the positive terminal voltage of the battery. The "upper" load therefore acts as a voltage controlled current source while the "lower" load acts as a voltage controlled current sink. 

With the loads beeing made from non precise components it is necessary to measure the current going in and out of the battery independently. This is done by using a ACS712-05 Current sense Module which uses the ACS712 Hall based current sensor IC configured to a range of +-5A. The uuput of the current sensor, as well as the voltage of the battery is measured by a ADS1115 16-bit ADC sensor. While the voltage of the current sensor is measured single ended, the battery voltage is measured differentially to provide better accuracy. The sample rate of all values is approx 100ms and the delay between current and voltage measurements is approx 20ms. To mitigate the influence of wiring on impedance measurements, the cell holder provides the option to perform 4-wire measurements of the cell under test.

The setup is controlled by an Arduino Nano implementing all necessary controlers. A PC running a python script is used to control the experiment, save log data and communicate with the Arduino. A KiCAD Project containing the schematics for the Hardware can be found in the Hardware folder. The actual Hardware is based on Breakout Boards soldered on Perfboard so the project doesn't contain any Layout data.

## Results

### Inital Cell condition

My four cells arrived with the following voltages:

| Cell | Voltage |
| ---- | ------- |
| Cell 1 | 2.562V |
| Cell 2 | 2.560V |
| Cell 3 | 2.560V |
| Cell 4 | 2.559V |

I measured all cells with a no name, non calibrated 4 1/2 Digit multimeter so the difference might as well come from the measurement equipment

Weight is between 36.53g and 37.00g according to a pocket scale.

### Static capacity tests

The first static capacity test used the following parameters: A CCCV charge to 4.1V with a cut-off current of 0.075mA followed by a CC Discharge with 1C (1500mA) and a CCCV charge with the same parameters as the initial charge. Due to noise issues with the rudamentary cell tester, the charge was terminated a bit earlier near 100mA. Nonetheless the dischargeable capacity is in the range of 1500mAh stated in the datasheet. 

The Coulomb efficency seems to be highly dependent on the charge current during the CC Phase. Using 0.5C as recommended in the datasheet, leads to efficencies in the region of 1 (sometimes slightly larger due to noisy measurements and possible DC offsets in the current sensor). Using charge currents of 1C, which is still allowed in the datasheet, leads to efficencies lower then 0.95 

The following Figure shows the discharge behaviour at 1C

![Sodium Ion discharge curve at 1C](/Measurement_Data/static_capacity_tests/discharge_curve_1c.jpg) 

Sodium Ion discharge curve at 1C

Note that the voltage decreases nearly linear until 1Ah discharged current after which it plateaus at approx. 2.5V before starting to decrease rapidly. In comparison, a Molicel P45B NCA based cell, which was also tested with the same Hardware at a sligthly lower C rate can be seen in the Figure below:

![Molicel P45B discharge curve at 2/3C](/Measurement_Data/static_capacity_tests/discharge_curve_molicel_comparison.jpg)

Molicel P45B discharge curve at 2/3C

The NCA based chemistry shows a significantly smaller voltage decrease over SoC and lacks the voltage plateau at a SoC around 30% as well as a higher voltage in general.
In contrast LFP based chemistrys show a nearly flat discharge voltage over the SoC range between 80% and 20%. This leads to the conclusion that this cells are in fact real Sodium Ion cells.

![](/Measurement_Data/static_capacity_tests/discharge_curves_multiple_c_rates_extended.png)

Constant current discharges at different C-rates show a slight correlation between useable capacity and discharge rate similar to Lithium based chemistries. As expected from a different chemistry, DV/DA analysis, also shows a rather different plot then expected from Lithium chemistrys. 

![](/Measurement_Data/static_capacity_tests/dVdA.png)

### HPPC Test

A HPPC test is performed to get information about the internal resistance as well as dynamic behaviour of the cell. Using the voltage difference between the start of a discharge step and the end of the 10 second discharge pulse and the discharge current, the internal resistance is approximated in the following Figure:

![](/Measurement_Data/HPPC_Test/Rin_SoC.jpg)

This is far off from the <20mOhm stated in the Datasheet. Looking at EIS measurements done at TU Berlin shows the reason for this discrepancy. The Impedance is highly frequency dependent, falling below 20mOhm at frequencys in the kHz range, increasing drasticly at lower frequencys. Because my Hardware only samples in 10Hz intervals, we see a large internal resistance. While the AC resistance might be interesting for EIS diagnostic techniques, the much higher DC impedance is way more relevant in practice.


### OCV Test

To measure the OCV, an incremental OCV measurement method was used. After charging to a cut-off current of approx. 75mA and 4.1V and a 1h rest periode, the battery was considered fully charged. The Cell was then discharged with 0.5 Ampere (1/3C) for 540 seconds, which is equivalent to 75mAh or 1/20th of the cells nominal capacity. Each discharge was followed by a 20 minute rest time, after which the OCV was measured. The discharge steps continoued until the cell voltage falls below 1.5V. The charge steps follow the same process, except that the charge current is reduced to 200mA with the charge step duration increased accordingly. This was done to prevent early abortion of the experiment due to overvoltage. The following figure shows the results of the second test performed with cell 2 (Due to Software issues with the first test, the SoC of these is inprecise and the curves therefore don't align based on coulomb counting so it was not used for this figure).

![](/Measurement_Data/OCV_Test/OCV_Approximation.png)

The OCV-SoC relationship shows a large hysteresis in the "flat" ocv-region around 0-35% SoC of up to around 80mV and a much lower hysteresis of around 20mV in the linear section from 35-100% SoC

### CSV Format descripion

If you want to use the raw csv data, here is a small description of the format:

| field | description |
| --- | --- |
| step | Current Instruction Pointer |
| mode | Operating Mode |
| time | Time since the start of the cell tester in milliseconds |
| voltage | Cell Voltage in V |
| current | Cell Current in A |

Discharge currents have a negative sign, while charging currents have a positive

| Mode Number | Operating Mode |
| ---- | ---- |
| 0 | IDLE |
| 1 | CCCV |
| 2 | Unregulated current pulse |
| 3 | Regulated current pulse |

Unregulated current pulses are used for fast discharges where a PI controller might take too long to stabilize but with lower accuracy

Regulated current charges/discharges are controlled by an PI controller leading too better accuracy but with a small stabilization time.

## Measurement Data naming convention

To differentiate static capacity, HPPC and OCV tests, each csv includes the name of the test and is found in the respective folder. All tests roughly follow the naming convention testname-cellnumber-testnumber-comment(optional).csv The Cellnumber is unique to each cell and the testnumber is used to differentiate tests on the same cell with the same conditions. 

## License

All Measurement Data is Licensed under CC0 1.0 Universal. All Python and C Software falls under the MIT License. If you include this data in your own research, a mention/link to this repo would be appriciated