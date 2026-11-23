---
name: criar-explainer-3d
description: Criar animações explicativas verticais em Blender a partir de tema, roteiro, nicho ou vídeo de referência. Usar para produzir Reels e Shorts narrados em português com personagens low-poly, metáforas físicas, sistemas construídos peça a peça ou trajetórias, com câmera em perspectiva, geografia de cena, animação de ações em sequência, locução, legendas por palavra e MP4. Inclui comparação temporal com um Reel de referência e entrega de cena .blend editável.
---

# Criar um explainer 3D

Converter uma ideia em uma mudança que se possa filmar. Entregar o estudo de referência, roteiro, prévia ou vídeo pronto que a pessoa solicitou. Para um pedido de produção com terminal e ferramentas disponíveis, executar o render, montar o MP4 e abrir o arquivo resultante.

**Reproduzir o exemplo principal** com `python3 scripts/produzir.py --exemplo vila --saida minha-vila` na pasta da skill. A voz em português, os efeitos, a mão articulada e a textura de céu vêm no pacote. Ver [instalação e primeiro vídeo](references/primeiro-video.md).

## 1. Identificar o que dá identidade à referência

Quando a pessoa pedir “mais parecido com este Reel”, comparar o vídeo anterior e a referência em movimento **antes de escolher uma cena-base**. Fazer uma folha com cinco instantes correspondentes (abertura, entrada, contato, reação, consequência). Observar se o plano tem horizonte ou fundo de estúdio, perspectiva ou projeção ortográfica, personagem minúsculo ou em close, sombra dura ou difusa. Identificar o que realmente se desloca e em que ordem. Consultar [comparação de ritmo e quadros](references/medir-fidelidade.md).

- **Gancho de exterior com mudança de escala.** Usar [o plano da vila](references/vila.md) como exemplo de direção. Mostrar o mundo no primeiro quadro, introduzir o agente de mudança, animar os objetos em ondas e reenquadrar o efeito. Variar tema, geometria e ação de acordo com o pedido. Usar 24 quadros distintos por segundo e a lente de perspectiva na primeira prova.
- **História com diálogo.** Planejar o vídeo em sequências: apresentação do motivo visual, novo espaço, planos e contraplanos com personagens reconhecíveis e retorno ao motivo inicial. Usar as [receitas de direção](references/linguagem-visual.md) como ponto de partida. Uma história mais longa precisa de desenvolvimento próprio.
- **Demonstração técnica ou maquete pedida explicitamente.** Os exemplos fila, cisterna e eremita têm composição ortográfica e luz de estúdio. São pontos de partida úteis para explicar mecanismos.

## 2. Escolher uma história que se possa animar

- **Tema definido:** resumir a pergunta central, a pessoa que vai assistir e a consequência visível. Adotar 9:16 e português brasileiro quando o pedido estiver em português e não indicar outro formato. Para uma história nova, partir de 18–35 segundos, ajustando à voz e ao mecanismo.
- **Só um nicho:** propor três ideias, cada uma com pergunta, objeto em cena e transformação. Se a pessoa pediu a produção completa, escolher a mais fácil de demonstrar visualmente e produzir. Se pediu opções ou aprovação, parar no ponto indicado.
- **Referência em vídeo:** usar o arquivo anexado ou uma mídia pública acessível, rodar [análise de vídeo](references/analise.md) e examinar os quadros. Registrar quais segundos foram observados, áudio disponível, escala dos objetos, câmera, faixa da legenda e pelo menos uma relação de causa e efeito. Se o link abrir apenas um login, aproveitar o material público disponível. Pedir o MP4 específico quando a comparação depender dele.
- **Nenhuma referência fornecida:** partir das [quatro padrões visuais e três receitas de direção](references/linguagem-visual.md). Escolher entre um fenômeno em escala exagerada, um sistema montado em etapas, uma relação por personagens ou uma trajetória. Criar roteiro, modelos, vozes e cenas próprios.

## 3. Fechar o roteiro e o tempo

