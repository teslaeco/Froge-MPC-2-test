"""Validate bounded browser measurements, bound to the exact uploaded JPEG."""
import math


def validate(value, width, height, digest):
    if value is None:
        return None
    if not isinstance(value,dict) or value.get('revision')!=1 or value.get('width')!=width or value.get('height')!=height or value.get('imageSha256')!=digest:
        raise ValueError('Pomiary twarzy nie pasuja do zdjecia. Dodaj je ponownie.')
    points=value.get('points')
    if not isinstance(points,list) or len(points)!=478:
        raise ValueError('Niepelne pomiary twarzy.')
    for point in points:
        if not isinstance(point,list) or len(point)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>2 for x in point):
            raise ValueError('Nieprawidlowe wspolrzedne twarzy.')
    return {key:value[key] for key in ('revision','width','height','imageSha256','points')}
