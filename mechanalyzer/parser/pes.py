"""
Read the mechanism file
"""

import automol
from mechanalyzer.parser import ckin_ as ckin


# PARSE THE MECHANISM FIle 
def read_mechanism_file(mech_str, mech_type, spc_dct, sort_rxns=False):
    """ Get the reactions and species from the mechanism input
    """

    # Parse the info from the chemkin file
    if mech_type == 'chemkin':
        formulas, rct_names, prd_names, rxn_names = ckin.parse(
            mech_str, spc_dct, sort_rxns)
    else:
        raise NotImplementedError

    return [formulas, rct_names, prd_names, rxn_names]


# FUNTIONS FOR THE PES DICT OBJECTS CONTAINING INFO FOR THE REACTIONS ON PES
def build_pes_dct(formula_str_lst, rct_names_lst, prd_names_lst, rxn_name_lst):
    """ Build a dictionary of the PESs
    """

    pes_dct = {}
    current_formula = ''
    for fidx, formula in enumerate(formula_str_lst):
        if current_formula == formula:
            pes_dct[formula]['rct_names_lst'].append(rct_names_lst[fidx])
            pes_dct[formula]['prd_names_lst'].append(prd_names_lst[fidx])
            pes_dct[formula]['rxn_name_lst'].append(rxn_name_lst[fidx])
        else:
            current_formula = formula
            pes_dct[formula] = {}
            pes_dct[formula]['rct_names_lst'] = [rct_names_lst[fidx]]
            pes_dct[formula]['prd_names_lst'] = [prd_names_lst[fidx]]
            pes_dct[formula]['rxn_name_lst'] = [rxn_name_lst[fidx]]

    return pes_dct


# FUNCTIONS FOR THE CHANNELS DICT OBJECTS
def connected_channels_dct(pes_dct):
    """ Determine all the connected reaction channels for each PES
        Build a dictionary for each PES with lists of connected channels:
            dct[PES_FORMULA] = [ [SUB_PES_1], [SUB_PES_2], ... , [SUB_PES_N] ]
            where each SUB_PES = [n1, n2, ... , nN],
            where n1 to nN correspond to ixds for channels that are
            connected to each other
        For efficiency we only determine channels for PESs we wish to run.
    """
    conn_chn_dct = {}
    for _, formula in enumerate(pes_dct):
        # Set the names lists for the rxns and species needed below
        pes_rct_names_lst = pes_dct[formula]['rct_names_lst']
        pes_prd_names_lst = pes_dct[formula]['prd_names_lst']
        pes_rxn_name_lst = pes_dct[formula]['rxn_name_lst']

        # Split up channels into a connected sub-pes within a formula
        subpes_idx = 0
        conndct = {}
        connchnls = {}
        for chnl_idx, _ in enumerate(pes_rxn_name_lst):
            connected_to = []
            chnl_species = [list(pes_rct_names_lst[chnl_idx]),
                            list(pes_prd_names_lst[chnl_idx])]
            for conn_chnls_idx in conndct:
                for spc_pair in chnl_species:
                    if len(spc_pair) == 1:
                        if spc_pair in conndct[conn_chnls_idx]:
                            if conn_chnls_idx not in connected_to:
                                connected_to.append(conn_chnls_idx)
                        elif spc_pair[::-1] in conndct[conn_chnls_idx]:
                            if conn_chnls_idx not in connected_to:
                                connected_to.append(conn_chnls_idx)
            if not connected_to:
                conndct[subpes_idx] = chnl_species
                connchnls[subpes_idx] = [chnl_idx]
                subpes_idx += 1
            else:
                conndct[connected_to[0]].extend(chnl_species)
                connchnls[connected_to[0]].append(chnl_idx)
                if len(connected_to) > 1:
                    for cidx, cval in enumerate(connected_to):
                        if cidx > 0:
                            conn_specs = conndct.pop(cval, None)
                            conn_chnls = connchnls.pop(cval, None)
                            conndct[connected_to[0]].extend(conn_specs)
                            connchnls[connected_to[0]].extend(conn_chnls)
                for cidx in conndct:
                    conndct[cidx].sort()
                    conndct[cidx] = [
                        conndct[cidx][i] for i in
                        range(len(conndct[cidx])) if i == 0 or
                        conndct[cidx][i] != conndct[cidx][i-1]]

        # Add connected channels list to the dictionary
        conn_chn_dct[formula] = connchnls

    return conn_chn_dct


# PES MODIFIERS
def sort_by_rxn(pes_dct, spc_dct, wanted_rxns):
    """ toy code for sorting by reactions
    """

    for formula in pes_dct:
        # Get rct and prd names
        rct_names = pes_dct[formula]['rct_names_lst']
        prd_names = pes_dct[formula]['rct_names_lst']
        for rcts, prds in zip(rct_names, prd_names):
            # Get the inchis and grabhs
            rct_ichs = tuple(spc_dct[rct]['inchi'] for rct in rcts)
            rct_gras = tuple(automol.inchi.graph(ich) for ich in rct_ichs) 
            prd_ichs = tuple(spc_dct[prd]['inchi'] for prd in prds)
            prd_gras = tuple(automol.inchi.graph(ich) for ich in rct_ichs) 
            # ID reaction
            rclass = automol.graph.reac.classify(rct_gras, prd_gras)
            # Sort using reaction ID...

# WRITERS
def write_mechanism_file(pes_dct, path, outname):
    """ Write the mechanism file from a mech dct
    """

    mech_str = ''

    for pes_idx, formula in enumerate(pes_dct):
        print('! PES:', pes_idx+1, formula)
        pes_rxn_name_lst = pes_dct[formula]['rxn_name_lst']
        pes_rct_names_lst = pes_dct[formula]['rct_names_lst']
        pes_prd_names_lst = pes_dct[formula]['prd_names_lst']
        for chn_idx, _ in enumerate(pes_rxn_name_lst):
            mech_str += (
                '  {} = {}   1.0 0.0 0.0'.format(
                ' + '.join(pes_rct_names_lst[chn_idx]),
                ' + '.join(pes_prd_names_lst[chn_idx]))
            )

    # Write the file
    
    mech_file = os.path.join(path, outname)
    with open(mech_file, 'w') as file_obj:
        file_obj.write(spc_str)
