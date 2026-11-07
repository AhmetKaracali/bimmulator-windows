/* BO03 GSS 007_003_005 KSS replay. Loaded only into temporary guest RAM. */
.equ KSS_MANAGER_LUN, 7
.equ IPC_SEND_CONTINUE, 0x800d9180
.equ IPC_PARSE_RX, 0x800d9a18
.equ PDU_RECEIVE, 0x80065670
.equ HUD_INITIALIZATION_FINISHED, 0x8021e260
.equ HUD_TEST_IMAGE, 0x800a27b8
.equ HUD_STATUS, 0x8021a560
.equ HMI_SCHEDULER_PROCESS, 0x8012cba0
.equ GSS_MANAGER_STATE, 0x804a8b44
.equ RPM_MAILBOX, 0xa1000800
.equ SPEED_MAILBOX, 0xa1000808
.equ HUD_STATUS_SEEN, 0xa1000810
.equ ENGINE_RPM_PDU, 0x92
.equ SPEEDOMETER_PDU, 0x8a
.equ HUD_SPEED_PDU, 0x15

.macro load_address reg, addr
    lui \reg, %hi(\addr)
    daddiu \reg, \reg, %lo(\addr)
.endm

.set noreorder
.set noat
.text
entry:
    addiu $8, $zero, KSS_MANAGER_LUN
    beq $a0, $8, kss
    nop
    /* Resume ipcSendReq for all other LUNs, restoring its second instruction. */
    load_address $25, IPC_SEND_CONTINUE
    jr $25
    lw $v1, -0x7714($v1)
kss:
    daddiu $sp, $sp, -96
    sw $a1, 76($sp)
    sd $ra, 88($sp)
    /* Reply to the GSS started, RTE version, RTE ready and HCC ready messages. */
    move $8, $a1
    addiu $9, $zero, 1
    beq $8, $9, started
    addiu $9, $zero, 0x14
    beq $8, $9, version
    addiu $9, $zero, 0x16
    beq $8, $9, ready
    addiu $9, $zero, 4
    bne $8, $9, done
    nop
    addiu $10, $zero, 0x92
    b receive
    move $11, $zero
started:
    addiu $10, $zero, 0x8b
    b receive
    move $11, $zero
version:
    addiu $10, $zero, 0x95
    b receive
    addiu $11, $zero, 1
ready:
    addiu $10, $zero, 0x8a
    move $11, $zero
receive:
    /* RX block length, message length, LUN, final-fragment CID, payload. */
    addiu $8, $zero, 4
    sb $8, 32($sp)
    addiu $8, $zero, 1
    sb $8, 33($sp)
    addiu $8, $zero, KSS_MANAGER_LUN
    sb $8, 34($sp)
    sb $10, 35($sp)
    sb $11, 36($sp)
    load_address $25, IPC_PARSE_RX
    jalr $25
    addiu $a0, $sp, 32
    lw $8, 76($sp)
    addiu $9, $zero, 4
    bne $8, $9, done
    nop
    load_address $25, PDU_RECEIVE
    /* Blk3008 region coding, with zero error flags after the payload. */
    addiu $a0, $zero, 0xb3
    addiu $a1, $sp, 32
    addiu $a2, $zero, 2
    addiu $8, $zero, 1
    sw $8, 32($sp)
    jalr $25
    nop
    /* Blk3003 equipment coding, HUD present. */
    sd $zero, 32($sp)
    sd $zero, 40($sp)
    sd $zero, 48($sp)
    sd $zero, 56($sp)
    sd $zero, 64($sp)
    sw $zero, 72($sp)
    addiu $8, $zero, 2
    sb $8, 37($sp)
    load_address $25, PDU_RECEIVE
    addiu $a0, $zero, 0xb0
    addiu $a1, $sp, 32
    jalr $25
    addiu $a2, $zero, 26
    /* Blk300B parameter coding, HUD sideband over APIX. */
    sb $zero, 37($sp)
    addiu $8, $zero, 1
    sb $8, 72($sp)
    load_address $25, PDU_RECEIVE
    addiu $a0, $zero, 0xb5
    addiu $a1, $sp, 32
    jalr $25
    addiu $a2, $zero, 42
    load_address $25, PDU_RECEIVE
    /* Synthetic terminal-on state with a zero error byte. */
    addiu $a0, $zero, 2
    addiu $a1, $sp, 32
    addiu $a2, $zero, 1
    addiu $8, $zero, 0x001d
    sh $8, 32($sp)
    jalr $25
    nop
done:
    ld $ra, 88($sp)
    move $v0, $zero
    jr $ra
    daddiu $sp, $sp, 96

