#ifndef IDRIVE6_ANGLE_FRAME_RPC_H
#define IDRIVE6_ANGLE_FRAME_RPC_H

#define IDRIVE_ANGLE_RPC_PORT 41416u
#define IDRIVE_ANGLE_RPC_REQUEST_SIZE 24u
#define IDRIVE_ANGLE_RPC_RESPONSE_SIZE 20u
#define IDRIVE_ANGLE_RPC_MAX_WIDTH 1440u
#define IDRIVE_ANGLE_RPC_MAX_HEIGHT 540u
#define IDRIVE_ANGLE_RPC_MAX_BYTES \
    (IDRIVE_ANGLE_RPC_MAX_WIDTH * IDRIVE_ANGLE_RPC_MAX_HEIGHT * 4u)

static inline unsigned int idrive_rpc_get_u16(const unsigned char *p)
{
    return ((unsigned int)p[0] << 8) | p[1];
}

static inline unsigned int idrive_rpc_get_u32(const unsigned char *p)
{
    return ((unsigned int)p[0] << 24) | ((unsigned int)p[1] << 16) |
           ((unsigned int)p[2] << 8) | (unsigned int)p[3];
}

static inline void idrive_rpc_put_u16(unsigned char *p, unsigned int value)
{
    p[0] = (unsigned char)(value >> 8);
    p[1] = (unsigned char)value;
}

static inline void idrive_rpc_put_u32(unsigned char *p, unsigned int value)
{
    p[0] = (unsigned char)(value >> 24);
    p[1] = (unsigned char)(value >> 16);
    p[2] = (unsigned char)(value >> 8);
    p[3] = (unsigned char)value;
}

#endif
