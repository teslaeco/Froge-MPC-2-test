"""Tiny textured cube used ONLY to check installation/import/export, without AI."""
import json
import struct
import zlib


def make_fixture():
    positions, normals, uvs, indices = [], [], [], []
    for normal, u, v in (
        ((1,0,0),(0,1,0),(0,0,1)), ((-1,0,0),(0,-1,0),(0,0,1)),
        ((0,1,0),(-1,0,0),(0,0,1)), ((0,-1,0),(1,0,0),(0,0,1)),
        ((0,0,1),(1,0,0),(0,1,0)), ((0,0,-1),(-1,0,0),(0,1,0))):
        start = len(positions)
        for a,b in ((-1,-1),(1,-1),(1,1),(-1,1)):
            positions.append(tuple((normal[i]+a*u[i]+b*v[i])*.5 for i in range(3)))
            normals.append(normal); uvs.append(((a+1)/2,(b+1)/2))
        indices.extend((start,start+1,start+2,start,start+2,start+3))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB',2,2,8,2,0,0,0))
    png += chunk(b'IDAT', zlib.compress(b'\x00\x20\xa0\xc0\xe0\x90\x30\x00\x30\x60\xa0\x90\xc0\x40')) + chunk(b'IEND', b'')
    binary = bytearray(); views=[]
    for raw in (struct.pack('<72f',*(x for p in positions for x in p)),
                struct.pack('<72f',*(x for p in normals for x in p)),
                struct.pack('<48f',*(x for p in uvs for x in p)),
                struct.pack('<36H',*indices),png):
        binary.extend(b'\0' * (-len(binary) % 4))
        views.append({'buffer':0,'byteOffset':len(binary),'byteLength':len(raw)})
        binary.extend(raw)
    binary.extend(b'\0' * (-len(binary) % 4))
    accessors=[{'bufferView':i,'componentType':5126,'count':24,'type':kind} for i,kind in enumerate(('VEC3','VEC3','VEC2'))]
    accessors[0].update(min=[-.5]*3,max=[.5]*3)
    accessors.append({'bufferView':3,'componentType':5123,'count':36,'type':'SCALAR'})
    data={'asset':{'version':'2.0','generator':'FORGE offline installation fixture'},
          'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors,
          'images':[{'bufferView':4,'mimeType':'image/png'}], 'textures':[{'source':0}],
          'materials':[{'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':.6}}],
          'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3,'material':0}]}],
          'nodes':[{'mesh':0,'name':'Installation fixture'}], 'scenes':[{'nodes':[0]}],'scene':0}
    raw=json.dumps(data,separators=(',',':')).encode();raw+=b' '*(-len(raw)%4)
    return struct.pack('<III',0x46546c67,2,28+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(binary),0x004e4942)+binary