/* Call site 0x802170dc branches here after the HUD queue is available. */
.org 0x200
hud_initialized:
    b hud_start
    addiu $8, $zero, 1

.org 0x210
hud_live_initialized:
    move $8, $zero
hud_start:
    daddiu $sp, $sp, -48
    sd $ra, 40($sp)
    sw $8, 36($sp)
    load_address $25, HUD_INITIALIZATION_FINISHED
    jalr $25
    nop
    load_address $25, PDU_RECEIVE
    /* StartHUD with a zero error byte. */
    addiu $a0, $zero, 0x123
    addiu $a1, $sp, 32
    addiu $a2, $zero, 1
    addiu $8, $zero, 0xaa
    sh $8, 32($sp)
    jalr $25
    nop
    lw $8, 36($sp)
    beqz $8, hud_init_done
    nop
    /* Request the stock HUD startup image on the production test plane. */
    load_address $25, HUD_TEST_IMAGE
    jalr $25
    addiu $a0, $zero, 0xc5f
hud_init_done:
    ld $ra, 40($sp)
    jr $ra
    daddiu $sp, $sp, 48

/* Call site 0x8005d898 branches here before running the draw scheduler. */
.org 0x300
poll_vehicle:
    load_address $8, GSS_MANAGER_STATE
    lbu $9, 0($8)
    addiu $10, $zero, 5
    bne $9, $10, run_scheduler
    nop
    daddiu $sp, $sp, -56
    sd $ra, 48($sp)
    load_address $8, RPM_MAILBOX
    lw $9, 0($8)
    beqz $9, poll_speed
    lw $10, 4($8)
    beq $9, $10, poll_speed
    nop
    sw $9, 40($sp)
    /* The host stores one plus RPM in units of 10. Send the PDU and validity byte. */
    addiu $9, $9, -1
    srl $10, $9, 8
    sb $10, 32($sp)
    sb $9, 33($sp)
    sb $zero, 34($sp)
    load_address $25, PDU_RECEIVE
    addiu $a0, $zero, ENGINE_RPM_PDU
    addiu $a1, $sp, 32
    jalr $25
    addiu $a2, $zero, 2
    load_address $8, RPM_MAILBOX
    lw $9, 40($sp)
    sw $9, 4($8)
poll_speed:
    /* Wait for the HUD's stock startup status before injecting readiness. */
    load_address $8, HUD_STATUS_SEEN
    lw $9, 0($8)
    beqz $9, inputs_done
    nop
    load_address $8, SPEED_MAILBOX
    lw $9, 0($8)
    beqz $9, inputs_done
    lw $10, 4($8)
    beq $9, $10, inputs_done
    nop
    sw $9, 40($sp)
    bnez $10, send_speed
    nop
    /* Replay display-ready status and the driver's HUD selection. */
    load_address $25, HUD_STATUS
    jalr $25
    addiu $a0, $zero, 1
    load_address $25, PDU_RECEIVE
    addiu $a0, $zero, 0xf5
    addiu $a1, $sp, 32
    addiu $8, $zero, 0x40
    sw $8, 32($sp)
    jalr $25
    addiu $a2, $zero, 2
send_speed:
    lw $9, 40($sp)
    /* Both records carry deci-km/h. SpeedometerData adds a qualifier. */
    addiu $9, $9, -1
    srl $10, $9, 8
    sb $10, 32($sp)
    sb $9, 33($sp)
    sh $zero, 34($sp)
    load_address $25, PDU_RECEIVE
    addiu $a0, $zero, SPEEDOMETER_PDU
    addiu $a1, $sp, 32
    jalr $25
    addiu $a2, $zero, 3
    load_address $25, PDU_RECEIVE
    addiu $a0, $zero, HUD_SPEED_PDU
    addiu $a1, $sp, 32
    jalr $25
    addiu $a2, $zero, 2
    load_address $8, SPEED_MAILBOX
    lw $9, 40($sp)
    sw $9, 4($8)
inputs_done:
    ld $ra, 48($sp)
    daddiu $sp, $sp, 56
run_scheduler:
    load_address $25, HMI_SCHEDULER_PROCESS
    jr $25
    nop

/* Call site 0x8021d200 publishes the HUD manager's initial status. */
.org 0x480
hud_startup_status:
    daddiu $sp, $sp, -40
    sd $ra, 32($sp)
    load_address $25, HUD_STATUS
    jalr $25
    nop
    load_address $8, HUD_STATUS_SEEN
    addiu $9, $zero, 1
    sw $9, 0($8)
    ld $ra, 32($sp)
    jr $ra
    daddiu $sp, $sp, 40
