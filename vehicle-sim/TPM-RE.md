# TPM page RE: HmiMain3D 006.027.001 (static only)

How the "Tire Pressure Monitor" page decides between "active" (tyres drawn, pressures shown) and
"failure". All VAs are HmiMain3D.006 VAs. The English texts come from `bmw/db/text.db`
(fw006 rootfs, NRV2D blocks, `id\ttext` lines; text id = low 20 bits of the 0x2000xxxx resource id).
Confidence: **H** = read directly in code, **M** = inferred from code and texts, **L** = guess.

## 0. Root cause (H)

* The current simulator sends CTyresStatus 05/0:C01 as all zero. **Byte 2** is the status the code
  reads. 0x00 is not a known code, so the status becomes 0xFF, which shows
  "Tyre Pressure Monitor failure". Byte 0 is never read, so the earlier byte-0 scans could not
  change anything.
* There is also a **17.5 s watchdog**. If bytes 1..3 of C01 do not change for 17.5 s while KL15
  is on, the status is forced to 0x60 (failure) and the qualifier to 0x80. The HMI then stops
  showing pressures. A static payload is therefore never enough: **byte 1 must keep changing**
  (it works like an alive counter).

## 1. Property map (CPxyVehicle member offset -> MOST id: ctor at 0x2267900..0x2268380, `movw r2,#fkt`)

| CPxyVehicle+ | 05/0 fkt | class | used by |
|---|---|---|---|
| 0x07ac | 0x21F | CTerminalStatus | CDevCarClamp (0xcfba2c) |
| 0x14cc | 0x621 | CCarSpeed2 | TpmStatus onPxyCarSpeed2 0xd01f2c |
| 0x1e3c | 0xC01 | CTyresStatus | TpmStatus 0xd02194 (callback 0xd02858) |
| 0x1ec8 | 0xC02 | CTyrePressure | TpmMeasurements 0xd03fec |
| 0x20ac | 0xC09 | CTyreTemperature | TpmMeasurements 0xd03fec |
| 0x27f8 | 0xC18 | CTyreState | TpmStatus 0xd02194 (callback 0xd02848, only if variant 0x4f94) |
| 0x58b4 | 0xCFA | CTargetTyrePressure | TpmMeasurements 0xd03e04 |
| 0x5a6c | 0xCFD | CRearAxleTyre | CDevCarTpmSettingsEx 0xf601xx (RID/tyre-type state) |

## 2. Payload layouts (deserializers)

* **CTyresStatus C01**, 5 bytes (deserializer 0x22716f0). Proxy members: +0x78 b0, +0x7c b1 (<=15),
  +0x80 b2, +0x84 b3, +0x88 b4. The accessors called from TPM code are 0x22659f8 (b1), 0x22659bc (b2)
  and 0x2265980 (b3). The b0 accessor (0x2265a34) and the b4 accessor (0x2265944) have no callers.
  b0 and b4 are unused (H).
* **CTyreState C18**, 12 bytes (deserializer 0x22719a0): 4×u8, 5×u8, u8, u16. The earlier probe only
  sent 9 bytes. TpmStatus reads **byte 0 only** (accessor 0x2264954, member +0x78) (H).
* **CTyrePressure C02**: 4×u16 FL, FR, RL, RR (members +0x78/+0x7a/+0x7c/+0x7e, accessors 0x2265908..854) (H).
* **CTyreTemperature C09**: 4×u16. **CTargetTyrePressure CFA**: 4×u16.
* **CTerminalStatus 21F**: 3×u8<=15. CDevCarClamp reads byte 0 only (0x2267168, member +0x78).
* **CCarSpeed2 621**: u16.

## 3. CDevCarTpmStatusImpl (vtable 0x2c095e8). Fields and getters