1. Escrever a locução como fala. Usar uma ação por frase, com um gancho que a imagem começa a responder imediatamente. Para afirmações verificáveis, conferir fontes adequadas ao assunto e mantê-las num arquivo no projeto. Representar cenários hipotéticos como tal.
2. Converter cada frase em uma linha de storyboard com início/fim, sujeito, estado inicial → ação → resultado, câmera e palavra-chave. Exemplo: “B fica livre” → o atendente de B acena ao lado do balcão vazio, enquanto duas pessoas ainda esperam em A. Conservar A e B no plano tempo suficiente para compará-los.
3. Gravar, importar ou sintetizar a voz; medir sua duração real e ajustar as batidas. Conferir nomes, siglas e pausas. Para experimentar uma nova fala, usar o contrato de [locução e montagem](references/montagem.md). Guardar vozes reais para as quais o projeto tem autorização.
4. Se o pedido incluir aprovação de roteiro ou voz, entregar esse material antes do render longo. Num pedido de vídeo pronto, continuar com as decisões usuais de produção.

## 4. Construir e dirigir a cena

- Para reaproveitar a direção exterior em um novo assunto, ativar `"look":"exterior"` em uma cena JSON genérica e configurar planos com `lens_mm`, `eye` e `target`. Criar o agente visual apropriado ao assunto. Usar [a cena principal](assets/vila.json) quando a geografia da rua ou o gesto de recolher objetos fizerem sentido.
- Copiar o exemplo mais próximo para uma pasta de projeto. Em [fila-unica.json](assets/fila-unica.json), estudar personagens com passos, acenos e mudança de fila. Em [cisterna.json](assets/cisterna.json), estudar peças que entram e o nível de água que sobe. Em [eremita.json](assets/eremita.json), acompanhar o mesmo animal antes, durante e depois de trocar de concha.
- Criar um novo JSON de cena e o JSON correspondente de falas e legendas. Usar o [contrato de cena](references/cena.md) e a [direção de câmera, ação e figurantes](references/direcao.md). Trocar a geometria e o mecanismo causal junto com o tema. Preservar a identidade visual do protagonista entre planos.
- Usar a câmera para apresentar espaço, revelar mudança ou mostrar consequência. Preparar o contato do objeto antes de cortar. Deixar o sujeito principal visível quando a legenda aparecer, começando a faixa de texto por volta de 74% da altura.
- Para um assunto que exija mais do que as peças do JSON, copiar o script Blender para o projeto e criar a geometria ou atuação necessária em Python. O arquivo .blend também aceita edição manual. Usar assets locais ou licenciados se forem mais apropriados e guardar as fontes.

## 5. Renderizar e entregar

Executar os comandos na raiz da skill, substituindo os caminhos. `--saida` deve identificar uma pasta nova por versão.

```sh
python3 scripts/produzir.py --cena projeto/cena.json --roteiro projeto/locucao.json --quadro 1 --saida projeto/quadro-teste
python3 scripts/produzir.py --cena projeto/cena.json --roteiro projeto/locucao.json --voz projeto/voz.wav --saida projeto/previa
python3 scripts/produzir.py --cena projeto/cena.json --roteiro projeto/locucao.json --voz projeto/voz.wav --qualidade final --saida projeto/entrega
```

Para uma voz de sistema instalada, trocar `--voz projeto/voz.wav` por `--tts`. Para uma revisão com legenda e sem locução, usar `--mudo`. Para usar a narração neural local com modelo próprio ou acrescentar efeitos sincronizados, consultar [montagem](references/montagem.md). Para renderizar cenas complexas, medir a duração de um quadro no equipamento antes de estimar o tempo de entrega.

Antes de finalizar um Reel baseado em referência, comparar o rascunho com o original nos cinco acontecimentos escolhidos. Se o cenário ocupar pouca tela, aproximar a câmera ou mudar a lente. Se a reação demorar, antecipar a animação do primeiro objeto. Se o movimento for difícil de ler, separar as saídas e conservar o pano de fundo por alguns quadros. Abrir o MP4 no tamanho de um celular. Assistir aos momentos de mudança com e sem som. Checar as legendas mais compridas, pausa final, cortes, pico de áudio e pronúncia. Confirmar duração, dimensões, fps e faixas pelo ffprobe. Corrigir a etapa que produziu o erro. Entregar final.mp4, cena.blend, legendas.srt e arquivos de origem quando houver entrega editável. Informar resolução real, presença de voz e qualquer parte que só tenha chegado à etapa de storyboard ou prévia.
