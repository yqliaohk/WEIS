import os
import numpy as np
from dtqpy.src.DTQPy_oloc import DTQPy_oloc

radps2rpm = 30 / np.pi
from pCrunch.io import OpenFASTOutput

from weis.aeroelasticse.CaseGen_General import case_naming


def dtqp_wrapper(LinearTurbine,level2_disturbances,analysis_options,fst_vt,loads_analysis,magnitude_channels,run_dir):
    ''' 
    Convert weis information to DTQP and vice versa
    Catch errors to ensure we are using DTQP in a way that it is able to be used


    Inputs:         LinearTurbine:  LinearTurbineModel object
                    level2_disturbances: list of disturbance dicts with Time and Wind keys
                    analysis_options: weis analysis options with constraints, merit figures
                    fst_vt: dict with OpenFAST/ROSCO variables
                    loads_analysis: pCrunch LoadsAnalysis object
                    magnitude_channels: dict for pCrunch
                    run_dir: run directory (self.FAST_runDirectory)

    '''


    ### Set up constraints
    dtqp_constraints = {}

    # catch any other flags, maybe this is better handled elsehwere
    blade_const = analysis_options['constraints']['blade']
    if any([blade_const[co]['flag'] for co in blade_const if 'flag' in blade_const[co]]):
        raise Exception('WEIS blade constraints are not currently supported in DTQP')

    tower_const = analysis_options['constraints']['tower']
    if any([tower_const[co]['flag'] for co in tower_const if 'flag' in tower_const[co]]):
        raise Exception('WEIS tower constraints are not currently supported in DTQP')

    monopile_const = analysis_options['constraints']['monopile']
    if any([monopile_const[co]['flag'] for co in monopile_const if 'flag' in monopile_const[co]]):
        raise Exception('WEIS monopile constraints are not currently supported in DTQP')

    hub_const = analysis_options['constraints']['hub']
    if any([hub_const[co]['flag'] for co in hub_const if 'flag' in hub_const[co]]):
        raise Exception('WEIS hub constraints are not currently supported in DTQP')

    drivetrain_const = analysis_options['constraints']['drivetrain']
    if any([drivetrain_const[co]['flag'] for co in drivetrain_const if 'flag' in drivetrain_const[co]]):
        raise Exception('WEIS drivetrain constraints are not currently supported in DTQP')

    floating_const = analysis_options['constraints']['floating']
    if any([floating_const[co]['flag'] for co in floating_const if 'flag' in floating_const[co]]):
        raise Exception('WEIS floating constraints are not currently supported in DTQP')


    # Control constraints that are supported
    control_const = analysis_options['constraints']['control']

    # Rotor overspeed
    if control_const['rotor_overspeed']['flag']:
        desc = 'ED First time derivative of Variable speed generator DOF (internal DOF index = DOF_GeAz), rad/s'
        if desc in LinearTurbine.DescStates:
            dtqp_constraints[desc] = [-np.inf,(1 + control_const['rotor_overspeed']['max']) * fst_vt['DISCON_in']['PC_RefSpd'] ]
        else:
            raise Exception('rotor_overspeed constraint is set, but ED GenSpeed is not a state in the LinearModel')

    if control_const['Max_PtfmPitch']['flag']:
        desc = 'ED Platform pitch tilt rotation DOF (internal DOF index = DOF_P), rad'
        if desc in LinearTurbine.DescStates:
            dtqp_constraints[desc] = [-np.inf,control_const['Max_PtfmPitch']['max'] * np.deg2rad(1)]
        else:
            raise Exception('Max_PtfmPitch constraint is set, but ED PtfmPitch is not a state in the LinearModel')
            

    ### Loop throught and call DTQP for each disturbance
    case_names = case_naming(len(level2_disturbances),'oloc')

    ss = {}
    et = {}
    dl = {}
    dam = {}
    ct = []

    for i_oloc, dist in enumerate(level2_disturbances): 
        T,U,X,Y = DTQPy_oloc(LinearTurbine,dist,dtqp_constraints,plot=True)

        # Shorten output names from linearization output to one like level3 openfast output
        # This depends on how openfast sets up the linearization output names and may break if that is changed
        OutList     = [out_name.split()[1][:-1] for out_name in LinearTurbine.DescOutput]

        # Turn OutData into dict like in ROSCO_toolbox
        OutData = {}
        for i, out_chan in enumerate(OutList):
            OutData[out_chan] = Y[:,i]

        # Add time to OutData
        OutData['Time'] = T.flatten()

        output = OpenFASTOutput.from_dict(OutData, case_names[i_oloc],magnitude_channels=magnitude_channels)      # 

        _name, _ss, _et, _dl, _dam = loads_analysis._process_output(output)
        ss[_name] = _ss
        et[_name] = _et
        dl[_name] = _dl
        dam[_name] = _dam
        ct.append(OutData)

        output.df.to_pickle(os.path.join(run_dir,case_names[i_oloc]+'.p'))

    summary_stats, extreme_table, DELs, Damage = loads_analysis.post_process(ss, et, dl, dam)

    return summary_stats, extreme_table, DELs, Damage



