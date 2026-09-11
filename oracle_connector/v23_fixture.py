"""Offline v23 installation fixture; authored geometry and synthetic colours."""
import base64, hashlib, json

IMAGES = ['/9j/4AAQSkZJRgABAQAAAQABAAD/4QAMTmVvR2VvAAAAWv/bAEMAAwICAwICAwMDAwQDAwQFCAUFBAQFCgcHBggMCgwMCwoLCw0OEhANDhEOCwsQFhARExQVFRUMDxcYFhQYEhQVFP/bAEMBAwQEBQQFCQUFCRQNCw0UFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFP/AABEIAEAAQAMBIgACEQEDEQH/xAAfAAABBQEBAQEBAQAAAAAAAAAAAQIDBAUGBwgJCgv/xAC1EAACAQMDAgQDBQUEBAAAAX0BAgMABBEFEiExQQYTUWEHInEUMoGRoQgjQrHBFVLR8CQzYnKCCQoWFxgZGiUmJygpKjQ1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4eLj5OXm5+jp6vHy8/T19vf4+fr/xAAfAQADAQEBAQEBAQEBAAAAAAAAAQIDBAUGBwgJCgv/xAC1EQACAQIEBAMEBwUEBAABAncAAQIDEQQFITEGEkFRB2FxEyIygQgUQpGhscEJIzNS8BVictEKFiQ04SXxFxgZGiYnKCkqNTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqCg4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2dri4+Tl5ufo6ery8/T19vf4+fr/2gAMAwEAAhEDEQA/APnqiiivxw/vAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooAKKKKACiiigAooooA//Z', '/9j/4AAQSkZJRgABAQAAAQABAAD/4QAMTmVvR2VvAAAAWv/bAEMAAwICAwICAwMDAwQDAwQFCAUFBAQFCgcHBggMCgwMCwoLCw0OEhANDhEOCwsQFhARExQVFRUMDxcYFhQYEhQVFP/bAEMBAwQEBQQFCQUFCRQNCw0UFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFP/AABEIAEAAQAMBIgACEQEDEQH/xAAfAAABBQEBAQEBAQAAAAAAAAAAAQIDBAUGBwgJCgv/xAC1EAACAQMDAgQDBQUEBAAAAX0BAgMABBEFEiExQQYTUWEHInEUMoGRoQgjQrHBFVLR8CQzYnKCCQoWFxgZGiUmJygpKjQ1Njc4OTpDREVGR0hJSlNUVVZXWFlaY2RlZmdoaWpzdHV2d3h5eoOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4eLj5OXm5+jp6vHy8/T19vf4+fr/xAAfAQADAQEBAQEBAQEBAAAAAAAAAQIDBAUGBwgJCgv/xAC1EQACAQIEBAMEBwUEBAABAncAAQIDEQQFITEGEkFRB2FxEyIygQgUQpGhscEJIzNS8BVictEKFiQ04SXxFxgZGiYnKCkqNTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqCg4SFhoeIiYqSk5SVlpeYmZqio6Slpqeoqaqys7S1tre4ubrCw8TFxsfIycrS09TV1tfY2dri4+Tl5ufo6ery8/T19vf4+fr/2gAMAwEAAhEDEQA/AKlFFFfzYfw4FFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAFFFFABRRRQAUUUUAf//Z']

def write_fixture(folder):
    material={'name':'base','rgb':[.1,.2,.4],'pattern':'plain','roughness':.5,'metallic':0,'emission':0}
    vertices=[[-.5,0,0],[0,0,0],[.5,0,0],[-.5,0,1],[0,0,1],[.5,0,1],[-.5,.4,0],[.5,.4,0],[.5,.4,1],[-.5,.4,1]]
    parts=[{'kind':'mesh','name':'target','material':'base','vertices':vertices,'faces':[[0,1,4,3],[1,2,5,4],[9,8,7,6]]},
        {'kind':'mesh','name':'occluder','material':'base','vertices':[[-.6,-.2,-.1],[0,-.2,-.1],[0,-.2,1.1],[-.6,-.2,1.1]],'faces':[[0,1,2,3]]},
        {'kind':'surface_grid','name':'curved-panel','material':'base','control_grid':[[[2,0,0],[2.5,.1,0],[3,0,0]],[[2,0,.5],[2.5,.2,.5],[3,0,.5]],[[2,0,1],[2.5,.1,1],[3,0,1]]],'samples':3,'thickness':.02},
        {'kind':'contour_loft','name':'asymmetric-vessel','material':'base','rings':[[[4,0,0],[4.6,0,0],[4.5,.4,0],[4,.3,0]],[[4.1,.1,.5],[4.5,.1,.5],[4.4,.3,.5],[4.1,.4,.5]],[[4.2,.1,1],[4.4,.1,1],[4.4,.3,1],[4.2,.3,1]]],'samples':3,'caps':True}]
    views=[{'photo_index':i,'position':[0,y,.5],'target':[0,0,.5],'up':[0,0,1], 'projection':'orthographic','vertical_span':2,'fov':1,
        'regions':[{'part':'target','polygon':[[.1,.1],[.9,.1],[.9,.9],[.1,.9]]}]} for i,y in [(0,-3),(1,3)]]
    (folder/'scene.json').write_text(json.dumps({'version':2,'name':'Offline installation test','subject_type':'object','materials':[material],'parts':parts,'reference_views':views}))
    metadata=[]
    for i,encoded in enumerate(IMAGES):
        data=base64.b64decode(encoded)
        (folder/('reference-%d.jpg'%i)).write_bytes(data)
        metadata.append({'name':'Synthetic colour fixture','view':'front' if i==0 else 'back','sha256':hashlib.sha256(data).hexdigest()})
    (folder/'reference-photos.json').write_text(json.dumps(metadata))
