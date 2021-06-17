import numpy as np
import os
import weis.inputs as sch
from weis.dlc_driver.turbulence_models import IEC_TurbulenceModels


class DLCInstance(object):
    
    def __init__(self):
        # Set default DLC with empty properties
        self.wind_heading = 0.0
        self.yaw_misalign = 0.0
        self.turbine_status = ''
        self.wave_spectrum = ''
        self.turbulent_wind = False
        self.label = '' # For 1.1/Custom

    def default_turbsim_props(self, options):
        for key in options['turbulent_wind'].keys():
            setattr(self, key, options['turbulent_wind'][key])

    def to_dict(self):
        out = {}
        keys = ['wind_speed','wind_heading','yaw_misalign','turbsim_seed','turbine_status',
                'wave_spectrum','turbulent_wind','label']
        for k in keys:
            out[k] = getattr(self, k)
        return out


        
class DLCGenerator(object):

    def __init__(self, ws_cut_in=4.0, ws_cut_out=25.0, ws_rated=10.0, wind_class = 'I'):
        self.ws_cut_in = ws_cut_in
        self.ws_cut_out = ws_cut_out
        self.wind_class = wind_class

        self.ws_rated = ws_rated
        self.cases = []
        self.rng = np.random.default_rng()
        self.n_cases = 0
    
    def IECwind(self):
        IECturb = IEC_TurbulenceModels()
        IECturb.Turbine_Class = self.wind_class
        IECturb.setup()
        _, self.V_e50, self.V_e1, _, _ = IECturb.EWM(0.)
        self.V_ref = IECturb.V_ref
        self.wind_class_num = IECturb.Turbine_Class_Num

    def to_dict(self):
        return [m.to_dict() for m in self.cases]
    
    def generate(self, label, options):
        known_dlcs = [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 6.1, 6.2, 6.3, 6.4]
        
        # Get extreme wind speeds
        self.IECwind()

        found = False
        for ilab in known_dlcs:
            func_name = 'generate_'+str(ilab).replace('.','p')
            
            if label in [ilab, str(ilab)]: # Match either 1.1 or '1.1'
                found = True
                getattr(self, func_name)(options) # calls self.generate_1p1(options)
                break
            
        if not found:
            raise ValueError(f'DLC {label} is not currently supported')

        self.n_cases = len(self.cases)
        
    def generate_custom(self, options):
        pass
    
    def generate_1p1(self, options):
        wind_speeds = np.arange(self.ws_cut_in, self.ws_cut_out+1.0, options['ws_bin_size'])
        if wind_speeds[-1] != self.ws_cut_out:
            wind_speeds = np.append(wind_speeds, self.ws_cut_out)
            
        seeds = self.rng.integers(2147483648, size=options['n_seeds'], dtype=int)

        for ws in wind_speeds:
            for seed in seeds:
                idlc = DLCInstance()
                idlc.default_turbsim_props(options)
                idlc.URef = ws
                idlc.RandSeed1 = seed
                idlc.IEC_WindType = 'NTM'
                idlc.turbulent_wind = True
                idlc.turbine_status = 'operating'
                idlc.label = '1.1'
                self.cases.append(idlc)
        self.n_cases_dlc11 = len(wind_speeds)*len(seeds)
    
    def generate_1p2(self, options):
        wind_speeds = np.arange(self.ws_cut_in, self.ws_cut_out+1.0, options['ws_bin_size'])
        if wind_speeds[-1] != self.ws_cut_out:
            wind_speeds = np.append(wind_speeds, self.ws_cut_out)
            
        seeds = self.rng.integers(2147483648, size=options['n_seeds'], dtype=int)

        for ws in wind_speeds:
            for seed in seeds:
                idlc = DLCInstance()
                idlc.default_turbsim_props(options)
                idlc.URef = ws
                idlc.RandSeed1 = seed
                idlc.IEC_WindType = 'NTM'
                idlc.turbulent_wind = True
                idlc.turbine_status = 'operating'
                idlc.label = '1.2'
                self.cases.append(idlc)
    
    def generate_1p3(self, options):
        wind_speeds = np.arange(self.ws_cut_in, self.ws_cut_out+1.0, options['ws_bin_size'])
        if wind_speeds[-1] != self.ws_cut_out:
            wind_speeds = np.append(wind_speeds, self.ws_cut_out)
            
        seeds = self.rng.integers(2147483648, size=options['n_seeds'], dtype=int)

        for ws in wind_speeds:
            for seed in seeds:
                idlc = DLCInstance()
                idlc.default_turbsim_props(options)
                idlc.URef = ws
                idlc.RandSeed1 = seed
                idlc.IEC_WindType = self.wind_class_num + 'ETM'
                idlc.turbulent_wind = True
                idlc.turbine_status = 'operating'
                idlc.label = '1.3'
                self.cases.append(idlc)

    def generate_6p1(self, options):
            
        seeds = self.rng.integers(2147483648, size=options['n_seeds'], dtype=int)
        yaw_misalign_deg = np.array([-8., 8.])
        for yaw_ms in yaw_misalign_deg:
            for seed in seeds:
                idlc = DLCInstance()
                idlc.default_turbsim_props(options)
                idlc.URef = self.V_e50
                idlc.yaw_misalign = yaw_ms
                idlc.RandSeed1 = seed
                idlc.IEC_WindType = self.wind_class_num + 'EWM50'
                idlc.turbulent_wind = True
                if idlc.turbine_status == 'operating':
                    idlc.turbine_status = 'parked'
                idlc.label = '6.1'
                self.cases.append(idlc)

    def generate_6p3(self, options):
            
        seeds = self.rng.integers(2147483648, size=options['n_seeds'], dtype=int)
        yaw_misalign_deg = np.array([-20., 20.])

        for yaw_ms in yaw_misalign_deg:
            for seed in seeds:
                idlc = DLCInstance()
                idlc.default_turbsim_props(options)
                idlc.URef = self.V_e1
                idlc.yaw_misalign = yaw_ms
                idlc.RandSeed1 = seed
                idlc.IEC_WindType = self.wind_class_num + 'EWM1'
                idlc.turbulent_wind = True
                if idlc.turbine_status == 'operating':
                    idlc.turbine_status = 'parked'
                idlc.label = '6.3'
                self.cases.append(idlc)

    def generate_6p4(self, options):
        wind_speeds = np.arange(self.ws_cut_in, 0.7 * self.V_ref, options['ws_bin_size'])
        if wind_speeds[-1] != self.V_ref:
            wind_speeds = np.append(wind_speeds, self.V_ref)
        seeds = self.rng.integers(2147483648, size=options['n_seeds'], dtype=int)

        for ws in wind_speeds:
            for seed in seeds:
                idlc = DLCInstance()
                idlc.default_turbsim_props(options)
                idlc.URef = ws
                idlc.RandSeed1 = seed
                idlc.IEC_WindType = 'NTM'
                idlc.turbulent_wind = True
                if idlc.turbine_status == 'operating':
                    idlc.turbine_status = 'parked'
                idlc.label = '6.4'
                self.cases.append(idlc)


if __name__ == "__main__":
    
    # Wind turbine inputs that will eventually come in from somewhere
    ws_cut_in = 4.
    ws_cut_out = 25.
    ws_rated = 10.
    wind_class = 'I'

    # Load modeling options file
    weis_dir                = os.path.dirname( os.path.dirname( os.path.dirname( os.path.realpath(__file__) ) ) ) + os.sep
    fname_modeling_options = os.path.join(weis_dir , "examples", "05_IEA-3.4-130-RWT", "modeling_options.yaml")
    modeling_options = sch.load_modeling_yaml(fname_modeling_options)
    
    # Extract user defined list of cases
    DLCs = modeling_options['DLC_driver']['DLCs']
    
    # Initialize the generator
    dlc_generator = DLCGenerator(ws_cut_in, ws_cut_out, ws_rated, wind_class)

    # Generate cases from user inputs
    for i_DLC in range(len(DLCs)):
        DLCopt = DLCs[i_DLC]
        dlc_generator.generate(DLCopt['DLC'], DLCopt)

    print(dlc_generator.cases[5].URef)
    print(dlc_generator.n_cases)
                
