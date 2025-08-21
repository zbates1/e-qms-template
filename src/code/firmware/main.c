/**
 * @file main.c
 * @brief Main firmware for IoT Glucose Monitoring Patch
 * @version 1.0.0
 * @date 2025-01-19
 * 
 * Device: ARM Cortex-M4 with Bluetooth 5.2 LE
 * Purpose: Continuous glucose monitoring with wireless data transmission
 * Compliance: IEC 62304 Class B medical device software
 */

#include <stdint.h>
#include <stdbool.h>
#include "glucose_sensor.h"
#include "bluetooth_stack.h"
#include "power_management.h"
#include "data_validation.h"
#include "security.h"

#define MEASUREMENT_INTERVAL_MS     60000   // 1 minute
#define GLUCOSE_BUFFER_SIZE         1440    // 24 hours of data
#define LOW_BATTERY_THRESHOLD       15      // 15% battery remaining

typedef struct {
    uint32_t timestamp;
    uint16_t glucose_mg_dl;
    uint8_t  sensor_temp;
    uint8_t  battery_level;
    uint16_t checksum;
} glucose_measurement_t;

static glucose_measurement_t glucose_buffer[GLUCOSE_BUFFER_SIZE];
static uint16_t buffer_head = 0;
static uint32_t measurement_count = 0;
static bool device_paired = false;

/**
 * @brief System initialization
 * @return 0 on success, error code on failure
 */
int system_init(void) {
    // Initialize power management
    if (power_mgmt_init() != 0) return -1;
    
    // Initialize glucose sensor
    if (glucose_sensor_init() != 0) return -2;
    
    // Initialize Bluetooth stack
    if (bluetooth_init() != 0) return -3;
    
    // Initialize security module
    if (security_init() != 0) return -4;
    
    return 0;
}

/**
 * @brief Take glucose measurement and store in buffer
 * @return 0 on success, error code on failure
 */
int take_measurement(void) {
    glucose_measurement_t measurement = {0};
    
    // Get current timestamp
    measurement.timestamp = get_system_time();
    
    // Read glucose sensor
    int sensor_result = glucose_sensor_read(&measurement.glucose_mg_dl, 
                                          &measurement.sensor_temp);
    if (sensor_result != 0) {
        return -1;
    }
    
    // Validate measurement
    if (!validate_glucose_reading(measurement.glucose_mg_dl)) {
        return -2;
    }
    
    // Read battery level
    measurement.battery_level = power_mgmt_get_battery_level();
    
    // Calculate checksum
    measurement.checksum = calculate_checksum(&measurement);
    
    // Store in circular buffer
    glucose_buffer[buffer_head] = measurement;
    buffer_head = (buffer_head + 1) % GLUCOSE_BUFFER_SIZE;
    measurement_count++;
    
    return 0;
}

/**
 * @brief Transmit buffered data via Bluetooth
 * @return Number of measurements transmitted
 */
int transmit_data(void) {
    if (!device_paired || !bluetooth_is_connected()) {
        return 0;
    }
    
    int transmitted = 0;
    uint16_t current_pos = buffer_head;
    
    // Transmit last 10 measurements
    for (int i = 0; i < 10 && i < measurement_count; i++) {
        uint16_t pos = (current_pos - 1 - i + GLUCOSE_BUFFER_SIZE) % GLUCOSE_BUFFER_SIZE;
        
        // Encrypt measurement data
        uint8_t encrypted_data[sizeof(glucose_measurement_t)];
        if (encrypt_measurement(&glucose_buffer[pos], encrypted_data) == 0) {
            if (bluetooth_transmit(encrypted_data, sizeof(encrypted_data)) == 0) {
                transmitted++;
            }
        }
    }
    
    return transmitted;
}

/**
 * @brief Handle low glucose alert
 * @param glucose_level Current glucose level in mg/dL
 */
void handle_glucose_alert(uint16_t glucose_level) {
    if (glucose_level < 70) {  // Hypoglycemia threshold
        bluetooth_send_alert(ALERT_LOW_GLUCOSE, glucose_level);
        // Increase measurement frequency for critical readings
        set_measurement_interval(30000);  // 30 seconds
    } else if (glucose_level > 250) {  // Hyperglycemia threshold
        bluetooth_send_alert(ALERT_HIGH_GLUCOSE, glucose_level);
    } else {
        // Return to normal measurement interval
        set_measurement_interval(MEASUREMENT_INTERVAL_MS);
    }
}

/**
 * @brief Main application loop
 */
int main(void) {
    // System initialization
    if (system_init() != 0) {
        power_mgmt_enter_error_state();
        return -1;
    }
    
    // Main execution loop
    while (1) {
        // Check if it's time for a measurement
        if (is_measurement_time()) {
            int result = take_measurement();
            if (result == 0) {
                uint16_t latest_glucose = glucose_buffer[(buffer_head - 1 + GLUCOSE_BUFFER_SIZE) % GLUCOSE_BUFFER_SIZE].glucose_mg_dl;
                handle_glucose_alert(latest_glucose);
            }
        }
        
        // Attempt data transmission if connected
        if (device_paired && bluetooth_is_connected()) {
            transmit_data();
        }
        
        // Check battery level
        uint8_t battery_level = power_mgmt_get_battery_level();
        if (battery_level <= LOW_BATTERY_THRESHOLD) {
            bluetooth_send_alert(ALERT_LOW_BATTERY, battery_level);
        }
        
        // Handle Bluetooth pairing requests
        if (bluetooth_pairing_requested()) {
            device_paired = bluetooth_complete_pairing();
        }
        
        // Enter low power mode until next event
        power_mgmt_enter_sleep();
    }
    
    return 0;
}