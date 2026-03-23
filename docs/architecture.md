# Arquitetura detalhada

## Camadas do sistema

### Camada A — Percepção
Executada em Python no computador host.

Responsabilidades:
- captura da região de interesse;
- segmentação de cor;
- extração de coordenadas;
- geração dos deltas.

### Camada B — Transporte
Executada pela interface HID/RawHID entre o host e o Arduino Leonardo R3.

Responsabilidades:
- empacotar;
- transmitir;
- receber;
- remontar o bloco de 64 bytes.

### Camada C — Consolidação embarcada
Executada no Arduino Leonardo R3.

Responsabilidades:
- combinar múltiplas fontes de entrada;
- preservar frações;
- aplicar polling periódico;
- emitir HID final ao host.

## Topologia física

```text
PC Host
 ├─ USB nativa para Arduino Leonardo R3
 └─ aplicação Python + DXCam + OpenCV

Arduino Leonardo R3
 ├─ USB device nativo (ATmega32U4)
 └─ USB Host Shield

USB Host Shield
 └─ dispositivo HID USB externo
```

## Racional de projeto

### FOV pequeno
Minimiza custo de processamento.

### Máscara circular
Reduz ruído espacial.

### Seleção do pixel mais alto
Fornece uma referência geométrica simples e de baixo custo.

### Acumuladores fracionários
Preservam resolução efetiva.

### Polling fixo no firmware
Transforma entradas assíncronas em saída periódica controlada.

### Watchdog + recuperação USB
Aumentam robustez em cenários reais de desconexão e falha temporária.
