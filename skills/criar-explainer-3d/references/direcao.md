# Do argumento à cena de Blender

## Encontrar o plano que explica a ideia

Escrever a mudança em uma frase concreta. Exemplo: “Ainda há três pessoas esperando no guichê A quando o atendente B fica livre”. Desenhar a frase com objetos que se possam contar. Se o efeito depender de um elemento fora do quadro, mostrar os dois juntos pelo menos uma vez antes de aproximar a câmera.

| Decisão | Pergunta para o diretor | Exemplo de execução |
|---|---|---|
| Gancho | Que pergunta o primeiro quadro deixa em aberto? | Um atendente livre acena para uma fila que continua parada no outro balcão. |
| Geografia | Onde o público deve olhar depois? | Fixar A à esquerda e B à direita. Repetir a cor do balcão no seu letreiro. |
| Causa | Qual é o instante em que a regra muda? | As duas filas convergem em um corredor. Manter os mesmos atendentes e a mesma multidão. |
| Consequência | Que coisa pode acontecer agora? | O primeiro da fila vira e anda para a vaga de B. Fazer a vaga aparecer antes do passo. |
| Fechamento | Que conclusão a imagem permite? | Ver os dois atendendo. A locução qualifica o exemplo quando o princípio tem condições. |

Trabalhar os tempos em segundos ou quadros, sempre com a mesma origem. Para cada plano escrever: início e fim, fala, sujeito, estado inicial → ação → estado final, câmera, legenda e sinal sonoro. Marcar o quadro de contato, entrega, queda ou chegada. Sincronizar o verbo e o efeito ao contato. Se a locução real ultrapassar a janela, encurtar a frase ou aumentar a janela e propagar as mudanças pelo restante da montagem.

## Encenação para o celular

- Fazer um plano aberto curto para localizar os elementos e um médio ou detalhe para provar o efeito. Manter o lado de tela dos personagens durante a troca de câmera. Em travelling, usar um elemento no primeiro plano para evidenciar o deslocamento.
- Concentrar as silhuetas decisivas na metade central do quadro. Testar a imagem a cerca de 200 px de largura. Se duas silhuetas virarem uma, afastá-las lateralmente ou variar luminosidade antes de acrescentar um rótulo.
- Num movimento, reservar uma pose de preparação, um trajeto e uma pose final legível. Repetir personagens com pequenas variações de roupa e postura. Um grupo parado ao mesmo tempo parece um conjunto de peças. Alternar os passos e os olhares do primeiro e do último.
- Usar uma cor para cada função estável. Para indicar uma mudança, usar também movimento, forma, posição ou um som. Preparar o sujeito contra um fundo mais simples que ele. Sombras de contato ajudam a ler pés, rodas e objetos suspensos.
- Centralizar legendas curtas abaixo da ação. Um bom ponto de partida é por volta de três quartos da altura. Renderizar uma amostra com as palavras mais largas, acentos e cedilha. Ajustar se a interface ou a ação ocupar a mesma área.
- Escolher a dinâmica de câmera que serve ao assunto. Uma balança pede prato e contrapeso visíveis antes do close. Uma calha pede acompanhar a gota até a curva. Uma história de vida pede manter um traço reconhecível do protagonista entre idades.

## Exemplo de trajetória original: a jornada de uma folha

**Pergunta:** onde uma folha presa num bueiro foi parar? Personagem: folha com ponta rasgada e um veio amarelo. Espaço: calçada, boca de lobo fictícia e cesto de retenção. Apresentar como uma história ambientada naquele cenário; só atribuir esse tipo de cesto a lugares reais com fonte.

| Tempo de partida | Ação visível | Câmera e som |
|---|---|---|
| 0–3 s | A folha gira junto à grade e desaparece por uma fresta. | Close no rasgo. Ouve-se o primeiro pingo. |
| 3–7 s | Recuar para revelar a inclinação da rua; uma pequena corrente carrega outras folhas. | Plano geral oblíquo e deslocamento no sentido da corrente. |
| 7–12 s | Atravessar a parede do cenário em corte para mostrar o cesto. A folha encosta na malha; a água continua. | Travelling para baixo. Som curto no contato. |
| 12–16 s | Uma mão levanta o cesto. A ponta rasgada reaparece. | Enquadrar a folha contra o céu na mesma escala da abertura. |

Para histórias de animais, escolher uma marca de identificação, o lugar e o esforço que move cada etapa. Um caranguejo eremita, por exemplo, pede duas conchas de tamanhos diferentes e uma ação clara de troca. Conferir comportamento, escala e habitat antes de representar uma espécie. Tratar falas inventadas de um personagem como ficção.

## Personagens, cenários e movimento fora dos exemplos

As quatro cenas do pacote são geradas por código. Para cenas novas, copiar o arquivo de cena para a produção e escolher o menor conjunto de elementos capaz de explicar a ação. Usar os tipos presentes no gerador. Para inserir um GLB autocontido, usar por exemplo `{"id":"casa","type":"glb","file":"modelos/casa.glb","scale":1}`. O comando de produção guarda uma cópia do modelo na pasta fontes. Se a silhueta ou a atuação pedirem algo novo, criar uma função em uma cópia local de cena_3d.py, ou importar um modelo disponível para aquele projeto.

- **Personagem articulado.** Importar o GLB com armature e malha na mesma coleção. Conferir altura em relação a uma porta ou bancada. Colocar um Empty na raiz para o deslocamento pelo chão. Testar andar, parar e virar em uma faixa curta antes de povoar o cenário. Conferir se a ação já move a raiz: aplicar a velocidade de avanço uma vez para evitar patinar. [Personagens](https://quaternius.com/packs/universalbasecharacters.html) · [Animações](https://quaternius.com/packs/universalanimationlibrary.html)
- **Multidão.** Reutilizar os dados da malha, variar paleta e defasar o ciclo. Dê um gesto legível ao protagonista e use os figurantes como contexto. Pés que atravessam o chão e personagens que se cruzam no mesmo lugar ficam especialmente visíveis em plano baixo.
- **Cidade modular.** Escolher um prédio reconhecível, uma fileira de fundo e poucos marcos. Testar escala, texturas e caminhos relativos reabrindo o .blend. Registrar fonte, autor e licença dos itens realmente usados. [City Kit de Kenney](https://kenney.nl/assets/city-kit-suburban)
- **Som.** Dar prioridade à voz. Reservar efeitos para eventos que tenham um quadro identificável, como uma ficha batendo no prato ou água entrando no reservatório. Baixar o volume do efeito até as consoantes da voz ficarem claras num alto-falante de celular. Dados, música, voz e assets adicionados pelo usuário conservam suas condições de uso.

## Revisão antes de entregar

1. Assistir sem som, ocultando a legenda. Dizer em voz alta o que mudou. Se só for possível repetir o tema, a animação precisa de uma ação mais clara.
2. Ouvir sem imagem. Checar pronúncia de nomes, siglas e números. Abrir a janela do player quando a boca ou o objeto tocar para conferir sincronia.
3. Assistir no tamanho de um celular. Pausar no pior quadro de cada transição e no texto mais longo. Verificar corte de letras, sobreposição com a ação e horizonte atravessando rostos.
4. Conferir o MP4 entregue com ffprobe, reabrir o projeto editável e anotar o que ficou ilustrativo, medido, ou dependente de gravação externa.
