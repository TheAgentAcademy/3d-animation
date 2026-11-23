# Comparar a direção e o ritmo de dois vídeos

Escolha a mesma ação nos dois vídeos e identifique onde ela começa em cada um. Guarde as fontes como MP4s locais em sua pasta de estudo. Rode o comando a partir da pasta que contém SKILL.md.

```sh
python3 scripts/comparar_ritmo.py referencia.mp4 meu-reel.mp4 --inicio-ref 0 --inicio-video 0 --duracao 7 --passo 0.25 --saida estudo/comparacao-01
```

Abra **comparacao.html**. Cada cartão contém os dois quadros correspondentes ao mesmo tempo relativo. Abaixo da imagem ficam o timestamp efetivo desde o primeiro quadro da respectiva faixa e o índice do quadro, começando em zero. Abra **Série temporal completa** para localizar intervalos parados, explosões de atividade e mudanças de contraste. Os dados também ficam em medidas.json. Mantenha os quadros extraídos e a folha lado a lado na pasta de análise quando o material de referência for de outra pessoa.

## Como ler as medidas

- **Janela.** Os inícios e a duração estão em segundos. O instante inicial entra na amostragem e o limite final fica de fora. Cada alvo usa o quadro que estava na tela naquele instante, pelos timestamps do vídeo, inclusive em taxa variável. Se uma faixa tem cadência menor que a amostragem, um mesmo quadro pode aparecer duas vezes. Ajuste o passo para medir batidas mais curtas ou estudar vídeos maiores.
- **Variação entre amostras.** Reduzir cada quadro em tons de cinza a 64 × 64. Para cada pixel, calcular quanto seu valor mudou entre os dois instantes e tirar a média das diferenças absolutas. O primeiro instante fica em branco. Cortes, ação, câmera, flashes e legendas alteram o valor. Para identificar a causa, ampliar os dois quadros. Uma ação breve pode acontecer entre as amostras. Reduza o passo para observá-la. A unidade é nível de cinza, de 0 a 255.
- **Contraste.** Subtrair o décimo percentil da luminância do nonagésimo percentil em cada quadro reduzido. Seguir essa amplitude ao longo do filme e observar o que ganhou ou perdeu destaque. Em uma praça clara, o contraste pode cair quando o céu deixa o enquadramento.
- **Medianas.** Resumem a distribuição temporal de cada vídeo. Duas cenas diferentes podem ter as mesmas medianas. Na avaliação, dar prioridade à leitura da silhueta, ao instante da ação, ao deslocamento de câmera, ao desenho da luz e à consequência visível.
- **Imagem.** Os JPEGs mantêm a proporção visual original. A redução quadrada serve ao cálculo da estatística dentro de cada imagem. A medição inclui as bordas, o texto e eventuais faixas pretas do vídeo. Para avaliar som, ouvir uma fonte que contenha áudio.

### Marcar eventos observados

Para comparar escolhas específicas, escreva um eventos.json com os instantes relativos ao início de cada janela. Inclua só eventos efetivamente conferidos. Se um evento existe em apenas um dos vídeos, preencha apenas sua chave. O exemplo registra a entrada do personagem nos dois vídeos e o corte para o plano fechado apenas na referência.

```json
[
  {"nome":"O personagem entra em quadro","ref":2.0,"video":2.5},
  {"nome":"A câmera corta para o plano fechado","ref":5.0}
]
```

Acrescente `--eventos eventos.json --pares 12` ao comando. A tabela de eventos mostra o deslocamento em segundos entre os dois instantes anotados. O relatório insere o par de imagens em cada instante marcado, inclusive entre as medições periódicas. Para conferir um movimento inferior a um quarto de segundo, use também os quadros consecutivos indicados no guia analise.md.
