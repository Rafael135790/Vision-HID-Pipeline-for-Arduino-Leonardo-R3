#ifndef IMPROVED_MOUSE_H
#define IMPROVED_MOUSE_H

#include <Arduino.h>
#include "HID.h"

// Definições de botões compatíveis com o seu descritor de 5 botões
#define MOUSE_LEFT    (1 << 0)
#define MOUSE_RIGHT   (1 << 1)
#define MOUSE_MIDDLE  (1 << 2)
#define MOUSE_PREV    (1 << 3)
#define MOUSE_NEXT    (1 << 4)
#define MOUSE_ALL     (MOUSE_LEFT | MOUSE_RIGHT | MOUSE_MIDDLE | MOUSE_PREV | MOUSE_NEXT)

class Mouse_ {
protected:
    uint8_t _buttons; // Aqui é onde o erro "_buttons does not have any field" morre

public:
    Mouse_(void);
    void begin(void);
    void end(void);
    
    // Mudamos para int16_t para aceitar a alta resolução do seu mouse real
    void move(int16_t x, int16_t y, signed char wheel = 0);
    
    void click(uint8_t b = MOUSE_LEFT);
    void buttons(uint8_t b);
    void press(uint8_t b = MOUSE_LEFT);
    void release(uint8_t b = MOUSE_LEFT);
    bool isPressed(uint8_t b = MOUSE_LEFT);

    // Função para enviar o report de 7 bytes
    void SendReport(void* data, int length);
};

extern Mouse_ Mouse;

#endif