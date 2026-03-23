#include "ImprovedMouse.h"

// Descritor de 16 bits COM Report ID (para a biblioteca funcionar)
static const uint8_t _hidMultiReportDescriptorMouse[] PROGMEM = {
    0x05, 0x01,                    // USAGE_PAGE (Generic Desktop)
    0x09, 0x02,                    // USAGE (Mouse)
    0xA1, 0x01,                    // COLLECTION (Application)
    0x85, 0x01,                    //   REPORT_ID (1) <--- VOLTOU AQUI PARA O WINDOWS ACEITAR O PACOTE
    0x09, 0x01,                    //   USAGE (Pointer)
    0xA1, 0x00,                    //   COLLECTION (Physical)
    
    // --- BOTÕES (5 bits + 3 bits padding) ---
    0x05, 0x09,                    //     USAGE_PAGE (Button)
    0x15, 0x00,                    //     LOGICAL_MINIMUM (0)
    0x25, 0x01,                    //     LOGICAL_MAXIMUM (1)
    0x19, 0x01,                    //     USAGE_MINIMUM (Button 1)
    0x29, 0x05,                    //     USAGE_MAXIMUM (Button 5)
    0x75, 0x01,                    //     REPORT_SIZE (1)
    0x95, 0x05,                    //     REPORT_COUNT (5)
    0x81, 0x02,                    //     INPUT (Data,Var,Abs)
    0x95, 0x03,                    //     REPORT_COUNT (3)
    0x81, 0x01,                    //     INPUT (Cnst,Ary,Abs)
    
    // --- EIXOS X e Y (16 bits cada) ---
    0x05, 0x01,                    //     USAGE_PAGE (Generic Desktop)
    0x16, 0x01, 0x80,              //     LOGICAL_MINIMUM (-32767)
    0x26, 0xFF, 0x7F,              //     LOGICAL_MAXIMUM (32767)
    0x09, 0x30,                    //     USAGE (X)
    0x09, 0x31,                    //     USAGE (Y)
    0x75, 0x10,                    //     REPORT_SIZE (16)
    0x95, 0x02,                    //     REPORT_COUNT (2)
    0x81, 0x06,                    //     INPUT (Data,Var,Rel)
    
    // --- WHEEL (Vertical Scroll - 8 bits) ---
    0x15, 0x81,                    //     LOGICAL_MINIMUM (-127)
    0x25, 0x7F,                    //     LOGICAL_MAXIMUM (127)
    0x09, 0x38,                    //     USAGE (Wheel)
    0x75, 0x08,                    //     REPORT_SIZE (8)
    0x95, 0x01,                    //     REPORT_COUNT (1)
    0x81, 0x06,                    //     INPUT (Data,Var,Rel)
    
    // --- AC PAN (Horizontal Scroll - 8 bits) ---
    0x05, 0x0C,                    //     USAGE_PAGE (Consumer Devices)
    0x0A, 0x38, 0x02,              //     USAGE (AC Pan)
    0x95, 0x01,                    //     REPORT_COUNT (1)
    0x81, 0x06,                    //     INPUT (Data,Var,Rel)
    
    0xC0,                          //   END_COLLECTION (Physical)
    0xC0                           // END_COLLECTION (Application)
};

Mouse_::Mouse_(void) : _buttons(0)
{
    static HIDSubDescriptor node(_hidMultiReportDescriptorMouse, sizeof(_hidMultiReportDescriptorMouse));
    HID().AppendDescriptor(&node);
}

void Mouse_::begin(void) { }
void Mouse_::end(void) { }

void Mouse_::click(uint8_t b) {
    _buttons = b;
    move(0, 0, 0);
    _buttons = 0;
    move(0, 0, 0);
}

void Mouse_::move(int16_t x, int16_t y, signed char wheel) {
    uint8_t m[7];
    m[0] = _buttons;         
    m[1] = x & 0xFF;         
    m[2] = (x >> 8) & 0xFF;  
    m[3] = y & 0xFF;         
    m[4] = (y >> 8) & 0xFF;  
    m[5] = (uint8_t)wheel;   
    m[6] = 0;                
    
    // Agora o Windows sabe que o Arduino vai mandar o ID 1 na frente!
    HID().SendReport(1, m, 7);
}

void Mouse_::buttons(uint8_t b) {
    if (b != _buttons) {
        _buttons = b;
        move(0, 0, 0);
    }
}

void Mouse_::press(uint8_t b) {
    buttons(_buttons | b);
}

void Mouse_::release(uint8_t b) {
    buttons(_buttons & ~b);
}

bool Mouse_::isPressed(uint8_t b) {
    return ((b & _buttons) > 0);
}

void Mouse_::SendReport(void* data, int length)
{
    HID().SendReport(1, data, length);
}

Mouse_ Mouse;