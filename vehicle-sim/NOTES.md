# Jacinto (J5) MOST server stand-in — research notes

Goal: fill the native My Vehicle menus in the car-006027 emulator by standing in for the HU's
Jacinto, which hosts the MOST network server (`MOSTSubSystemServer`) the OMAP depends on.

## Why My Vehicle is empty
- OTF: `CDevApplicationAvailability ... ePowerMode=0, bKeyInCar=0 => bMenuEnabled=0`.
- HMI proxies (`CPxySystemFunctionPowerMode`, ...) are MOST FBlock proxies found through the MOST
  central registry. The OMAP runs only `/opt/sys/bin/most --devmode=client
  --serverRoleName=MOSTSubSystemServer` (starter #105, active for variant 0x80000004).
- The server role lives on the J5 (`most --devmode=master`, INIC on MediaLB). OMAP<->J5 is one QNX
  qnet cluster (`/net/hu-jacinto`, boot script runs things `on -f /net/hu-jacinto`).
- pcap of a full boot: no IP traffic towards a J5 at all except NAL-SIPC 5555 (raw MOST messages,
  0x1C header + payload; parser most!0x185140) -> DSI to the J5 is message passing (qnet), which
  the emulator lacks.

## DSI C API (libsys_dsi_base.cpp-ne.so.4, exported, C linkage)
- `DSIServerInit(DSIServer *srv /*0xE8 bytes, memset*/, const char *iface, const char *role,
   int major, int minor)` -> name "role.iface" at srv+0x18, major +0x98, minor +0x9C, +0xD0=-1.
- `DSIServerRegister(srv)`: srv+8 = DSICreateId(); SBRegisterInterface(DSIGetSBHandle(),
   srv+0x18, major, minor, chid=[srv+0xA8], &srv[0x10]).
- `DSIServerRun(srv)`: DSIChannelCreate, SBRegisterInterface, DSIOpen, DSIReceive loop ->
   DSIServerHandleConnectRequest / DSIServerHandleDataRequest / HandleClientDetach.
- `DSIServerHandleDataRequest(srv, stream)`: reads 16-byte header via DSIRead:
   +4 type, +8 id, +0xC session. type 0x100 -> cb[srv+0xE4](srv,id) (notification id map, may be
   NULL) then request cb[srv+0xD8](srv, stream, id); 0x101/0x105 set-notification (table at
   srv+0xB4, 24-byte entries); 0x102 clear one; 0x104 clear all; 0x103 logged only.
- Also exported: DSIServerPrepareResponse 0x4D70, DSIServerSendResponse 0x5660,
   DSIServerSendNotification 0x5C44, DSIRead/DSIWrite/DSIGetDataPtr/DSIGetSize/DSIWriteString2.

## DSYSMOSTServer interface (symbols in libimp_sys_most_base_nbt.cpp-ne.so.17; list via
   `nm -D` of that library)
Requests: RegisterDevices, RegisterExtDevices, RegisterDevCtrls, UnregisterDevices,
UnregisterDevCtrls, ProcessMessage, ProcessMessageVector, SetRegistryFilter,
SetCommunicationCtrl, ChangeInstID, CleanUp, EnableNotificationProxy.
Responses: responseMOSTClient(u32, u16), responseMOSTSubnet(u32), responseInvalid.
Informations: Registry, Connect, Disconnect, Activate, Deactivate, ProcessMessage,
ChangeInstID, CleanUp.

## Confirmed at runtime (2026-11-09, car-006027 emulator)
- Bridge works: the real `most` client finds MOSTSubSystemServer.DSYSMOSTServer **4.5** (version from
  CHBVersion(4,5,0) in CDSYSMOSTServerProxy static init) through the guest broker.
- ID map (toDSI(CDSYSMOSTServerRequest/Response)): requests 0x00 RegisterDevices(u32 h, vec<u16>),
  0x01 RegisterDevCtrls, 0x02 ProcessMessage(u32, Message), 0x04/0x05 Unregister..., 0x06
  ChangeInstID(u32,u16,u8), 0x07/0x11 (u32), 0x09 registerMOSTSubnet(u16), 0x0B SetRegistryFilter,
  0x0C SetCommunicationCtrl(u32), 0x0D RegisterExtDevices, 0x0E ProcessMessageVector,
  0x0F registerMOSTClientExt(string "most-MOSTSubSystem"); 0x03/0x08/0x0A/0x10 no args.
  Responses: 0x80000000 responseMOSTClient(u32,u16), 1 informationProcessMessage(Message),
  2 ChangeInstID(u16,u8), 3 Connect(vec<DeviceInfo u16,u16>), 4 Disconnect, 5 Activate,
  6 Deactivate (vec<u16 key>), 7 CleanUp(u32,u16,u16), 8 responseMOSTSubnet(u32), 9 informationRegistry.
  Attributes: 0xC0000000 MOSTCommunicationState(u32; most!0x144314 switch 0..4, 2 = cancels
  SYSAVAIL timeout), 1 Registry(vec<u16 key,u16 dev>), 2 DeviceID(u16), 3 CommCtrl(u32, 0=ENABLE),
  4 ExtDeviceID(u16).
