# Contrato da cena editável

Cada arquivo JSON descreve uma cena independente. O modelo especializado da vila tem [contrato próprio](vila.md). As opções a seguir se aplicam às cenas genéricas com entities e shots.

### Exterior em perspectiva

Use `"look":"exterior"` para carregar o céu fotográfico incorporado, sol e câmera em perspectiva. Posicione a fachada ou uma colina de fundo junto da linha do horizonte. Um plano pode definir `"projection":"perspective"` e `"lens_mm":35` independentemente da luz. Cada chave de câmera aceita eye, target e uma nova lens_mm opcional. Para um travelling, desloque a posição para que o primeiro plano passe mais rápido que o fundo. Para um zoom, anime a lente. O modo orthographic continua usando scale para a abertura.

Exemplo de plano: `{"name":"Recuo na praça","at":0,"projection":"perspective","lens_mm":32,"eye":[1,-6,1.8],"target":[0,0,1.6],"keys":[{"at":1.2,"eye":[1.8,-9,2.2],"target":[0,0,1.8]}]}`. O bloco opcional `"sun":{"direction_from":[-7,-5,8],"strength":3.0,"angle":2.1}` define a direção de onde vem a luz, intensidade e diâmetro angular em graus.
 O script scripts/cena_3d.py lê o JSON dentro do Blender. Os nomes de campos são em inglês e os textos que aparecem no vídeo podem estar em português.

## Uma cena completa em quatro segundos

Este arquivo mostra uma caixa atravessar duas marcas no chão. A câmera aproxima enquanto a caixa se move. Salve como cena.json e use --quadro para verificar a geometria antes da animação completa.

```json
{
  "duration": 4,
  "fps": 12,
  "width": 432,
  "height": 768,
  "samples": 8,
  "stage": "plain",
  "floor": "#E7DAC3",
  "entities": [
    {"id":"início","type":"disc","radius":0.55,"xyz":[-1,0,0],"color":"teal"},
    {"id":"fim","type":"disc","radius":0.55,"xyz":[1,0,0],"color":"teal"},
    {"id":"caixa","type":"box","dimensions":[0.65,0.65,0.65],"xyz":[-1,0,0.03],"color":"coral",
     "keys":[{"at":0.8,"xyz":[-1,0,0.03]},{"at":2.7,"xyz":[1,0,0.03]}]}
  ],
  "shots": [
    {"name":"Travessia","at":0,"eye":[1,-8,4],"target":[0,0,0.45],"scale":6.2,
     "keys":[{"at":3.4,"eye":[1,-7,3],"target":[0.5,0,0.4],"scale":5.1}]}
  ]
}
```

| Campo | Uso |
|---|---|
| duration, fps | Segundos totais e quadros por segundo inteiros. Quadro 1 = 0 s. O último quadro exibido vem antes do instante final. A quantidade de quadros é duration × fps, arredondada. |
| width, height, samples | Tamanho da prévia e amostras de luz por pixel. Para render final vertical, o comando produzir.py substitui essas medidas por 1080 × 1920, 24 fps e 32 amostras. |
| stage, floor | hall cria o saguão dos guichês. plain cria um piso, com cor definida em floor. Ambos incluem iluminação. |
| palette | Dicionário opcional de nomes para cores hexadecimais da forma #RRGGBB. Cada color pode usar uma cor hexadecimal diretamente ou um nome como ivory, teal, navy, coral e gold. |
| entities | Objetos da cena, cada um com id único, type e campos geométricos. xyz dá a posição em unidades Blender, Z para cima. |
| keys | Lista cronológica da entidade. at é o instante absoluto em segundos. xyz muda a posição. scale aceita número ou vetor [x,y,z]. roll, pitch e yaw giram, em graus, nos eixos X, Y e Z, respectivamente. |
| shots | Lista de câmeras em ordem. A primeira começa em at = 0. Cada câmera tem eye (posição) e target (ponto observado). Na câmera ortográfica, use scale para a abertura. Na câmera de perspectiva, use lens_mm. Cada novo plano corta no seu at. |
| shots[].keys | Animam uma mesma câmera. Fornecer at, eye e target em cada chave, com tempos absolutos dentro do plano. Na projeção ortográfica, incluir scale em cada chave. Na perspectiva, lens_mm é opcional e conserva a última focal quando omitido. Usar isso para acompanhar um ator ou revelar um detalhe. |

### Peças disponíveis

| type | Parâmetros |
|---|---|
| person | color (roupa), pants, skin, hair, accent, style (crop, bun, cap, curls), bag (booleano). walk aceita pares [início,fim]; adicionar keys de xyz para avançar enquanto as pernas andam. gesture e lean aceitam [tempo,graus] para braço e tronco. |
| counter | color, label (por exemplo A) e sign opcional. Inclui bancada, terminal, placa e chamada superior. |
| plant | Vaso e folhas prontos. Ajustar tamanho com scale. |
| box, bar | dimensions [largura,profundidade,altura]. A origem fica no centro da base. Animar scale no eixo Z para fazer uma barra crescer a partir do chão. |
| sphere | dimensions [largura,profundidade,altura]. A origem fica no centro. |
| disc | Disco no chão. radius controla o tamanho. |
| route | Tubo seguindo points, uma lista de pelo menos dois [x,y,z]. radius muda a espessura. Os pontos são locais à entidade. |
| glb | file é o caminho de um modelo .glb autocontido, relativo ao JSON. Preserva hierarquia e pivô. Posicionar o conjunto com xyz, scale e keys, como nas demais peças. |
| label | text e text_size. O letreiro fica de pé voltado para a frente. Ajustar yaw se a câmera olhar de outro ângulo. |

Para segurar uma pose inicial até 2 s, repetir o valor na chave de 2 s e colocar o valor final na chave seguinte. Caso contrário, o Blender começa a interpolar logo após a última chave da propriedade. O narrador pode dizer “agora” quando a ação muda; sincronizar o gesto com o tempo efetivo da voz.

## Trabalhar direto no Blender

```sh
blender -b --python-exit-code 1 -P scripts/cena_3d.py -- --scene assets/fila-unica.json --out estudo --still 97
```

Abra estudo/cena.blend e pressione 0 no teclado numérico para ver pela câmera. Os marcadores na Timeline alternam os planos. Os objetos têm nomes legíveis e controles de posição, rotação e escala. Após editar o .blend, renderize a nova sequência de PNGs em uma pasta da produção e use scripts/montar.py para aplicar voz e legendas. Guarde uma cópia do .blend editado antes de recriar uma cena por JSON.
