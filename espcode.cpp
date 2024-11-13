#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DMD32.h>  // Correct header file for DMD library

// Wi-Fi credentials
const char *ssid = "sample12";
const char *password = "sample12";

// API endpoint to fetch lecture status
const char *serverUrl = "http://f0a2-2401-4900-7971-9c3c-7d8a-29b-169a-b882.ngrok-free.app/api/timetable_status";

// Time interval for polling (in milliseconds)
const unsigned long pollingInterval = 10000; // 10 seconds
unsigned long previousMillis = 0;

// Define DMD object for 32x16 matrix display (1 panel wide, 1 panel high)
DMD matrix(1, 1);  // 1 panel wide, 1 panel high

// Function to fetch the latest lecture status from the server and update the display
void fetchAndUpdateDisplay()
{
    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;
        http.begin(serverUrl);

        int httpResponseCode = http.GET();

        if (httpResponseCode == 200)
        {
            String response = http.getString();
            Serial.println(response); // Debugging output

            // Parse JSON response
            DynamicJsonDocument doc(1024);
            DeserializationError error = deserializeJson(doc, response);
            if (error)
            {
                Serial.print("JSON parsing failed: ");
                Serial.println(error.c_str());
                return;
            }

            matrix.clearScreen(LOW); // Clear the display before showing new data

            // Display only the latest lecture's status (first item in the JSON array)
            JsonObject latestLecture = doc[0];
            const char *subject_name = latestLecture["subject_name"];
            const char *lecture_status = latestLecture["lecture_status"];

            // Create a concise display message
            String displayMessage = String(subject_name) + ": " + lecture_status;

            // Display text on the matrix
            matrix.drawString(0, 0, displayMessage.c_str(), displayMessage.length(), GRAPHICS_NORMAL);
            delay(3000); // Display the message for 3 seconds
        }
        else
        {
            Serial.print("Error in HTTP request: ");
            Serial.println(httpResponseCode);
        }

        http.end();
    }
    else
    {
        Serial.println("WiFi not connected");
    }
}

void setup()
{
    Serial.begin(115200);

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("Connected to WiFi");

    matrix.clearScreen(LOW);  // Clear the display on startup
}

void loop()
{    
    unsigned long currentMillis = millis();

    if (currentMillis - previousMillis >= pollingInterval)
    {
        previousMillis = currentMillis;
        fetchAndUpdateDisplay();
    }
    delay(500);
}
