#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>  // You need to install the ArduinoJson library

// Wi-Fi credentials
const char* ssid = "your-ssid";
const char* password = "your-password";

// API endpoint to fetch lecture status
const char* serverUrl = "http://your-ngrok-url.com/api/timetable_status";

// Time interval for polling (in milliseconds)
const unsigned long pollingInterval = 60000;  // 60 seconds
unsigned long previousMillis = 0;

// Function to fetch lecture statuses from the server
void fetchAndUpdateDisplay() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);  // Start the HTTP request
    
    int httpResponseCode = http.GET();  // Send the GET request
    
    if (httpResponseCode == 200) {  // If the request was successful
      String response = http.getString();  // Get the response as a String
      Serial.println(response);  // Print response for debugging
      
      // Parse JSON response
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, response);
      
      // Extract and display lecture statuses
      for (JsonObject lecture : doc.as<JsonArray>()) {
        const char* subject_name = lecture["subject_name"];
        const char* lecture_time = lecture["lecture_time"];
        const char* teacher_name = lecture["teacher_name"];
        const char* lecture_status = lecture["lecture_status"];
        
        // Display status on P10 (adjust this according to your display library)
        Serial.print("Subject: "); Serial.println(subject_name);
        Serial.print("Time: "); Serial.println(lecture_time);
        Serial.print("Teacher: "); Serial.println(teacher_name);
        Serial.print("Status: "); Serial.println(lecture_status);
        Serial.println("------------------------");
        
        // Here you would call your P10 display function to update the status
        // For example: P10_Display(subject_name, lecture_time, lecture_status);
      }
    }
    else {
      Serial.print("Error in HTTP request: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();  // Close the HTTP connection
  }
  else {
    Serial.println("WiFi not connected");
  }
}

void setup() {
  // Start the serial communication for debugging
  Serial.begin(115200);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("Connected to WiFi");

  // Initialize your P10 display here
  // Example: P10_Init();
}

void loop() {
  // Polling logic
  unsigned long currentMillis = millis();
  
  if (currentMillis - previousMillis >= pollingInterval) {
    previousMillis = currentMillis;  // Update the last poll time
    fetchAndUpdateDisplay();  // Fetch and display the latest lecture status
  }
}
