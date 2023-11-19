close all

testdata = csvread("ocv_test_inc_2-2.csv",2,0);
charge_steps = find(testdata(:,1) > 43);
charge_step = testdata(charge_steps,1);
charge_command = testdata(charge_steps,2);
time = testdata(charge_steps,3)/1000;
charge_time = time - time(1);
%time(find(step > 44)) = time(find(step > 44)) + max(time(find(step == 44))); 
charge_voltage = (testdata(charge_steps,4));
charge_current = (testdata(charge_steps,5));

%testdata = csvread("ocv_test_inc_2-1.csv",2,0);
discharge_steps = find(testdata(:,1) < 43);
discharge_step = testdata(discharge_steps,1);
discharge_command = testdata(discharge_steps,2);
time = testdata(discharge_steps,3)/1000;
time = time(find(discharge_step > 2));
discharge_time = time - time(1);
%time(find(step > 44)) = time(find(step > 44)) + max(time(find(step == 44))); 
discharge_voltage = (testdata(discharge_steps,4));
discharge_voltage = discharge_voltage(find(discharge_step > 2));
discharge_current = (testdata(discharge_steps,5));
discharge_current = discharge_current(find(discharge_step > 2));

discharged_current_sum = cumsum(discharge_current(2:end).*diff(discharge_time)/3600);
charged_current_sum = cumsum(charge_current(2:end).*diff(charge_time)/3600);

cell_capacity = max(charged_current_sum);
%cell_capacity = 1.5346;
soc_vect_discharge = (discharged_current_sum+cell_capacity)./cell_capacity;
%cell_capacity = 1.5346;
soc_vect_charge = (charged_current_sum)./cell_capacity;

discharge_step_start = find(diff(discharge_current) < -0.1);
ocv_voltage_discharge = discharge_voltage(discharge_step_start);
ocv_soc_discharge = soc_vect_discharge(discharge_step_start);

charge_step_start = find(diff(charge_current) > 0.15);
ocv_voltage_charge = charge_voltage(charge_step_start);
ocv_soc_charge = soc_vect_charge(charge_step_start);

figure()
hold on
plot(charge_voltage);
plot(charge_step_start, ocv_voltage_charge, "-x");
hold off

figure()
hold on
plot(discharge_voltage);
plot(discharge_step_start, ocv_voltage_discharge, "-x");
hold off

figure()
hold on
plot(linspace(0,1,100),interp1(ocv_soc_discharge, ocv_voltage_discharge,linspace(0,1,100)));
plot(linspace(0,1,100),interp1(ocv_soc_charge, ocv_voltage_charge,linspace(0,1,100)));
plot(ocv_soc_discharge, ocv_voltage_discharge,"x");
plot(ocv_soc_charge,ocv_voltage_charge,"x");

legend({"Discharge OCV interpolated","Charge OCV interpolated","Discharge Measurement Points", "Charge Measurement Points"},'location','southeast');
ylabel("Cell Voltage in [V]")
xlabel("SoC")
hold off
