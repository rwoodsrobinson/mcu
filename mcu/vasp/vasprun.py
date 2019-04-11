#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
from mcu.vasp import utils

class read:
    def __init__(self, file="vasprun.xml"):
        
        if not utils.check_exist(file):
            print('Cannot find the vasprun.xml file. Check the path:', file)
        else:
            self.vasprun = open(file, "r").readlines()  

            # Read parameters:
            generator = self.copy_block(self.vasprun,'generator', level=1)
            incar = self.copy_block(self.vasprun,'incar', level=1)       
            self.generator = self.extract_param(generator)
            self.incar = self.extract_param(incar)     
            self.kpoints = self.get_kpoints()
            self.parameters = self.get_parameters() 
            self.get_atominfo()         
            self.get_structure()     
            self.calculation_block = self.copy_block(self.vasprun,'calculation', level=1)    
            self.lm = None
        
        
    def get_kpoints(self):    
        ''' Extract the <kpoints> block'''
        
        kpoints = self.copy_block(self.vasprun,'kpoints', level=1) 
        generation = self.copy_block(kpoints,'generation', level=2) 
        kpointlist = self.copy_block(kpoints,'varray','kpointlist', level=2)     
        weights = self.copy_block(kpoints,'varray','weights', level=2) 
        kpoints_dict = {}
        
        if len(generation) == 1:
            if 'listgenerated' in generation[0][0]:
                kpoints_dict['type'] = 'listgenerated'
                kpoints_dict['divisions'] = np.int64(utils.str_extract(generation[0][1],'>','<').strip())         
                kpoints_dict['points'] = self.extract_vec(generation[0][1:])      
            elif 'Gamma' in generation[0][0] or 'Monkhorst-Pack' in generation[0][0]:
                if 'Gamma' in generation[0][0]:
                    kpoints_dict['type'] = 'Gamma'       
                else:
                    kpoints_dict['type'] = 'Monkhorst-Pack'                   
                kpoints_dict['divisions'] = np.int64(utils.str_extract(generation[0][1],'>','<').strip().split())
                kpoints_dict['usershift'] = np.float64(utils.str_extract(generation[0][2],'>','<').strip().split()) 
                kpoints_dict['genvec'] = self.extract_vec(generation[0][2:-1])             
                kpoints_dict['usershift'] = np.float64(utils.str_extract(generation[0][2],'>','<').strip().split())  
                
        kpoints_dict['kpointlist'] = self.extract_vec(kpointlist)   # fractional        
        kpoints_dict['weights'] = self.extract_vec(weights)           
        
        return kpoints_dict
        
    def get_parameters(self):    
        ''' Extract the <parameters> block'''

        para_dict = {}
        parameters = self.copy_block(self.vasprun,'parameters', level=1)   

        # General
        general = self.copy_block(parameters,'separator', 'general', level=2)
        para_dict['general'] = self.extract_param(general)       

        # Electronic        
        electronic = self.copy_block(parameters,'separator', 'electronic', level=2)        
        class elec_class:
            def __init__(self, vasprun):
                self.general = vasprun.extract_param(electronic[0][1:14]) 
                
                smearing = vasprun.copy_block(electronic,'separator', 'electronic smearing', level=3)
                self.smearing = vasprun.extract_param(smearing) 
                
                projectors = vasprun.copy_block(electronic,'separator', 'electronic projectors', level=3)
                self.projectors = vasprun.extract_param(projectors)     
                
                startup = vasprun.copy_block(electronic,'separator', 'electronic startup', level=3)
                self.startup = vasprun.extract_param(startup)              
                
                spin = vasprun.copy_block(electronic,'separator', 'electronic spin', level=3)
                self.spin = vasprun.extract_param(spin) 
                
                XC = vasprun.copy_block(electronic,'separator', 'electronic exchange-correlation', level=3)
                self.XC = vasprun.extract_param(XC) 
              
                convergence = vasprun.copy_block(electronic,'separator', 'electronic convergence', level=3)
                conver_general = vasprun.extract_param(convergence[0][1:5]) 
                convergence_detail = vasprun.copy_block(convergence,'separator', 'electronic convergence detail', level=4)
                conver_detail = vasprun.extract_param(convergence_detail) 
                self.convergence = {**conver_general,**conver_detail}
                
                mixer = vasprun.copy_block(electronic,'separator', 'electronic mixer', level=3)
                mix_general = vasprun.extract_param(mixer[0][1:6]) 
                mixer_detail = vasprun.copy_block(mixer,'separator', 'electronic mixer details', level=4)
                mix_detail = vasprun.extract_param(mixer_detail) 
                self.mixer = {**mix_general,**mix_detail}            

                dipolcorrection = vasprun.copy_block(electronic,'separator', 'electronic dipolcorrection', level=3)
                self.dipolcorrection = vasprun.extract_param(dipolcorrection) 
                
        elec = elec_class(self)                  
        para_dict['electronic'] = elec
        
        # grids 
        grids = self.copy_block(parameters,'separator', 'grids', level=2)
        para_dict['grids'] = self.extract_param(grids)   

        # ionic
        ionic = self.copy_block(parameters,'separator', 'ionic"', level=2)
        para_dict['ionic'] = self.extract_param(ionic)             

        # ionic md
        ionic_md = self.copy_block(parameters,'separator', 'ionic md', level=2)
        para_dict['ionic md'] = self.extract_param(ionic_md)          

        # symmetry
        symmetry = self.copy_block(parameters,'separator', 'symmetry', level=2)
        para_dict['symmetry'] = self.extract_param(symmetry) 
        
        # dos
        dos = self.copy_block(parameters,'separator', 'dos', level=2)
        para_dict['dos'] = self.extract_param(dos)         

        # writing
        writing = self.copy_block(parameters,'separator', 'writing', level=2)
        para_dict['writing'] = self.extract_param(writing)  
        
        # performance
        performance = self.copy_block(parameters,'separator', 'performance', level=2)
        para_dict['performance'] = self.extract_param(performance)          

        # miscellaneous
        miscellaneous = self.copy_block(parameters,'separator', 'miscellaneous', level=2)
        para_dict['miscellaneous'] = self.extract_param(miscellaneous)  

        # exchange-correlation
        XC = self.copy_block(parameters,'separator', 'electronic exchange-correlation', level=2)
        para_dict['XC'] = self.extract_param(XC) 

        # vdW_DFT
        vdW_DFT = self.copy_block(parameters,'separator', 'vdW DFT', level=2)
        para_dict['vdW_DFT'] = self.extract_param(vdW_DFT) 

        # linear response
        linear_response = self.copy_block(parameters,'separator', 'linear response parameters', level=2)
        para_dict['linear response'] = self.extract_param(linear_response) 

        # orbital magnetization
        orb_magnetization = self.copy_block(parameters,'separator', 'orbital magnetization', level=2)
        para_dict['orb magnetization'] = self.extract_param(orb_magnetization)     

        # response functions
        response_functions = self.copy_block(parameters,'separator', 'response functions', level=2)
        para_dict['response functions'] = self.extract_param(response_functions)     

        # External order field
        ext_order_field = self.copy_block(parameters,'separator', 'External order field', level=2)
        para_dict['ext order field'] = self.extract_param(ext_order_field)  

        # External order field
        ext_order_field = self.copy_block(parameters,'separator', 'External order field', level=2)
        para_dict['ext order field'] = self.extract_param(ext_order_field)          
        
        return para_dict

    def get_atominfo(self):    
        ''' Extract the <atominfo> block'''
        
        atominfo = self.copy_block(self.vasprun,'atominfo', level=1)   
        atoms = self.copy_block(atominfo,'array', 'atoms', level=2) 
        atoms_set = self.copy_block(atoms,'set', level=3)[0][1:-1] 
        atomtypes = self.copy_block(atominfo,'array', 'atomtypes', level=2)           
        atomtypes_set = self.copy_block(atomtypes,'set', level=3)[0][1:-1]  
        
        self.natom = np.int64(utils.str_extract(atominfo[0][1],'>','<').strip())
        self.ntypes = np.int64(utils.str_extract(atominfo[0][2],'>','<').strip())

        # atom = [element], atm = [element, atomtype]     
        self.atom = []   
        self.atm = []           
        for line in atoms_set:
            temp = utils.str_extract(line,'<c>','</c>')
            atom = temp[0].strip()
            type = np.int64(temp[1].strip()) - 1
            self.atm.append([atom,type])
            self.atom.append(atom)
            
        # types = [atoms_per_type, element, mass, valence, pseudopotential]       
        self.types = []
        for line in atomtypes_set:
            temp = utils.str_extract(line,'<c>','</c>')
            natom = np.int64(temp[0].strip())
            atom = temp[1].strip()
            mass = np.float64(temp[2].strip())
            elec = np.int64(np.float64(temp[3].strip()))
            paw = temp[4].strip()            
            self.types.append([natom,atom,mass,elec,paw]) 

    def get_cell(self, structure, level=1):  
        '''Get info from a <structure> block
           the structure could be at level 1 or level 2 inside the <calculation> block
           Return: lattice, reciprocal lattice, volume, ions positions'''

        basis = self.copy_block(structure,'varray', 'basis', level=level+2)            
        rec_basis = self.copy_block(structure,'varray', 'rec_basis', level=level+2)  
        positions = self.copy_block(structure,'varray', 'positions', level=level+1) 
        volume = np.float64(utils.str_extract(structure[0][7],'>','<').strip())
        

        lattice = self.extract_vec(basis)
        recip_lattice = self.extract_vec(rec_basis)   
        positions = self.extract_vec(positions) 

        return lattice, recip_lattice, positions, volume

            
    def get_structure(self): 
        '''Get the initial and final structures'''
        
        initialpos = self.copy_block(self.vasprun,'structure', 'initialpos', level=1)           
        finalpos = self.copy_block(self.vasprun,'structure', 'finalpos', level=1)  
        
        self.cell_init = self.get_cell(initialpos,level=1)  
        self.cell_final = self.get_cell(finalpos,level=1)  

    def get_sc(self, calculation): 
        '''Get <scstep> block for each <calcualtion> block'''
        
        scstep = self.copy_block(calculation,'scstep', level=2)
        
        # Get info from the first and the last scstep:
        sc_first_last = []
        for i in [0,-1]:
            energy = self.copy_block(scstep[i],'energy', level=3)[0][1:-1]
            values = []
            for line in energy:
                val = np.float64(utils.str_extract(line,'>','<').strip())
                values.append(val)
            sc_first_last.append(values)
                
        sc_list = []   
        sc_list.append(sc_first_last[0])             
        for sc in scstep[1:-1]:
            energy = self.copy_block(sc,'energy', level=3)[0][1:-1]
            values = []
            for line in energy:
                val = np.float64(utils.str_extract(line,'>','<').strip())
                values.append(val)
            sc_list.append(values) 
            
        sc_list.append(sc_first_last[1])             
        
        return sc_list
        
    def get_calculation(self,calculation_block):
        '''Get info from the <calculation> block(s)'''
    
        calculation = []
        for calc in calculation_block:
            # Get <scstep>
            scstep = self.get_sc(calc)     
            
            # Get <structure>
            structure = self.copy_block(calc,'structure', level=2)           
            cell = self.get_cell(structure,level=2)              
            
            # Get <varray name="forces" >
            forces = self.copy_block(calc,'varray', 'forces', level=2) 
            forces_mat = self.extract_vec(forces) 
            
            # Get <varray name="stress" >
            stress = self.copy_block(calc,'varray', 'stress', level=2) 
            stress_mat = self.extract_vec(stress) 

            # Get <time name="totalsc">  
            time = self.copy_line(calc,'time',level=2)
            time = np.float64(utils.str_extract(time,'>','<').strip().split())
            calculation.append([cell,scstep,forces_mat,stress_mat,time])
            
        return calculation
        
    def get_eigenvalues(self, block, level=2):
        '''Get info from the <eigenvalues> block''' 

        eigenvalues = self.copy_block(block,'eigenvalues', level=level) 
        eigvals_spin = self.copy_block(eigenvalues,'set', 'spin', level=level+3)
        out = []
        for spin in eigvals_spin:
            eigs_kpts = self.copy_block(spin,'set', 'kpoint', level=level+4)
            out_spin = []
            for kpt in eigs_kpts:
                eigvals = self.extract_vec(kpt)
                out_spin.append(eigvals)
            out.append(out_spin)
            
        return np.asarray(out)
        
    def get_band(self):
        '''Get band (eigenvalues)'''
        self.band = self.get_eigenvalues(self.calculation_block[-1], level=2)
        
    def get_dos(self):
        '''Get info from the <dos> block''' 

        DOS = self.copy_block(self.calculation_block[-1],'dos', level=2) 
        
        if len(DOS) == 0:
            print('DOS was not computed')        
        else:
            print('Get total density of states (tdos)')           
            self.efermi = np.float64(utils.str_extract(DOS[0][1],'>','<').strip())
            
            # Total DOS
            total = self.copy_block(DOS,'total', level=3)
            dos_spin = self.copy_block(total,'set', 'spin', level=6)
            total_out = []
            for spin in dos_spin:
                total_out.append(self.extract_vec(spin))
                
            self.tdos = np.asarray(total_out) 
            
            # Partial DOS            
            partial = self.copy_block(DOS,'partial', level=3) 
            
            if len(partial) == 1 and self.lm != None:
                print('Get partial density of states (pdos)')             
                # Get lm 
                self.lm = []
                for line in partial[0][6:]:
                    if '<field>' not in line: break  
                    self.lm.append(utils.str_extract(line,'>','<').strip())

                # Get pdos                     
                dos_ion = self.copy_block(partial,'set', 'ion', level=6)
                partial_out = []
                for ion in dos_ion:
                    dos_spin = self.copy_block(ion,'set', 'spin', level=7)
                    out_ion = []                 
                    for spin in dos_spin:
                        out_ion.append(self.extract_vec(spin))
                    partial_out.append(out_ion)

                self.pdos = np.asarray(partial_out)
                  
    def get_projected(self):
        '''Get info from the <projected> block'''         
        
        projected = self.copy_block(self.calculation_block[-1],'projected', level=2)
        if len(projected) == 0:
            print('Projected wave function character was not computed')        
        else:  
            print('Get projected wave function character')             
            self.pro_band = self.get_eigenvalues(projected[0], level=3)
            array = self.copy_block(projected,'array', level=3)
            if self.lm == None:
                self.lm = []
                for line in array[0][5:]:
                    if '<field>' not in line: break  
                    self.lm.append(utils.str_extract(line,'>','<').strip())  
            
            pro_spin = self.copy_block(array,'set', 'spin', level=5)
            out = []            
            for spin in pro_spin:
                pro_spin = self.copy_block(spin,'set', 'kpoint', level=6)   
                out_spin = []                
                for kpt in pro_spin:
                    pro_kpt = self.copy_block(kpt,'set', 'band', level=7) 
                    out_kpt = []
                    for band in pro_kpt:
                        pro = self.extract_vec(band)
                        out_kpt.append(pro)
                    out_spin.append(out_kpt)
                out.append(out_spin)
                
            self.pro_wf = np.asarray(out)         
      
    def get_dielectric(self):
        '''Get info from the <dielectricfunction> block'''

        dielectric = self.copy_block(self.calculation_block[-1],'dielectricfunction', level=2)  
        if len(dielectric) == 0:
            print('Frequency-dependent dielectric function was not computed')        
        else:  
            print('Get frequency-dependent dielectric function')
            out = []
            for dielec in dielectric:
                imag = self.copy_block(dielec,'imag', level=3)
                imag_set = self.copy_block(imag,'set', level=5)                
                real = self.copy_block(dielec,'real', level=3) 
                real_set = self.copy_block(real,'set', level=5) 
                out.append([self.extract_vec(imag_set),self.extract_vec(real_set)])
                
            self.freq_dielectric = np.asarray(out)   
            
