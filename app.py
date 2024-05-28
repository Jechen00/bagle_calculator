############################################################
# Packages
############################################################
import streamlit as st
from streamlit import session_state as ss
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.row import row
import re
import numpy as np
from bagle import model, model_fitter

############################################################
# BAGLE Initializations
############################################################
all_models = [
    'PSPL_Phot_noPar_Param1', 'PSPL_Phot_noPar_Param2',
    'PSPL_PhotAstrom_noPar_Param1', 'PSPL_PhotAstrom_noPar_Param2', 'PSPL_PhotAstrom_noPar_Param3', 'PSPL_PhotAstrom_noPar_Param4',
    'PSPL_Astrom_Par_Param3', 'PSPL_Astrom_Par_Param4',
    'PSPL_PhotAstrom_Par_Param1', 'PSPL_PhotAstrom_Par_Param2', 'PSPL_PhotAstrom_Par_Param3', 'PSPL_PhotAstrom_Par_Param4'
]

srclens_labels = {'Point-Source Point-Lens': 'PSPL'}
data_labels = {'Photometry': '_Phot',
               'Astrometry': '_Astrom',
               'Photometry-Astrometry': '_PhotAstrom'}
par_labels = {'No Parallax': '_noPar',
              'Parallax': '_Par'}
gp_labels = {'No Gaussian Process': '',
             'Gaussian Process': '_GP'}

default_ranges = {
        'mL': (10.0, 0.0, 100.0, 'Msun'),
        't0': (None, None, None, 'MJD'),
        't0_prim': (None, None, None, None),
        'xS0': (None, None, None,'src pos'),
        'xS0_E': (0.0, -5.0, 5.0, 'src pos'),
        'xS0_N': (0.0, -5.0, 5.0, 'src pos'),
        'xL0': (None, None, None, 'lens pos'),
        'u0': (None, None, None, 'Einstein units'),
        'u0_amp': (0.0, -1.0, 1.0, 'Einstein units'),
        'u0_hat': (None, None, None, ''),
        'u0_amp_prim': (0.0, -1.0, 1.0, 'Einstein units'),
        'thetaS0': (None, None, None, 'mas'),
        'beta': (0.0, -2.0, 2.0, 'mas'),
        'muL': (None, None, None,'mas/yr'),
        'muL_E': (0.0, -20.0, 20.0, 'mas/yr'),
        'muL_N': (0.0, -20.0, 20.0, 'mas/yr'),
        'muS': (None, None, None,'mas/yr'),
        'muS_E': (-3.0, -13.0, 7.0, 'mas/yr'),
        'muS_N': (-3.0, -13.0, 7.0, 'mas/yr'),
        'muRel': (None, None, None, 'mas/yr'),
        'muRel_amp': (None, None, None,'mas'),
        'muRel_hat': (None, None, None,''),
        'kappa': (None, None, None,'mas/Msun'),
        'dL': (3500.0, 1000.0, 8000.0, 'pc'),
        'dS': (5000.0, 100.0, 10000.0, 'pc'),
        'dL_dS': (0.5, 0.01, 0.99, None),
        'b_sff': (0.75, 0.0, 1.5, None),
        'mag_src': (19.0, 14.0, 24.0, 'mag'),
        'mag_src_pri': (19.0, 14.0, 24.0,'mag'),
        'mag_src_sec': (19.0, 14.0, 24.0,'mag'),
        'mag_base': (19.0, 14.0, 24.0,'mag'),
        'tE': (200.0, 1.0, 400.0, 'days'),
        'piE': (None, None, None, 'Einstein units'),
        'piE_amp': (None, None, None, 'Einstein units'),
        'piE_E': (0.0, -1.0, 1.0, 'Einstein units'),
        'piE_N': (0.0, -1.0, 1.0, 'Einstein units'),
        'piEN_piEE' : (0.0, -10.0, 10.0, ''),
        'thetaE': (0.5, 0.0, 1.0, 'mas'),
        'thetaE_amp': (None, None, None, 'mas'),
        'thetaE_hat': (None, None, None, ''),
        'log10_thetaE': (-0.2, 0.0, 0.3, 'mas'),
        'piS': (0.12, 0.01, 1.0, 'mas'),
        'piL': (0.12, 0.01, 1.0, 'mas'),
        'raL': (None, None, None,'deg'),
        'decL': (None, None, None,'deg')
    }

