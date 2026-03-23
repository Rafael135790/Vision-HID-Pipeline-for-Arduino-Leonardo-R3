# Notas sobre o Arduino Leonardo R3

## Por que usar o Leonardo R3

O Arduino Leonardo R3 é baseado no ATmega32U4, que possui USB nativo.
Isso o torna muito mais adequado para aplicações HID customizadas do que placas que dependem de um chip USB-serial separado.

## Papel no projeto

No projeto, o Leonardo R3 não é um simples periférico de execução.
Ele é um componente central da arquitetura:

- recebe pacotes RawHID;
- processa input do USB Host Shield;
- agrega múltiplas entradas;
- emite HID ao host.

## Consequência para o desenvolvimento

Como a USB é nativa, o comportamento final depende de:
- sketch;
- bibliotecas HID;
- core USB;
- descriptors;
- endpoints.

Ou seja, ajustes no core fazem parte do projeto e não são apenas detalhes secundários.

## Cuidados

Mudanças no core USB podem:
- quebrar compatibilidade com updates da IDE;
- exigir recompilação e testes adicionais;
- alterar enumeração do dispositivo no sistema operacional.
