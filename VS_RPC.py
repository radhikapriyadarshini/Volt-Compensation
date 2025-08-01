import pandapower as pp
import pandapower.networks as pn

# Step 1: Load the IEEE 14-bus system
net = pn.case14()

# Fix for missing shunt_characteristic_table
import pandas as pd
if not hasattr(net, "shunt_characteristic_table"):
    net.shunt_characteristic_table = pd.DataFrame(columns=[
        "id_characteristic", "step", "p_mw_char", "q_mvar_char", "vm_pu"
    ])

# Step 2: Run initial power flow
pp.runpp(net)
print("Initial Bus Voltages (p.u.):")
print(net.res_bus.vm_pu)

# Step 3: Identify weakest bus before load increase
weakest_bus = net.res_bus.vm_pu.idxmin()
print(f"\nWeakest bus before load increase: {weakest_bus}, Voltage: {net.res_bus.vm_pu.loc[weakest_bus]:.4f}")


# Step 4: Force load increase at bus 3 to drop voltage < 0.95 p.u.
target_bus = 3  # Force bus 3 as the weak spot

loads_at_bus3 = net.load[net.load.bus == target_bus]

if loads_at_bus3.empty:
    print(f"No load at bus {target_bus}, adding large load: 60 MW, 30 MVar")
    pp.create_load(net, bus=target_bus, p_mw=60, q_mvar=30, name="Forced Load Bus 3")
else:
    for idx, load in loads_at_bus3.iterrows():
        net.load.at[idx, "p_mw"] *= 10.0
        net.load.at[idx, "q_mvar"] *= 10.0
        print(f"Load at bus 3 increased to {net.load.at[idx, 'p_mw']} MW / {net.load.at[idx, 'q_mvar']} MVar")
        
# Step 5: Run power flow after load increase
pp.runpp(net, max_iteration=50, tolerance_kva=1e-4)

print("\nBus Voltages after load increase (p.u.):")
print(net.res_bus.vm_pu)

# Step 6: Find updated weakest bus
weakest_bus = net.res_bus.vm_pu.idxmin()
initial_voltage = net.res_bus.vm_pu.loc[weakest_bus]
print(f"\nWeakest bus after load increase: {weakest_bus}, Voltage: {initial_voltage:.4f}")

# Step 7: Apply shunt compensation only if needed
if initial_voltage < 0.95:
    print("\n🔧 Starting voltage compensation...")

    max_q_mvar = 100
    step_q = 1
    q_inject = 0
    prev_voltage = initial_voltage
    voltage = initial_voltage

    while voltage < 0.95 and q_inject <= max_q_mvar:
        # Remove any old shunts at this bus
        shunts_at_bus = net.shunt[net.shunt.bus == weakest_bus]
        for sh_idx in shunts_at_bus.index:
            pp.drop_elements(net, 'shunt', [sh_idx])
        q_inject += step_q
        pp.create_shunt(net, bus=weakest_bus, p_mw=0, q_mvar=-q_inject, name="VoltageCompensation")

        pp.runpp(net, max_iteration=50, tolerance_kva=1e-4)
        voltage = net.res_bus.vm_pu.loc[weakest_bus]
        print(f"Injected Q={q_inject} MVar at bus {weakest_bus}, Voltage={voltage:.4f}")

        if voltage <= prev_voltage:
            print("⚠️  Voltage did not improve further. Stopping compensation loop.")
            break
        prev_voltage = voltage

    if voltage > initial_voltage:
        print(f"\n✅ Voltage boosted from {initial_voltage:.4f} to {voltage:.4f} p.u. at bus {weakest_bus}")
    else:
        print(f"\n⚠️  Reached Q={q_inject} MVar but voltage stayed at {voltage:.4f} p.u.")
else:
    print(f"\nℹ️  No compensation applied — voltage already within acceptable range: {initial_voltage:.4f} p.u.")

