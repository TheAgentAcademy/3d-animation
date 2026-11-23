"""Elenco original de uma aldeia em Blender. Os personagens olham para -Y."""
import math
import bpy
from mathutils import Vector

# Pele, cabelo, tecido principal, tecido de baixo, sapatos, acessório e faixa.
FIGURINOS = [
    ("E9AA82", "E2E4D9", "248F7B", "E9DEC1", "493924", "FFD378", "15574B"),
    ("BF825F", "31252A", "A4ABB1", "384050", "3F302B", "C8C3A8", "515965"),
    ("D69868", "48302B", "D49E33", "4D5961", "4B342D", "F5D17B", "87532F"),
    ("9D6749", "30272A", "9E6C4F", "EEE0B9", "403330", "D4A773", "5D4139"),
    ("B77958", "493039", "65B9C9", "495A7B", "50362E", "DDD9C7", "364259"),
    ("E6A078", "974C34", "AD5C45", "837056", "4C3531", "E5B980", "784735"),
]


def tinta(cor):
    nome = 'Povo_' + cor
    mat = bpy.data.materials.get(nome)
    if mat is None:
        mat = bpy.data.materials.new(nome)
        rgb = [int(cor[i:i+2], 16) / 255 for i in (0, 2, 4)]
        rgba = tuple(c / 12.92 if c < .04045 else ((c+.055)/1.055)**2.4 for c in rgb) + (1,)
        mat.diffuse_color = rgba
        mat.roughness = .88
        mat.specular_intensity = .18
        mat.use_nodes = True
        bs = mat.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value = rgba
        bs.inputs['Roughness'].default_value = .85
    return mat


class Escultura:
    def __init__(self):
        self.v, self.f, self.c = [], [], []

    def face(self, indices, cor):
        self.f.append(indices)
        self.c.append(cor)

    def aneis(self, perfis, cor, lados=12, fase=0):
        # Each horizontal ring has its own elliptical radii and centre.
        inicio = len(self.v)
        for z, rx, ry, cx, cy in perfis:
            for i in range(lados):
                a = fase - math.pi/2 + 2*math.pi*i/lados
                self.v.append((cx + rx*math.cos(a), cy + ry*math.sin(a), z))
        self.face(tuple(inicio+i for i in reversed(range(lados))),cor)
        for k in range(len(perfis)-1):
            for i in range(lados):
                a=inicio+k*lados+i
                b=inicio+k*lados+(i+1)%lados
                self.face((a,b,b+lados,a+lados),cor)
        ult=inicio+(len(perfis)-1)*lados
        self.face(tuple(ult+i for i in range(lados)),cor)

    def bola(self, p, raios, cor, n=12, perfis=(-.96,-.69,-.28,.20,.68,.96)):
        x,y,z=p; rx,ry,rz=raios
        self.aneis([(z+t*rz,rx*math.sqrt(1-t*t),ry*math.sqrt(1-t*t),x,y) for t in perfis],cor,n)

    def vara(self, a, b, r1, r2, cor, n=8):
        a,b=Vector(a),Vector(b)
        d=(b-a).normalized()
        if d.length == 0: return
        h=Vector((0,0,1)) if abs(d.z)<.9 else Vector((0,1,0))
        u=d.cross(h).normalized(); v=d.cross(u)
        inicio=len(self.v)
        for p,r in ((a,r1),(b,r2)):
            for i in range(n):
                ang=2*math.pi*i/n
                self.v.append(tuple(p+r*(math.cos(ang)*u+math.sin(ang)*v)))
        self.face(tuple(inicio+i for i in reversed(range(n))),cor)
        for i in range(n):
            aa=inicio+i;bb=inicio+(i+1)%n
            self.face((aa,bb,bb+n,aa+n),cor)
        self.face(tuple(inicio+n+i for i in range(n)),cor)

    def chapa(self, pts, cor):
        i=len(self.v)
        self.v.extend(pts)
        self.face(tuple(range(i,i+len(pts))),cor)

    def tecido(self, linhas, cor, fase=math.pi/12):
        self.aneis([(z,rx,ry,0,0) for z,rx,ry in linhas],cor,12,fase)

    def gerar(self,nome):
        m=bpy.data.meshes.new(nome);m.from_pydata(self.v,[],self.f);m.update()
        mapa={cor:i for i,cor in enumerate(dict.fromkeys(self.c))}
        for cor in mapa:m.materials.append(tinta(cor))
        m.polygons.foreach_set('material_index',[mapa[cor] for cor in self.c])
        return m


