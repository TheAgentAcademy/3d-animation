"""Decoração original da aldeia. Coordenadas em metros, fachada voltada para -Y."""
import base64
import colorsys
import json
import math
from pathlib import Path
import random
import zlib

import bpy
from mathutils import Vector

TAU = 2 * math.pi


def _linear(s):
    c = s / 255
    return c / 12.92 if c < .04045 else ((c + .055) / 1.055) ** 2.4


def _cor(nome, rgb):
    nome = 'Aldeia/' + nome
    mat = bpy.data.materials.get(nome)
    if mat is None:
        mat = bpy.data.materials.new(nome)
        mat.diffuse_color = (*(_linear(x) for x in rgb), 1)
    return mat


class _Partes:
    def __init__(self):
        self.verts = []
        self.faces = []
        self.indices = []
        self.mats = []
        self.slots = {}

    def faces_em(self, verts, faces, mat):
        start = len(self.verts)
        self.verts.extend(verts)
        slot = self.slots.get(mat.name)
        if slot is None:
            slot = len(self.mats)
            self.mats.append(mat)
            self.slots[mat.name] = slot
        for fa in faces:
            self.faces.append(tuple(start + i for i in fa))
            self.indices.append(slot)

    def pol(self, verts, mat):
        self.faces_em(verts, [range(len(verts))], mat)

    def caixa(self, loc, size, mat):
        x,y,z = loc
        w,d,h = (a*.5 for a in size)
        vs=[(x+a*w,y+b*d,z+c*h) for a,b,c in
            [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.faces_em(vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], mat)

    def haste(self, ini, fim, raio, mat, n=6, raio2=None):
        a,b = Vector(ini),Vector(fim)
        eixo = (b-a).normalized()
        ref = Vector((1,0,0)) if abs(eixo.x)<.8 else Vector((0,1,0))
        u=eixo.cross(ref).normalized()
        v=eixo.cross(u)
        r2=raio if raio2 is None else raio2
        vs = [tuple(cent+rad*(u*math.cos(i*TAU/n)+v*math.sin(i*TAU/n))) for cent,rad in [(a,raio),(b,r2)] for i in range(n)]
        fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.faces_em(vs,fs,mat)

    def copa(self, loc, size, mats, seed=0):
        rng=random.Random(seed)
        x,y,z=loc
        rx,ry,rz=size
        n=8
        rings=[]
        for level,rr,phase in [(-.67,.65,.16),(-.04,1.,0),(.56,.80,.38)]:
            ring=[]
            for i in range(n):
                ang=i*TAU/n+phase+rng.uniform(-.09,.09)
                rad=rr*rng.uniform(.86,1.05)
                ring.append((x+rx*rad*math.cos(ang),y+ry*rad*math.sin(ang),z+rz*(level+rng.uniform(-.10,.10))))
            rings.append(ring)
        low=(x-.08*rx,y-.03*ry,z-rz); top=(x+.13*rx,y,z+rz)
        for i in range(n):
            j=(i+1)%n
            self.pol([low,rings[0][j],rings[0][i]],mats[0])
            for k in range(2):
                r,s=rings[k:k+2]
                mat=mats[min(len(mats)-1,max(0,k+rng.choice((-1,0,0,1))))]
                self.pol([r[i],r[j],s[j]],mat)
                self.pol([r[i],s[j],s[i]],mats[min(len(mats)-1,k+rng.choice((0,1)))])
            self.pol([rings[-1][i],rings[-1][j],top],mats[-rng.choice((1,1,2))])

    def terminar(self,nome,x=0,y=0,rot=0,escala=1):
        mesh=bpy.data.meshes.new(nome)
        mesh.from_pydata(self.verts,[],self.faces)
        for mat in self.mats:
            mesh.materials.append(mat)
        mesh.polygons.foreach_set('material_index',self.indices)
        mesh.update()
        ob=bpy.data.objects.new(nome,mesh)
        bpy.context.collection.objects.link(ob)
        ob.location=(x,y,0)
        ob.rotation_euler.z=rot
        ob.scale=(escala,)*3
        return ob


def _madeiras():
    return [_cor('Carvalho',(108,72,46)),_cor('Madeira clara',(157,114,72)),_cor('Pontas escuras',(74,51,41))]


def _folhas():
    return [_cor('Folha escura',(62,108,80)),_cor('Folha fria',(78,130,89)),_cor('Folha média',(101,153,91)),_cor('Folha clara',(133,172,107))]


def tenda(nome,x,y,rot=0,escala=1):
    b=_Partes()
    carvalho,madeira,escura=_madeiras()
    fios=_cor('Corda',(154,127,85))
    panos=[_cor('Lona petróleo',(66,94,106)),_cor('Lona aço',(74,106,117)),_cor('Lona seca',(61,88,100))]
    remendo=_cor('Remendo de lona',(115,136,138))
    pano_fundo=_cor('Lona de estopa',(150,119,82))
    # Os nós e o caimento acentuam a diferença entre a lona e as estacas retas.
    for u in (-1,1):
        for v in (-1,1):
            a=(2.02*u,1.12*v,.03)
            top=(1.95*u,1.09*v,2.60+.10*v+.05*u)
            b.haste(a,top,.065,carvalho,7,.047)
            b.haste((top[0],top[1],top[2]-.15),(top[0],top[1],top[2]-.045),.064,fios,7)
            base=(2.34*u,1.40*v,.065)
            b.haste(top,base,.016,fios,5)
            b.haste((base[0],base[1],0),(base[0]-.02*u,base[1],.20),.032,madeira)
    def pt(ax,ay):
        # Bordas irregulares e centro mais alto em profundidade.
        return (ax,ay,2.48+.075*ay+.043*ax+.15*max(0,1-abs(ay/1.14))-.16*max(0,1-abs(ax/2.06)))
    for i in range(8):
        x0=-2.10+i*.525; x1=x0+.525
        for k,(a,c) in enumerate([(-1.18,0),(0,1.18)]):
            corn=[pt(x0,a),pt(x1,a),pt(x1,c),pt(x0,c)]
            b.pol(corn,panos[(i//3+k)%3])
        p,q=pt(x0,-1.18),pt(x1,-1.18)
        b.pol([p,(p[0],p[1]-.024,p[2]-.13-.022*(i%3)),(q[0],q[1]-.024,q[2]-.14-.017*(i%2)),q],panos[i%3])
    for xx,yy in [(-1.48,-.94),(.69,-.95),(1.32,.35),(-.32,-.42)]:
        verts=[pt(xx+dx,yy+dy) for dx,dy in [(-.10,-.13),(.12,-.12),(.11,.13),(-.09,.15)]]
        b.pol([(a,c,d+.012) for a,c,d in verts],remendo)
    for i in range(4):
        x0=-1.95+i*.98
        b.pol([(x0,1.03,.23),(x0+.96,1.03,.22+.05*(i%2)),(x0+.96,1.03,2.34),(x0,1.03,2.32)],pano_fundo)
    b.caixa((1.68,.30,.22),(.52,.73,.42),madeira)
    for z in (.11,.30): b.caixa((1.68,-.076,z),(.54,.022,.047),carvalho)
    return b.terminar(nome,x,y,rot,escala)


def arvore(nome,x,y,escala=1):
    b=_Partes(); trunk,lighter,_=_madeiras(); folhas=_folhas()
    s=round((abs(x)*170+abs(y)*71))%991
    b.haste((0,0,0),(.055,0,1.95),.20,trunk,7,.12)
    for i,(xx,yy,z,r) in enumerate([(-.62,.06,2.29,1.01),(.62,.08,2.42,.91),(.12,.36,2.88,1.04),(.04,-.42,2.44,.86)]):
        b.haste((.01,.01,1.33),(xx,yy,z),.108,lighter,6,.065)
        b.copa((xx,yy,z),(r,r*.87,r*1.02),folhas,s+31*i)
    return b.terminar(nome,x,y,0,escala)


def gramado(nome,x,y,largura=6,profundidade=5):
    b=_Partes(); rng=random.Random(51)
    mats=[_cor('Grama sol',(136,194,76)),_cor('Grama luz',(145,201,87)),_cor('Grama fria',(125,182,73)),_cor('Talude',(112,140,65))]
    n=32; w=largura/2; d=profundidade/2; ring=[]
    # Superelipse com pontas suaves, talude visível em close.
    for i in range(n):
        t=TAU*i/n; co,si=math.cos(t),math.sin(t); var=rng.uniform(.97,1.02)
        ring.append((math.copysign(abs(co)**.40,w*co)*w*var,math.copysign(abs(si)**.40,d*si)*d*var,.055))
    b.pol(ring,mats[0])
    for i,p in enumerate(ring):
        q=ring[(i+1)%n]; b.pol([p,(p[0]*1.02,p[1]*1.02,.002),(q[0]*1.02,q[1]*1.02,.002),q],mats[3])
    for _ in range(36):
        xx,yy=rng.uniform(-.83,.83)*w,rng.uniform(-.82,.82)*d
        for k in range(rng.randint(2,4)):
            j=xx+rng.uniform(-.08,.08); v=yy+rng.uniform(-.03,.03)
            b.pol([(j-.013,v,.056),(j+.022,v,.056),(j+.04,v+.025,.10+rng.random()*.06)],mats[rng.choice((1,2))])
    return b.terminar(nome,x,y)


def casa(nome,x,y,tipo=0,rot=0,escala=1):
    b=_Partes(); w,d,h=(2.7,2.25,2.22) if tipo in (0,'chale') else (3.15,2.72,3.62)
    alto=h>3
    carvalho,madeira,escura=_madeiras()
    base=_cor('Pedra da base',(141,119,94))
    parede=_cor('Reboco dourado',(211,173,113)) if alto else _cor('Reboco de cal',(238,218,175))
    guarnicao=_cor('Esquadria de creme',(248,229,187))
    escuro=_cor('Vidro',(52,80,98)); ref=_cor('Vidro refletido',(103,143,155))
    telha=_cor('Telha carvão',(91,85,78)) if alto else _cor('Telha de barro',(169,75,56))
    telha2=_cor('Cumeeira',(111,100,86)) if alto else _cor('Cumeeira terracota',(192,94,70))
    xx=w/2; yy=d/2; z=h+(.89 if alto else .79); frente=-yy
    b.caixa((0,0,.135),(w+.10,d+.10,.27),base); b.caixa((0,0,(h+.21)/2),(w,d,h-.21),parede)
    b.pol([(-xx,frente,h),(xx,frente,h),(0,frente,z)],parede)
    b.pol([(xx,-frente,h),(-xx,-frente,h),(0,-frente,z)],parede)
    for s in (-1,1):
        inner=(0, -yy-.20,z+.03); inner2=(0,yy+.17,z+.03)
        outer=(s*(xx+.17),-yy-.20,h-.07); outer2=(s*(xx+.17),yy+.17,h-.07)
        b.pol([inner,inner2,outer2,outer],telha)
        b.haste(outer,outer2,.052,telha2,6)
        b.haste(inner,outer,.061,guarnicao,6)
        for i in range(1,6):
            f=i/6; start=tuple(inner[j]*(1-f)+outer[j]*f for j in range(3))
            end=(start[0],yy+.17,start[2]); b.haste(start,end,.013,telha2,5)
    b.haste((0,-yy-.21,z+.04),(0,yy+.19,z+.04),.061,telha2,7)
    b.caixa((.70,.47,z-.13),(.34,.38,.66),_cor('Tijolo',(158,85,61))); b.caixa((.70,.47,z+.205),(.41,.45,.09),telha2)
    for u in (-1,1):
        b.caixa((xx*u,frente-.014,(h+.22)/2),(.11,.11,h-.22),guarnicao if alto else carvalho)
    for hz in ([.27,1.85,h] if alto else [.26,h]):
        b.caixa((0,frente-.05,hz),(w+.03,.11,.09),guarnicao if alto else carvalho)
    def win(cx,cz,sw,sh):
        b.caixa((cx,frente-.076,cz),(sw+.14,.095,sh+.14),guarnicao)
        b.caixa((cx,frente-.132,cz),(sw,.045,sh),escuro)
        b.pol([(cx-sw*.45,frente-.161,cz-sh*.34),(cx-sw*.38,frente-.161,cz+sh*.32),(cx-sw*.06,frente-.161,cz+sh*.43)],ref)
        b.caixa((cx,frente-.157,cz),(.031,.042,sh),guarnicao)
        b.caixa((cx,frente-.158,cz+.055),(sw,.041,.035),guarnicao)
        b.caixa((cx,frente-.11,cz-sh/2-.081),(sw+.22,.18,.07),guarnicao)
    for u in (-1,1): win(u*w*.315,1.17,.48 if not alto else .51,.62 if not alto else .82)
    if alto:
        for cx in (-.97,0,.97): win(cx,2.72,.52,.79)
    else:
        win(0,h+.25,.28,.30)
        for u in (-1,1):
            b.haste((u*(xx-.06),frente-.055,h-.02),(u*.42,frente-.055,h-.56),.043,carvalho,5)
    b.caixa((0,frente-.048,.82),(.63,.12,1.41),guarnicao)
    b.caixa((0,frente-.132,.80),(.48,.05,1.31),_cor('Porta da aldeia',(92,119,106)))
    b.caixa((.15,frente-.184,.80),(.048,.06,.063),_cor('Latão',(210,161,78)))
    b.caixa((0,frente-.26,.087),(.95,.42,.14),base)
    if alto:
        for u in (-1,1):
            for ay in (-.61,.58):
                b.caixa((xx*u,ay,2.6),(.06,.65,.87),guarnicao)
                b.caixa(((xx+.045)*u,ay,2.6),(.04,.51,.74),escuro)
    return b.terminar(nome,x,y,rot,escala)


def _recortar(poligono,nx,ny,limite):
    if not poligono: return []
    saida=[]; a=poligono[-1]; av=a[0]*nx+a[1]*ny-limite
    for c in poligono:
        cv=c[0]*nx+c[1]*ny-limite
        if (cv<0)!=(av<0):
            t=av/(av-cv); saida.append((a[0]+t*(c[0]-a[0]),a[1]+t*(c[1]-a[1])))
        if cv<=0: saida.append(c)
        a=c; av=cv
    return saida


def _terreno(b,noite,rng):
    pal=[(213,173,117),(219,179,124),(213,174,119),(209,169,114),(220,182,127),(216,176,121)]
    if noite: pal=[(108+2*i,80+2*i,62+i) for i in range(6)]
    barros=[_cor(('Noite/' if noite else '')+'Argila '+str(i),rgb) for i,rgb in enumerate(pal)]
    fissura=_cor('Solo sob crosta à noite' if noite else 'Solo sob crosta',(77,57,48) if noite else (138,105,77))
    b.pol([(-48,-48,-.025),(48,-48,-.025),(48,48,-.025),(-48,48,-.025)],fissura)
    step=1.10; limit=23
    centros={(i,j):((i+rng.uniform(-.37,.37))*step,(j+rng.uniform(-.37,.37))*step) for i in range(-limit-2,limit+3) for j in range(-limit-2,limit+3)}
    for i in range(-limit,limit+1):
        for j in range(-limit,limit+1):
            x,y=centros[i,j]; d=step*1.75
            poly=[(x-d,y-d),(x+d,y-d),(x+d,y+d),(x-d,y+d)]
            for ii in range(i-2,i+3):
                for jj in range(j-2,j+3):
                    if (ii,jj)==(i,j): continue
                    u,v=centros[ii,jj]; ax,ay=u-x,v-y
                    poly=_recortar(poly,ax,ay,(u*u+v*v-x*x-y*y)*.5)
            k=rng.uniform(.958,.982)
            b.pol([(x+(a-x)*k,y+(c-y)*k,-.003) for a,c in poly],rng.choice(barros))
    for _ in range(95):
        x,y=rng.uniform(-18,18),rng.uniform(-12,18); z=rng.uniform(.026,.064)
        b.copa((x,y,.008),(z*1.3,z,.021),[barros[1],barros[3]],rng.randint(0,999))


def _ceu(b,noite):
    if noite:
        pal=[(59,61,90),(55,58,87),(52,56,84),(47,53,79),(42,47,74),(37,43,70),(31,36,64)]
        mats=[_cor('Céu noturno '+str(i),v) for i,v in enumerate(pal)]
        w,h=64,len(mats); ids=None
    else:
        src=Path(__file__).with_name('ceu-paleta.json')
        if src.is_file():
            cfg=json.loads(src.read_text()); w,h=cfg['width'],cfg['height']
            ids=zlib.decompress(base64.b85decode(cfg['data'])); mats=[_cor('Céu diurno '+str(i),tuple(v)) for i,v in enumerate(cfg['palette'])]
        else:
            w,h=72,7; ids=None
            mats=[_cor('Céu degradê '+str(i),v) for i,v in enumerate([(170,202,212),(152,191,211),(123,168,198),(107,152,188),(95,138,178),(78,124,166),(68,110,150)])]
    radius=63; verts=[]
    for j in range(h+1):
        e=math.radians(-4+94*j/h); ce,se=math.cos(e),math.sin(e)
        for i in range(w):
            ang=i*TAU/w
            verts.append((radius*ce*math.cos(ang),radius*ce*math.sin(ang),radius*se))
    # The image is stored from zenith to horizon, while the rings build upwards.
    base=len(b.verts); b.verts.extend(verts)
    for j in range(h):
        for i in range(w):
            ni=(i+1)%w
            mat=mats[ids[(h-1-j)*w+i] if ids else min(j,len(mats)-1)]
            slot=b.slots.get(mat.name)
            if slot is None:
                slot=len(b.mats); b.mats.append(mat); b.slots[mat.name]=slot
            b.faces.append((base+j*w+i,base+(j+1)*w+i,base+(j+1)*w+ni,base+j*w+ni))
            b.indices.append(slot)


def paisagem(noite=False):
    rng=random.Random(8997); b=_Partes()
    c=_Partes(); _ceu(c,noite)
    cupula=c.terminar("Céu local de prévia"); cupula["ceu_panoramico"]=True
    _terreno(b,noite,rng)
    campo=_cor('Planície distante à noite' if noite else 'Planície distante',(99,101,78) if noite else (147,188,96))
    b.pol([(-55,-55,-.041),(55,-55,-.041),(55,55,-.041),(-55,55,-.041)],campo)
    # Talude mais distante, verde junto ao horizonte e coberto de bosque nas extremidades.
    mats=([_cor('Morros noturnos 1',(74,87,80)),_cor('Morros noturnos 2',(85,100,89)),_cor('Morros noturnos 3',(90,111,101))]
          if noite else [_cor('Morros 1',(112,153,109)),_cor('Morros 2',(135,172,119)),_cor('Morros 3',(156,183,135))])
    n=46; inner=[]; ridge=[]
    for i in range(n):
        a=TAU*i/n; variation=1.7*math.sin(3*a)+.9*math.sin(6*a)+rng.uniform(-.5,.5)
        inner.append((23.4*math.cos(a),23.4*math.sin(a),-.041))
        ridge.append((41*math.cos(a),41*math.sin(a),1.55+variation*.44))
    for i in range(n):
        j=(i+1)%n; b.pol([inner[i],ridge[i],ridge[j],inner[j]],mats[i//4%3])
    horizon=b.terminar('Paisagem noturna' if noite else 'Paisagem diurna')
    return horizon