#--------------------------------------------------------------------------------------------------------- 
# USEFUL FUNCTIONS TO MANIPULATE vasprun.xml file 
#---------------------------------------------------------------------------------------------------------
         
    def copy_block(self, big_block, key, subkey='', level=1):
        ''' Copy one or more blocks from a block starting with <key> and ending with </key>
            level indicates how many blank space before <key> '''
        
        if len(big_block) == 1: big_block = big_block[0]
        copy = None
        blocks = []
        block = None
        start_key = level*' ' + '<' + key
        end_key = level*' ' + '</' + key  
        
        for line in big_block:
            if (start_key == line[:len(start_key)]) and (subkey in line): 
                copy = True
                block = []
                
            if copy == True:
                block.append(line)
            elif copy == False:
                break
                
            if end_key == line[:len(end_key)] and block != None: 
                blocks.append(block)            
                copy = False               
                
        return blocks 

    def copy_line(self, big_block, key, subkey='', level=1):
        ''' Copy one or more lines from a block starting with <key>'''
        
        if len(big_block) == 1: big_block = big_block[0]
        copy = None
        lines = []
        line_copy = None
        start_key = level*' ' + '<' + key
        end_key = level*' ' + '</' + key  
        
        for line in big_block:
            if (start_key == line[:len(start_key)]) and (subkey in line): 
                lines.append(line)
                
        if len(lines) == 1: lines = lines[0]
        
        return lines 
        
    def extract_param(self, block):
        ''' This extracting function is used for a block containing data with keywords.
            Get the keyword and corresponding value and put them in a dictionary '''

        if len(block) == 1: block = block[0]
        
        dict = {}
        for line in block[1:-1]:
            if 'name="' in line:
                key = utils.str_extract(line,'name="','"')
                data_type = None
                
                if 'type="' in line:
                    data_type = utils.str_extract(line,'type="','"')                                
                value = utils.str_extract(line,'>','<').strip()

                if '<v' in line:   
                    value = value.split()
                if data_type == None:
                    value = np.float64(value)
                elif data_type == 'int':
                    value = np.int64(value) 
                elif data_type == 'logical':
                    if value == 'T': 
                        value = True
                    else:
                        value = False
                       
                dict[key] = value
                
        return dict
        

    def extract_vec(self, block):    
        '''This extracting function is used for a block containing a matrix or vector'''    
        
        if len(block) == 1: block = block[0]
        
        array = []
        for line in block[1:-1]:        
            vec = utils.str_extract(line,'>','<').strip().split()
            vec = np.float64(vec)    
            array.append(vec)
            
        return np.asarray(array)                        
        