def _rosto(e,tipo,gesto,pele,cabelo):
    e.vara((0,.008,1.22),(0,0,1.49),.075,.074,pele)
    largo=(.181,.159,.179,.192,.164,.161)[tipo]
    # Squared temples, a narrower jaw and a separate chin plane.
    e.aneis([(1.405,.075,.105,0,-.010),(1.455,largo*.82,.14,0,-.010),
             (1.52,largo,.151,0,-.002),(1.65,largo,.148,0,0),
             (1.72,largo*.91,.135,0,.010),(1.76,largo*.63,.099,0,.008)],pele,12,math.pi/12)
    for lado in (-1,1):
        e.bola((lado*largo*.97,.002,1.566),(.035,.032,.055),pele,n=8)
        if tipo==0: e.bola((lado*largo,.003,1.521),(.012,.015,.020),"EDB858",n=8)
        x=lado*largo*.405
        e.bola((x,-.146,1.60),(.043,.014,.042),"634439")
        e.bola((x,-.155,1.601),(.037,.011,.037),"FFF7D9")
        e.bola((x+.005,-.163,1.599),(.019,.008,.024),("5B4D45","4F443B","79573C","6C5044","795132","536348")[tipo])
        e.bola((x+.005,-.170,1.599),(.010,.005,.014),"29232C",n=8)
        e.bola((x+.000,-.175,1.609),(.005,.003,.006),"FAEFDC",n=8)
        incl=.008 if gesto in ('fome','propor') else -.001
        e.vara((x-lado*.037,-.148,1.658+incl),(x+lado*.034,-.131,1.65-incl),.012,.010,cabelo)
        if tipo==0:
            e.vara((x+lado*.025,-.14,1.548),(x+lado*.041,-.125,1.552),.004,.003,"B47E65")
    e.bola((0,-.160,1.548),(.030,.032,.042),pele,n=8)
    e.bola((.002,-.175,1.529),(.037,.022,.017),pele,n=8)
    if gesto in ('propor','festa'):
        e.bola((0,-.146,1.483),(.042,.006,.018),"703E36",n=10)
        e.vara((-.030,-.150,1.492),(.030,-.150,1.492),.006,.006,"FBE7C6")
    else:
        e.vara((-.036,-.142,1.487),(0,-.149,1.482),.006,.007,"9B5B52")
        e.vara((0,-.149,1.482),(.035,-.142,1.489),.007,.004,"9B5B52")
    e.aneis([(1.671,largo*1.025,.157,0,.010),(1.732,largo*.99,.148,0,.014),
             (1.775,largo*.77,.127,0,.010),(1.791,largo*.40,.068,0,.010)],cabelo,12,math.pi/12)
    e.bola((0,.093,1.658),(.162,.084,.108),cabelo)
    for lado in (-1,1):
        e.bola((lado*largo*.88,.017,1.649),(.037,.065,.066),cabelo,n=9)
    if tipo==0:
        e.bola((0,.155,1.715),(.108,.098,.091),"C8CFCC")
        e.bola((-.012,.180,1.731),(.089,.068,.061),cabelo)
        for lado in (-1,1):
            e.vara((lado*.034,-.116,1.741),(lado*.128,-.095,1.687),.027,.021,"F0EFE1")
    elif tipo in (1,2,3,5):
        for j in range(4):
            x=(j-1.5)*.057
            e.bola((x,-.114+(abs(x)*.12),1.708+.012*j),(.059,.048,.047),cabelo,n=9)
        if tipo in (2,3,5):
            for lado in (-1,1):
                e.vara((lado*.007,-.151,1.510),(lado*.063,-.135,1.493),.011,.009,cabelo)
        if tipo==2:
            for i in range(7):
                a = i * 2 * math.pi / 7
                e.bola((math.cos(a)*.122,.015+math.sin(a)*.083,1.724),(.073,.061,.065),cabelo,n=8)
        if tipo==5:
            for lado in (-1,1):
                for j in range(3):
                    e.bola((lado*(.079+.014*j),-.135+.006*j,1.542+.005*(j%2)),(.004,.003,.004),"9A6044",n=8)
        if tipo==3:
            e.aneis([(1.708,.20,.162,0,.014),(1.743,.197,.164,.002,.015),
                     (1.780,.184,.156,.005,.02),(1.798,.151,.124,.012,.026)],"C1A687",12,math.pi/12)
            e.aneis([(1.700,.201,.164,0,.013),(1.719,.202,.165,0,.014)],"7B685A",12,math.pi/12)
            e.aneis([(1.398,.075,.10,0,-.011),(1.425,.123,.13,0,-.011),(1.457,.139,.142,0,-.010)],cabelo,12,math.pi/12)
            for lado in (-1,1):
                e.vara((lado*.148,-.018,1.571),(lado*.130,-.053,1.461),.024,.028,cabelo)
    elif tipo==4:
        e.bola((0,.118,1.548),(.14,.072,.154),cabelo)
        e.aneis([(1.702,.18,.16,0,.01),(1.733,.18,.155,0,.01),(1.767,.13,.12,0,.018)],"E7DFCE",12)
        e.bola((.121,.111,1.697),(.055,.050,.039),"D9CCB3",n=8)


