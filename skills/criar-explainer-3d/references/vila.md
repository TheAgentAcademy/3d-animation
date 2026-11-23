# Dirigir o Reel da vila

**Uma rua inteira cabe numa mão?** é uma cena contínua de dez segundos. A câmera recua, uma mão articulada invade o céu, as moedas sobem e as casas levantam pelas fundações. A praça perde a calçada. A pessoa que ficou e a placa da rua dão escala ao plano final.

## Reproduzir ou mudar a cena

Na pasta da skill, execute:

```sh
python3 scripts/produzir.py --exemplo vila --saida minha-vila
```

O MP4 tem narração, efeitos e legendas. O arquivo cena.blend contém a animação, as câmeras, a mão e o céu. O painel Timeline inclui marcadores para os acontecimentos. Para ver um quadro sem esperar pelo filme todo, use `--quadro 110` e escolha outra pasta de saída. Para gerar em 1080 × 1920, acrescente `--qualidade final`.

O comando de produção renderiza a vila em blocos sequenciais de 12 quadros. A cada bloco, o Blender libera a memória e o comando confere os PNGs. Se um processo parar, ele retoma do primeiro quadro incompleto em blocos menores. Os PNGs já concluídos ficam em `frames`.

Para variar o roteiro, copie assets/vila.json e assets/vila-locucao.json. Passe as cópias a `--cena` e `--roteiro`. Use uma gravação sincronizada em `--voz`, ou a síntese local descrita em [montagem](montagem.md). Os efeitos originais são uma faixa única alinhada às ações do exemplo. Ao alterar a ordem dos acontecimentos, realinhe também os impactos e os ruídos no editor de áudio.

| Campo de vila.json | O que ele dirige |
|---|---|
| modelo | O valor vila seleciona este diretor no comando produzir.py. |
| placa | Texto da placa física que sobra após a praça desaparecer. Use um nome curto e confirme a leitura no último quadro. |
| eventos | Instantes absolutos de entrada da mão, moedas, casas, árvores, calçada e marcador de revelação. Cada grupo se move com pequenos atrasos entre seus objetos. O enquadramento da revelação é definido na câmera. |
| camera | Lista de poses com s (segundos), eye (posição), target (ponto observado) e mm (lente em milímetros). Deslocar a câmera muda o movimento relativo entre o primeiro plano e o fundo. |
| duration, fps, width, height, samples | Duração e propriedades da imagem. Ajustar planos e voz junto com qualquer mudança de duração. |
| engine | EEVEE usa o motor em tempo real do Blender. Para experimentar o motor de CPU, selecionar CYCLES e renderizar primeiro um quadro para conferir luz e tempo. |
| seed | Variações determinísticas das trajetórias e partículas. Conserve a mesma semente ao comparar duas câmeras. |

Exemplo de uma variação simples: mude a placa, filme a entrada a partir de outra esquina e antecipe as moedas em meio segundo. Compare no quadro em que elas passam pelos telhados. Para uma história nova sobre uma colheita, troque a unidade visual por árvores carregadas e frutos, defina como o peso dobra os galhos e modele o que deve ficar após a ação. A câmera, a luz e o contraste de escala podem voltar; a transformação física precisa ser própria do assunto.

## Dirigir outro tema com esse acabamento

1. Identificar a figura que dá escala e o elemento que domina o quadro. No exemplo, são uma moradora e os dedos de uma mão. Fazer a primeira renderização pequena, em três instantes, para checar se essas silhuetas se distinguem.
2. Construir o primeiro plano, um plano médio de ação e um fundo que atravesse o enquadramento durante o movimento da câmera. Em uma fachada, telhas, molduras, janelas e sombra do beiral explicam o tamanho melhor que um bloco com uma cor.
3. Dar a cada transformação um início reconhecível (moeda levanta), uma trajetória (ela faz uma curva acima do telhado) e uma consequência (fica um espaço vazio). Defasar elementos semelhantes. Segurar a câmera quando o espectador precisar perceber o que sobrou.
4. Para um cenário genérico, usar `"look":"exterior"` e as opções de lente no [contrato de cena](cena.md). Se o assunto exigir um personagem articulado, importar um GLB adequado. Revisar textura, silhueta e pose do primeiro plano em resolução de entrega.
5. Definir `"estilo_legenda":"palavra"` no roteiro para usar o desenho de legendas do exemplo. Cada item da lista legendas contém uma palavra e seus tempos reais. Conferir acentos, contorno e contraste sobre a área mais clara da imagem.
6. Abrir o rascunho e a versão anterior nos mesmos acontecimentos. Comparar as trajetórias, não apenas o cenário congelado. Para medir e exportar uma folha de pares, seguir [comparação de ritmo e quadros](medir-fidelidade.md).

## Recursos visuais

Os modelos e materiais da rua foram construídos para o exemplo. O céu é uma fotografia panorâmica de Greg Zaal e Jarod Guest. A mão tem malha e esqueleto da Innerscene, derivados de MakeHuman. Ambos os recursos externos são CC0. A licença da fonte acompanha o arquivo de fonte em assets. [Céu da Poly Haven](https://polyhaven.com/a/kloofendal_48d_partly_cloudy_puresky) · [Mão articulada](https://www.innerscene.com/tools/library/3d-parts/posable-anatomical-right-hand-f6098b4f)