- Encoding: natural alignment; string/buffer = u32 length + bytes (string incl. NUL);
  Message = i32 transmission, i32 variant(1 TXControl/2 Info), i32 value, header
  (u16 dst,u16 src,u8 fb,u8 inst,u16 func,u8 op,u32 tag), buffer.
- DSI C API: callback srv+0xE4(srv, reqId) must return the response id (else replies are dropped);
  srv+0xD4(srv, stream, attrId) fills attribute data; srv+0xD8(srv, stream, reqId) handles requests.
- Flow seen: 0x0F -> we answer responseMOSTClient(1, 0x0100); 0x09(0x2000) -> responseMOSTSubnet(1);
  then RegisterDevices for OMAP FBlocks 0711, D701, D801, D901, 1001, CF01, CA00, D126.
- The client subscribes to 0x80000001..7 and attributes 0/2/3/4 — NOT to the registry.
- OTF after our handshake: HMI `SvcFunctionProxy try to send msg on inactive FBlock (05.00.CA0)` and
  `notification retry` on D8.01 / 10.01 / CF.01 -> remote FBlock availability still not reaching the
  HMI. informationConnect(all FBlocks, DeviceInfo=(key, 0x0200)), Activate(OMAP keys), NWM
  Configuration.Status(OK) via informationProcessMessage did not change that.
- NAL-SIPC 5555 only carries FBlock CA.00 fn 0x247 Status (10 s) and E0.01 Notification ClearAll.
- Client-side library traces ("MOSTClient %d processNewRegistry", "connect fbKey %04X devId %04X")
  live in libimp; app clients (HMI, NBTCarHU) are clients of the OMAP `most` bridge stub.

## Breakthrough (2026-11-09 evening)
- Visibility: text trace config `--tp=/opt/idrive/most.tp` (HBTracePersistence 1.1.0, `[*]`, lines
  `<scopeprefix> <levelmask> <outputmask>`, output 8 = console) added to the `most` client via
  IDRIVE_MOST_TRACE_CONFIG (archive-idrive-rootfs.py). Trace lands in serial as `[MSG]@pid (...)`;
  extract them from the serial log (helper scripts not included).
- In client mode `most` gets the *network* registry and comm state from the Jacinto as internal MSS
  messages over **NAL-SIPC (5555, ioc_sim)**, not over DSI: FBlock 0x02, inst 0, op 0xC,
  tag 0xF0000000, **src 0x1000 (J5 MSS subnet), dst 0x2000 (OMAP subnet)**; fn 0xF00 payload
  `<HB 1, 1>` = MOST comm OK; fn 0xF02 payload `<H 2` + `(u16 device, u16 fblockKey)` pairs = RegSync
  (trace `MSS::RegSync RX: |0200 0500|...`). After that the HMI subscribes to vehicle FBlocks.
- Vehicle data = Notification.Set (fn 0x001, op 0, payload 01|dev BE|fkt BE) -> answer ack (fn 1
  Status, same payload) + property Status. Values/semantics from herrbimmer/IDEmu (cloned read-only to
  a local IDEmu checkout; docs/V850.md, idemu/most.py, idemu/data/hmi_property_defaults.json,
  hmi_most_map.json): Vehicle 05/0, Kombi E0/0, PowerMode D1/2 (0xC10 key bit, 0x430=3, 0x434=0x63),
  CTerminalStatus 05/0:0x21F first byte 12 = KL15 enables My Vehicle items (verified by IDEmu).
- RESULT (full OTF boot, everything automatic): HMI log `CDevCarPowerMode::onPxyPowerState power mode
  change: PM unknown -> PM_fullon_useron`, `ePowerMode=3, bKeyInCar=1 => bMenuEnabled=1`; main menu
  titles turn white; first popup is CEntNoWarningTonesActivity ("Note", close with back); My Vehicle
  opens with "Vehicle settings" -> "Lighting". (The earlier black frame was that popup after a
  hot-reload mid-session.)
- Open: lists show only their first row (rendering/asset gap? stage-psdz-hmi stages a subset of
  data/ro; IDEmu notes say some items stay grey without more FBlocks), Kombi/Vehicle props without
  values (logged by ioc_sim as "no value for ..."), E5/1 C30 Sets from the HMI unanswered.

## Vehicle values (2026-11-10)
- The HMI repeats a Notification.Set until it receives the property's Status (not just the ack);
  serving a value stops the retries. rules.py starts a per-session ticker thread (calls the newest
  hot-reloaded module) that pushes LIVE values every TICK s and PUSH_ONCE values when they change.
