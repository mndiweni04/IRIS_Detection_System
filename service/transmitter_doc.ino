#include <Wire.h>
 
// -------------------- GLOBAL DEFINES & VARIABLES --------------------

#define SDA_PIN 5
#define SCL_PIN 6
#define MPU6050_ADDR 0x68    // Confirmed by I2C scanner!
#define IR_LED 4
// Global state flag for MPU
bool mpu_ok = false; 

// Low-pass filter alpha (0 = no smoothing, 1 = full previous)
#define ALPHA 0.9
 
// Filtered values
float ax_f = 0, ay_f = 0, az_f = 0;
float gx_f = 0, gy_f = 0, gz_f = 0;
 
// -------------------- Photodiode (analog) --------------------
#define PHOTO_PIN 2              // GPIO2 = ADC1_CH2 on ESP32-C3
float ir_f = 0;                  // filtered IR reading
 
// -------------------- BLE (NimBLE) --------------------
#include <NimBLEDevice.h>        // Install "NimBLE-Arduino" library
 
const char* BLE_NAME      = "AntiSleep-Glasses-ESP32";  // ← Adds "ESP32" for clarity
const char* SERVICE_UUID  = "b86f0001-3e1d-4ad6-98ef-6b93f33e5a4a";
const char* CHAR_UUID_DATA = "b86f0002-3e1d-4ad6-98ef-6b93f33e5a4a";

NimBLECharacteristic* gDataChar = nullptr;

// Global pointers for control
NimBLEServer* gServer = nullptr;
NimBLEAdvertising* gAdvertising = nullptr;

/**
 * @brief Custom class to handle BLE server events.
 */
class ServerCallbacks: public NimBLEServerCallbacks {
    void onConnect(NimBLEServer* pServer) {
        Serial.println("CLIENT CONNECTED! Advertising stopped.");
    };

    // --- ORIGINAL, SIMPLE DISCONNECT LOGIC ---
    void onDisconnect(NimBLEServer* pServer) {
        Serial.println("CLIENT DISCONNECTED. Restarting advertising...");
        
        // Simple restart with delay
        delay(500);  // Give time for cleanup
        gAdvertising->start();
        
        Serial.println("✅ Advertising RESTARTED.");
    }
    // ------------------------------------------
};

// ------------------------------------------------------------------
// HELPER FUNCTIONS (MPU READ/WAKE)
// ------------------------------------------------------------------

void wakeMPU() {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B); // Power Management 1 register
  Wire.write(0x00); // Set to 0 to wake up
  Wire.endTransmission(true);
}

bool readMPU(int16_t &AcX, int16_t &AcY, int16_t &AcZ,
             int16_t &GyX, int16_t &GyY, int16_t &GyZ) {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B); // Start register for Accel X High
  if (Wire.endTransmission(false) != 0) return false;

  Wire.requestFrom(MPU6050_ADDR, 14, true);

  if (Wire.available() < 14) return false;
  
  AcX = Wire.read() << 8 | Wire.read();
  AcY = Wire.read() << 8 | Wire.read();
  AcZ = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read(); // temperature
  GyX = Wire.read() << 8 | Wire.read();
  GyY = Wire.read() << 8 | Wire.read();
  GyZ = Wire.read() << 8 | Wire.read();

  return true;
}

// ------------------------------------------------------------------
// SETUP 
// ------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("Starting AntiSleep Glasses Server...");
  pinMode(IR_LED, OUTPUT);
  
  // I2C Init
  Wire.begin(SDA_PIN, SCL_PIN);
  
  // MPU Initialization
  Serial.println("Attempting to wake MPU6050...");
  wakeMPU(); 
  delay(500); 

  // Photodiode Init
  pinMode(PHOTO_PIN, INPUT);
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  // BLE Init
  NimBLEDevice::init(BLE_NAME);
  gServer = NimBLEDevice::createServer();
  
  // Set callbacks
  gServer->setCallbacks(new ServerCallbacks()); 

  // Main service
  NimBLEService* service = gServer->createService(SERVICE_UUID);
  gDataChar = service->createCharacteristic(
      CHAR_UUID_DATA,
      NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY
  );
  service->start();

  // Device Information Service (for proper Windows identification)
  NimBLEService* disService = gServer->createService("180A");
  
  NimBLECharacteristic* manufChar = disService->createCharacteristic(
      "2A29", NIMBLE_PROPERTY::READ
  );
  manufChar->setValue("AntiSleep-Labs");
  
  NimBLECharacteristic* modelChar = disService->createCharacteristic(
      "2A24", NIMBLE_PROPERTY::READ
  );
  modelChar->setValue("ESP32-C3-Glasses-v1");
  
  disService->start();

  // Advertising setup
  gAdvertising = NimBLEDevice::getAdvertising();
  gAdvertising->addServiceUUID(SERVICE_UUID);
  gAdvertising->setMinInterval(0x0040); 
  gAdvertising->setMaxInterval(0x0040); 
  gAdvertising->setName(BLE_NAME); 
  gAdvertising->enableScanResponse(true);
  gAdvertising->addTxPower();  // ← Corrected method
  
  // Start advertising with verification
  gAdvertising->start();
  delay(100);
  Serial.println("✅ BLE Advertising STARTED in setup().");
}

