#!/usr/bin/env python3
"""
IoT Device Test Automation Script
Automated testing framework for Smart Glucose Monitoring Patch

This script implements automated test cases for:
- Bluetooth communication testing
- Data validation and integrity
- Power consumption monitoring
- Security verification
- Environmental stress simulation

Compliance: IEC 62304, ISO 14971, FDA 21 CFR 820
"""

import pytest
import asyncio
import time
import struct
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Test infrastructure imports
from bluetooth_test_harness import BluetoothTestHarness
from glucose_simulator import GlucoseSimulator
from power_analyzer import PowerAnalyzer
from environmental_chamber import EnvironmentalChamber


@dataclass
class GlucoseMeasurement:
    """Data structure matching firmware glucose_measurement_t"""
    timestamp: int
    glucose_mg_dl: int
    sensor_temp: int
    battery_level: int
    checksum: int


@dataclass
class TestResult:
    """Standard test result structure"""
    test_case: str
    passed: bool
    measured_value: float
    expected_value: float
    tolerance: float
    timestamp: datetime
    notes: str = ""


class IoTDeviceTestSuite:
    """Main test suite for IoT glucose monitoring device"""
    
    def __init__(self):
        self.bluetooth_harness = BluetoothTestHarness()
        self.glucose_simulator = GlucoseSimulator()
        self.power_analyzer = PowerAnalyzer()
        self.env_chamber = EnvironmentalChamber()
        self.test_results: List[TestResult] = []
        
    def setup_test_environment(self):
        """Initialize all test equipment and connections"""
        print("Setting up test environment...")
        
        # Initialize Bluetooth test harness
        self.bluetooth_harness.connect()
        
        # Connect glucose simulator
        self.glucose_simulator.connect()
        
        # Initialize power analyzer
        self.power_analyzer.connect()
        
        # Set environmental chamber to nominal conditions
        self.env_chamber.set_temperature(25.0)  # 25°C
        self.env_chamber.set_humidity(50.0)     # 50% RH
        
        print("Test environment ready.")

    async def test_glucose_accuracy(self) -> List[TestResult]:
        """TC-001: Test glucose measurement accuracy"""
        print("Running TC-001: Glucose Measurement Accuracy Test")
        
        results = []
        reference_levels = [50, 70, 100, 150, 200, 250, 300]  # mg/dL
        
        for ref_level in reference_levels:
            print(f"Testing glucose level: {ref_level} mg/dL")
            
            # Set glucose simulator to reference level
            self.glucose_simulator.set_glucose_level(ref_level)
            await asyncio.sleep(2)  # Allow stabilization
            
            # Take 100 measurements for statistical analysis
            measurements = []
            for i in range(100):
                # Trigger measurement on device
                measured_value = await self.bluetooth_harness.request_glucose_reading()
                measurements.append(measured_value)
                await asyncio.sleep(0.1)
            
            # Calculate accuracy statistics
            avg_measured = sum(measurements) / len(measurements)
            percent_error = abs(avg_measured - ref_level) / ref_level * 100
            within_spec = percent_error <= 15.0
            
            result = TestResult(
                test_case=f"TC-001-{ref_level}mg/dL",
                passed=within_spec,
                measured_value=avg_measured,
                expected_value=ref_level,
                tolerance=15.0,
                timestamp=datetime.now(),
                notes=f"n=100, error={percent_error:.2f}%"
            )
            results.append(result)
            
            print(f"  Measured: {avg_measured:.1f} mg/dL, Error: {percent_error:.2f}%")
        
        return results

    async def test_bluetooth_reliability(self) -> TestResult:
        """TC-002: Test Bluetooth communication reliability"""
        print("Running TC-002: Bluetooth Communication Reliability Test")
        
        total_transmissions = 1000
        successful_transmissions = 0
        
        for i in range(total_transmissions):
            # Generate test data
            test_measurement = GlucoseMeasurement(
                timestamp=int(time.time()),
                glucose_mg_dl=100 + (i % 200),  # Vary glucose readings
                sensor_temp=36,
                battery_level=100 - (i // 20),  # Simulate battery drain
                checksum=0
            )
            
            # Calculate checksum
            test_measurement.checksum = self._calculate_checksum(test_measurement)
            
            # Attempt transmission
            try:
                success = await self.bluetooth_harness.transmit_data(test_measurement)
                if success:
                    successful_transmissions += 1
            except Exception as e:
                print(f"Transmission {i} failed: {e}")
            
            if i % 100 == 0:
                print(f"Progress: {i}/{total_transmissions} transmissions")
        
        success_rate = (successful_transmissions / total_transmissions) * 100
        
        return TestResult(
            test_case="TC-002",
            passed=success_rate >= 99.5,
            measured_value=success_rate,
            expected_value=99.5,
            tolerance=0.0,
            timestamp=datetime.now(),
            notes=f"{successful_transmissions}/{total_transmissions} successful"
        )

    async def test_power_consumption(self) -> TestResult:
        """TC-003: Test power consumption and battery life"""
        print("Running TC-003: Power Consumption Test")
        
        # Monitor power consumption for 1 hour (scaled test)
        test_duration_hours = 1.0
        measurements_per_hour = 60  # 1 per minute
        
        current_readings = []
        
        print(f"Monitoring power consumption for {test_duration_hours} hour(s)...")
        
        for i in range(int(test_duration_hours * measurements_per_hour)):
            # Trigger device activity (measurement + transmission)
            await self.bluetooth_harness.request_glucose_reading()
            
            # Measure current consumption
            current_ma = self.power_analyzer.measure_current()
            current_readings.append(current_ma)
            
            await asyncio.sleep(60)  # Wait 1 minute
            
            if i % 10 == 0:
                print(f"  {i}/{int(test_duration_hours * measurements_per_hour)} measurements, "
                      f"current: {current_ma:.2f} mA")
        
        # Calculate average current consumption
        avg_current_ma = sum(current_readings) / len(current_readings)
        
        # Project battery life (230 mAh coin cell)
        battery_capacity_mah = 230.0
        projected_life_hours = battery_capacity_mah / avg_current_ma
        projected_life_days = projected_life_hours / 24.0
        
        print(f"Average current: {avg_current_ma:.3f} mA")
        print(f"Projected battery life: {projected_life_days:.1f} days")
        
        return TestResult(
            test_case="TC-003",
            passed=projected_life_days >= 14.0,
            measured_value=projected_life_days,
            expected_value=14.0,
            tolerance=0.0,
            timestamp=datetime.now(),
            notes=f"Avg current: {avg_current_ma:.3f} mA"
        )

    async def test_data_security(self) -> List[TestResult]:
        """TC-004: Test data encryption and security"""
        print("Running TC-004: Data Security Test")
        
        results = []
        
        # Test 1: Verify encryption is active
        plaintext_data = GlucoseMeasurement(
            timestamp=1642636800,  # Known timestamp
            glucose_mg_dl=150,     # Known glucose level
            sensor_temp=36,
            battery_level=85,
            checksum=0xABCD
        )
        
        # Capture encrypted transmission
        encrypted_data = await self.bluetooth_harness.capture_encrypted_transmission(plaintext_data)
        
        # Check for plaintext leakage
        plaintext_detected = self._check_plaintext_leakage(encrypted_data, plaintext_data)
        
        encryption_result = TestResult(
            test_case="TC-004-Encryption",
            passed=not plaintext_detected,
            measured_value=0 if not plaintext_detected else 1,
            expected_value=0,
            tolerance=0,
            timestamp=datetime.now(),
            notes="No plaintext glucose data should be visible"
        )
        results.append(encryption_result)
        
        # Test 2: Verify key exchange security
        pairing_secure = await self.bluetooth_harness.test_pairing_security()
        
        pairing_result = TestResult(
            test_case="TC-004-Pairing",
            passed=pairing_secure,
            measured_value=1 if pairing_secure else 0,
            expected_value=1,
            tolerance=0,
            timestamp=datetime.now(),
            notes="Secure key exchange during pairing"
        )
        results.append(pairing_result)
        
        return results

    async def test_environmental_conditions(self) -> List[TestResult]:
        """TC-005: Test device under environmental stress"""
        print("Running TC-005: Environmental Stress Test")
        
        results = []
        test_conditions = [
            (-10, 50, "Cold temperature"),
            (50, 50, "Hot temperature"),
            (25, 95, "High humidity")
        ]
        
        for temp_c, humidity_pct, condition_name in test_conditions:
            print(f"Testing condition: {condition_name} ({temp_c}°C, {humidity_pct}% RH)")
            
            # Set environmental conditions
            self.env_chamber.set_temperature(temp_c)
            self.env_chamber.set_humidity(humidity_pct)
            await asyncio.sleep(300)  # 5 minutes stabilization
            
            # Test glucose accuracy under stress
            self.glucose_simulator.set_glucose_level(150)  # Reference level
            await asyncio.sleep(60)
            
            # Take measurements
            measurements = []
            for _ in range(20):
                reading = await self.bluetooth_harness.request_glucose_reading()
                if reading is not None:
                    measurements.append(reading)
                await asyncio.sleep(30)
            
            if measurements:
                avg_reading = sum(measurements) / len(measurements)
                error_pct = abs(avg_reading - 150) / 150 * 100
                passed = error_pct <= 15.0
            else:
                avg_reading = 0
                error_pct = 100
                passed = False
            
            result = TestResult(
                test_case=f"TC-005-{condition_name.replace(' ', '_')}",
                passed=passed,
                measured_value=avg_reading,
                expected_value=150.0,
                tolerance=15.0,
                timestamp=datetime.now(),
                notes=f"{temp_c}°C, {humidity_pct}% RH, error={error_pct:.1f}%"
            )
            results.append(result)
        
        # Return to nominal conditions
        self.env_chamber.set_temperature(25.0)
        self.env_chamber.set_humidity(50.0)
        
        return results

    def _calculate_checksum(self, measurement: GlucoseMeasurement) -> int:
        """Calculate checksum for measurement data"""
        data = struct.pack('<IHBB', 
                          measurement.timestamp,
                          measurement.glucose_mg_dl,
                          measurement.sensor_temp,
                          measurement.battery_level)
        return sum(data) & 0xFFFF

    def _check_plaintext_leakage(self, encrypted_data: bytes, original_data: GlucoseMeasurement) -> bool:
        """Check if plaintext glucose data is visible in encrypted transmission"""
        # Convert glucose value to bytes and check if present in encrypted data
        glucose_bytes = struct.pack('<H', original_data.glucose_mg_dl)
        return glucose_bytes in encrypted_data

    def generate_test_report(self, output_file: str = "iot_test_report.md"):
        """Generate comprehensive test report"""
        print(f"Generating test report: {output_file}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        
        with open(output_file, 'w') as f:
            f.write("# IoT Device Test Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Device**: Smart Glucose Monitoring Patch\n")
            f.write(f"**Test Protocol**: TP-001\n\n")
            
            f.write("## Test Summary\n")
            f.write(f"- **Total Tests**: {total_tests}\n")
            f.write(f"- **Passed**: {passed_tests}\n")
            f.write(f"- **Failed**: {total_tests - passed_tests}\n")
            f.write(f"- **Pass Rate**: {(passed_tests/total_tests)*100:.1f}%\n\n")
            
            f.write("## Detailed Results\n\n")
            f.write("| Test Case | Result | Measured | Expected | Tolerance | Notes |\n")
            f.write("|-----------|--------|----------|----------|-----------|-------|\n")
            
            for result in self.test_results:
                status = "✅ PASS" if result.passed else "❌ FAIL"
                f.write(f"| {result.test_case} | {status} | "
                       f"{result.measured_value:.2f} | {result.expected_value:.2f} | "
                       f"±{result.tolerance:.2f} | {result.notes} |\n")
            
            f.write("\n## Compliance Statement\n")
            f.write("This testing was conducted in accordance with:\n")
            f.write("- IEC 62304: Medical device software lifecycle processes\n")
            f.write("- ISO 14971: Risk management for medical devices\n")
            f.write("- FDA 21 CFR 820: Quality system regulation\n")
            f.write("- ISO 15197: In vitro diagnostic test systems\n")


async def main():
    """Main test execution function"""
    test_suite = IoTDeviceTestSuite()
    
    try:
        # Setup test environment
        test_suite.setup_test_environment()
        
        # Run all test cases
        print("Starting IoT Device Test Suite...\n")
        
        # TC-001: Glucose accuracy
        accuracy_results = await test_suite.test_glucose_accuracy()
        test_suite.test_results.extend(accuracy_results)
        
        # TC-002: Bluetooth reliability
        bluetooth_result = await test_suite.test_bluetooth_reliability()
        test_suite.test_results.append(bluetooth_result)
        
        # TC-003: Power consumption
        power_result = await test_suite.test_power_consumption()
        test_suite.test_results.append(power_result)
        
        # TC-004: Data security
        security_results = await test_suite.test_data_security()
        test_suite.test_results.extend(security_results)
        
        # TC-005: Environmental stress
        env_results = await test_suite.test_environmental_conditions()
        test_suite.test_results.extend(env_results)
        
        # Generate test report
        test_suite.generate_test_report()
        
        print("\nTest suite completed successfully!")
        
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())