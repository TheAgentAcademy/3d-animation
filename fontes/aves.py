"""Elementos rurais low-poly. Unidades em metros. Frente das aves e cabana: -Y."""
import hashlib
import math
import random

import bmesh
import bpy
from mathutils import Vector

_MATERIAIS = {}
_FORMAS = {}


def cor(nome, valor):
    chave = (nome, valor)
    if chave not in _MATERIAIS:
        mat = bpy.data.materials.new("Aves • " + nome)
        rgba = tuple(int(valor[i:i + 2], 16) / 255 for i in (0, 2, 4))
        # As cores difusas do Blender usam valores lineares.
        linear = tuple(x / 12.92 if x <= 0.04045 else ((x + .055) / 1.055) ** 2.4 for x in rgba)
        mat.diffuse_color = (*linear, 1.0)
        mat.use_nodes = True
        principled = mat.node_tree.nodes.get("Principled BSDF")
        principled.inputs["Base Color"].default_value = (*linear, 1.0)
        principled.inputs["Roughness"].default_value = .79
        _MATERIAIS[chave] = mat
    return _MATERIAIS[chave]


def grupo(nome, x=0, y=0, z=0, rot=0, escala=1, parent=None):
    obj = bpy.data.objects.new(nome, None)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.location = x, y, z
    obj.rotation_euler.z = rot
    obj.scale = (escala,) * 3
    obj.empty_display_size = .1
    return obj


def malha(nome, forma, material):
    k = (forma, material.name)
    if k not in _FORMAS:
        mesh = bpy.data.meshes.new(nome)
        bm = bmesh.new()
        if forma == "cubo":
            bmesh.ops.create_cube(bm, size=2)
        elif forma == "esfera":
            bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
        elif forma == "pedra":
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1)
        else:
            raio_topo, lados = forma
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=lados,
                                  radius1=1, radius2=raio_topo, depth=2)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(material)
        _FORMAS[k] = mesh
    return _FORMAS[k]


def fig(p, nome, forma, pos, dimensoes, material, giro=None):
    m = malha(nome, forma, material)
    o = bpy.data.objects.new(nome, m)
    bpy.context.collection.objects.link(o)
    o.parent, o.location, o.scale = p, pos, dimensoes
    if giro:
        o.rotation_euler = giro
    return o


def entre(p, nome, a, b, raio, mat, topo=1, lados=7):
    a, b = Vector(a), Vector(b)
    d = b - a
    o = fig(p, nome, (topo, lados), (a + b) / 2, (raio, raio, d.length / 2), mat)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    return o


def oval(p, nome, pos, escala, mat, giro=None):
    return fig(p, nome, "esfera", pos, escala, mat, giro)


def caixa(p, nome, pos, escala, mat, giro=None):
    return fig(p, nome, "cubo", pos, escala, mat, giro)


def _cores_ave(variante):
    cores = [
        ("Pérola", "E8E1CB", "F9F3DD", "C0B294", "504748"),
        ("Galo cobre", "994729", "E8A23A", "743B28", "1C5756"),
        ("Caramelo", "C28B5A", "E9C695", "A66842", "765340"),
        ("Ardósia", "49575A", "6B7A79", "39454B", "303B47"),
    ]
    n, *cores = cores[variante % len(cores)]
    return [cor(n + " " + str(i), hex_) for i, hex_ in enumerate(cores)]


def _pernas(p, largura, alto, mat):
    for lado in (-1, 1):
        x = lado * largura
        a = (x, .003, .035)
        entre(p, "Canela", a, (x * .84, -.014, alto), .024, mat, .79, 6)
        for k in (-1, 0, 1):
            entre(p, "Dedo", a, (x + k * .077, -.125 + abs(k) * .036, .018),
                  .018, mat, .16, 5)
        entre(p, "Esporão", a, (x + lado * .011, .065, .023), .015, mat, .13, 5)


