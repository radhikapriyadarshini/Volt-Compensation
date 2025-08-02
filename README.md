# Enhanced Voltage Compensation System

A comprehensive Python tool for voltage stability analysis and reactive power compensation in IEEE power system test cases.

## 🔌 Features

### Core Capabilities
- **Multiple Network Support**: IEEE 14, 30, 57, and 118 bus systems
- **Interactive Weak Bus Creation**: Multiple scenarios to create voltage violations
- **Advanced Compensation Strategies**: Targeted, global, and optimal compensation approaches
- **Robust Convergence Handling**: Automatic recovery from power flow failures
- **Comprehensive Reporting**: Detailed analysis and system health assessment

### Analysis Modes
1. **Initial Condition Analysis**: System health check and weakest bus identification
2. **Weak Bus Scenario Creation**: Five different methods to create voltage violations
3. **Voltage Compensation**: Three intelligent compensation strategies
4. **Performance Reporting**: Before/after comparison with detailed metrics

## 📋 Requirements

```bash
pip install pandapower pandas numpy
```

### Dependencies
- `pandapower`: Power system analysis library
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computing

## 🚀 Quick Start

### Basic Usage
```python
from voltage_compensation_system import VoltageCompensationSystem

# Initialize with IEEE 14-bus system
system = VoltageCompensationSystem("case14")

# Analyze initial conditions
initial_analysis = system.analyze_initial_conditions()

# Create weak bus scenario (auto mode)
scenario = system.create_weak_bus_scenario("auto_weakest")

# Apply global compensation
results = system.apply_voltage_compensation("global")

# Generate comprehensive report
system.generate_report(results)
```

### Interactive Mode
```python
# Run full interactive interface
if __name__ == "__main__":
    main()
```

## 📊 Usage Guide

### 1. Network Selection
Choose from available IEEE test cases:
- `case14`: 14-bus system (default)
- `case30`: 30-bus system
- `case57`: 57-bus system  
- `case118`: 118-bus system

### 2. Weak Bus Scenario Options

| Mode | Description | Use Case |
|------|-------------|----------|
| `interactive` | User selects bus and parameters | Custom testing scenarios |
| `auto_weakest` | Targets weakest bus automatically | Quick vulnerability assessment |
| `auto_random` | Random bus selection | Monte Carlo analysis |
| `global_increase` | Proportional load increase | System-wide stress testing |
| `skip` | Use current conditions | Analysis of existing violations |

### 3. Compensation Strategies

#### Targeted Strategy
- Focuses on single weakest bus
- Minimal reactive power injection
- Fast convergence

```python
results = system.apply_voltage_compensation("targeted")
```

#### Global Strategy
- Compensates all voltage violations
- Comprehensive system improvement
- Higher reactive power requirements

```python
results = system.apply_voltage_compensation("global")
```

#### Optimal Strategy
- Prioritized compensation approach
- Considers system efficiency
- Balanced performance/cost trade-off

```python
results = system.apply_voltage_compensation("optimal")
```

## 🔧 Advanced Configuration

### Custom Load Modification
```python
# Manual load adjustment
system._modify_bus_load(
    bus_id=14,           # Target bus
    multiplier=2.5,      # Load multiplier
    add_p=30.0,         # Additional P load (MW)
    add_q=15.0          # Additional Q load (MVar)
)
```

### Compensation Parameters
```python
# Custom compensation settings
result = system._compensate_single_bus(
    bus_id=14,          # Target bus
    max_q=150,          # Maximum reactive power (MVar)
    step_q=5            # Step size (MVar)
)
```

## 📈 Output Interpretation

### Initial Analysis Output
```
🔍 Initial Network Analysis:
   • Total buses: 14
   • Buses with loads: 11
   • Weakest bus: 14 (V = 1.0355 p.u.)
   • Voltage violations (V < 0.95): 0
```

### Scenario Creation Output
```
🔧 Modified load at bus 14:
   P: 11.20 → 37.40 MW
   Q: 7.50 → 22.50 MVar

✅ Scenario created: 2 voltage violations
```

### Compensation Results
```
📋 VOLTAGE COMPENSATION REPORT
======================================================================
Strategy: GLOBAL
Total Q Injected: 25.0 MVar
Buses Compensated: 2

Detailed Results:
----------------------------------------------------------------------
Bus  14: 0.9234 → 0.9567 p.u. (+0.0333) Q= 15.0 MVar [Success]
Bus   9: 0.9456 → 0.9523 p.u. (+0.0067) Q= 10.0 MVar [Limited improvement]

Final System Status:
• Minimum voltage: 0.9523 p.u.
• Voltage violations: 0
• System status: ✅ HEALTHY
```

## 🛠️ Error Handling

The system includes robust error handling for common issues:

### Convergence Failures
- Automatic load reduction and retry
- Multiple convergence attempts
- Fallback to stable configurations

### Invalid Inputs
- Input validation and default values
- Graceful handling of out-of-range parameters
- Clear error messages and suggestions

### Network Instability
- Progressive load adjustment
- System recovery mechanisms
- Safe operation boundaries

## 📖 Example Workflows

### Voltage Stability Assessment
```python
# Load network and analyze
system = VoltageCompensationSystem("case30")
analysis = system.analyze_initial_conditions()

# Create stress scenario
if analysis['voltage_violations'] == 0:
    scenario = system.create_weak_bus_scenario("global_increase")
    
# Apply compensation
results = system.apply_voltage_compensation("optimal")
system.generate_report(results)
```

### Batch Analysis
```python
networks = ["case14", "case30", "case57"]
strategies = ["targeted", "global", "optimal"]

for network in networks:
    system = VoltageCompensationSystem(network)
    system.create_weak_bus_scenario("auto_weakest")
    
    for strategy in strategies:
        results = system.apply_voltage_compensation(strategy)
        print(f"{network} - {strategy}: {results['total_q_injected']} MVar")
```

### Custom Scenario Testing
```python
# Interactive mode for specific testing
system = VoltageCompensationSystem("case14")
system.display_bus_options()

# Test specific bus with custom parameters
result = system._modify_bus_load(
    bus_id=int(input("Enter bus ID: ")),
    multiplier=float(input("Load multiplier: ")),
    add_p=float(input("Additional P (MW): ")),
    add_q=float(input("Additional Q (MVar): "))
)
```

## 🔍 Troubleshooting

### Common Issues

**Power Flow Convergence Errors**
- Reduce load multipliers (< 3.0)
- Lower additional loads (< 50 MW)
- Use smaller compensation steps (< 5 MVar)

**No Voltage Violations Created**
- Increase load multipliers
- Try different target buses
- Use global load increase mode

**Compensation Not Effective**
- Check bus connectivity
- Verify generator reactive limits
- Try multiple compensation points

### Performance Tips

- Start with smaller test cases (case14) for development
- Use targeted strategy for quick results
- Apply global strategy for comprehensive analysis
- Monitor system convergence during testing

## 📚 References

- IEEE Test Cases: [University of Washington Power Systems Test Case Archive](https://labs.ece.uw.edu/pstca/)
- PandaPower Documentation: [pandapower.org](https://www.pandapower.org/)
- Power System Analysis: Hadi Saadat, "Power System Analysis"

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/enhancement`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/enhancement`)
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.



**Version**: 1.0.0  
**Author**: Enhanced Voltage Compensation System  
**Last Updated**: August 2025
