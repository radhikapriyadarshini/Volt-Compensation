import pandapower as pp
import pandapower.networks as pn
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class VoltageCompensationSystem:
    def __init__(self, network_case: str = "case14"):
        """Initialize the voltage compensation system with specified network."""
        self.net = self._load_network(network_case)
        self.original_loads = self.net.load.copy()
        self.compensation_history = []
        
    def _load_network(self, case: str):
        """Load the specified IEEE test case network."""
        networks = {
            "case14": pn.case14,
            "case30": pn.case30,
            "case57": pn.case57,
            "case118": pn.case118
        }
        
        if case not in networks:
            print(f"⚠️  Unknown case '{case}'. Using case14 as default.")
            case = "case14"
            
        net = networks[case]()
        
        # Fix for missing shunt_characteristic_table
        if not hasattr(net, "shunt_characteristic_table"):
            net.shunt_characteristic_table = pd.DataFrame(columns=[
                "id_characteristic", "step", "p_mw_char", "q_mvar_char", "vm_pu"
            ])
        
        print(f"✅ Loaded {case} network with {len(net.bus)} buses")
        return net
    
    def analyze_initial_conditions(self) -> Dict:
        """Analyze initial network conditions."""
        pp.runpp(self.net)
        
        analysis = {
            'bus_voltages': self.net.res_bus.vm_pu.copy(),
            'weakest_bus': self.net.res_bus.vm_pu.idxmin(),
            'weakest_voltage': self.net.res_bus.vm_pu.min(),
            'voltage_violations': (self.net.res_bus.vm_pu < 0.95).sum(),
            'load_buses': self.net.load.bus.unique().tolist()
        }
        
        print("🔍 Initial Network Analysis:")
        print(f"   • Total buses: {len(self.net.bus)}")
        print(f"   • Buses with loads: {len(analysis['load_buses'])}")
        print(f"   • Weakest bus: {analysis['weakest_bus']} (V = {analysis['weakest_voltage']:.4f} p.u.)")
        print(f"   • Voltage violations (V < 0.95): {analysis['voltage_violations']}")
        
        return analysis
    
    def display_bus_options(self) -> None:
        """Display available buses for load modification."""
        print("\n📊 Available buses for load modification:")
        print("Bus ID | Current Load (MW) | Current Load (MVar) | Voltage (p.u.)")
        print("-" * 65)
        
        for bus_id in sorted(self.net.bus.index):
            loads_at_bus = self.net.load[self.net.load.bus == bus_id]
            if not loads_at_bus.empty:
                total_p = loads_at_bus.p_mw.sum()
                total_q = loads_at_bus.q_mvar.sum()
                voltage = self.net.res_bus.vm_pu.loc[bus_id]
                print(f"{bus_id:6d} | {total_p:13.2f} | {total_q:15.2f} | {voltage:11.4f}")
            else:
                voltage = self.net.res_bus.vm_pu.loc[bus_id]
                print(f"{bus_id:6d} | {'No load':>13} | {'No load':>15} | {voltage:11.4f}")
    
    def create_weak_bus_scenario(self, mode: str = "interactive") -> Dict:
        """Create weak bus scenario based on selected mode."""
        if mode == "interactive":
            return self._interactive_load_modification()
        elif mode == "auto_weakest":
            return self._auto_modify_weakest()
        elif mode == "auto_random":
            return self._auto_modify_random()
        elif mode == "global_increase":
            return self._global_load_increase()
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def _interactive_load_modification(self) -> Dict:
        """Interactive mode for load modification."""
        self.display_bus_options()
        
        try:
            bus_choice = int(input("\n🎯 Enter bus ID for load modification: "))
            if bus_choice not in self.net.bus.index:
                print(f"⚠️  Invalid bus ID. Using weakest bus {self.net.res_bus.vm_pu.idxmin()}")
                bus_choice = self.net.res_bus.vm_pu.idxmin()
            
            load_multiplier = float(input("🔧 Enter load multiplier (e.g., 2.0 for double): "))
            additional_p = float(input("⚡ Additional P load (MW) [0 for none]: ") or "0")
            additional_q = float(input("⚡ Additional Q load (MVar) [0 for none]: ") or "0")
            
        except (ValueError, KeyboardInterrupt):
            print("🔄 Using default values...")
            bus_choice = self.net.res_bus.vm_pu.idxmin()
            load_multiplier = 3.0
            additional_p = 50.0
            additional_q = 25.0
        
        return self._modify_bus_load(bus_choice, load_multiplier, additional_p, additional_q)
    
    def _auto_modify_weakest(self) -> Dict:
        """Automatically modify the weakest bus."""
        weakest_bus = self.net.res_bus.vm_pu.idxmin()
        return self._modify_bus_load(weakest_bus, 2.0, 20.0, 10.0)
    
    def _auto_modify_random(self) -> Dict:
        """Randomly select and modify a bus with existing load."""
        load_buses = self.net.load.bus.unique()
        if len(load_buses) == 0:
            # If no load buses, use the weakest bus
            selected_bus = self.net.res_bus.vm_pu.idxmin()
        else:
            selected_bus = np.random.choice(load_buses)
        
        # More conservative random parameters to avoid convergence issues
        multiplier = np.random.uniform(1.5, 2.5)
        add_p = np.random.uniform(10, 30)
        add_q = np.random.uniform(5, 15)
        
        return self._modify_bus_load(selected_bus, multiplier, add_p, add_q)
    
    def _global_load_increase(self) -> Dict:
        """Increase all loads globally."""
        multiplier = 1.5  # 50% increase
        modified_buses = []
        
        for idx in self.net.load.index:
            original_p = self.net.load.at[idx, 'p_mw']
            original_q = self.net.load.at[idx, 'q_mvar']
            
            self.net.load.at[idx, 'p_mw'] *= multiplier
            self.net.load.at[idx, 'q_mvar'] *= multiplier
            
            modified_buses.append({
                'bus': self.net.load.at[idx, 'bus'],
                'original_p': original_p,
                'original_q': original_q,
                'new_p': self.net.load.at[idx, 'p_mw'],
                'new_q': self.net.load.at[idx, 'q_mvar']
            })
        
        pp.runpp(self.net)
        weakest_bus = self.net.res_bus.vm_pu.idxmin()
        
        print(f"\n🌍 Global load increase applied (×{multiplier})")
        print(f"   • Modified {len(modified_buses)} loads")
        print(f"   • New weakest bus: {weakest_bus} (V = {self.net.res_bus.vm_pu.loc[weakest_bus]:.4f} p.u.)")
        
        return {
            'modified_buses': modified_buses,
            'weakest_bus': weakest_bus,
            'weakest_voltage': self.net.res_bus.vm_pu.loc[weakest_bus],
            'voltage_violations': (self.net.res_bus.vm_pu < 0.95).sum()
        }
    
    def _modify_bus_load(self, bus_id: int, multiplier: float, add_p: float, add_q: float) -> Dict:
        """Modify load at specified bus with convergence checking."""
        loads_at_bus = self.net.load[self.net.load.bus == bus_id]
        
        if loads_at_bus.empty:
            # Create new load if none exists - start conservative
            pp.create_load(self.net, bus=bus_id, p_mw=add_p, q_mvar=add_q, 
                          name=f"Created_Load_Bus_{bus_id}")
            print(f"✨ Created new load at bus {bus_id}: {add_p} MW, {add_q} MVar")
        else:
            # Modify existing loads
            for idx in loads_at_bus.index:
                original_p = self.net.load.at[idx, 'p_mw']
                original_q = self.net.load.at[idx, 'q_mvar']
                
                self.net.load.at[idx, 'p_mw'] = original_p * multiplier + add_p
                self.net.load.at[idx, 'q_mvar'] = original_q * multiplier + add_q
                
                print(f"🔧 Modified load at bus {bus_id}:")
                print(f"   P: {original_p:.2f} → {self.net.load.at[idx, 'p_mw']:.2f} MW")
                print(f"   Q: {original_q:.2f} → {self.net.load.at[idx, 'q_mvar']:.2f} MVar")
        
        # Try power flow with enhanced parameters
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                pp.runpp(self.net, max_iteration=50, tolerance_kva=1e-3, 
                        algorithm='nr', init='auto')
                break
            except Exception as e:
                print(f"⚠️  Power flow attempt {attempt + 1} failed: {str(e)[:50]}...")
                
                if attempt < max_attempts - 1:
                    # Reduce load incrementally
                    reduction_factor = 0.7
                    if not loads_at_bus.empty:
                        for idx in loads_at_bus.index:
                            current_p = self.net.load.at[idx, 'p_mw']
                            current_q = self.net.load.at[idx, 'q_mvar']
                            
                            self.net.load.at[idx, 'p_mw'] *= reduction_factor
                            self.net.load.at[idx, 'q_mvar'] *= reduction_factor
                            
                            print(f"   🔧 Reducing load: {current_p:.2f} → {self.net.load.at[idx, 'p_mw']:.2f} MW")
                    else:
                        # Reduce newly created load
                        new_loads = self.net.load[self.net.load.bus == bus_id]
                        for idx in new_loads.index:
                            self.net.load.at[idx, 'p_mw'] *= reduction_factor
                            self.net.load.at[idx, 'q_mvar'] *= reduction_factor
                else:
                    print(f"❌ Unable to achieve convergence at bus {bus_id}. Using last stable state.")
                    # Restore original loads for this bus
                    original_bus_loads = self.original_loads[self.original_loads.bus == bus_id]
                    if not original_bus_loads.empty:
                        # Remove current loads at this bus
                        current_loads = self.net.load[self.net.load.bus == bus_id]
                        if not current_loads.empty:
                            pp.drop_elements(self.net, 'load', current_loads.index.tolist())
                        
                        # Restore original loads
                        for _, row in original_bus_loads.iterrows():
                            pp.create_load(self.net, bus=row.bus, p_mw=row.p_mw, 
                                         q_mvar=row.q_mvar, name=row.get('name', f'Load_Bus_{bus_id}'))
                    
                    # Try final power flow
                    try:
                        pp.runpp(self.net, max_iteration=30, tolerance_kva=1e-3)
                    except:
                        print("❌ Critical: Cannot restore network stability!")
                        return {
                            'modified_bus': bus_id,
                            'weakest_bus': None,
                            'weakest_voltage': 0.0,
                            'voltage_violations': -1,
                            'error': 'Power flow convergence failed'
                        }
        
        weakest_bus = self.net.res_bus.vm_pu.idxmin()
        
        return {
            'modified_bus': bus_id,
            'weakest_bus': weakest_bus,
            'weakest_voltage': self.net.res_bus.vm_pu.loc[weakest_bus],
            'voltage_violations': (self.net.res_bus.vm_pu < 0.95).sum()
        }
    
    def apply_voltage_compensation(self, strategy: str = "targeted") -> Dict:
        """Apply voltage compensation using specified strategy."""
        strategies = {
            "targeted": self._targeted_compensation,
            "global": self._global_compensation,
            "optimal": self._optimal_compensation
        }
        
        if strategy not in strategies:
            print(f"⚠️  Unknown strategy '{strategy}'. Using 'targeted'.")
            strategy = "targeted"
        
        print(f"\n🔧 Applying {strategy} voltage compensation...")
        return strategies[strategy]()
    
    def _targeted_compensation(self) -> Dict:
        """Apply compensation only to the weakest bus."""
        weak_buses = self.net.res_bus[self.net.res_bus.vm_pu < 0.95].index.tolist()
        
        if not weak_buses:
            return {"message": "No buses require compensation", "compensated_buses": []}
        
        # Focus on the weakest bus
        weakest_bus = self.net.res_bus.vm_pu.idxmin()
        compensation_result = self._compensate_single_bus(weakest_bus)
        
        return {
            "strategy": "targeted",
            "compensated_buses": [compensation_result],
            "total_q_injected": compensation_result['q_injected']
        }
    
    def _global_compensation(self) -> Dict:
        """Apply compensation to all buses with voltage violations."""
        weak_buses = self.net.res_bus[self.net.res_bus.vm_pu < 0.95].index.tolist()
        
        if not weak_buses:
            return {"message": "No buses require compensation", "compensated_buses": []}
        
        compensated_buses = []
        total_q_injected = 0
        
        for bus_id in weak_buses:
            result = self._compensate_single_bus(bus_id)
            compensated_buses.append(result)
            total_q_injected += result['q_injected']
        
        return {
            "strategy": "global",
            "compensated_buses": compensated_buses,
            "total_q_injected": total_q_injected
        }
    
    def _optimal_compensation(self) -> Dict:
        """Apply optimal compensation considering system efficiency."""
        weak_buses = self.net.res_bus[self.net.res_bus.vm_pu < 0.95].index.tolist()
        
        if not weak_buses:
            return {"message": "No buses require compensation", "compensated_buses": []}
        
        # Sort buses by voltage level (weakest first) and proximity to generators
        bus_priorities = []
        for bus_id in weak_buses:
            voltage = self.net.res_bus.vm_pu.loc[bus_id]
            # Simple heuristic: prioritize by voltage level
            priority_score = 1 / voltage  # Lower voltage = higher priority
            bus_priorities.append((bus_id, priority_score, voltage))
        
        bus_priorities.sort(key=lambda x: x[1], reverse=True)
        
        compensated_buses = []
        total_q_injected = 0
        
        for bus_id, _, voltage in bus_priorities:
            if voltage < 0.95:  # Re-check after previous compensations
                pp.runpp(self.net)
                current_voltage = self.net.res_bus.vm_pu.loc[bus_id]
                if current_voltage < 0.95:
                    result = self._compensate_single_bus(bus_id, max_q=75)  # Limit per bus
                    compensated_buses.append(result)
                    total_q_injected += result['q_injected']
        
        return {
            "strategy": "optimal",
            "compensated_buses": compensated_buses,
            "total_q_injected": total_q_injected
        }
    
    def _compensate_single_bus(self, bus_id: int, max_q: float = 100, step_q: float = 2) -> Dict:
        """Apply shunt compensation to a single bus with improved convergence."""
        try:
            pp.runpp(self.net, max_iteration=30, tolerance_kva=1e-3)
            initial_voltage = self.net.res_bus.vm_pu.loc[bus_id]
        except Exception as e:
            print(f"❌ Initial power flow failed for bus {bus_id}: {e}")
            return {
                'bus_id': bus_id,
                'initial_voltage': 0.0,
                'final_voltage': 0.0,
                'q_injected': 0,
                'improvement': 0,
                'status': 'Power flow failed'
            }
        
        if initial_voltage >= 0.95:
            return {
                'bus_id': bus_id,
                'initial_voltage': initial_voltage,
                'final_voltage': initial_voltage,
                'q_injected': 0,
                'improvement': 0,
                'status': 'No compensation needed'
            }
        
        # Remove existing shunts at this bus
        existing_shunts = self.net.shunt[self.net.shunt.bus == bus_id]
        if not existing_shunts.empty:
            pp.drop_elements(self.net, 'shunt', existing_shunts.index.tolist())
        
        q_inject = 0
        prev_voltage = initial_voltage
        best_q = 0
        best_voltage = initial_voltage
        
        while q_inject < max_q:
            q_inject += step_q
            
            # Remove old shunt and create new one
            current_shunts = self.net.shunt[self.net.shunt.bus == bus_id]
            if not current_shunts.empty:
                pp.drop_elements(self.net, 'shunt', current_shunts.index.tolist())
            
            pp.create_shunt(self.net, bus=bus_id, p_mw=0, q_mvar=-q_inject, 
                           name=f"Compensation_Bus_{bus_id}")
            
            try:
                pp.runpp(self.net, max_iteration=50, tolerance_kva=1e-3, 
                        algorithm='nr', init='auto')
                current_voltage = self.net.res_bus.vm_pu.loc[bus_id]
                
                print(f"   Bus {bus_id}: Q={q_inject:5.1f} MVar → V={current_voltage:.4f} p.u.")
                
                # Track best result
                if current_voltage > best_voltage:
                    best_voltage = current_voltage
                    best_q = q_inject
                
                # Check if target achieved
                if current_voltage >= 0.95:
                    break
                
                # Check for convergence issues or no improvement
                if current_voltage <= prev_voltage + 1e-6:  # No significant improvement
                    print(f"   ⚠️  Minimal improvement at bus {bus_id}. Stopping.")
                    break
                
                prev_voltage = current_voltage
                
            except Exception as e:
                print(f"   ❌ Power flow failed at bus {bus_id} with Q={q_inject} MVar")
                # Revert to best known configuration
                current_shunts = self.net.shunt[self.net.shunt.bus == bus_id]
                if not current_shunts.empty:
                    pp.drop_elements(self.net, 'shunt', current_shunts.index.tolist())
                
                if best_q > 0:
                    pp.create_shunt(self.net, bus=bus_id, p_mw=0, q_mvar=-best_q, 
                                   name=f"Compensation_Bus_{bus_id}")
                    try:
                        pp.runpp(self.net, max_iteration=30, tolerance_kva=1e-3)
                    except:
                        pass
                break
        
        # Final voltage check
        try:
            pp.runpp(self.net, max_iteration=30, tolerance_kva=1e-3)
            final_voltage = self.net.res_bus.vm_pu.loc[bus_id]
        except:
            final_voltage = best_voltage
        
        improvement = final_voltage - initial_voltage
        status = "Success" if final_voltage >= 0.95 else "Limited improvement"
        
        return {
            'bus_id': bus_id,
            'initial_voltage': initial_voltage,
            'final_voltage': final_voltage,
            'q_injected': best_q if best_q > 0 else q_inject,
            'improvement': improvement,
            'status': status
        }
    
    def generate_report(self, compensation_results: Dict) -> None:
        """Generate comprehensive compensation report."""
        print("\n" + "="*70)
        print("📋 VOLTAGE COMPENSATION REPORT")
        print("="*70)
        
        if "compensated_buses" in compensation_results:
            compensated = compensation_results["compensated_buses"]
            if compensated:
                print(f"Strategy: {compensation_results.get('strategy', 'N/A').upper()}")
                print(f"Total Q Injected: {compensation_results.get('total_q_injected', 0):.1f} MVar")
                print(f"Buses Compensated: {len(compensated)}")
                print("\nDetailed Results:")
                print("-" * 70)
                
                for result in compensated:
                    print(f"Bus {result['bus_id']:3d}: "
                          f"{result['initial_voltage']:.4f} → {result['final_voltage']:.4f} p.u. "
                          f"(+{result['improvement']:.4f}) "
                          f"Q={result['q_injected']:5.1f} MVar "
                          f"[{result['status']}]")
            else:
                print("No compensation was required.")
        
        # Final system status
        pp.runpp(self.net)
        final_violations = (self.net.res_bus.vm_pu < 0.95).sum()
        min_voltage = self.net.res_bus.vm_pu.min()
        
        print(f"\nFinal System Status:")
        print(f"• Minimum voltage: {min_voltage:.4f} p.u.")
        print(f"• Voltage violations: {final_violations}")
        print(f"• System status: {'✅ HEALTHY' if final_violations == 0 else '⚠️  NEEDS ATTENTION'}")
        print("="*70)
    
    def reset_network(self) -> None:
        """Reset network to original state."""
        # Remove all shunts
        if not self.net.shunt.empty:
            pp.drop_elements(self.net, 'shunt', self.net.shunt.index.tolist())
        
        # Reset loads
        self.net.load = self.original_loads.copy()
        
        print("🔄 Network reset to original state")

