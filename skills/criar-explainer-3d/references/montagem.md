# Montagem, fala e legendas

Use Python 3.9+ e FFmpeg com ffprobe, libx264, AAC e libass no PATH. Rode os comandos na pasta que contém SKILL.md. Os modelos de voz são opcionais. As quatro locuções de exemplo já vêm prontas.

## Montar

```sh
python3 scripts/montar.py --quadros trabalho/frames --fps 12 --roteiro assets/fila-locucao.json --voz assets/fila-voz.m4a --efeitos assets/fila-efeitos.m4a --saida trabalho/fila.mp4 --srt trabalho/fila.srt
```

Para a cisterna, use os quadros da cisterna, `assets/cisterna-locucao.json`, `assets/cisterna-voz.m4a` e `assets/cisterna-efeitos.m4a`. Para o eremita, use os respectivos quadros, `assets/eremita-locucao.json` e `assets/eremita-voz.m4a`. Use nomes de saída novos em cada versão.

- **Quadros de Blender.** Informe o FPS da cena. A duração é a quantidade de PNGs dividida pelo FPS. Use uma pasta com uma única sequência contínua, como `0001.png` ou `plano_0001.png`. Aceita cadências fracionárias como `30000/1001`.
- **Vídeo existente.** Substitua `--quadros trabalho/frames --fps 12` por `--video base.mp4`. Sem nova voz, o som original segue no arquivo. Com `--voz`, `--tts` ou `--piper-modelo`, a nova locução ocupa essa faixa. A montagem mantém as proporções do material.
- **Voz gravada.** Grave em local silencioso. Posicione a primeira palavra de cada trecho no tempo marcado antes de passar a faixa única com `--voz locucao.wav`. O roteiro controla a exibição das legendas. A faixa gravada deve caber no vídeo.
- **Voz sintética.** `--tts` procura eSpeak NG/eSpeak em pt-br ou uma voz brasileira do comando say no macOS. Para maior naturalidade, use `--piper-modelo /caminho/pt_BR-faber-medium.onnx` com o comando `piper` no PATH e o arquivo `.onnx.json` junto ao modelo. No Windows, use a faixa pronta, uma gravação ou Piper. A síntese de cada frase e a montagem rodam localmente.
- **Efeitos.** Passe uma faixa de foley alinhada ao início do vídeo com `--efeitos efeitos.wav`. O ganho inicial é −12 dB. Para mudar, use por exemplo `--ganho-efeitos -18`. Sem trilhas de áudio, a saída inclui uma faixa AAC silenciosa.
- **Legenda.** O script queima texto branco com contorno e dá destaque opcional em amarelo. Em vídeo vertical, a base fica a 82% da altura. Reserve a faixa entre 72% e 82% para até duas linhas. Use uma ideia por cartão e ajuste as quebras com `\n` quando necessário. O SRT opcional deixa a legenda editável.

### Marcar as palavras em um Reel

Para usar legendas por palavra em qualquer cena, especificar o texto e o tempo de uma palavra da voz em cada entrada da lista legendas. Acrescente `"estilo_legenda":"palavra"` e, opcionalmente, `"altura_legenda":0.74` ao objeto do roteiro. Para uma palavra-chave, use o mesmo texto em destaque. Observe os tempos de [vila-locucao.json](../assets/vila-locucao.json). Se uma palavra tem uma pausa longa depois, termine a legenda junto da fala ou mantenha a palavra em tela por decisão de direção.

Com um modelo Piper instalado, também é possível alinhar palavras de uma narração nova automaticamente. No ambiente Python com piper-tts disponível, passe o modelo ONNX local e um roteiro com a lista fala. O arquivo de configuração .onnx.json da voz deve estar ao lado do modelo.

```sh
python3 scripts/alinha_fala.py --roteiro frases.json --modelo vozes/pt_BR-faber-medium.onnx --duracao 10 --saida voz-nova
```

Em frases.json, cada fala informa inicio, fim e texto. A lista opcional destaques contém as palavras que devem ficar amarelas. Use voz-nova/voz.wav e voz-nova/locucao.json com o montador. O alinhamento reflete a síntese do Piper. Para uma voz gravada por outra pessoa, medir os tempos no áudio correspondente.

## Escrever o roteiro temporizado

Use segundos decimais a partir do início. Em cada lista, os intervalos devem seguir a ordem de exibição e caber no filme. `fala` pode unir vários cartões em uma sentença para manter a entonação. Na ausência dessa lista, a síntese lê cada cartão de legenda em separado. `destaque` deve corresponder a uma expressão do texto, inclusive maiúsculas e acentos.

```json
{
  "fala": [
    {"inicio": 0.2, "fim": 3.8, "texto": "O elevador parou. Qual porta abre primeiro?"}
  ],
  "legendas": [
    {"inicio": 0.2, "fim": 1.6, "texto": "O elevador parou."},
    {"inicio": 1.6, "fim": 3.8, "texto": "Qual porta abre primeiro?", "destaque": "primeiro"}
  ]
}
```

Faça a primeira escuta com a voz sozinha. Ajuste cada troca de cartão ao momento em que a frase começa. Uma troca num silêncio de 300 ms pode funcionar melhor que uma quebra matemática no meio da palavra. Se a síntese ultrapassar a janela em mais de 28%, a montagem indica o trecho a reescrever. Preserve um instante para observar o efeito após a fala.

## Verificar a entrega

```sh
ffprobe -v error -show_entries stream=codec_name,width,height,pix_fmt,avg_frame_rate,duration,nb_frames -of json trabalho/fila.mp4
```

No exemplo da fila, procure 240 quadros a 12 fps, 20 s, H.264 yuv420p e áudio AAC. Confira ao menos a abertura, um movimento de corpo, cada mudança de destino e a frase final em tela de celular. Escute em volume baixo para detectar efeito cobrindo consoantes. O cruzamento de duas falas, uma imagem pulada ou uma legenda tapando o objeto exigem correção no tempo correspondente.

A faixa cisterna-efeitos.m4a acrescenta chuva, encaixes e pingos sincronizados ao exemplo da cisterna. As locuções originais incluídas foram sintetizadas com a voz brasileira Faber medium do Piper e os textos dos exemplos. Os sinais de guichê, os passos, os pingos no telhado e os encaixes no cano são efeitos originais sintetizados para os exemplos. A ficha do modelo credita o conjunto de gravações sob CC0. Para instalar o motor opcional, consulte [Piper](https://github.com/OHF-Voice/piper1-gpl) e a [ficha da voz](https://huggingface.co/rhasspy/piper-voices/blob/main/pt/pt_BR/faber/medium/MODEL_CARD).
