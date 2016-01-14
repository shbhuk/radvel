import numpy as np        
import copy
import pandas as pd
# List of available bases
BASIS_NAMES = [
'per tc secosw sesinw logk',
'per tc secosw sesinw k',
'per tc e w k'
]
    
def _print_valid_basis():
    print "Available bases:"
    print "\n".join(BASIS_NAMES)

class Basis(object):
    """
    Object that knows how to convert between the various Keplerian bases
    """

    cps_params = 'per tp e w k'.split()
    def __init__(self, *args):
        self.name = None
        self.num_planets = 0
        if len(args)==0:
            _print_valid_basis()
            return None
        
        name, num_planets = args

        if BASIS_NAMES.count(name)==0:
            print "{} not valid basis".format(name)
            _print_valid_basis()
            return None

        self.name = name
        self.num_planets = num_planets
        self.params = name.split()

    def __repr__(self):
        return "Basis Object <{}>".format(self.name)

    def to_cps(self, params_in):
        if isinstance(params_in,dict):
            return self._to_cps(params_in)
        if isinstance(params_in,pd.core.frame.DataFrame):
            params_out = []
            for i,row in params_in.iterrows():
                row = dict(row)
                params_out += [self._to_cps(row)]
            params_out = pd.DataFrame(params_out)
            return params_out

    def _to_cps(self, params_in):
        """
        Convert to CPS basis

        Convert a dictionary with parameters of a given basis into the cps basis

        :param params_in: planet parameters expressed in current basis
        :type params_in: dict
        """

        params_out = copy.copy(params_in)
        for num_planet in range(1,1+self.num_planets):
            def _getpar(key):
                return params_out['{}{}'.format(key,num_planet)]
            def _setpar(key, value):
                params_out['{}{}'.format(key,num_planet)] = value

            # transform into CPS basis
            if self.name == 'per tc e w k':
                per = _getpar('per')
                tc = _getpar('tc')
                e = _getpar('e')
                w = _getpar('w')
                k = _getpar('k')
                
                ecosw = e*np.cos(w)
                esinw = e*np.sin(w)
                tp, e, w = _tcecos2cps(per, tc, ecosw, esinw)
            
            if self.name=='per tc secosw sesinw logk':
                # pull out parameters
                per = _getpar('per')
                tc = _getpar('tc')
                secosw = _getpar('secosw')
                sesinw = _getpar('sesinw')
                logk = _getpar('logk')

                k = np.exp(logk)
                e = secosw**2 + sesinw**2
                se = np.sqrt(e)
                ecosw = se*secosw
                esinw = se*sesinw
                tp, e, w = _tcecos2cps(per, tc, ecosw, esinw)

            if self.name=='per tc secosw sesinw k':
                # pull out parameters
                per = _getpar('per')
                tc = _getpar('tc')
                secosw = _getpar('secosw')
                sesinw = _getpar('sesinw')
                k = _getpar('k')
            
                # transform into CPS basis
                e = secosw**2 + sesinw**2
                se = np.sqrt(e)
                ecosw = se*secosw
                esinw = se*sesinw
                tp, e, w = _tcecos2cps(per, tc, ecosw, esinw)

               
            # shoves cps parameters from namespace into param_out
            _setpar('per', per)
            _setpar('tp', tp)
            _setpar('e', e)
            _setpar('w', w)
            _setpar('k', k)

        return params_out


    def from_cps(self, params):
        """
        Convert from CPS basis

        Convert a dictionary with parameters of a given basis into the cps basis

        :param params: planet parameters expressed in cps basis
        :type params: dict
        """
def _tcecos2cps(per, tc, ecosw, esinw):
    """
    Convert (per, tc, ecosw, esinw) to ( tp, e, w)

    :param per: period
    :type tc: float

    :param tc: time of conjunction
    :type tc: float

    :param ecosw: e*cosw
    :type ecosw: float

    :param esinw: e*sinw
    :type esinw: float

    .. doctest::
       >>> per, tc, ecosw, esinw  = 1,0.0,0.5,0.5
       >>> tc, e, w = radvel.basis._tcecos2cps(per, tc, ecosw, esinw )
       >>> truth = array([ -1.657354e-02,   7.071067e-01,   4.500000e+01])
       >>> output = np.array([tc, e, w])
       >>> np.allclose(truth,output,rtol=1e-5)    

    """

    # converting ecosom, esinom to e, omega (degrees)
    e = np.sqrt(ecosw**2 + esinw**2)
    if e >= 1.0:
        e = 0.99

    w = np.arctan2( esinw , ecosw ) / np.pi * 180

    # om in [0.,360)
    while w < 0.:
         w += 360.0

    # true anomaly during conjunction
    f = np.pi / 2.0 - w / 180.0 * np.pi 

    # eccentric anomaly
    EE = 2.0 * np.arctan( np.tan( f / 2 ) * np.sqrt( (1.0 - e) / (1.0 + e) ) )

    tp = tc - per / (2.0 * np.pi ) * (EE - e*np.sin(EE))
    return tp, e, w
