# Ler uma referência em movimento

Comece pelo arquivo do vídeo. Se só houver link, procure um clipe público reproduzível na página. Caso a plataforma apresente apenas uma capa ou peça login, use a capa somente para composição e peça o MP4 para medir movimento, cortes ou som. Mantenha os quadros de referência na pasta de estudo. Produza a peça compartilhável com roteiro, áudio e cenas próprios.

## Medir os planos

A partir da pasta da skill, execute com Python 3, FFmpeg e ffprobe instalados. No Windows, substitua `python3` por `py -3` se necessário.

```sh
python3 scripts/medir_referencia.py "referencias/exemplo.mp4" --saida "estudo/exemplo"
```

Abra `contato.html`. A primeira grade percorre o vídeo. Os grupos seguintes mostram o quadro anterior ao possível corte, o quadro marcado e o seguinte, quando existem. O número embaixo da imagem é o índice real de exibição, começando em zero. O tempo começa no primeiro quadro de vídeo, inclusive quando o arquivo possui uma faixa de áudio que começa antes. Guarde junto o `medidas.json` e os JPEGs para consultar o estudo offline.

Se um corte discreto ficou de fora, tente `--limiar 0.20 --amostras 24` em outra pasta. Se flashes ou mudanças de luz dominarem a lista, aumente para `--limiar 0.45`. O detector avalia diferenças visuais com a imagem reduzida a 160 px de largura. Um corte sugerido exige confirmação visual. Dissoluções, aproximações contínuas e trocas de palavras podem escapar. Use o arquivo original para ouvir a fala e os efeitos. `trilhas_de_audio: []` indica ausência de faixa no arquivo estudado. Uma faixa presente ainda pode conter silêncio.

Use `medidas.json` para ver a resolução, rotação, taxa média, número de quadros, duração da imagem e faixas de áudio. Os tempos são calculados pelos timestamps individuais, inclusive com taxa variável. `pts` é o timestamp nativo na base registrada. O detector lista todos os candidatos. Por padrão o HTML detalha até 12 deles, espalhados pelo vídeo quando há mais. Ajuste com `--max-cortes`. Para inspecionar um instante específico, p. ex. quadros 79 a 87, execute na pasta de estudo com um caminho real para o arquivo.

```sh
ffmpeg -i "exemplo.mp4" -vf "select=between(n\,79\,87)" -vsync 0 -start_number 79 "detalhe-%04d.png"
```

## Passar da medida à direção

Para cada plano que altera o entendimento, registre o intervalo, o que o público precisa entender ali, o que ocupa o primeiro plano, qual elemento se move e qual palavra ou som acompanha a mudança. Separe a descrição observada da hipótese de execução. Um personagem crescer na tela pode vir tanto de uma aproximação de câmera quanto da troca de lente.

| Observação no clipe | Pergunta para o novo filme |
| --- | --- |
| O mesmo enquadramento ganha objetos sucessivos | Qual peça nova altera o estado do sistema e merece entrar no próximo verbo? |
| Uma pessoa atravessa, entrega ou retira algo | Em que mão, posição e direção termina o movimento para o plano seguinte? |
| Uma palavra troca de cor no meio da frase | Qual termo da nossa locução precisa de ênfase, e por quantos quadros ele continua legível? |
| O último plano mostra uma consequência | O público consegue deduzir essa consequência com o vídeo no mudo? |

Compare o rascunho com a referência por função: tempo até reconhecer o assunto, densidade de ações, ação visível em cada frase, sincronismo de voz e legibilidade no celular. Uma diferença de pixels terá pouca utilidade quando personagens e assunto forem novos.

O projeto HyperFrames oferece uma abordagem de comparação quadro a quadro. O recurso oficial `reverse-any-video` é apresentado como Pro. O medidor deste pacote roda localmente com FFmpeg e Python. [Referência do HyperFrames](https://github.com/heygen-com/hyperframes/blob/main/skills/reverse-any-video/SKILL.md) · [Detector visual do FFmpeg](https://ffmpeg.org/ffmpeg-filters.html) · [Documentação do ffprobe](https://ffmpeg.org/ffprobe.html)