| field | getter (vt off) | meaning |
|---|---|---|
| +0x58 | 0xd01d1c (+0x24) | variant 0x4f94 (CTyreState/reset-progress support) |
| +0x5c | 0xd01d2c (+0x28) | 1 = RDC (variant 0x4f91 set) else 0 |
| +0x60 | 0xd01c8c (+0x0c) | **status code** (init 0xFF) |
| +0x64 | 0xd01c9c (+0x10) | reset state: 0 = in progress, 1 = done, 2 = normal (init 2) |
| +0x68 | 0xd01cbc (+0x18 returns !moving) | moving flag (init 1) |
| +0x69 | 0xd01d84 (+0x30) | vehicle state ok (KL15 / PWF) |
| +0x6a | 0xd01cac (+0x14) | reset progress % |
| +0x6b | 0xd01d4c (+0x20) | {pressure-loss qualifier, valid} (init {0xA0,0}) |
| +0x74 | n/a | CPrcTimer, setTiming(0x445c = 17500 ms) at 0xd03204 |
| — | 0xd01cd0 (+0x1c) | "pressures valid" = status in {0x20,0xA0,0xA8,0xB8} && +0x64 in {1,2} |

### Init and coding (H)
* 0xd01db8 reads the variant server (`vs->vt+0xc(id)`):
  * 0x4f91 = rdcFlag
  * 0x4f93 = rpaFlag
  * 0x500f = secCarFlag (asserts "!(rdcFlag && rpaFlag)" and "!(rpaFlag && secCarFlag)")
  * With RDC set: +0x5c = 1 and +0x58 = variant(0x4f94). Otherwise both are 0.
* 0xd0299c setNotifications:
  * It needs CCarSpeed2 and CTyresStatus to be "initialised" (0x1f8db54 checks prop+0x58 != 0), plus
    CTyreState when +0x58 is set. Otherwise it logs "Cannot set notifications…" and **init aborts**
    (0xd02cfc). Then the timer and the +0xc "initialised" flag are never set, so the status stays 0xFF
    forever.
  * The vehicle state concept must be coded: PWF = variant 0x51f6 (0xe8e1b4) or
    Clamp = variant 0x51ef (0xcfbe64). Otherwise it logs "No valid vehicle state concept coded."
    and init also aborts. The F30 should be the Clamp/KL concept (M).
  * Check the HMI log for those two messages.

### Vehicle state +0x69 (Clamp concept) (H)
* CDevCarClamp (0xcfba2c, jump table 0xcfba6c) maps CTerminalStatus byte0:
  * 6, 7 -> 0
  * 8, 9 -> 1
  * 10, 12 -> 2
  * 13 -> 3
  * other values -> unchanged (init 0)
* TPM sets +0x69 = (state ∈ {2,3}) (0xd02da8, 0xcfb958), so **byte0 ∈ {10,12,13}**. The sim's 12 is fine.
* With +0x69 = 0 the status is forced to 0xFF = failure (0xd02378).

### Speed (H)
* 0xd01f2c: 0xFFFF is ignored.
* moving = speed > 0x6e when already moving, else speed > 0x80 (hysteresis).
* Speed 0 = standing. Standing only matters for the reset texts.

### Status evaluation 0xd02194 (runs on C01, C18, KL15/PWF changes and on the timer)
1. If +0x69 == 0 -> +0x60 = 0xFF, qualifier = {0x80,0}.
2. Read C01 b1/b2/b3 and call 0xd0213c:
   * If b2 == 0xFF, ignore.
   * If (b1,b2,b3) changed, store them, `CPrcTimer::restart`, clear the +0x70 timeout flag.
3. Timer expiry 0xd02868 sets +0x70 = +0x69 and re-runs. With +0x70 set, **b2 := 0x60, b3 := 0x80**
   (0xd0225c).
4. Switch on `b2 & 0xFC` (0xd0228c; the low 2 bits are ignored):
   * 0x20, 0xA0, 0xA8, 0xB0, 0xB8, 0xE8 -> +0x60 = code. For all but 0xE8 the qualifier is set from b3
     via 0xd01b98.
   * 0x60, 0x80, 0xE0 -> +0x60 = code, qualifier {0x80,0}.
   * Anything else -> **0xFF**.
5. If +0x58 is set and the code is one of 0x20/0xA0/0xA8/0xB0/0xB8/0xE8, read C18 byte0 (0xd023c4):
   * <= 100 -> +0x6a = value, +0x64 = 0
   * 0xFD -> +0x64 = 1
   * 0xFE -> +0x64 = 2
   * else unchanged
6. Notify the listeners (activity, TpmMeasurements).

### C01 byte 3 = QualifierTyrePressureLoss (0xd01b98, readers 0xd01984..0xd01ab8) (H)

