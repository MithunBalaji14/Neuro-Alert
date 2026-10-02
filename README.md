# EEG Panic Detector - CyberNuts

Automatic panic detection wearable using EEG signals.
Detects panic states by analyzing Alpha/Beta brain wave ratio.

## Team
- Lead: Mithun Balaji Kumaresan
- Members: Joshpin Kayalvizhi, Hiruthik
- Mentor: Sujith
- Lab: CD | Cohort: 2024-2028

## Hardware
- BioAmp EXG Pill
- ESP32 Dev Module
- BioAmp EEG Headband (3-ch)
- Bio Snap Cable
- Micro SD Card Adapter
- LED (alert indicator)

## How it works
1. EEG headband captures brain signals
2. BioAmp EXG Pill amplifies the signal
3. ESP32 samples at 256Hz and runs FFT
4. Alpha (8-13Hz) and Beta (13-30Hz) band power calculated
5. If Beta/Alpha ratio > 1.5 for 3 consecutive seconds = PANIC
6. LED blinks rapidly as alert
7. All data logged to SD card CSV

## Files
- sketch_mar22a.ino - ESP32 firmware (Arduino)
- eeg_dashboard.py - Real-time Python dashboard

## Results
- Signal stable: YES
- Panic detection: Working
- Alert latency: under 2 seconds
- Cost: under $30
