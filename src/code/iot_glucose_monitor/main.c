/**
 * @file main.c
 * @brief IoT Glucose Monitor - Main Application
 * @version 0.1.0-alpha
 * @date 2025-08-19
 * 
 * @copyright Copyright (c) 2025 MedTech Startup Inc.
 * @license MIT License
 * 
 * Main application for continuous glucose monitoring IoT device.
 * Implements glucose sensing, data processing, wireless transmission,
 * and alarm management for diabetic patients.
 */

#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>

#include "stm32l4xx_hal.h"
#include "glucose_sensor.h"
#include "ble_glucose_service.h"
#include "power_manager.h"
#include "security.h"
#include "alarm_manager.h"
#include "data_logger.h"

// Application constants
#define MEASUREMENT_INTERVAL_MS     300000  // 5 minutes
#define SENSOR_WARMUP_TIME_MS       60000   // 1 minute
#define LOW_BATTERY_THRESHOLD_MV    3200    // 3.2V
#define GLUCOSE_SMOOTHING_WINDOW    3       // Rolling average samples

// Application state
typedef struct {
    bool sensor_calibrated;
    bool ble_connected;
    bool wifi_connected;
    uint16_t battery_voltage_mv;
    float last_glucose_values[GLUCOSE_SMOOTHING_WINDOW];
    uint8_t glucose_index;
    uint32_t last_measurement_time;
    uint32_t next_measurement_time;
} app_state_t;

static app_state_t app_state = {0};

// Function prototypes
static void system_init(void);
static void glucose_measurement_task(void);
static void connectivity_task(void);
static void power_management_task(void);
static void alarm_check_task(void);
static float calculate_smoothed_glucose(float new_value);
static void handle_glucose_reading(float glucose_mg_dl);
static void enter_low_power_mode(void);

/**
 * @brief Main application entry point
 */
int main(void)
{
    // Initialize system hardware and peripherals
    system_init();
    
    printf("IoT Glucose Monitor v0.1.0-alpha starting...\n");
    
    // Start sensor warm-up period
    glucose_sensor_start_warmup();
    HAL_Delay(SENSOR_WARMUP_TIME_MS);
    
    // Main application loop
    while (1) {
        uint32_t current_time = HAL_GetTick();
        
        // Glucose measurement every 5 minutes
        if (current_time >= app_state.next_measurement_time) {
            glucose_measurement_task();
            app_state.next_measurement_time = current_time + MEASUREMENT_INTERVAL_MS;
        }
        
        // Connectivity management
        connectivity_task();
        
        // Power management
        power_management_task();
        
        // Alarm checking
        alarm_check_task();
        
        // Enter low power mode until next task
        enter_low_power_mode();
    }
}

/**
 * @brief Initialize system hardware and software components
 */
static void system_init(void)
{
    // HAL initialization
    HAL_Init();
    
    // Configure system clock for low power operation
    SystemClock_Config();
    
    // Initialize security subsystem
    security_init();
    
    // Initialize glucose sensor
    glucose_sensor_init();
    
    // Initialize BLE stack
    ble_glucose_service_init();
    
    // Initialize power management
    power_manager_init();
    
    // Initialize alarm system
    alarm_manager_init();
    
    // Initialize data logger
    data_logger_init();
    
    // Initialize application state
    memset(&app_state, 0, sizeof(app_state_t));
    app_state.next_measurement_time = HAL_GetTick() + SENSOR_WARMUP_TIME_MS;
}

/**
 * @brief Perform glucose measurement and processing
 */
static void glucose_measurement_task(void)
{
    if (!app_state.sensor_calibrated) {
        printf("Warning: Sensor not calibrated\n");
        return;
    }
    
    // Read raw sensor value
    uint16_t raw_sensor_value = glucose_sensor_read_raw();
    
    // Convert to glucose concentration with temperature compensation
    float temperature_c = glucose_sensor_read_temperature();
    float glucose_mg_dl = glucose_sensor_convert_to_glucose(raw_sensor_value, temperature_c);
    
    // Apply smoothing filter
    float smoothed_glucose = calculate_smoothed_glucose(glucose_mg_dl);
    
    // Log measurement
    printf("Glucose: %.1f mg/dL (raw: %d, temp: %.1f°C)\n", 
           smoothed_glucose, raw_sensor_value, temperature_c);
    
    // Process the glucose reading
    handle_glucose_reading(smoothed_glucose);
    
    // Update last measurement time
    app_state.last_measurement_time = HAL_GetTick();
}

/**
 * @brief Handle connectivity management
 */
static void connectivity_task(void)
{
    // Check BLE connection status
    app_state.ble_connected = ble_glucose_service_is_connected();
    
    // Transmit pending data if connected
    if (app_state.ble_connected) {
        glucose_data_t pending_data;
        if (data_logger_get_pending_data(&pending_data)) {
            ble_glucose_service_send_measurement(&pending_data);
        }
    }
    
    // WiFi backup transmission (every 30 minutes)
    static uint32_t last_wifi_sync = 0;
    if (HAL_GetTick() - last_wifi_sync > 1800000) { // 30 minutes
        wifi_sync_data();
        last_wifi_sync = HAL_GetTick();
    }
}

