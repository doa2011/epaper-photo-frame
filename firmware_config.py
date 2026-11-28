"""Offline firmware configuration planner. This does not build or flash firmware."""
import argparse
import json
from pathlib import Path
from device_profiles import PANELS

# Capability assumptions for planning only; no board pinout or firmware verified.
CHIPS = {
    "esp32": {"wifi", "ble"},
    "esp32-s3": {"wifi", "ble"},
    "esp32-c3": {"wifi", "ble"},
    "esp32-c6": {"wifi", "ble"},
    "tlsr8258": {"ble"},
    "tlsr8359": {"ble"},
    "nrf52832": {"ble", "nfc_wake"},
    "nrf52840": {"ble", "nfc_wake"},
    "efr32bg22": {"ble"},
    "efr32mg21": {"ble"},
    "efr32mg22": {"ble"},
    "ch592": {"ble"},
    "da14531": {"ble"},
    "passive-nfc": {"nfc"},
    "tn2115s2": {"nfc"},
}
# Generic geometry only; no driver assignment for these portable candidates.
PORTABLE = {"generic-154": (200, 200), "generic-290": (296, 128),
            "generic-420": (400, 300)}
FEATURES = {"ha", "mqtt", "http", "storage", "battery_status", "deep_sleep", "timer"}
KEYS = {"chip", "panel", "mode", "power", "transports", "features"}

def _choices(config, key, allowed):
    value = config.get(key)
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ValueError(f"{key}: expected list of strings")
    if len(set(value)) != len(value) or set(value) - allowed:
        raise ValueError(f"{key}: duplicate or unsupported selection")
    return set(value)

def plan(config):
    if not isinstance(config, dict) or set(config) != KEYS:
        raise ValueError("configuration must contain exactly: " + ", ".join(sorted(KEYS)))
    chip, panel, mode, power = (config[k] for k in ("chip", "panel", "mode", "power"))
    if not all(isinstance(x, str) for x in (chip, panel, mode, power)):
        raise ValueError("chip, panel, mode and power must be strings")
    if chip not in CHIPS or panel not in (PANELS.keys() | PORTABLE.keys()):
        raise ValueError("unknown chip or panel")
    if mode not in {"slideshow", "polaroid", "hybrid"} or power not in {"usb", "battery", "passive_nfc"}:
        raise ValueError("unknown mode or power")
    transports = _choices(config, "transports", {"wifi", "ble", "nfc", "nfc_wake"})
    features = _choices(config, "features", FEATURES)
    if not transports or transports - CHIPS[chip]:
        raise ValueError("transport unsupported by selected chip")
    if "nfc_wake" in transports and "ble" not in transports:
        raise ValueError("NFC wake requires BLE image transport")
    if (chip in {"passive-nfc", "tn2115s2"}) != (power == "passive_nfc"):
        raise ValueError("passive NFC requires a dedicated passive device profile")
    if power == "passive_nfc" and (mode != "polaroid" or transports != {"nfc"} or features):
        raise ValueError("passive NFC planning supports only tap-to-write without active modules")
    if features & {"mqtt", "http"} and "wifi" not in transports:
        raise ValueError("MQTT/HTTP requires Wi-Fi")
    if "ha" in features and not ({"ble"} & transports or features & {"mqtt", "http"}):
        raise ValueError("HA requires BLE or a selected network backend")
    if "battery_status" in features and power != "battery":
        raise ValueError("battery status requires battery power")
    if "timer" in features and mode == "polaroid":
        raise ValueError("timer requires slideshow or hybrid mode")
    if panel in PANELS:
        p = PANELS[panel]
        width, height, driver = p.width, p.height, p.driver
    else:
        width, height = PORTABLE[panel]
        driver = None
    return {
        "schema_version": 1,
        "status": "candidate_plan_only",
        "buildable": False,
        "hardware_verified": False,
        "chip": chip, "panel": panel, "mode": mode, "power": power,
        "transports": sorted(transports), "features": sorted(features),
        "display": {"width": width, "height": height, "driver_candidate": driver,
                    "four_color_frame_bytes": ((width * 2 + 7) // 8) * height},
        "blockers": ["board pinout and resources unverified",
                     "panel encoding and electrical compatibility unverified",
                     "firmware target and toolchain not implemented"] + (
                         ["TN2115S2 NFC SDK and harvested power unverified"] if chip == "tn2115s2" else []),
    }

PRESETS = {
    "polaroid-tn2115s2": dict(chip="tn2115s2", panel="gdem0397f81", mode="polaroid",
                              power="passive_nfc", transports=["nfc"], features=[]),
    "frame-usb": dict(chip="esp32-s3", panel="gdey116f51", mode="slideshow", power="usb",
                      transports=["wifi", "ble"], features=["http", "ha", "timer"]),
    "polaroid-ble": dict(chip="nrf52840", panel="generic-420", mode="polaroid", power="battery",
                         transports=["ble"], features=["deep_sleep", "battery_status"]),
    "polaroid-hybrid": dict(chip="nrf52840", panel="generic-420", mode="polaroid", power="battery",
                            transports=["ble", "nfc_wake"], features=["deep_sleep"]),
    "polaroid-passive": dict(chip="passive-nfc", panel="generic-154", mode="polaroid",
                             power="passive_nfc", transports=["nfc"], features=[]),
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preset", choices=sorted(PRESETS))
    group.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        config = PRESETS[args.preset] if args.preset else json.loads(args.config.read_text(encoding="utf-8"))
        result = json.dumps(plan(config), indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.write_text(result, encoding="utf-8")
        else:
            print(result, end="")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))

if __name__ == "__main__":
    main()
