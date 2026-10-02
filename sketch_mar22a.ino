#include <SD.h>
#include <SPI.h>
#include <arduinoFFT.h>

// ── Pin definitions ──────────────────────────────
#define EEG_PIN       34
#define LED_PIN       27
#define SD_CS_PIN     5

// ── FFT config ───────────────────────────────────
#define SAMPLES       256
#define SAMPLE_RATE   256.0

double vReal[SAMPLES], vImag[SAMPLES];
ArduinoFFT<double> FFT = ArduinoFFT<double>(vReal, vImag, SAMPLES, SAMPLE_RATE);

// ── Globals ──────────────────────────────────────
File logFile;
unsigned long lastSample = 0;
int bufIdx = 0;
int panicCount = 0;        // consecutive panic seconds counter
int trialCount = 0;        // counts how many analysis windows done
int panicTrials = 0;       // counts how many triggered panic

// ──────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // SD card init
  if (SD.begin(SD_CS_PIN)) {
    Serial.println("SD card OK");
    logFile = SD.open("/eeg_log.csv", FILE_WRITE);
    if (logFile) {
      logFile.println("time_ms,raw_avg,alpha,beta,ratio,signal_valid,panic_count,panic");
      logFile.flush();
      Serial.println("Log file created: eeg_log.csv");
    }
  } else {
    Serial.println("SD failed - running without SD logging");
  }

  Serial.println("====================================");
  Serial.println("  EEG Panic Detector - CyberNuts");
  Serial.println("  Put on headband and stay calm...");
  Serial.println("====================================");
  delay(2000);
}

// ──────────────────────────────────────────────────
double bandPower(double* data, int n, double rate, double low, double high) {
  double power = 0;
  double binHz = rate / n;
  for (int i = 1; i < n / 2; i++) {
    double freq = i * binHz;
    if (freq >= low && freq <= high)
      power += data[i] * data[i];
  }
  return power;
}

// ──────────────────────────────────────────────────
void panicAlert() {
  // Rapid blink 5 times = PANIC alert
  for (int i = 0; i < 5; i++) {
    digitalWrite(LED_PIN, HIGH); delay(100);
    digitalWrite(LED_PIN, LOW);  delay(100);
  }
}

void calmBlink() {
  // Single slow blink = calm/normal
  digitalWrite(LED_PIN, HIGH); delay(500);
  digitalWrite(LED_PIN, LOW);
}

// ──────────────────────────────────────────────────
void loop() {
  unsigned long now = micros();

  if (now - lastSample >= (1000000 / (int)SAMPLE_RATE)) {
    lastSample = now;

    int raw = analogRead(EEG_PIN);
    vReal[bufIdx] = raw - 2048;
    vImag[bufIdx] = 0;

    // Send raw to Serial Plotter
    Serial.println(raw);

    bufIdx++;

    if (bufIdx >= SAMPLES) {
      bufIdx = 0;
      trialCount++;

      // ── Signal quality check ──────────────────
      // If signal is flat (0 or 4095) or out of range = headband off
      int rawCheck = analogRead(EEG_PIN);
      bool signalValid = (rawCheck > 300 && rawCheck < 3800);

      // ── FFT ──────────────────────────────────
      FFT.windowing(FFTWindow::Hamming, FFTDirection::Forward);
      FFT.compute(FFTDirection::Forward);
      FFT.complexToMagnitude();

      // ── Band power ───────────────────────────
      double alpha = bandPower(vReal, SAMPLES, SAMPLE_RATE, 8,  13);
      double beta  = bandPower(vReal, SAMPLES, SAMPLE_RATE, 13, 30);
      double theta = bandPower(vReal, SAMPLES, SAMPLE_RATE, 4,  8);
      double ratio = (alpha > 0) ? (beta / alpha) : 0;

      // ── Panic logic (3 consecutive seconds) ──
      if ((ratio > 1.5) && signalValid) {
        panicCount++;
      } else {
        panicCount = 0;
      }

      bool panic = (panicCount >= 3);

      if (panic) panicTrials++;

      // ── Accuracy tracking ─────────────────────
      float accuracy = (trialCount > 0) ?
                       ((float)panicTrials / trialCount * 100.0) : 0;

      // ── Serial Monitor output ─────────────────
      Serial.println("------------------------------------");
      Serial.print("Signal valid : "); Serial.println(signalValid ? "YES" : "NO - headband off?");
      Serial.print("Alpha power  : "); Serial.println(alpha, 1);
      Serial.print("Beta power   : "); Serial.println(beta, 1);
      Serial.print("Theta power  : "); Serial.println(theta, 1);
      Serial.print("Beta/Alpha   : "); Serial.println(ratio, 2);
      Serial.print("Panic count  : "); Serial.print(panicCount);
                                        Serial.println("/3 needed");
      Serial.print("STATUS       : ");
      if (!signalValid) {
        Serial.println("⚠ HEADBAND NOT DETECTED");
      } else if (panic) {
        Serial.println("🚨 PANIC DETECTED !!!");
      } else if (ratio > 1.2) {
        Serial.println("⚡ STRESS RISING...");
      } else {
        Serial.println("✅ CALM");
      }
      Serial.print("Trial #      : "); Serial.println(trialCount);
      Serial.println("------------------------------------");

      // ── LED control ───────────────────────────
      if (!signalValid) {
        digitalWrite(LED_PIN, LOW);   // headband off = LED off
      } else if (panic) {
        panicAlert();                 // rapid blink
      } else if (ratio > 1.2) {
        digitalWrite(LED_PIN, HIGH);  // stress rising = LED solid on
      } else {
        calmBlink();                  // calm = slow single blink
      }

      // ── SD card logging ───────────────────────
      if (logFile) {
        logFile.print(millis());       logFile.print(",");
        logFile.print(rawCheck);       logFile.print(",");
        logFile.print(alpha, 1);       logFile.print(",");
        logFile.print(beta, 1);        logFile.print(",");
        logFile.print(ratio, 2);       logFile.print(",");
        logFile.print(signalValid ? 1 : 0); logFile.print(",");
        logFile.print(panicCount);     logFile.print(",");
        logFile.println(panic ? 1 : 0);
        logFile.flush();
      }
    }
  }
}