/**
 * @brief Manage power consumption and battery monitoring
 */
static void power_management_task(void)
{
    // Read battery voltage
    app_state.battery_voltage_mv = power_manager_get_battery_voltage();
    
    // Check for low battery condition
    if (app_state.battery_voltage_mv < LOW_BATTERY_THRESHOLD_MV) {
        alarm_manager_trigger_low_battery();
        
        // Enter ultra-low power mode
        power_manager_enter_emergency_mode();
    }
    
    // Log battery status periodically
    static uint32_t last_battery_log = 0;
    if (HAL_GetTick() - last_battery_log > 3600000) { // 1 hour
        printf("Battery: %d mV\n", app_state.battery_voltage_mv);
        last_battery_log = HAL_GetTick();
    }
}

/**
 * @brief Check for alarm conditions
 */
static void alarm_check_task(void)
{
    if (app_state.glucose_index == 0) return; // No readings yet
    
    float current_glucose = app_state.last_glucose_values[
        (app_state.glucose_index - 1) % GLUCOSE_SMOOTHING_WINDOW];
    
    // Check for hypoglycemia (<70 mg/dL)
    if (current_glucose < 70.0f) {
        alarm_manager_trigger_hypoglycemia(current_glucose);
    }
    
    // Check for hyperglycemia (>250 mg/dL)
    if (current_glucose > 250.0f) {
        alarm_manager_trigger_hyperglycemia(current_glucose);
    }
    
    // Check for rapid glucose changes (>3 mg/dL/min)
    if (app_state.glucose_index >= 2) {
        float prev_glucose = app_state.last_glucose_values[
            (app_state.glucose_index - 2) % GLUCOSE_SMOOTHING_WINDOW];
        float rate_mg_dl_per_min = (current_glucose - prev_glucose) / 5.0f; // 5-minute intervals
        
        if (fabs(rate_mg_dl_per_min) > 3.0f) {
            alarm_manager_trigger_rapid_change(rate_mg_dl_per_min);
        }
    }
}

/**
 * @brief Calculate smoothed glucose value using rolling average
 */
static float calculate_smoothed_glucose(float new_value)
{
    // Store new value
    app_state.last_glucose_values[app_state.glucose_index % GLUCOSE_SMOOTHING_WINDOW] = new_value;
    app_state.glucose_index++;
    
    // Calculate average of available samples
    float sum = 0.0f;
    int count = (app_state.glucose_index < GLUCOSE_SMOOTHING_WINDOW) ? 
                app_state.glucose_index : GLUCOSE_SMOOTHING_WINDOW;
    
    for (int i = 0; i < count; i++) {
        sum += app_state.last_glucose_values[i];
    }
    
    return sum / count;
}

/**
 * @brief Process glucose reading and store data
 */
static void handle_glucose_reading(float glucose_mg_dl)
{
    // Create data record
    glucose_data_t data = {
        .timestamp = HAL_GetTick(),
        .glucose_mg_dl = glucose_mg_dl,
        .battery_voltage_mv = app_state.battery_voltage_mv,
        .temperature_c = glucose_sensor_read_temperature(),
        .sensor_id = glucose_sensor_get_serial_number()
    };
    
    // Store locally
    data_logger_store_measurement(&data);
    
    // Attempt immediate BLE transmission
    if (app_state.ble_connected) {
        ble_glucose_service_send_measurement(&data);
    }
}

/**
 * @brief Enter low power mode until next task
 */
static void enter_low_power_mode(void)
{
    // Calculate time until next measurement
    uint32_t current_time = HAL_GetTick();
    uint32_t sleep_time_ms = 0;
    
    if (app_state.next_measurement_time > current_time) {
        sleep_time_ms = app_state.next_measurement_time - current_time;
    }
    
    // Don't sleep if next measurement is soon
    if (sleep_time_ms < 1000) {
        HAL_Delay(100); // Short delay
        return;
    }
    
    // Enter Stop 2 mode for maximum power savings
    power_manager_enter_stop_mode(sleep_time_ms);
}

/**
 * @brief System Clock Configuration for low power operation
 */
void SystemClock_Config(void)
{
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

    // Configure the main internal regulator output voltage for low power
    HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE2);

    // Initialize the RCC Oscillators
    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI | RCC_OSCILLATORTYPE_LSE;
    RCC_OscInitStruct.HSIState = RCC_HSI_ON;
    RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    RCC_OscInitStruct.LSEState = RCC_LSE_ON;
    RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
    
    if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK) {
        Error_Handler();
    }

    // Initialize the CPU, AHB and APB bus clocks (16 MHz for low power)
    RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                                | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
    RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

    if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK) {
        Error_Handler();
    }
}

/**
 * @brief Error Handler
 */
void Error_Handler(void)
{
    __disable_irq();
    while (1) {
        // Flash LED to indicate error
        HAL_GPIO_TogglePin(GPIOB, GPIO_PIN_3);
        HAL_Delay(100);
    }
}