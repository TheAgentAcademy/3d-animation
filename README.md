# A parábola das galinhas

Um projeto de animação vertical em Blender. Uma aldeia perde suas casas, seus habitantes recebem galinhas e três grupos escolhem o que fazer com elas. As cenas têm câmeras animadas, personagens, acampamento, galinheiros e bairros editáveis.

**Para editar o exemplo**, abra uma das [16 cenas prontas](cenas/) no Blender. **Para criar outro vídeo com um agente de IA**, use a [skill de animação 3D](skills/criar-explainer-3d/SKILL.md). Os modelos, créditos e instruções acompanham o projeto.

## Abra uma cena

1. Baixe o projeto em **Code → Download ZIP** e extraia os arquivos, ou clone o repositório. Abra `cenas/tres-destinos.blend` no Blender 4.3 ou superior para ver os três bairros, ou `cenas/nascimento.blend` para explorar o galinheiro.
2. Na linha do tempo, aperte a barra de espaço para ver a ação. A tecla **0** do teclado numérico alterna a visão da câmera. Use **Render → Render Image** ou **F12** para renderizar o quadro atual.
3. Para mudar o lugar, a escala ou o movimento de um aldeão ou de uma ave, selecione sua instância pelo **Outliner**. As coleções `Modelo` guardam as geometrias compartilhadas. Uma alteração no modelo aparece em todas as suas instâncias. Para separar uma cópia, use **Object → Apply → Make Instances Real**.
4. Use **Render → Render Animation** para gravar PNGs em `quadros/NOME-DO-PLANO/`. Na criação de uma nova história, grave a própria voz e importe a sequência de imagens e a locução em um editor de vídeo a 24 fps.

## Troque um personagem

Por exemplo, para colocar a senhora de vestido verde no lugar do camponês de amarelo na cena do jantar:

1. Abra [fontes/tomadas.py](fontes/tomadas.py) e procure a função `jantar()`.
2. Na chamada que começa com `humano(2,-1.15`, troque apenas o primeiro número de `2` para `0`. Esse número escolhe o personagem. Os demais valores mantêm sua posição e seu gesto.
3. Na raiz do projeto, rode o comando abaixo e abra o novo arquivo `cenas-geradas/jantar.blend`. Se já houver uma versão gerada, escolha outra pasta de saída com `--destino jantar-v2`.

```sh
blender -b --python-exit-code 1 -P criar_planos.py -- --plano jantar
```

## Crie outro vídeo com a skill

Abra a pasta do repositório no Codex ou no Claude Code com acesso ao terminal e dê um pedido como este:

> Leia `skills/criar-explainer-3d/SKILL.md`. Crie um Reel de 20 segundos mostrando como uma correspondência atravessa a cidade. Use narração em português, legendas sincronizadas e me entregue o MP4 e a cena editável.

Para renderizar os exemplos da skill, siga o [guia de instalação e primeiro vídeo](skills/criar-explainer-3d/references/primeiro-video.md). O pacote também inclui [quatro demonstrações em vídeo](skills/criar-explainer-3d/demonstracoes/).

## Ordem da montagem

| Tempo aproximado | Arquivo e conteúdo |
| --- | --- |
| 0–6 s | `abertura` — praça e cartela |
| 6–13 s | `vila-mao` — ouro, casas e calçada se desprendem |
| 13–19 s | `aldeia-sem-terra` — aldeões sob a lona |
| 19–27 s | `jantar` — fogueira do primeiro grupo |
| 27–34 s | `galinhas-vivas` — aves do segundo grupo |
| 34–37 s | `galo` — o reprodutor |
| 37–42 s | `proposta` — uma das moradoras propõe cooperar |
| 42–50,5 s | `acordo` — os vizinhos se reúnem |
| 50,5–55 s | `nascimento` — ovos e pintinhos |
| 55–58,5 s | `ovos` — coleta |
| 58,5–63 s | `multiplicacao` — o quintal vira aldeia |
| 63–69 s | `reclamacao` — sobram ossos no acampamento |
| 69–74 s | `sustento` — ovos em casa |
| 74–78,5 s | `multidao` — quintal cheio de aves |
| 78,5–83 s | `trabalho` — nova conversa |
| 83–94,33 s | `tres-destinos` — panorama final |

Cada projeto usa a numeração local a partir de 1. Na edição de sete segundos da mão, conserve a velocidade original nos primeiros 4,5 s e acelere o restante para 142%. O arquivo-fonte da mão tem 10 segundos e usa EEVEE para renderizar os materiais e o céu fotográfico. Os demais planos usam Workbench com materiais coloridos e céu fotográfico empacotado em cada cena. No MP4, a iluminação direcional, as sombras projetadas e a composição do céu foram calculadas por um renderizador OpenGL. A luz de estúdio do Blender e as sombras de contato do MP4 podem diferir.

## Reconstrua os projetos

A pasta `fontes` contém os modelos e a direção das cenas. Os comandos a seguir usam apenas o Blender. No terminal, entre na pasta que contém este guia. Troque `blender` pelo caminho do programa se necessário. No macOS, a instalação padrão costuma aceitar `/Applications/Blender.app/Contents/MacOS/Blender`.

Liste os nomes e intervalos exatos:

```sh
blender -b --python-exit-code 1 -P criar_planos.py -- --listar
```

Para gerar uma cena, escolha seu nome. O arquivo novo será salvo em `cenas-geradas/`.

```sh
blender -b --python-exit-code 1 -P criar_planos.py -- --plano nascimento
```

Para reconstruir todas em uma pasta nova:

```sh
blender -b --python-exit-code 1 -P criar_planos.py -- --plano todos --destino cenas-novas
```

Você pode renderizar sem abrir a interface. O primeiro comando produz o quadro 15. O segundo exporta a animação inteira no destino configurado no projeto.

```sh
blender -b cenas/nascimento.blend -f 15
blender -b cenas/nascimento.blend -a
```

Edite `fontes/tomadas.py` para alterar os deslocamentos de câmera, o momento em que os objetos aparecem e as posições dos grupos. Os modelos estão em `povo.py`, `aves.py` e `locais.py`. O arquivo `abertura.py` controla a abertura. O arquivo editável da mão já contém a animação e o céu empacotado.

Consulte os [créditos e a permissão de uso das cenas](CREDITOS.txt) e as [permissões e os créditos da skill](skills/criar-explainer-3d/LICENSE.txt).