Accepted values: high nibble 0x2_ or 0x8_, or exactly 0x30, 0x31, 0xA0. Anything else logs
"Unknown value…" and is treated as 0x80.

| b3 | meaning (from texts via 0x8d48d0) |
|---|---|
| 0x80, 0x20 | no loss -> "Tyre Pressure Monitor active…" |
| 0x2X | bit1 = left front, bit0 = right front, bit3 = left rear, bit2 = right rear low; more than one bit -> "Tyre pressure low" |
| 0x30 | all low -> "Tyre pressure low. Inflate tyres…" |
| 0x31 | "Check all tyre pressures and inflate at your convenience" |
| 0xA0 | reset/learn qualifier: RDC shows "Resetting tyre pressure… %" or "drive off"; RPA shows "Flat Tyre Monitor active" |

## 4. Status code -> page text (CCarVehicleStatusTyrePressureActivity)

0x8d4e90 selects the RDC text function 0x8d4b44 when vt+0x28 (+0x5c) == 1, else the RPA text function
0x8d4a10. The generic text function is 0x8d4424. Mapping from C01 b2 (& 0xFC) for RDC:

| b2 | text (EN) | pressures drawn? |
|---|---|---|
| **0xA0** | **"Tyre Pressure Monitor active. See label…"** (0x6d18; 0x8b50 temperature variant) | **yes** |
| 0xB0 | same text | **no**: 0xd01cd0 excludes 0xB0, so TpmMeasurements blanks the values |
| 0xA8 / 0xB8 | "Check tyre pressure and correct if necessary." (0xe6d8/0x9240) | yes |
| 0x20 | "Measuring tyre pressure…" (0x6d78) | yes |
| 0xE8 | "Resetting Tyre Pressure Monitor…" (0x6d70) / standing: "To check tyre pressure, drive off." (0x6d88) | no |
| 0xE0 | "Tyre Pressure Monitor **fault**" (0x6d28) = malfunction | no: the view accepts E0, but TpmMeasurements gating (0xd01cd0) blanks the values to "--" |
| 0x60 / 0xFF / unknown / timeout | "Tyre Pressure Monitor **failure**" (0x6d58) | no |
| 0x80 | blank text (0x20000001) | no |

### Page mode 0x8d4628 (jump table 0x8d5ccc; it is not the UiStateController)

| mode | when | function |
|---|---|---|
| 5 | +0x64 == 1 and code ∈ {A0,A8,B0,B8,20,E8} and SettingsEx(+0xfc)+0x18 ∈ {1,2} | 0x8d5a58: "tyre type recognised" |
| 4 | SettingsEx vt+0x50 (= +0x13c, from CRearAxleTyre CFD last byte) == 1 | 0x8d55fc: RID measuring |
| **3** | qualifier != 0xA0 and code ∈ {A0,A8,B0,B8,20} | **0x8d4ef8: status + loss text (normal case)** |
| 1 | variant 0x4f94 set and +0x64 <= 1 and code ∈ {A0,A8,B0,B8,E8,20} | 0x8d4fa4: reset/measurement result |
| 2 | some tyre has pressure status 1 and code ∈ {A0,A8} | 0x8d456c: "Measuring…/drive off" |
| 0 | otherwise | 0x8d4424: plain status text |

### Tyre values (CCarTyrePressureView::update 0x9fae04, CDevCarTpmMeasurementsImpl vt 0x2c09ab8) (H)

* 0xd03fec stores the C02 and C09 u16s (0xFFFF entries are skipped) only if both hold:
  * status vt+0x1c is true (code ∈ {0x20,0xA0,0xA8,0xB8} and +0x64 ∈ {1,2})
  * vt+0x30 (+0x69) is true in the Clamp concept
* Otherwise all values are set to 0xFFFE. It re-runs on every TpmStatus listener callback.
* Pressure status 0xd03cc0:
  * 0xFFFF -> 2 (empty)
  * 0xFFFE or 0xFFFC -> 1 ("--" when +0x64 != 0)
  * anything else -> 0 (value shown)
* Value = raw × 0.1 (0xd03c40), with no unit conversion in the view; floor() is applied when the
  units pressure setting != 0 (0x9faa00).
