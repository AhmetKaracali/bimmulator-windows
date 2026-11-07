/*
 * CPU-rendered development fallback for the recovered F32 iDrive 6 runtime.
 * This uses QNX Screen's software window path; it is not BMW's HmiMain3D.
 */
typedef unsigned int uint32_t;
extern int screen_create_context(void **, int);
extern int screen_create_window(void **, void *);
extern int screen_set_window_property_iv(void *, int, const int *);
extern int screen_create_window_buffers(void *, int);
extern int screen_get_window_property_pv(void *, int, void **);
extern int screen_get_buffer_property_pv(void *, int, void **);
extern int screen_get_buffer_property_iv(void *, int, int *);
extern int screen_post_window(void *, void *, int, const int *, int);
extern int puts(const char *);
extern unsigned sleep(unsigned);
extern void _exit(int);

enum {
    PROP_BUFFER_SIZE=5, PROP_POINTER=34,
    PROP_RENDER_BUFFERS=37, PROP_SIZE=40,
    PROP_STRIDE=44, PROP_USAGE=48, PROP_VISIBLE=51, PROP_ZORDER=54,
    USAGE_READ_WRITE=6,
    WIDTH=1280, HEIGHT=480
};
static uint32_t *frame;
static int frame_stride;
static uint32_t rgb(unsigned r,unsigned g,unsigned b)
{ return 0xff000000u|((r&255u)<<16)|((g&255u)<<8)|(b&255u); }
static void fill(int x,int y,int w,int h,uint32_t c)
{
    if(x<0){w+=x;x=0;} if(y<0){h+=y;y=0;}
    if(x+w>WIDTH)w=WIDTH-x; if(y+h>HEIGHT)h=HEIGHT-y;
    for(int yy=y;yy<y+h;yy++){
        uint32_t *p=(uint32_t*)((char*)frame+yy*frame_stride)+x;
        for(int xx=0;xx<w;xx++)p[xx]=c;
    }
}
static void line(int x0,int y0,int x1,int y1,uint32_t c)
{
    int dx=x1>x0?x1-x0:x0-x1,sx=x0<x1?1:-1;
    int dy=y1>y0?y0-y1:y1-y0,sy=y0<y1?1:-1,e=dx+dy;
    for(;;){
        if(x0>=0&&x0<WIDTH&&y0>=0&&y0<HEIGHT)
            *(uint32_t*)((char*)frame+y0*frame_stride+x0*4)=c;
        if(x0==x1&&y0==y1)break;
        int e2=2*e;if(e2>=dy){e+=dy;x0+=sx;}if(e2<=dx){e+=dx;y0+=sy;}
    }
}
static void border(int x,int y,int w,int h,uint32_t c)
{ line(x,y,x+w-1,y,c);line(x,y+h-1,x+w-1,y+h-1,c);
  line(x,y,x,y+h-1,c);line(x+w-1,y,x+w-1,y+h-1,c); }