def _modelar(tipo,gesto):
    pele,cabelo,base,calca,bota,acento,faixa=FIGURINOS[tipo]
    e=Escultura()
    saia=tipo in (0,3,4)
    for s in (-1,1):
        x=s*.098
        e.bola((x,-.045,.085),(.081,.150,.077),bota)
        e.aneis([(.018,.080,.145,x,-.044),(.043,.082,.150,x,-.044)],"3D342E",10)
        e.vara((x,.008,.11),(x,.0,.45),.058,.073,calca)
        e.vara((x,.0,.43),(s*.09,.01,.80),.081,.088,calca)
        e.vara((x,.0,.105),(x,.0,.23),.061,.066,bota)
    ombro=(.220,.232,.246,.257,.206,.225)[tipo]
    largo=(.204,.17,.188,.221,.17,.181)[tipo]
    camisa=calca if tipo in (0,3) else base
    e.tecido([(.67,largo,.133),(.80,largo*.9,.143),(.98,largo,.149),
              (1.20,ombro,.136),(1.296,ombro*.92,.116),(1.343,.090,.081)],camisa)
    if saia:
        if tipo!=3:
            e.tecido([(.23,largo*1.31,.194),(.26,largo*1.45,.211),(.38,largo*1.42,.205),
                      (.66,largo*1.05,.158),(.89,largo*.79,.132)],base if tipo==0 else calca)
            e.tecido([(.265,largo*1.45+.001,.213),(.285,largo*1.44+.001,.214)],faixa)
        avental=base if tipo in (0,3) else faixa
        if tipo in (0,3):
            e.chapa([(-largo*.67,-.135,1.258),(-largo*.63,-.154,.86),(largo*.63,-.154,.86),(largo*.67,-.135,1.258)],avental)
            for s in (-1,1):
                e.vara((s*.155,-.093,1.302),(s*.104,-.141,1.19),.021,.023,avental)
            e.chapa([(-largo*.67,-.150,.91),(-largo*.91,-.185,.40),(largo*.91,-.185,.40),(largo*.67,-.150,.91)],avental)
            e.chapa([(-.078,-.187,.738),(-.071,-.188,.656),(.052,-.188,.651),(.064,-.187,.731)],faixa)
            e.vara((-.077,-.19,.735),(.067,-.19,.729),.004,.004,acento)
    else:
        if tipo==5:
            e.chapa([(-.099,-.115,1.308),(.006,-.152,1.192),(.095,-.122,1.311)],"E2A359")
            e.chapa([(.014,-.153,1.226),(.096,-.155,1.134),(.084,-.156,1.235)],"C78149")
        e.tecido([(.679,largo*1.07,.144),(.71,largo*1.06,.144),(.877,largo*.92,.142)],base)
        if tipo in (1,2):
            for s in (-1,1):
                e.chapa([(0,-.141,1.231),(s*.086,-.138,1.297),(s*.115,-.123,1.316),(s*.062,-.144,1.211)],acento)
            for z in (.976,1.073,1.167):e.bola((.017,-.149,z),(.010,.006,.010),acento,n=8)
    e.tecido([(.858,largo*.99,.149),(.899,largo*.97,.149)],faixa)
    e.chapa([(-.028,-.150,.901),(-.028,-.150,.854),(.027,-.15,.854),(.027,-.15,.901)],acento)
    # Keep arms separate from the torso silhouette so hands read in wide shots.
    if gesto=='propor':
        juntas=[((-.33,-.05,.97),(-.38,-.17,1.15)),((.35,-.04,1.03),(.44,-.19,1.20))]
    elif gesto=='apontar':
        juntas=[((-.29,-.01,.97),(-.26,-.13,.82)),((.45,-.05,1.21),(.63,-.14,1.29))]
    elif gesto=='fome':
        juntas=[((-.31,-.02,1.01),(-.08,-.19,.94)),((.30,-.03,.99),(.02,-.22,1.03))]
    elif gesto=='festa':
        juntas=[((-.37,-.03,1.30),(-.43,-.11,1.52)),((.37,-.03,1.31),(.42,-.12,1.54))]
    else:
        juntas=[((-.278,.005,1.02),(-.277,-.057,.79)),((.284,.004,1.025),(.286,-.057,.80))]
    for i,s in enumerate((-1,1)):
        om=(s*ombro*.94,.0,1.24)
        cotovelo,punho=juntas[i]
        ponta=tuple(Vector(om).lerp(Vector(cotovelo),.72))
        e.bola(om,(.085,.079,.089),camisa,n=10)
        e.vara(om,ponta,.084,.075,camisa)
        e.vara(ponta,cotovelo,.065,.052,pele if tipo in (0,3,4) else camisa)
        e.vara(cotovelo,punho,.053,.038,pele if tipo in (0,2,3,4,5) else base)
        e.bola(punho,(.053,.044,.059),pele,n=10)
        if gesto=='apontar' and i==1:
            e.vara(punho,(punho[0]+.095,punho[1]-.02,punho[2]+.018),.016,.011,pele,8)
        else:
            e.bola((punho[0]-s*.034,punho[1]-.018,punho[2]+.008),(.027,.023,.033),pele,n=8)
    _rosto(e,tipo,gesto,pele,cabelo)
    return e.gerar('Elenco_%d_%s'%(tipo,gesto))


def pessoa(nome,x,y,tipo=0,rot=0,escala=1,gesto='repouso'):
    """Cria uma instância com a postura solicitada, olhando para -Y, a partir do chão."""
    tipo=int(tipo)%len(FIGURINOS)
    if gesto not in ('repouso','propor','fome','apontar','festa'):
        raise ValueError('Gesto desconhecido: '+str(gesto))
    key=tipo,gesto
    mesh=bpy.data.meshes.get('Elenco_%d_%s'%key)
    if mesh is None: mesh=_modelar(tipo,gesto)
    obj=bpy.data.objects.new(nome,mesh)
    bpy.context.collection.objects.link(obj)
    obj.location=(x,y,0);obj.rotation_euler.z=rot;obj.scale=(escala,)*3
    return obj