- Payload layouts come from HmiMain3D 006: vtable slot 6 of `CPxy<Group>::<Property>` is the
  deserializer; reader helpers 0x1f91e70 u8(min,max), 0x1f923b8 u16, 0x1f922c4 u32
  (hmi_layouts.py records the read sequence per class).
- Verified on screen:
  - Kombi E0/0:509 CBordcomputerAverage: Onboard info shows B = avg speed, D = avg consumption
    (0.1 units); the main-menu My Vehicle tile reads C / E.
  - Vehicle 05/0:C7A CVehicleDynamicEngineScaling: byte0 = torque scale index, byte1 = power
    scale index, full scale = 80*(index+1); C7B CVehicleDynamicEngine = power %, torque % of full
    scale. Sport displays (My Vehicle > Technology in action) need the hand-written
    id5_sport_instruments shaders (bimmulator b45ee7b).
- TPM investigation (2026-11-10): live probes (rules.py PROBE_FILE $IDRIVE_HOME/probe.json) of
  CTyresStatus 05/0:C01 (members +0x78 u8, +0x7c u8<=15, +0x80/+0x84/+0x88 u8) byte0 0..7 and
  CTyreState C18 (all 9 bytes 1..5) did not change the "malfunction" text. CDevCarTpmStatusImpl
  (HmiMain3D ~0xd01000-0xd04800) reads them through CPxyVehicle accessors (calls into
  0x2264954-0x22662e0); it also gates on "vehicle state concept" coding, Clamp15 / PWF status
  and CarSpeed2 (vehicle standing). Next: decode those accessors and the activity's status map.
- Not yet right: TPM shows "malfunction" (CTyresStatus C01 / CTyreState C18 semantics unknown),
  Onboard info "0 km" is not CRangeTankStatus 512, oil temp scaling (assumed +48) not seen on screen.

## Next steps
- Visibility: get the `most` trace (HB trace -> /dev/mv2trace; trace-recorder-app -> 127.0.0.1:851;
  TRACE packages are STOP in starter) or patch CHBTraceHelper::sendToConsole (class check at
  libsys_trace_clienttrace!0x113bc) and restart `most` from autostart.sh with stdout on ser1.
- Then: find the state the client waits for before forwarding RegisterDevCtrls / using registry
  (NWMS state machine: "NWMS::changeToStateOn", "onConfigOKMsg nwmDevId").

## Plan (original)
1. Guest bridge (QNX C, built like bimmulator's build-qnx-wsl-fetch.sh): dlopen
   libsys_dsi_base, DSIServerInit("DSYSMOSTServer", "MOSTSubSystemServer"), forward every
   request (type, id, raw payload) over TCP to the host; host sends back responses /
   notifications as (kind, id, raw payload).
2. Host (Python): implement DSYSMOSTServer: accept registrations, answer responseMOSTClient,
   publish informationRegistry (OMAP devices + simulated vehicle FBlocks), route ProcessMessage.
3. Start with logging to learn payload layouts, then serve power mode / vehicle FBlocks.

## Tools
elfsyms.py (ELF symbols/offsets, included), capstone-based disassembly, ioc_sim.py (NAL-SIPC 5555
logger). Firmware binaries come from your own staged rootfs.

## 2026-11-10 night findings
- TPM OK (verified on screen): CTyresStatus 05/0:C01 = 00, counter (must change < 17.5 s), A0
  (RDC active), 80 (no loss), 00; CTyreState C18 = FE + 11 x 00; CTyrePressure C02 = bar x 10.
  Full analysis: TPM-RE.md.
- Clock: Kombi CShowTimeDate E0/0:0x515 = u16 0, status 1 (valid), h, m, s, day, weekday (1=Mon),
  month, u16 year. Pushed once a minute. Also fills the Communication tile with the date.
- hmi_neutral.py: empty lists (header 0 count -> element readers skipped), s8 0x1f91de0, enum
  0x1f91ae8, readUByte 0x258df8, "C" prefix fallback, any-instance FBlock fallback: 59 of 99
  previously unanswered subscriptions now answered. NO_NEUTRAL: Kombi CTimer 0x506, hybrid ECOTip.
- The HMI restores its last screen at boot: a "Uyari - Akustik uyari yok" (audio settings, empty
  warning-tone list) page reappeared after reboots; leave it with MENU.
- rules.py is hot-reloaded by ioc_sim.py when the file changes.
  _SESSION_START survives hot reloads now (a reload used to restart the welcome phase).
- diag_sim.py: HSFZ 6801 gateway simulator for the OEM+ apps (car capture replay, DTCs, clear,
  MHD echoes, OBD 0C/0D/42, `touch $IDRIVE_HOME/dragsim` = simulated full-throttle run).
