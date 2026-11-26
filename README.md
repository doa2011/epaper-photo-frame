# E-Paper Photo Frame

Local photo service for Synology DSM7 and Home Assistant. Photos stay on LAN. Architecture: read-only photo source -> EXIF/crop/dither -> device-specific encoder -> queued transport -> acknowledgement. Never equate submission with physical display.

## Hardware evidence
User reports TLSR8359 and JD79665; board photo suggests GD25Q16E (2 MiB). Exact panel FPC, GPIO, flash layout and color count remain unverified. Reference projects: https://github.com/atc1441/ATC_TLSR_Paper and https://github.com/ZinggJM/GxEPD2 ; original BLE option https://github.com/eigger/hass-ble-esl . Verify licenses before reuse. No hardware tests yet.

Development occurs on feature branches; no automatic merges.
