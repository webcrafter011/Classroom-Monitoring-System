#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>  // To handle JSON
#include <PxMatrix.h>  // Library to control P10 LED display

// WiFi credentials
const char* ssid = "your-SSID";
const char* password = "your-WIFI-password";

// Server URL (your Flask web app hosted with Ngrok)
const String baseURL = "https://your-ngrok-app-link.com";  // Replace with your Flask URL
const String apiEndpoint = "/api/timetable_status?date=";

// Date to request timetable status
String selected_date = "2024-10-20";  // Update to the current date

// PxMatrix setup
#define P_LAT 22
#define P_A 19
#define P_B 23
#define P_C 18
#define P_OE 5
PxMatrix display(32, 16, P_LAT, P_OE, P_A, P_B, P_C);

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  // Wait for WiFi connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // Initialize display
  display.begin(16);
  display.setBrightness(50);

  // Fetch and display lecture status
  getLectureStatus();
}

void loop() {
  delay(60000);  // Check every 1 minute
  getLectureStatus();
}

// Function to get lecture status from the Flask server
void getLectureStatus() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    String requestURL = baseURL + apiEndpoint + selected_date;

    http.begin(requestURL);
    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      String payload = http.getString();
      Serial.println(payload);

      // Parse JSON response
      StaticJsonDocument<512> doc;
      deserializeJson(doc, payload);
      
      JsonArray lectures = doc["lectures"].as<JsonArray>();

      if (lectures.size() == 0) {
        displayStatus("No Lectures");
      } else {
        for (JsonObject lecture : lectures) {
          String subject = lecture["subject_name"];
          String status = lecture["lecture_status"];
          String message = subject + ": " + status;
          displayStatus(message);
          delay(5000);  // Show each status for 5 seconds
        }
      }
    } else {
      Serial.println("Error on HTTP request");
      displayStatus("HTTP Error");
    }
    http.end();
  } else {
    displayStatus("WiFi Error");
  }
}

// Function to display status on P10 display
void displayStatus(String message) {
  display.clear();
  display.print(message.c_str());
}