def main():
    """Main execution function with user interaction."""
    print("🔌 Enhanced Voltage Compensation System")
    print("="*50)
    
    # Initialize system
    try:
        network_choice = input("Enter network case (case14/case30/case57/case118) [case14]: ").strip() or "case14"
        system = VoltageCompensationSystem(network_choice)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return
    
    # Analyze initial conditions
    initial_analysis = system.analyze_initial_conditions()
    
    # Choose scenario creation mode
    print("\n🎯 Weak Bus Scenario Options:")
    print("1. Interactive (choose bus and parameters)")
    print("2. Auto - Weakest bus")
    print("3. Auto - Random bus")
    print("4. Global load increase")
    print("5. Skip (use current conditions)")
    
    try:
        mode_choice = input("Select option [1-5]: ").strip() or "1"
        mode_map = {
            "1": "interactive",
            "2": "auto_weakest", 
            "3": "auto_random",
            "4": "global_increase",
            "5": "skip"
        }
        
        if mode_choice != "5":
            scenario_mode = mode_map.get(mode_choice, "interactive")
            scenario_results = system.create_weak_bus_scenario(scenario_mode)
            print(f"\n✅ Scenario created: {scenario_results.get('voltage_violations', 0)} voltage violations")
    
    except KeyboardInterrupt:
        print("\n🔄 Using current network conditions...")
    
    # Choose compensation strategy
    print("\n🔧 Compensation Strategy Options:")
    print("1. Targeted (weakest bus only)")
    print("2. Global (all violation buses)")
    print("3. Optimal (prioritized approach)")
    
    try:
        strategy_choice = input("Select strategy [1-3]: ").strip() or "1"
        strategy_map = {"1": "targeted", "2": "global", "3": "optimal"}
        strategy = strategy_map.get(strategy_choice, "targeted")
        
        # Apply compensation
        compensation_results = system.apply_voltage_compensation(strategy)
        
        # Generate report
        system.generate_report(compensation_results)
        
    except KeyboardInterrupt:
        print("\n⏹️  Compensation cancelled")
    
    print("\n🎉 Analysis complete!")

if __name__ == "__main__":
    main()