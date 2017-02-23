# -*- coding: utf-8 -*-

class SuperFloat(float):
    precision = 0.000001
    def __repr__(self):
        return ('%.5f' % (round(self, 5) + 0)).rstrip('0').rstrip('.')
    def __eq__(self, other):
        return abs(self-other) < SuperFloat.precision
    def __ne__(self, other):
        return abs(self-other) >= SuperFloat.precision
    def __add__(self, other):
        return SuperFloat(super(SuperFloat, self).__add__(other))
    def __sub__(self, other):
        return SuperFloat(super(SuperFloat, self).__sub__(other))
    def __mul__(self, other):
        return SuperFloat(super(SuperFloat, self).__mul__(other))
    def __div__(self, other):
        return SuperFloat(super(SuperFloat, self).__div__(other))
    def __truediv__(self, other):
        return SuperFloat(super(SuperFloat, self).__truediv__(other))
    def __floordiv__(self, other):
        return SuperFloat(super(SuperFloat, self).__floordiv__(other))
    def __mod__(self, other):
        return SuperFloat(super(SuperFloat, self).__mod__(other))
    def __divmod__(self, other):
        return SuperFloat(super(SuperFloat, self).__divmod__(other))
    def __pow__(self, other, modulo = None):
        return SuperFloat(super(SuperFloat, self).__pow__(other, modulo))
    def __radd__(self, other):
        return SuperFloat(super(SuperFloat, self).__radd__(other))
    def __rsub__(self, other):
        return SuperFloat(super(SuperFloat, self).__rsub__(other))
    def __rmul__(self, other):
        return SuperFloat(super(SuperFloat, self).__rmul__(other))
    def __rdiv__(self, other):
        return SuperFloat(super(SuperFloat, self).__rdiv__(other))
    def __rtruediv__(self, other):
        return SuperFloat(super(SuperFloat, self).__rtruediv__(other))
    def __rfloordiv__(self, other):
        return SuperFloat(super(SuperFloat, self).__rfloordiv__(other))
    def __rmod__(self, other):
        return SuperFloat(super(SuperFloat, self).__rmod__(other))
    def __rdivmod__(self, other):
        return SuperFloat(super(SuperFloat, self).__rdivmod__(other))
    def __rpow__(self, other):
        return SuperFloat(super(SuperFloat, self).__rpow__(other))
    def __neg__(self, ):
        return SuperFloat(super(SuperFloat, self).__neg__())
    def __pos__(self, ):
        return SuperFloat(super(SuperFloat, self).__pos__())
    def __abs__(self, ):
        return SuperFloat(super(SuperFloat, self).__abs__())

def SuperFloats(obj):
    if isinstance(obj, float):
        return SuperFloat(obj)
    elif isinstance(obj, dict):
        return dict((k, SuperFloats(v)) for k, v in obj.items())
    elif isinstance(obj, (list, tuple)):
        return map(SuperFloats, obj)
    return obj