def galinha(nome, x, y, rot=0, escala=1, variante=0):
    p = grupo(nome, x, y, rot=rot, escala=escala)
    corpo, pescoco, asa, cauda = _cores_ave(variante)
    perna = cor("Ocre do pé", "D6A344")
    crista = cor("Crista vermelha", "C3332E")
    bico = cor("Bico de milho", "EEAD42")
    olho = cor("Olho castanho", "262221")
    _pernas(p, .10, .32, perna)
    oval(p, "Peito e corpo", (0, .014, .401), (.225, .35, .243), corpo, (-.13, 0, 0))
    for lado in (-1, 1):
        oval(p, "Asa", (lado * .19, .07, .42), (.066, .211, .132), asa, (.33, 0, lado * .07))
        for j in range(3):
            oval(p, "Pena de asa", (lado * (.214 - j * .006), .132 + .048 * j, .428 - .028 * j),
                 (.041, .112, .029), corpo, (.36, 0, 0))
    eh_galo = variante % 4 == 1
    for j, lado in enumerate((-.08, 0, .08)):
        oval(p, "Pena da cauda", (lado, .294 + .023 * (1 - j % 2), .525 + (.06 if eh_galo else 0)),
             (.057, .09, .249 if eh_galo else .16), cauda, (-.65 + .13 * (j % 2), lado * 2, 0))
    cab = grupo("Cabeça e pescoço", 0, -.215, .50, parent=p)
    oval(cab, "Pescoço", (0, .006, .045), (.132, .150, .187), pescoco, (-.20, 0, 0))
    oval(cab, "Cabeça", (0, -.047, .141), (.113, .124, .109), pescoco)
    for lado in (-1, 1):
        oval(cab, "Olho", (lado * .099, -.097, .162), (.023, .023, .026), olho)
    entre(cab, "Bico", (0, -.125, .115), (0, -.257, .090), .067, bico, .014)
    for j in range(3):
        oval(cab, "Crista", (0, -.12 + j * .055, .239 + (1 - abs(1-j)) * .015),
             (.029, .05, .084 if eh_galo else .049), crista)
    oval(cab, "Barbela", (0, -.107, .052), (.037, .039, .068 if eh_galo else .037), crista)
    return p


def pintinho(nome, x, y, rot=0, escala=1):
    p = grupo(nome, x, y, rot=rot, escala=escala)
    penugem = cor("Penugem amarela", "F5C84D")
    clara = cor("Penugem clara", "FFE680")
    olho = cor("Olho castanho", "262221")
    bico = cor("Bico de milho", "EEAD42")
    sub = grupo("Patas de pinto", escala=.48, parent=p)
    _pernas(sub, .100, .20, bico)
    oval(p, "Corpo do pinto", (0, .02, .135), (.108, .135, .107), penugem)
    oval(p, "Cabeça do pinto", (0, -.069, .235), (.098, .103, .096), clara)
    for l in (-1, 1):
        oval(p, "Olho", (l*.086,-.107,.246), (.015,.015,.015), olho)
        oval(p, "Asinha", (l*.088,.037,.138), (.028,.067,.042), clara)
    entre(p, "Bico", (0,-.145,.222), (0,-.210,.205), .039, bico, .02)
    return p


def ovo(nome, x, y, z=0, escala=1):
    p = grupo(nome, x, y, z=z, escala=escala)
    off = cor("Ovo marfim", "F4E2BB")
    oval(p, "Casca", (0,0,.088), (.061,.063,.091), off, (.16,0,0))
    return p


def galinheiro(nome, x, y, rot=0, escala=1):
    p = grupo(nome,x,y,rot=rot,escala=escala)
    escuro = cor("Interior do ninho", "362C25")
    viga = cor("Madeira escura", "694632")
    madeiras = [cor("Madeira palha", "CDA26D"),cor("Madeira mel","B58856"),cor("Madeira clara","D9AE75")]
    telhas = [cor("Telha coral", "B95545"),cor("Telha terracota", "A64D40"),cor("Telha clara", "C66D57")]
    for xx in (-1.04,1.04):
        for yy in (-.56,.56):
            caixa(p, "Pé do galinheiro", (xx,yy,.35), (.078,.078,.35), viga)
    caixa(p,"Tablado",(0,0,.51),(1.20,.70,.085),madeiras[1])
    caixa(p,"Fundo sombreado",(0,.55,1.06),(1.10,.045,.51),escuro)
    for j in range(8):
        xx = -.97+j*.275
        caixa(p, "Tábua de fachada", (xx,-.57,1.10 if j not in (3,4) else 1.47),
              (.133,.061,.50 if j not in (3,4) else .13), madeiras[j%3])
    for lado in (-1,1):
        for j in range(4):
            caixa(p, "Tábua lateral", (lado*1.065,-.43+j*.29,1.07),(.06,.14,.48), madeiras[(j+1)%3])
        caixa(p, "Batente da entrada",(lado*.31,-.65,1.02),(.035,.065,.46),viga)
        caixa(p,"Cantoneira",(lado*1.068,-.641,1.08),(.045,.04,.48),viga)
    caixa(p,"Lintel",(0,-.65,1.37),(.335,.05,.041),viga)
    caixa(p, "Soleira", (0,-.64,.63), (.34,.07,.045), viga)
    for lado in (-1,1):
        for j in range(10):
            xx=-1.167+j*.259
            caixa(p,"Telha ondulada",(xx,lado*.374,1.786),(.131,.461,.054),telhas[(j+int(lado>0))%3],(-lado*.467,0,0))
        caixa(p, "Testeira", (0,lado*.783,1.615),(1.327,.047,.084), viga)
    caixa(p,"Cumeeira",(0,0,1.99),(1.31,.069,.057),telhas[0])
    # Acesso em duas tábuas, com cinco travessas visíveis.
    ang = math.atan2(.52, .97)
    caixa(p,"Rampa",(0,-1.107,.295),(.257,.55,.036),madeiras[1],(ang,0,0))
    for j in range(6):
        frac = (j+.5)/6
        caixa(p,"Degrau", (0,-1.57+frac*.94,.067+frac*.50),(.258,.023,.027),viga,(ang,0,0))
    return p