* So the raw value is likely **0.1 × the display unit** (bar: 23 = 2.3; kPa: 2300) — **M**.
  The current 230 would show as 23.0 bar or 23 kPa.
* Temperature = raw − 40 (0xd03b94). It is only shown with variant 0x530c.
* Pressure numbers need view variant 0x4f95 (+0x1c, 0x9fb294).

## 5. Coding / activity choice

* RDC vs RPA (H for the meaning, from the assert strings):
  * Variant 0x4f91 = RDC flag.
  * Variant 0x4f93 = RPA flag.
  * Both set gives "CODING ERROR…". The RPA path then gives +0x5c = 0 and uses the RPA texts
    ("Flat Tyre Monitor…").
  * In libhmicoding these are probably `REIFENUEBERWACHUNG_RDC_RPA = rdc` / `RDC`, but I could not
    resolve the HMI variant ids (0x4fxx) to libhmicoding `va_` names (L).
* Other variant ids:

  | variant | meaning | confidence |
  |---|---|---|
  | 0x4f94 | CTyreState reset-progress support (+0x58), probably `RDC_FORTSCHRITTSANZEIGE` | M/L |
  | 0x4f95 | show pressure values | H that it gates the values, L for the name |
  | 0x530c | show temperatures (`RDC_DRUCK_TEMP=druck_und_temperatur`?) | name L |
  | 0x53b6 / 0x5442 | "readings change with temperature" text variants (activity +0x208) | M |
  | 0x51ef | Clamp concept | H |
  | 0x51f6 | PWF concept | H |

* **ERFS**: CCarVehicleStatusTyrePressureERFSActivity is gated by variant 0x53b1 (0x9ed588, also
  view +0x1e). Only this activity owns **CCarTirePressureUiStateController**.
  * Its `State` drives the ERFS settings dialog in onUiStateControllerChanged (0x9e78f0):
    * new = 1, old = 0 -> "ERFS settings change starts"
    * new = 0 -> "cancelled settings" / "close ERFS"
  * The ERFS activity re-evaluates on TpmStatus (0x9ea1a4: code == 0xE8 or +0x64 == 0, with SettingsEx
    selection byte == 0x3c), but it does not decide OK vs failure.
  * An F30 with plain RDC (no ERFS) uses CCarVehicleStatusTyrePressureActivity. Its "UI state" is the
    page mode in §4 (M; I did not check the state-machine data).

## 6. Values to send

C01 must be re-sent with a changing byte 1 at least every 17.5 s. Pushing it every 1–5 s with a 0..14
counter is enough (add it to LIVE).

```python
(0x05, 0x00, 0xC01): bytes([0x00, counter % 15, 0xA0, 0x80, 0x00]),  # H. b2=A0 OK, b3=80 no loss; b1 must change < 17.5 s
(0x05, 0x00, 0xC18): bytes([0xFE] + [0x00] * 11),                    # H for byte0 (FE = normal, +0x64=2); other bytes unused here
(0x05, 0x00, 0x21F): bytes([12, 1, 0]),                              # H: byte0 in {10,12,13} -> vehicle state ok
(0x05, 0x00, 0x621): bytes([0x00, 0x00]),                            # H: standing
(0x05, 0x00, 0xC02): struct.pack(">4H", 23, 23, 25, 25),             # M: raw*0.1 in display unit (bar); use 2300.. for kPa
(0x05, 0x00, 0xC09): struct.pack(">4H", 60, 60, 60, 60),             # M: deg C + 40 (only shown with temp coding)
# (0x05, 0x00, 0xCFD) CRearAxleTyre: leave unsent, or last byte != 1 (else page mode 4)
```

Payload values for the other states:

| state | C01 b2 | C18 byte0 |
|---|---|---|
| malfunction | 0xE0 ("fault"), or 0x60 / any unknown value ("failure") | — |
| not initialised / measuring | 0x20 | — |
| reset in progress | 0xE8 (with b3 = 0xA0 for the RDC progress text) | 0..100 = % |
| reset done | — | 0xFD |
| warning | 0xA8 | — |

Not determined:
* the pressure display unit/scale (M)
* the HMI variant id → coding name mapping (L)
* whether the setNotifications "initialised" check (prop+0x58) passes in the emulator (check the log)
