import os
import sys
from collections import OrderedDict
import sap2000
from modelclasses import Model

# %% OPEN SAP2000 AND READY PROGRAM

# check working directory
api_path_home = r'C:\Users\Felipe\Dropbox\PycharmProjects\CoupledStructures\models'
api_path_fluor = r'C:\Users\mej12981\PycharmProjects\CoupledStructures\models'
try:
    os.chdir(api_path_home)
except FileNotFoundError:
    try:
        os.chdir(api_path_fluor)
    except FileNotFoundError:
        print("Could not find api_path directory")
        sys.exit(1)
    else:
        api_path = api_path_fluor
else:
    api_path = api_path_home
    sap2000.checkinstall(api_path)

# create sap2000 object in memory
# in case user wants to attach to running instant, set attach_to_instance=True
# program finds most recent installation after SAP2000 v19. For other installs, set specify_path=True
program_path = r'C:\Program Files\Computers and Structures\SAP2000 20\SAP2000.exe'
sap_obj = sap2000.attachtoapi(attach_to_instance=False, specify_path=False, program_path=program_path)

# open sap2000
# to show sap2000 GUI, set visible=True
model_obj = Model(sap2000.opensap2000(sap_obj, visible=True))

# open new model in units of kip_in_F
model_obj.new()

#%% DEFINE MODEL GEOMETRY, PROPERTIES, AND LOADING

# initialize model object

# set degrees of freedom
model_obj.props.set_mdl_dof_df(dof='2-D')

# load degrees of freedom for 2-D motion into sap2000
model_obj.props.load_mdl_dof_df()

# set material properties
mat_steel = {'material': 'STEEL', 'material_id': sap2000.MATERIAL_TYPES['MATERIAL_STEEL'],
             'youngs': 29000, 'poisson': 0.3, 't_coeff': 6E-06}

model_obj.props.add_mat_df(mat_steel)

# load dataframe of material properties into sap2000
model_obj.props.load_mat_df()

# generate frame properties
model_obj.props.gen_frm_df(frm1_col_stiff=1, frm1_bm_stiff=1, frm2_col_stiff=1, frm2_bm_stiff=1)

# load dataframe of frame properties into sap2000
model_obj.props.load_frm_df()

# switch to k-ft units
model_obj.switch_units(units=sap2000.UNITS['kip_ft_F'])

# add frame object by coordinates

model_obj.members.gen_frm_df()

model_obj.members.load_frm_df()

print('generated and loaded members')

[Frame1, ret] = model_obj.sap_obj.FrameObj.AddByCoord(0, 0, 0, 0, 0, 20,  '', 'R1', '', 'Global')
[Frame2, ret] = model_obj.sap_obj.FrameObj.AddByCoord(20, 0, 0, 20, 0, 20, '', 'R1', '', 'Global')
[Frame3, ret] = model_obj.sap_obj.FrameObj.AddByCoord(0, 0, 20, 20, 0, 20, '', 'R2', '', 'Global')
[Frame4, ret] = model_obj.sap_obj.FrameObj.AddByCoord(40, 0, 0, 40, 0, 20, '', 'R3', '', 'Global')
[Frame5, ret] = model_obj.sap_obj.FrameObj.AddByCoord(60, 0, 0, 60, 0, 20, '', 'R3', '', 'Global')
[Frame6, ret] = model_obj.sap_obj.FrameObj.AddByCoord(40, 0, 20, 60, 0, 20, '', 'R4', '', 'Global')


# assign point object restraint at base

Restraint = [True, True, True, True, True, True]

[Frame1i, Frame1j, ret] = model_obj.sap_obj.FrameObj.GetPoints(Frame1, '', '')

model_obj.sap_obj.PointObj.SetRestraint(Frame1i, Restraint)

[Frame2i, Frame1j, ret] = model_obj.sap_obj.FrameObj.GetPoints(Frame2, '', '')

model_obj.sap_obj.PointObj.SetRestraint(Frame2i, Restraint)

[Frame4i, Frame4j, ret] = model_obj.sap_obj.FrameObj.GetPoints(Frame4, '', '')

model_obj.sap_obj.PointObj.SetRestraint(Frame4i, Restraint)

[Frame5i, Frame5j, ret] = model_obj.sap_obj.FrameObj.GetPoints(Frame5, '', '')

model_obj.sap_obj.PointObj.SetRestraint(Frame5i, Restraint)

# refresh view, update (initialize) zoom

model_obj.sap_obj.View.RefreshView(0, False)

# add load patterns

load_patterns = {1: 'LTYPE_DEAD', 2: 'LTYPE_OTHER'}

model_obj.sap_obj.LoadPatterns.Add(load_patterns[1], sap2000.LOAD_PATTERN_TYPES[load_patterns[1]], 0, True)
model_obj.sap_obj.LoadPatterns.Add(load_patterns[2], sap2000.LOAD_PATTERN_TYPES[load_patterns[2]], 0, True)

# assign loading for load pattern 'D'

[Frame3i, Frame3j, ret] = model_obj.sap_obj.FrameObj.GetPoints(Frame3, '', '')
model_obj.sap_obj.PointObj.SetLoadForce(Frame3i, load_patterns[1], [0, 0, -10, 0, 0, 0])
model_obj.sap_obj.PointObj.SetLoadForce(Frame3j, load_patterns[1], [0, 0, -10, 0, 0, 0])

# assign loading for load pattern 'EQ'
[Frame3i, Frame3j, ret] = model_obj.sap_obj.FrameObj.GetPoints(Frame3, '', '')
model_obj.sap_obj.FrameObj.SetLoadDistributed(Frame3, load_patterns[2], 1, 10, 0, 1, 1.8, 1.8)

# switch to k-in units

model_obj.sap_obj.SetPresentUnits(sap2000.UNITS['kip_in_F'])

#%% SAVE MODEL AND RUN IT

model_obj.saveandrun(api_path=api_path, file_name='API_1-001.sdb')

#%% OBTAIN RESULTS FROM SAP2000 MODEL

# initialize for Sap2000 results

[Frame3i, Frame3j, ret] = model_obj.sap_obj.FrameObj.GetPoints(Frame3, '', '')

# get Sap2000 results for all load patterns:

SapResult = OrderedDict()

for key, val in load_patterns.items():

    model_obj.sap_obj.Results.Setup.DeselectAllCasesAndCombosForOutput()

    model_obj.sap_obj.Results.Setup.SetCaseSelectedForOutput(val)

    [NumberResults, Obj, Elm, ACase, StepType, StepNum, U1, U2, U3, R1, R2, R3, ret] = model_obj.sap_obj.Results.JointDispl(
        Frame3i, 0, 0, [], [], [], [], [], [], [], [], [], [], [])

    SapResult[val] = U1[0]

print('Debugging line')

#%% CLOSE SAP2000 MODEL AND APPLICATION

sap_obj = sap2000.closesap2000(sap_obj, save_model=False)

#%% MANIPULATE DATA

# fill independent results

IndResult = OrderedDict([('LTYPE_DEAD', -0.02639), ('LTYPE_OTHER', 0.06296)])

# fill percent difference

PercentDiff = {}

for key, val in load_patterns.items():
    PercentDiff[val] = (SapResult[val] / IndResult[val]) - 1

# display results

for key, val in load_patterns.items():
    print()

    print(SapResult[val])

    print(IndResult[val])

    print(PercentDiff[val])

print('debugging line')