############################################################
# Functions
############################################################
def get_params(paramztn):
    param_class_str = srclens_labels[srclens_type] + gp_labels[gp_type] + data_labels[data_type] + paramztn.replace(selected_mod + '_', '')
    param_class = getattr(model, param_class_str)
    all_params = (param_class.fitter_param_names + param_class.phot_param_names + 
                  param_class.phot_optional_param_names + param_class.ast_optional_param_names)
    
    return all_params

def custom_button(label, key = None, help = None, on_click = None, args = None, 
                  bg_clr = 'null', txt_clr = 'null', brdr_clr = 'null'):
    style_cont = stylable_container(
            key = key,
            css_styles = '''
                button {
                    background-color: %s;
                    color: %s;
                    border-radius: 20px;
                    border-width: 1.5px;
                    border-color: %s;
                }
                ''' % (bg_clr, txt_clr, brdr_clr))

    return style_cont.button(label, key, help = help, on_click = on_click, args = args, use_container_width = True)

def new_btn_states():
    ss.new_btns = True
    ss.selected_paramztn = None

def change_btn_states(paramztns, idx):
    ss.btn_states = np.repeat(False, len(paramztns))
    ss.btn_states[idx] = not ss.btn_states[idx]

    ss.selected_paramztn = paramztns[idx]

############################################################
# App Initializations
############################################################
st. set_page_config(layout = 'wide', page_title = 'BAGLE Calculator')

st.markdown('''
    <style>
        .block-container {
            padding-top: 0rem;
        }
               
        div[data-testid = "stExpander"] span p {
            font-size: 2rem;
        }
            
        div[data-testid = "stSlider"] label[data-testid="stWidgetLabel"] p {
            font-size: 1rem;
        }
    </style>
    ''', unsafe_allow_html = True)

st.markdown('''<h1 style = "text-align: center"</style>BAGLE Calculator</h1>''', unsafe_allow_html = True)

if 'new_btns' not in ss:
    ss.new_btns = True

if 'selected_paramztn' not in ss:
    ss.selected_paramztn = None