// ------------------------------------------------------------------
// LOOP
// ------------------------------------------------------------------

void loop() {

  int16_t AcX, AcY, AcZ, GyX, GyY, GyZ;
  bool read_success = false;
  digitalWrite(IR_LED, HIGH);
  // 1. Attempt to read MPU data
  if (readMPU(AcX, AcY, AcZ, GyX, GyY, GyZ)) {
    read_success = true;
    
    if (!mpu_ok) {
        mpu_ok = true;
        Serial.println("✅ MPU6050 successfully read! All systems GO.");
    }
  } 
  
  // 3. Handle MPU Read Failure
  if (!read_success) {
    if (!mpu_ok) {
        // Only print error messages occasionally if MPU is not OK
        static unsigned long last_error_time = 0;
        if (millis() - last_error_time > 5000) {
            Serial.println("MPU6050 ERROR: Skipped reading. Attempting re-wake.");
            last_error_time = millis();
        }
    }
    // Try to re-wake the sensor regardless
    wakeMPU();
    
    // Use previous filtered data or zero if we haven't succeeded yet
    AcX = (int16_t)(ax_f * 16384.0);
    AcY = (int16_t)(ay_f * 16384.0);
    AcZ = (int16_t)(az_f * 16384.0);
    GyX = (int16_t)(gx_f * 131.0);
    GyY = (int16_t)(gy_f * 131.0);
    GyZ = (int16_t)(gz_f * 131.0);
    
  } else {
     // Convert and Filter only if read was successful to prevent filter creep
      float ax = AcX / 16384.0;
      float ay = AcY / 16384.0;
      float az = AcZ / 16384.0; 
      float gx = GyX / 131.0;
      float gy = GyY / 131.0;
      float gz = GyZ / 131.0;
    
      ax_f = ALPHA * ax_f + (1 - ALPHA) * ax;
      ay_f = ALPHA * ay_f + (1 - ALPHA) * ay;
      az_f = ALPHA * az_f + (1 - ALPHA) * az;
      gx_f = ALPHA * gx_f + (1 - ALPHA) * gx;
      gy_f = ALPHA * gy_f + (1 - ALPHA) * gy;
      gz_f = ALPHA * gz_f + (1 - ALPHA) * gz;
  }

  // Read & filter photodiode
  int ir_raw = analogRead(PHOTO_PIN);
  ir_f = ALPHA * ir_f + (1 - ALPHA) * ir_raw;
  float ir_mv = (ir_f / 4095.0f) * 3300.0f;

  // Serial output (only print if MPU is OK or we are failing gracefully)
  if (mpu_ok || !read_success) {
    Serial.print("Accel (g): ");
    Serial.print(ax_f, 3); Serial.print(" ");
    Serial.print(ay_f, 3); Serial.print(" ");
    Serial.println(az_f, 3);
    
    Serial.print("Gyro (°/s): ");
    Serial.print(gx_f, 2); Serial.print(" ");
    Serial.print(gy_f, 2); Serial.print(" ");
    Serial.println(gz_f, 2);
    
    Serial.print("IR ADC: raw=");
    Serial.print(ir_raw);
    Serial.print(" filtered=");
    Serial.print((int)ir_f);
    Serial.print(" mV≈");
    Serial.println((int)ir_mv);
    Serial.println(ir_f);
    Serial.println("--------------------");
  }


  // BLE payload (only notify if someone is connected)
  if (gDataChar && gServer->getConnectedCount() > 0) {
      char payload[160];

      // Format compact JSON into payload and use snprintf return value
      int len = snprintf(payload, sizeof(payload),
        "{\"ax\":%.3f,\"ay\":%.3f,\"az\":%.3f,"
        "\"gx\":%.2f,\"gy\":%.2f,\"gz\":%.2f,\"ir\":%d}",
        ax_f, ay_f, az_f, gx_f, gy_f, gz_f, ir_raw
      );

           // Fail-fast on format error or truncation to avoid sending invalid JSON
     if (len < 0) {
       Serial.println("snprintf error, skipping notify");
     } else if (len >= (int)sizeof(payload)) {
         Serial.println("payload truncated, increase buffer or reduce precision; skipping notify");
     } else {
         gDataChar->setValue((uint8_t*)payload, len);
         gDataChar->notify();
     }
  } else {Serial.println("Payload unsuccessful: no connected client or null data"); }

  // Add this to your main loop() - simple version without isAdvertising()
  static unsigned long last_status_check = 0;
  if (millis() - last_status_check > 10000) {  // Every 10 seconds
      last_status_check = millis();
      
      if (gServer->getConnectedCount() == 0) {
          Serial.println("No clients connected - advertising should be active");
          // Optionally restart advertising here
          // gAdvertising->start();
      } else {
          Serial.println("Client(s) connected - advertising stopped (normal)");
      }
  }

  delay(100);
}