def ossos(nome, x, y, escala=1):
    p=grupo(nome,x,y,escala=escala)
    osso=cor("Osso", "EEDDB5")
    rng=random.Random(int.from_bytes(hashlib.sha256(nome.encode()).digest()[:4],"big"))
    for j in range(5):
        g=grupo("Osso no chão",rng.uniform(-.34,.34),rng.uniform(-.22,.22),.063,rng.uniform(0,math.tau),rng.uniform(.70,1.08),p)
        entre(g,"Diáfise",(-.126,0,0),(.126,0,0),.033,osso,1)
        for l in (-1,1):
            for m in (-1,1):
                oval(g,"Extremidade",(.134*l,m*.025,0),(.041,.033,.033),osso)
    return p


def fogueira(nome, x, y, escala=1):
    p=grupo(nome,x,y,escala=escala)
    carvao=cor("Carvão", "3D3330")
    brasa=cor("Brasa", "D65F35")
    pedra=cor("Pedra quente", "88786B")
    fogo=cor("Laranja das chamas","F28524")
    claro=cor("Centro das chamas","FFD358")
    metal=cor("Ferro do espeto","363D42")
    assado=cor("Pele dourada", "BC662D")
    coxa=cor("Pele tostada", "864527")
    for j in range(10):
        a = math.tau*j/10
        fig(p,"Pedra do círculo","pedra",(.52*math.cos(a),.52*math.sin(a),.103),(.174,.154,.148),pedra,(.2,a,0))
    for a,dy in [(.19,-.055),(-.38,.07),(1.0,-.05)]:
        dx,ddy=math.cos(a)*.42,math.sin(a)*.42
        entre(p,"Lenha",(-dx,dy-ddy,.112), (dx,dy+ddy,.129), .086,carvao,.85)
        entre(p,"Ponta em brasa",(.78*dx,dy+.78*ddy,.13), (dx,dy+ddy,.128), .080,brasa,.84)
    for j in range(8):
        a=j*2.4
        vx,vy=math.cos(a)*.22, math.sin(a)*.20
        h=.44+.15*math.cos(j*1.72)
        entre(p,"Língua de fogo",(vx,vy,.15),(vx+.034,vy,h),.16,fogo,.02,5)
        entre(p,"Núcleo claro",(vx-.015,vy-.035,.16),(vx-.01,vy-.03,h*.81),.11,claro,.035,5)
    for xx in (-.66,.66):
        entre(p, "Suporte do espeto",(xx,-.16,0),(xx,0,.91),.034,metal)
        entre(p, "Pé traseiro",(xx,.22,0),(xx,0,.78),.030,metal)
    entre(p,"Espeto horizontal",(-.78,0,.84),(.90,0,.84),.031,metal)
    oval(p,"Frango assado",(0,0,.83),(.32,.219,.201),assado)
    for l in (-1,1):
        oval(p,"Coxa assada",(-.11,l*.172,.78),(.158,.093,.105),coxa,(0,-.51,l*.27))
        entre(p,"Ponta da coxa",(-.20,l*.195,.745),(-.30,l*.232,.69),.038,cor("Osso","EEDDB5"),.82)
        oval(p,"Asa tostada",(.11,l*.18,.83),(.106,.058,.073),coxa)
    return p