############################################################
# Model & Parameterization Selection
############################################################
with stylable_container(
    key = 'selection_container',
    css_styles = '''
    {
    width: 100%;
    border-bottom: #3D4044 solid 1px;
    border-top: #3D4044 solid 1px;
    padding-top: 1.5rem;
    padding-bottom: 1.5rem;
    }
    '''
):
    # Row for Model Selection
    mod_row = row([0.2, 0.8], vertical_align = 'center')
    mod_row.markdown('''<h2 style = "padding: 0">Model:</h2>''', unsafe_allow_html = True)

    plus_w = 0.04
    drop_w = (1 - plus_w) / 5
    with mod_row.container():
        srclens_col, plus1, data_col, plus2, par_col, plus3, gp_col = st.columns([drop_w, plus_w, drop_w, plus_w, drop_w, plus_w, drop_w])

        srclens_type = srclens_col.selectbox(label = 'src_lens', options = srclens_labels.keys(), label_visibility = 'collapsed', on_change = new_btn_states)
        data_type = data_col.selectbox(label = 'data', options = data_labels.keys(), label_visibility = 'collapsed', on_change = new_btn_states)
        par_type = par_col.selectbox(label = 'par', options = par_labels.keys(), label_visibility = 'collapsed', on_change = new_btn_states)
        gp_type = gp_col.selectbox(label = 'gp', options = gp_labels.keys(), label_visibility = 'collapsed', on_change = new_btn_states)

        for col in [plus1, plus2, plus3]:
            col.markdown('''<h3 style = "text-align: center">+</h3>''', unsafe_allow_html = True)

    selected_mod = srclens_labels[srclens_type] + data_labels[data_type] + par_labels[par_type] + gp_labels[gp_type]

    # Row for Parameterization Selection
    paramztn_row = row([0.2, 0.8], vertical_align = 'bottom')
    paramztn_row.markdown('''<h2 style = "padding: 0">Parameterization:</h2''', unsafe_allow_html = True)

    paramztns = [x for x in all_models if re.match(selected_mod, x)]
    num_paramztns = len(paramztns)

    if num_paramztns != 0:
            
        if ss.new_btns == True:
            ss.btn_states = np.repeat(False, num_paramztns)
            ss.new_btns = False

        paramztn_btn = paramztn_row.columns(num_paramztns)

        for i in range(num_paramztns):
            params = get_params(paramztns[i])
            param_tooltip = '  \n'.join(params)

            if ss.btn_states[i] == True:
                btn_clrs = ['#464646', '#4BFFEF', '#4BFFEF']
            else:
                btn_clrs = ['#7D7D7D', 'null', 'null']

            with paramztn_btn[i]:
                custom_button(label = paramztns[i], key = paramztns[i],
                            bg_clr = btn_clrs[0], txt_clr = btn_clrs[1], brdr_clr = btn_clrs[2],
                            help = param_tooltip, on_click = change_btn_states, args = (paramztns, i))

    else:
        paramztn_row.markdown('<h3 style = "color: red" >ERROR: There are currently no parameterizations for this model. Please try a different selection.</h3>', unsafe_allow_html = True)
        ss.selected_paramztn = None

############################################################
# Model Parameter Sliders, Plots, and Derived Parameters
############################################################
if ss.selected_paramztn != None:

    selected_params = get_params(ss.selected_paramztn)
    if 'noPar' not in ss.selected_paramztn:
        selected_params += ['raL', 'decL']

    # Expander for Parameter Sliders
    with st.expander(label = 'Paramerters'):
        param_cols = st.columns(4, gap = 'large')

        for i, param in enumerate(selected_params):
            col_idx = i % 4

            with param_cols[col_idx]:
                with stylable_container(
                    key = param,
                    css_styles = '''
                        {
                        margin: 0.5rem;
                        }
                    '''
                ):
                    if default_ranges[param][3] != None:
                        param_label = f'{param} [{default_ranges[param][3]}]'
                    else:
                        param_label = param

                    st.slider(label = param_label, key = param, 
                              min_value = default_ranges[param][1], max_value = default_ranges[param][2],
                              value = default_ranges[param][0], format = '%.2f')
    
    # Expander for Photometry Plot
    # param_dict = {}
    # for param in selected_params:
    #     param_dict[param] = ss[param]
    param_dict = {
        't0': 55763.84,
        'u0_amp': -0.05,
        'tE': 287.48,
        'log10_thetaE': 0.69,
        'piS': 0.12,
        'piE_E': 0.02,
        'piE_N': -0.09,
        'xS0_E': 230.35,
        'xS0_N': -214.73,
        'muS_E': -2.02,
        'muS_N': -3.45,
        'b_sff': 0.05,
        'mag_base': 16.49,
        'raL': 17.86,
        'decL': -29.89
    }
    mod = getattr(model, 'PSPL_PhotAstrom_Par_Param3')(**param_dict)
    t_obs = np.linspace(55000, 56500, 2000)
    phot = mod.get_photometry(t_obs)

    # with st.expander(label = 'Photometry Plot'):

    # # Expander for Astrometry Plot
    # if 'Astrom' in ss.selected_paramztn:
    #     print('Hello')