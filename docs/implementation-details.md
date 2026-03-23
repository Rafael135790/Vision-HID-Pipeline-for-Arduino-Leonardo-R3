# Detalhes de implementação

## Python

### Enumeração HID
A conexão é feita por VID, PID e interface number, evitando depender apenas de nome de dispositivo.

### Watchdog de frame
O pipeline observa mudança real de timestamp, não apenas existência de frame.

### Acumuladores float
Permitem saída discreta sem desperdiçar deltas subinteiros.

## Firmware

### Acumuladores separados
`deltaMouse` e `deltaPy` são mantidos separadamente para rastreabilidade e controle de fluxo.

### Polling periódico
A drenagem a cada ~1 ms melhora previsibilidade temporal.

### Watchdog do MCU
Garante recuperação em caso de travamento lógico.

### USB host recovery
Permite retomar operação após estados degradados do barramento.

## Core USB

### CDC desativado
Remove a serial virtual, simplificando a composição do dispositivo.

### Endpoint customizado
Permite configuração mais compatível com o comportamento desejado.

### Descriptor ajustado
Evita apresentar o dispositivo com uma classe inadequada quando CDC está desativado.
