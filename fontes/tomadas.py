"""Découpage original da parábola. Os limites da montagem são quadros de 24 fps."""
import math
import random
import sys
from pathlib import Path
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))

CORTES = [312, 454, 646, 815, 885, 1001, 1212, 1320, 1404, 1508, 1659, 1773, 1883, 1998, 2264]
NOMES = ["aldeia-sem-terra", "jantar", "galinhas-vivas", "galo", "proposta",
         "acordo", "nascimento", "ovos", "multiplicacao", "reclamacao",
         "sustento", "multidao", "trabalho", "tres-destinos"]
PLANOS = [(nome, a / 24, b / 24) for nome, a, b in zip(NOMES, CORTES, CORTES[1:])]

_prototipos = {}
_cores = {}
_n = 1


def vazio(nome):
    obj = bpy.data.objects.new(nome, None)
    bpy.context.scene.collection.objects.link(obj)
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = .16
    return obj


def modelo(chave, nome, construtor, x, y, z=0., rot=0., escala=1.):
    """Uma única geometria por figurino ou cor de ave em cada plano."""
    if chave not in _prototipos:
        collection = bpy.data.collections.new("Modelo | " + str(chave))
        raiz = construtor()
        for filho in (raiz, *raiz.children_recursive):
            origens = tuple(filho.users_collection)
            collection.objects.link(filho)
            for origem in origens:
                origem.objects.unlink(filho)
        _prototipos[chave] = collection
    nova = vazio(nome)
    nova.instance_type = 'COLLECTION'
    nova.instance_collection = _prototipos[chave]
    nova.location = (x, y, z)
    nova.rotation_euler.z = rot
    nova.scale = (escala,) * 3
    return nova


def cor(nome, rgba):
    if nome not in _cores:
        material = bpy.data.materials.new(nome)
        material.diffuse_color = (*rgba, 1)
        _cores[nome] = material
    return _cores[nome]


