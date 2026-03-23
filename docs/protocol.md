# Protocolo de transporte RawHID

## Estrutura lógica

O protocolo usa um bloco fixo de 64 bytes.

### Layout conceitual

- Byte 0: reservado / report id
- Byte 1: delta X
- Byte 2: delta Y
- Byte 3: wheel ou reservado
- Byte 4..63: preenchimento

## Vantagens

- parsing simples;
- framing previsível;
- implementação barata no firmware;
- depuração fácil;
- baixo overhead conceitual.

## Recepção

No Leonardo R3, os bytes são lidos um a um da fila RawHID e acumulados até que `rawFill == 64`.

Após isso:
- o pacote é interpretado;
- os deltas são incorporados aos acumuladores;
- o buffer é zerado para o próximo ciclo.

## Timeout de pacote parcial

Se bytes começam a chegar, mas o pacote não é concluído dentro da janela esperada, o preenchimento parcial é descartado.

Isso evita:
- desalinhamento;
- uso de dados incompletos;
- persistência de lixo no buffer.
