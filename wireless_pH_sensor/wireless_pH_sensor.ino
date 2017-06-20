// hao jin
// 2017.5.25
#include <SoftwareSerial.h> 
#include <SimpleDHT.h>
#include <Wire.h>
#include <Adafruit_ADS1015.h>

// BlueTooth
// [BT] <-->  [Arduino]
// VCC  <-->  5V
// GND  <-->  GND
// TxD  <-->  pin D2
// RxD  <-->  pin D3  
#define RxD 2
#define TxD 3
SoftwareSerial Serial_BT(RxD,TxD); 

// DHT11, temperature & humidity sensor
// [DHT11]  <-->    [Arduino]
// VCC      <-->    5V
// GND      <-->    GND
// DATA     <-->    pin D7
int pinDHT11 = 7;
SimpleDHT11 dht11;
byte temperature = 0;
byte humidity = 0;
byte data[40] = {0};

// ADS1115
// [ADS1115]  <-->    [Arduino]
// VDD        <-->    5V
// GND        <-->    GND
// SCL        <-->    pin A5
// SDA        <-->    pin A4
// ADDR       <-->    GND
Adafruit_ADS1115 ads(0x48);
float Voltage_RE = 0.0;
float Voltage_pH = 0.0;
 
void setup() 
{ 
    pinMode(pinDHT11, INPUT); 
    pinMode(RxD, INPUT); 
    pinMode(TxD, OUTPUT); 
    Serial_BT.begin(9600);         // Bluetooth baud rate  
    Serial.begin(9600);            // USB terminal baud rate 
    ads.begin();
} 
 
void loop() 
{ 
  // read DHT11 data
  if (dht11.read(pinDHT11, &temperature, &humidity, data)) {
    Serial_BT.println("Read DHT11 failed"); 
    Serial.println("Read DHT11 failed"); 
    return;
  }

  // ADS1115, 
  // read from the ADC, and obtain a sixteen bits integer as a result
  // adc1: A1 pin, sensing the setting voltage at reference electrode
  // adc3: A3 pin, sensing the voltage of pH electrode
  int16_t adc1;  
  int16_t adc3;
  adc1 = ads.readADC_SingleEnded(1);
  adc3 = ads.readADC_SingleEnded(3);
  Voltage_RE = (adc1 * 0.1875); // the resolution of ADC is 0.1875 mV
  Voltage_pH = (adc3 * 0.1875);

  // sending data to USB and Bluetooth ports
  // data format:
  Serial_BT.print((int)temperature); 
  Serial_BT.print(" ");
  Serial_BT.print((int)humidity); 
  Serial_BT.print(" ");
  Serial_BT.print(Voltage_RE, 4);
  Serial_BT.print(" ");
  Serial_BT.print(Voltage_pH, 4); 
  Serial_BT.print("\n");
  Serial.print((int)temperature); 
  Serial.print(" ");
  Serial.print((int)humidity); 
  Serial.print(" ");
  Serial.print(Voltage_RE, 4);
  Serial.print(" ");
  Serial.print(Voltage_pH, 4); 
  Serial.print("\n");
  
  // set sampling rate to 1 Hz.
  delay(1000);
}