def caixa(nome, pos, dim, material):
    x,y,z = (v/2 for v in dim)
    pontos = [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),
              (-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    malha = bpy.data.meshes.new(nome)
    malha.from_pydata(pontos, [], faces)
    obj = bpy.data.objects.new(nome, malha)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = pos
    malha.materials.append(material)
    return obj


def cerca(x,y,largura):
    madeira = cor("cerca | cedro", (.29,.145,.055))
    talho = cor("cerca | guarnição", (.47,.255,.105))
    caixas = []
    for z in (.3, .58):
        caixas.append(caixa("Travessa", (x,y,z), (largura,.08,.105), madeira))
    n=max(2,round(largura/1.3) + 1)
    for i in range(n):
        px=x-largura/2+largura*i/(n-1)
        caixas.append(caixa("Mourão", (px,y,.39), (.12,.13,.78), talho))
    return caixas


def chave(obj, caminho, frame):
    obj.keyframe_insert(data_path=caminho, frame=round(frame))


def tempo(fracao):
    return round(1+max(0,min(1,fracao))*(_n-1))


def mover(obj, pontos):
    for fracao,pos in pontos:
        obj.location = pos
        chave(obj, 'location', tempo(fracao))


def aparecer(obj, posicao, intervalo=.09):
    e=obj.scale.copy()
    for t,f in [(0,.0001),(max(0,posicao-.006),.0001),(posicao+intervalo*.75,1.08),(posicao+intervalo,1)]:
        obj.scale = e*f
        chave(obj, 'scale', tempo(t))


def cam(trajeto):
    cena=bpy.context.scene
    dados=bpy.data.cameras.new("Objetiva")
    dados.sensor_width = 36
    dados.sensor_fit = 'HORIZONTAL'
    dados.clip_end = 500
    c=bpy.data.objects.new("Câmera",dados)
    cena.collection.objects.link(c)
    cena.camera=c
    mira=vazio("Centro do enquadramento")
    rastreio=c.constraints.new('TRACK_TO')
    rastreio.target=mira
    rastreio.track_axis='TRACK_NEGATIVE_Z'
    rastreio.up_axis='UP_Y'
    for fracao, olho, alvo, largura in trajeto:
        quadro=tempo(fracao)
        c.location=olho; chave(c,'location',quadro)
        mira.location=alvo; chave(mira,'location',quadro)
        dados.lens=(Vector(olho)-Vector(alvo)).length*36/largura
        chave(dados,'lens',quadro)
    return c


def humano(tipo, x,y, rot=0., gesto='repouso', ritmo=0., largura=1.):
    import povo
    p=modelo(('gente',tipo,gesto), f"Morador {tipo} | {gesto}", lambda:povo.pessoa("Corpo",0,0,tipo=tipo,gesto=gesto),x,y,rot=rot,escala=largura)
    # Mudança de apoio e inclinação de tronco. Pausas entre gestos preservam silhueta.
    for parte in range(7):
        t=parte/6; fase=ritmo+t*math.pi*3
        p.rotation_euler=(.018*math.sin(fase),.021*math.cos(fase),rot+.055*math.sin(fase))
        chave(p,'rotation_euler',tempo(t))
    return p


def ave(x,y, v=0, direcao=0., passo=.4, fase=0., pequena=False, escala=1.):
    import aves
    chave_tipo=('filhote',) if pequena else ('ave',v)
    construir=(lambda:aves.pintinho("Pinto",0,0)) if pequena else (lambda:aves.galinha("Ave",0,0,variante=v))
    a=modelo(chave_tipo,"Pintinho" if pequena else "Ave",construir,x,y,rot=direcao,escala=escala)
    # Curta caminhada em diagonal com transferência de peso e bicadas.
    inicio=Vector((x,y,0))
    frente=Vector((math.sin(direcao),-math.cos(direcao),0))
    saltos=max(3,round(_n/15))
    for k in range(saltos+1):
        t=k/saltos
        afast=(t-.5)*passo
        pos=inicio+frente*afast
        pos.z=.0 if k%2==0 else (.055 if pequena else .034)
        a.location=pos
        chave(a,'location',tempo(t))
        a.rotation_euler=(.045*math.cos(k*.9+fase),.075*math.sin(k*1.45+fase),direcao+.16*math.sin(3*t+fase))
        chave(a,'rotation_euler',tempo(t))
    return a


def ovo(x,y,z=0,escala=1):
    import aves
    return modelo("ovo","Ovo fresco",lambda:aves.ovo("Ovo",0,0),x,y,z=z,escala=escala)


def barraca(x,y,rot=0,escala=1):
    import locais
    return modelo("tenda","Abrigo",lambda:locais.tenda("Tenda",0,0),x,y,rot=rot,escala=escala)


def arvore(x,y,s=1):
    import locais
    return modelo("arvore","Árvore",lambda:locais.arvore("Árvore-base",0,0),x,y,escala=s,rot=(x*.83)%6)


def casa(x,y,tipo=0,s=1,rot=0):
    import locais
    return modelo(('casa',tipo),"Moradia",lambda:locais.casa("Casa",0,0,tipo=tipo),x,y,rot=rot,escala=s)


def coop(x,y,escala=1,rot=0):
    import aves
    return modelo("galinheiro","Galinheiro",lambda:aves.galinheiro("Viveiro",0,0),x,y,escala=escala,rot=rot)


def ossos(x,y,escala=1,rot=0):
    import aves
    return modelo("ossos","Ossos",lambda:aves.ossos("Refeição terminada",0,0),x,y,escala=escala,rot=rot)


def relva(x,y,l=6,p=5):
    import locais
    return locais.gramado("Quintal",x,y,largura=l,profundidade=p)


def cesta(x,y,quantidade=8):
    madeira=cor("caixa | mel",(.47,.22,.055))
    clara=cor("caixa | ripas",(.69,.39,.15))
    caixa("Caixote | base",(x,y,.085),(1.32,.84,.13),madeira)
    for z in [.17,.31]:
        for d in [-1,1]:
            caixa("Ripa frontal",(x,y+d*.42,z),(1.42,.055,.11),clara)
            caixa("Ripa lateral",(x+d*.68,y,z),(.055,.79,.11),madeira)
    ovos=[]
    for i in range(quantidade):
        col=(i%4)-1.5; fila=(i//4)-.5
        ovos.append(ovo(x+col*.28,y+fila*.31,.13,1.12))
    return ovos


def grupo_tenda(lado=0,com_aves=False):
    barraca(lado,.92)
    povo=[humano(tipo,lado+x,y,r,g,i*.7) for i,(tipo,x,y,r,g) in enumerate([
        (1,-1.08,.42,.12,'fome'),(4,.03,.58,-.08,'repouso'),(3,1.38,.72,-.13,'fome')])]
    if com_aves:
        for i in range(3):
            ave(lado-.96+i*.87,-.48+(i%2)*.19,i,(i%2)*2.5+.2,.7,i)
    return povo


def aldeia():
    import locais
    locais.paisagem()
    grupo_tenda(-2.6); grupo_tenda(2.45)
    humano(0,-.3,-.64,.12,'fome',.5)
    for i in range(5):
        a=ave(-2.4+i*1.1,-.9+(i%2)*.5,i%3,i*1.45, .2,i)
        aparecer(a,.59+i*.035,.095)
    cam([(0,(-.6,-8,3.1),(0,.38,1.23),7.85),
         (.44,(.55,-6.3,2.1),(-.4,.12,1),5.65),
         (1,(1.05,-5.6,1.65),(.04,-.12,.8),4.9)])


def jantar():
    import locais,aves
    locais.paisagem(noite=True)
    barraca(0,1.25,escala=1.12)
    humano(2,-1.15,.65,.3,'festa',.4)
    humano(5,.4,1.12,-.10,'propor',.8)
    humano(3,1.45,.28,-.40,'festa',.2)
    fog=aves.fogueira("Fogo e assado",0,-.36)
    # Cinzas luminosas sobem por trilhas defasadas ao redor do alimento.
    brasa=cor("Centelha | cor quente",(1,.59,.055))
    for i in range(12):
        ang=i*2.39996; bx=.28*math.cos(ang); by=-.36+.2*math.sin(ang)
        o=caixa("Centelha",(bx,by,.3),(.035,.035,.054),brasa)
        passo=24+i%6
        for f in range(-i*9, _n+passo, passo):
            o.location=(bx,by,.27); chave(o,'location',f)
            o.scale=(.45,.45,.45); chave(o,'scale',f)
            o.location=(bx+.11*math.sin(ang),by,.94+(i%3)*.08); chave(o,'location',f+passo-2)
            o.scale=(.02,.02,.02); chave(o,'scale',f+passo-2)
    cam([(0,(-1.7,-6.6,2.25),(0,.20,1.13),5.3),
         (.39,(-.48,-4.3,1.6),(-.10,-.19,.85),3.1),
         (.67,(.72,-4.8,1.52),(.10,.25,1.03),3.8),
         (1,(1.10,-3.62,1.66),(.50,.95,1.43),1.83)])


def poedeiras():
    import locais
    locais.paisagem()
    barraca(0,1.6,escala=1.17)
    humano(0,-.63,.72,.16,'repouso')
    humano(1,1.13,.85,-.3,'apontar',1)
    humano(4,-1.7,1.11,.18,'fome',2)
    ave(-.88,-.67,0,.15,1.4,.7)
    ave(.88,-.24,2,2.95,.8,1.1)
    for i in range(4):
        o=ovo(.03+i*.22,-.5-(i%2)*.20,escala=1.17)
        aparecer(o,.5+i*.05,.08)
    cam([(0,(-1.4,-6.8,1.98),(-.2,.45,1.08),5.6),
         (.5,(.42,-4.68,1.55),(.25,-.05,.8),3.98),
         (1,(1.35,-3.73,1.08),(.38,-.32,.48),2.75)])


def reprodutor():
    import locais
    locais.paisagem()
    barraca(.3,2.25)
    humano(4,-1.2,1.09,.32,'propor',.6)
    humano(1,1.28,1.29,-.31,'repouso',.9)
    ave(.2,-.64,1,-.55,.75,.4,escala=1.2)
    ave(-.6,.45,0,.45,.44,1.6)
    cam([(0,(-1.7,-3.77,.82),(.1,-.39,.57),2.45),
         (1,(.63,-2.87,.84),(.19,-.48,.55),1.60)])


def proposta():
    import locais
    locais.paisagem()
    barraca(-3.0,2.12,.04); barraca(2.1,1.69,-.03)
    humano(4,1.43,.63,-.26,'repouso')
    humano(1,2.21,.63,-.57,'apontar')
    p=humano(0,-1.75,-.2,.54,'propor',.41)
    mover(p,[(0,(-2.05,-.2,0)),(.65,(-.32,-.22,0)),(1,(-.21,-.22,0))])
    humano(2,-2.02,.58,.13,'repouso',1)
    ave(.52,-.43,0,.58,.7,2)
    cam([(0,(-.7,-4.5,1.72),(-1.45,.2,1.15),3.3),
         (.55,(-.05,-5.15,1.83),(-.05,.18,1.08),4.15),
         (1,(1.2,-5.25,1.9),(.54,.28,1.1),4.5)])


def acordo():
    import locais
    locais.paisagem()
    barraca(-2.8,2.25);barraca(2.3,2.44)
    humano(0,-.96,.28,.45,'propor',.3); humano(1,1,.57,-.49,'propor',2)
    humano(4,2.42,1.05,-.45,'repouso',.7)
    ave(-.62,-.68,0,.1,1.02,.5); ave(1.23,-.7,2,2.8,.83,1.3)
    for i in range(3): ovo(.06+i*.24,-.59-(i%2)*.17)
    cam([(0,(-1.15,-5.85,1.63),(-.06,.25,1.20),4.78),
         (.48,(-.1,-5.3,1.88),(.04,.30,1.22),4.42),
         (1,(1.43,-5.45,1.55),(.52,.13,.89),4.8)])


def ninho():
    import locais
    locais.paisagem()
    relva(0,1,4.7,3.55); coop(.2,1.28,1.16)
    ave(1.1,.42,1,2.8,.35,1)
    for i in range(3):
        x=-.88+i*.57; y=-.31+(i%2)*.19
        o=ovo(x,y,.03,1.23)
        q=ave(x-.02,y+.02,0,.45+i*.78,.25,i,pequena=True,escala=1.23)
        e=o.scale.copy()
        bat=.18+i*.105
        for f,s in [(0,1),(bat,1),(bat+.045,.20),(bat+.075,.001)]:
            o.scale=e*s;chave(o,'scale',tempo(f))
        aparecer(q,bat+.018,.105)
    cam([(0,(-.48,-5.4,1.76),(0,.4,.89),4.05),
         (.52,(.34,-3.5,1.10),(-.12,-.25,.36),2.72),
         (1,(.70,-3.67,1.02),(.05,-.20,.43),2.68)])


def colher():
    import locais
    locais.paisagem();relva(0,.8,6.3,4.5)
    coop(-1.23,1.46,1.02); cerca(1.3,2.06,3.8)
    humano(2,1.56,.63,-.36,'apontar',.7)
    ave(-.97,-.42,0,.16,.57,.3);ave(.11,-.5,2,-.31,.47,1)
    ovos=cesta(.98,-.7,8)
    for i,o in enumerate(ovos): aparecer(o,.03+i*.057,.071)
    cam([(0,(-1.36,-4.15,1.24),(-.56,.16,.66),3.28),
         (1,(1.79,-2.85,1.29),(.77,-.47,.44),2.15)])


def fazenda():
    import locais
    locais.paisagem()
    rnd=random.Random(731)
    for i,(x,y) in enumerate([(0,0),(-4,4),(4.2,4.3),(-5.7,8),(0,8.4),(5.8,9.1)]):
        relva(x,y,4.,3.8);coop(x-.24,y+.65,.84,rnd.uniform(-.12,.12))
        if i%2==0: arvore(x+1.15,y+1.1,.61)
        for j in range(3):
            a=ave(x-.95+j*.8,y-.65+rnd.uniform(-.25,.22),j%3,rnd.uniform(0,6),.55,i+j)
            if i>0: aparecer(a,.13+i*.058,.06)
    casa(-4.8,10,0,.72);casa(3.2,11.15,0,.64)
    cam([(0,(.80,-4.64,1.98),(.05,-.11,.67),3.8),
         (.44,(2.1,-7.3,5.55),(0,2.5,.1),8.15),
         (1,(3.0,-9.5,14.4),(0,4.0,.05),16.7)])


def reclamar():
    import locais
    locais.paisagem();barraca(0,1.06,escala=1.22)
    humano(2,-1.32,.69,.23,'fome',1);humano(3,.26,.5,-.14,'fome',.2)
    humano(5,1.55,.82,-.42,'apontar',1.3)
    for i in range(6):ossos(-1.57+i*.54,-.69+(i%3)*.24,.72+i%2*.25,i*1.35)
    cam([(0,(-.33,-5.51,2.18),(0,.2,.86),4.9),
         (.46,(.57,-3.8,.98),(-.26,-.31,.44),3.16),
         (1,(.96,-3.22,1.62),(.24,.46,1.30),2.35)])


def sustento():
    import locais
    locais.paisagem();relva(0,.9,7.25,5.7);casa(-1.05,2.1,0,.76,-.08);arvore(2.03,1.69,.85)
    humano(4,-1.25,.23,.24,'repouso',.3);humano(1,.58,.33,-.25,'festa',.8)
    ave(-.65,-.62,0,.22,.67,.4);cesta(1.2,-.63,8)
    cam([(0,(-1.61,-5.56,1.96),(-.05,.2,1.09),4.9),
         (1,(1.51,-3.12,1.39),(.79,-.30,.54),2.55)])


def muitas():
    import locais
    locais.paisagem();relva(0,1,8.8,7.0);casa(.65,2.8,1,.98);arvore(-2.48,2.15,.96); coop(2.44,1.6,.71)
    humano(0,.28,.1,.05,'propor',.85); humano(2,-1.34,.5,.17,'apontar',.48)
    r=random.Random(204)
    for i in range(21):
        x=(i%7-3)*.75+r.uniform(-.14,.14);y=-1.91+(i//7)*.65+r.uniform(-.14,.14)
        ave(x,y,i%3,r.uniform(-2.6,2.7),r.uniform(.3,.87),i)
    cam([(0,(-.88,-4.93,1.32),(-.2,-.61,.71),3.93),
         (.45,(.28,-5.9,1.91),(.04,-.23,.88),5.45),
         (1,(1.55,-6.75,2.62),(.26,.08,1.08),6.75)])


def trabalho():
    import locais
    locais.paisagem(); barraca(.38,1.83,escala=1.12)
    p=humano(0,-1.22,-.24,.47,'propor',.8)
    mover(p,[(0,(-1.98,-.24,0)),(.4,(-1.04,-.24,0)),(1,(-1.04,-.24,0))])
    humano(3,.96,.18,-.51,'propor',.78);humano(5,1.78,.79,-.43,'repouso',1.15)
    for i in range(4):ossos(.71+i*.29,-.74+(i%2)*.2,.65,i*1.27)
    cesta(-.55,-.53,5)
    cam([(0,(-1.5,-5.04,1.63),(-.35,.21,1.17),4.25),
         (.52,(-.15,-5.65,1.88),(.0,.3,1.24),4.65),
         (1,(1.24,-5.44,1.63),(.23,.1,1.05),4.48)])


def destinos():
    import locais
    locais.paisagem()
    grupo_tenda(-4.65)
    for i in range(4):ossos(-5.6+i*.6,-.45+(i%2)*.3,.76,i*.8)
    relva(.05,1.55,4.9,4.7); casa(-.12,1.83,0,.7,.03);arvore(-1.56,2.28,.54)
    humano(4,-.53,.18,.09,'repouso',1.4,.9)
    ave(.25,-.28,0,2.6,.6,.3,False,.85); cesta(.9,-.25,5)
    relva(4.8,1.65,5.1,5.25); casa(4.65,2.62,1,1.02,.02);arvore(6.8,2.25,.75);coop(6.05,.86,.48)
    humano(0,4.57,.28,-.04,'repouso',.3,.93);humano(2,3.38,.36,.15,'propor',.9,.91)
    for i in range(9):
        x=3.25+(i%4)*.78;y=-.75+(i//4)*.4
        ave(x,y,i%3,i*1.29,.38,i,False,.85)
    cam([(0,(3.95,-6.24,2.42),(2.75,.9,1.07),7.55),
         (.40,(1.19,-11.55,4.81),(.02,.75,1.45),14.85),
         (.65,(.5,-12.84,5.33),(.15,.75,1.69),16.25),
         (1,(.76,-13.5,5.96),(.16,.75,1.9),16.98)])


def construir(indice):
    """Reinicia o conteúdo do arquivo e devolve a cena com câmera e animação."""
    global _n
    if isinstance(indice,str):indice=NOMES.index(indice)
    if not 0<=indice<len(PLANOS):raise ValueError(indice)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c, do_unlink=True)
    bpy.data.orphans_purge(do_recursive=True)
    import aves
    aves._MATERIAIS.clear(); aves._FORMAS.clear()
    _prototipos.clear();_cores.clear()
    _n=CORTES[indice+1]-CORTES[indice]
    cena=bpy.context.scene
    cena['noite'] = indice == 1
    cena.frame_start=1;cena.frame_end=_n;cena.render.fps=24
    cena.render.resolution_x=720;cena.render.resolution_y=1280
    cena.render.pixel_aspect_x=1;cena.render.pixel_aspect_y=1
    (aldeia,jantar,poedeiras,reprodutor,proposta,acordo,ninho,colher,
     fazenda,reclamar,sustento,muitas,trabalho,destinos)[indice]()
    cena.frame_set(1)
    bpy.context.view_layer.update()
    return cena