/* Five 5-bit rows for digits and uppercase letters. */
static const unsigned char font[36][5]={
 {14,17,19,21,14},{4,12,4,4,14},{14,17,2,4,31},{30,1,6,1,30},
 {2,6,10,31,2},{31,16,30,1,30},{6,8,30,17,14},{31,1,2,4,4},
 {14,17,14,17,14},{14,17,15,1,6},
 {14,17,31,17,17},{30,17,30,17,30},{14,17,16,17,14},
 {30,17,17,17,30},{31,16,30,16,31},{31,16,30,16,16},
 {14,17,23,17,15},{17,17,31,17,17},{14,4,4,4,14},
 {7,2,2,18,12},{17,18,28,18,17},{16,16,16,16,31},
 {17,27,21,17,17},{17,25,21,19,17},{14,17,17,17,14},
 {30,17,30,16,16},{14,17,21,18,13},{30,17,30,18,17},
 {15,16,14,1,30},{31,4,4,4,4},{17,17,17,17,14},
 {17,17,17,10,4},{17,17,21,27,17},{17,10,4,10,17},
 {17,10,4,4,4},{31,2,4,8,31}
};
static void text(int x,int y,int scale,uint32_t c,const char *s)
{
    for(;*s;s++,x+=scale*6){
        char ch=*s;if(ch>='a'&&ch<='z')ch-=32;
        int n=ch>='0'&&ch<='9'?ch-'0':ch>='A'&&ch<='Z'?10+ch-'A':-1;
        if(n>=0){for(int yy=0;yy<5;yy++)for(int xx=0;xx<5;xx++)
            if(font[n][yy]&(1<<(4-xx)))fill(x+xx*scale,y+yy*scale,scale,scale,c);}
        else if(ch=='-')fill(x,y+2*scale,4*scale,scale,c);
        else if(ch==':'){fill(x+2*scale,y+scale,scale,scale,c);fill(x+2*scale,y+4*scale,scale,scale,c);}
    }
}
static void icon(int cx,int cy,int type,uint32_t c)
{
    if(type==0){ /* media */
        fill(cx-24,cy-8,12,16,c);line(cx-12,cy-8,cx+3,cy-21,c);
        line(cx-12,cy+8,cx+3,cy+21,c);line(cx+3,cy-21,cx+3,cy+21,c);
        line(cx+12,cy-12,cx+23,cy,c);line(cx+23,cy,cx+12,cy+12,c);
    }else if(type==1){ /* phone */
        line(cx-20,cy-21,cx-8,cy-9,c);line(cx-8,cy-9,cx-2,cy-15,c);
        line(cx-2,cy-15,cx+15,cy+2,c);line(cx+15,cy+2,cx+9,cy+8,c);
        line(cx+9,cy+8,cx+20,cy+19,c);line(cx+20,cy+19,cx+12,cy+25,c);
        line(cx+12,cy+25,cx-8,cy+14,c);line(cx-8,cy+14,cx-20,cy-4,c);
        line(cx-20,cy-4,cx-20,cy-21,c);
    }else if(type==2){ /* navigation */
        line(cx-26,cy-24,cx-8,cy-30,c);line(cx-8,cy-30,cx+10,cy-22,c);
        line(cx+10,cy-22,cx+27,cy-28,c);line(cx-26,cy-24,cx-26,cy+23,c);
        line(cx-8,cy-30,cx-8,cy+18,c);line(cx+10,cy-22,cx+10,cy+27,c);
        line(cx+27,cy-28,cx+27,cy+20,c);line(cx-26,cy+23,cx-8,cy+18,c);
        line(cx-8,cy+18,cx+10,cy+27,c);line(cx+10,cy+27,cx+27,cy+20,c);
        line(cx-19,cy+10,cx-8,cy+1,rgb(67,181,231));
        line(cx-8,cy+1,cx+2,cy+8,rgb(67,181,231));line(cx+2,cy+8,cx+18,cy-9,rgb(67,181,231));
    }else if(type==3){ /* connected services */
        line(cx-22,cy+11,cx-8,cy-4,c);line(cx-8,cy-4,cx,cy-13,c);
        line(cx,cy-13,cx+9,cy-13,c);line(cx+9,cy-13,cx+22,cy,c);
        line(cx+22,cy,cx+22,cy+9,c);line(cx+22,cy+9,cx+7,cy+24,c);
        line(cx+7,cy+24,cx-3,cy+24,c);line(cx-3,cy+24,cx-15,cy+12,c);
        line(cx-15,cy+12,cx-15,cy+2,c);line(cx-15,cy+2,cx-8,cy-4,c);
        line(cx-7,cy+8,cx+8,cy-7,c);
    }else{ /* coupe silhouette */
        line(cx-39,cy+9,cx-28,cy-2,c);line(cx-28,cy-2,cx-17,cy-20,c);
        line(cx-17,cy-20,cx+18,cy-20,c);line(cx+18,cy-20,cx+33,cy+1,c);
        line(cx+33,cy+1,cx+41,cy+8,c);line(cx+41,cy+8,cx+41,cy+19,c);
        line(cx+41,cy+19,cx-39,cy+19,c);line(cx-39,cy+19,cx-39,cy+9,c);
        line(cx-12,cy-17,cx-4,cy-3,c);line(cx-4,cy-3,cx+24,cy-3,c);
        line(cx+24,cy-3,cx+16,cy-17,c);
        fill(cx-26,cy+14,12,12,rgb(7,10,15));fill(cx+20,cy+14,12,12,rgb(7,10,15));
        border(cx-26,cy+14,12,12,c);border(cx+20,cy+14,12,12,c);
    }
}
static void tile(int x,const char *title,const char *detail,int type,int selected)
{
    const int y=112,w=232,h=282;uint32_t accent=rgb(83,177,224);
    fill(x,y,w,h,rgb(25,34,45));fill(x+2,y+2,w-4,152,rgb(21,33,45));
    for(int yy=0;yy<150;yy++){int v=22+yy/12;fill(x+2,y+2+yy,w-4,1,rgb(v,v+9,v+17));}
    icon(x+w/2,y+76,type,selected?rgb(232,245,252):rgb(168,199,216));
    text(x+16,y+177,2,rgb(246,248,250),title);
    text(x+16,y+224,1,rgb(177,190,201),detail);
    border(x,y,w,h,selected?accent:rgb(57,72,86));
    if(selected)fill(x,y+h-4,w,4,accent);
}
static void draw_home(void)
{
    for(int y=0;y<HEIGHT;y++){int v=8+y*12/HEIGHT;fill(0,y,WIDTH,1,rgb(v,v+7,v+14));}
    fill(0,0,WIDTH,50,rgb(7,12,18));fill(0,48,WIDTH,2,rgb(56,146,194));
    text(28,16,2,rgb(241,245,248),"IDRIVE 6 DEVELOPMENT");
    text(930,18,2,rgb(214,226,234),"11:24 LTE BT");
    text(32,77,1,rgb(120,179,210),"F32 COUPE  NBTEVO X20511I");
    text(1000,77,1,rgb(155,170,182),"SOFTWARE DISPLAY PREVIEW");
    tile(38,"MEDIA","NO DEVICE CONNECTED",0,1);
    tile(290,"COMM","PHONE NOT CONNECTED",1,0);
    tile(542,"NAVIGATION","MAP DATA NOT LOADED",2,0);
    tile(794,"CONNECTED DRIVE","OFFLINE IN EMULATOR",3,0);
    tile(1046,"MY VEHICLE","BMW 440I COUPE",4,0);
    fill(0,420,WIDTH,60,rgb(7,11,16));fill(0,420,WIDTH,1,rgb(52,67,80));
    text(40,439,1,rgb(152,167,179),"MENU");text(156,439,1,rgb(152,167,179),"MEDIA");
    text(280,439,1,rgb(152,167,179),"RADIO");text(402,439,1,rgb(152,167,179),"PHONE");
    text(530,439,1,rgb(152,167,179),"NAV");
    text(640,439,1,rgb(103,178,218),"F32 PREVIEW  NATIVE HMI EGL UNAVAILABLE");
}
void _start(void)
{
    void *ctx=0,*win=0,*buf=0,*pixels=0;int size[2]={WIDTH,HEIGHT};
    int damage[4]={0,0,WIDTH,HEIGHT},usage=USAGE_READ_WRITE,visible=1,zorder=1000;
    if(screen_create_context(&ctx,0)||screen_create_window(&win,ctx)){
        puts("iDrive Screen preview: window creation failed");_exit(1);}
    if(screen_set_window_property_iv(win,PROP_USAGE,&usage)||
       screen_set_window_property_iv(win,PROP_BUFFER_SIZE,size)||
       screen_set_window_property_iv(win,PROP_SIZE,size)||
       screen_set_window_property_iv(win,PROP_ZORDER,&zorder)||
       screen_set_window_property_iv(win,PROP_VISIBLE,&visible)||
       screen_create_window_buffers(win,1)){
        puts("iDrive Screen preview: buffer setup failed");_exit(2);}
    if(screen_get_window_property_pv(win,PROP_RENDER_BUFFERS,&buf)||
       screen_get_buffer_property_pv(buf,PROP_POINTER,&pixels)||
       screen_get_buffer_property_iv(buf,PROP_STRIDE,&frame_stride)||
       !pixels||frame_stride<WIDTH*4){
        puts("iDrive Screen preview: buffer mapping failed");_exit(3);}
    frame=(uint32_t*)pixels;draw_home();
    if(screen_post_window(win,buf,1,damage,0)){
        puts("iDrive Screen preview: post failed");_exit(4);}
    puts("Displayed CPU-rendered F32 iDrive 6 development preview.");
    for(;;)sleep(36000);
}
