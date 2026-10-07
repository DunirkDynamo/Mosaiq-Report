#--------------------------------------------------------
# planqa_mainwindow.py

# This class searches a patient directory for plans and 
# returns a list of plan dictionaries (one for each Rx) when
# given a specific plan.
# It's entirely too long but mostly because the Monaco flat-file system
# is torturous and undocumented.
# -------------------------------------------------------

import os as os
#from . import hypfunctions as hyp
import hypfunctions as hyp
import monaco_read as mr

class monaco_plan:

    def __init__(self, ptid, newpath = None):

        if newpath == None:
            self.monaco_dir = '\\\\civic1.ottawahospital.on.ca\\medphys\\Monaco\\Clinic 1\\1~The Ottawa Hospital'
        else:
            self.monaco_dir = newpath

        self.get_plan_names_in_patient_folder(ptid)

        #BEAM MODEL DICTIONARY: used to relate beam model names with things like energgy, number of MLC leaves, etc.
        self.beam_model_dictionary = {}

        agility_machines = ['RUnit 07 A', 'RUnit 08 A', 'RUnit 09 A', 'RUnit 10 A',
                            'RUnit 21 A', 'RUnit 22 A', 'RUnit 23 A', 'RUnit 06 V', 'RUnit 05 V']

        #-------------------

        agility_6 = {'treatment unit': 'Agility', 
                             'machines': agility_machines,
                             'number of MLC leaves': 80,
                             'modality': 'X-rays',
                             'energy': 6}
        agility_10 = {'treatment unit': 'Agility', 
                             'machines': agility_machines,
                             'number of MLC leaves': 80,
                             'modality': 'X-rays',
                             'energy': 10}

        self.beam_model_dictionary['00Mon5mmMLC6x'] = agility_6
        self.beam_model_dictionary['OttawaAgility - 6MV'] = agility_6
        self.beam_model_dictionary['OttawaAgility - 10MV'] = agility_10


        #-------------------

        agility_6_final = {'treatment unit': 'Agilityfinal', 
                             'machines': agility_machines,
                             'number of MLC leaves': 80,
                             'modality': 'X-rays',
                             'energy': 6}
        agility_10_final = {'treatment unit': 'Agilityfinal', 
                             'machines': agility_machines,
                             'number of MLC leaves': 80,
                             'modality': 'X-rays',
                             'energy': 10}

        self.beam_model_dictionary['00Mon5mmMLC6xFINAL'] = agility_6_final
        self.beam_model_dictionary['Agilityfinal - 6MV'] = agility_6_final
        self.beam_model_dictionary['Agilityfinal - 10MV'] = agility_10_final

        #--------------------        

    def get_plan_names_in_patient_folder(self, ptid):
        # populates list for the Monaco plans table 

        file_and_folder_list = os.listdir(self.monaco_dir)

        self.plans = []

        for name in file_and_folder_list:
            if ptid in name:
                self.patient_folder = os.path.join(self.monaco_dir, name)
                if os.path.exists(os.path.join(self.monaco_dir, name, 'plan')):
                    
                    plan_names = []
                    must_have = ['tel.1', '.hyp', 'plan_comment', 'checksum', 'dose']
                    for temp_plan_name in os.listdir('\\'.join([self.monaco_dir, name, 'plan'])):

                        temp_path = os.path.join(self.monaco_dir, name, 'plan', temp_plan_name)

                        if os.path.isdir(temp_path):
                            valid_plan = True

                            filenames = os.listdir(temp_path)

                            for string in must_have:
                                if any(string in s for s in filenames) == False:
                                    valid_plan = False

                            if valid_plan:
                                
                                for hypfile in [f for f in filenames if '.hyp' in f]:
                                    print(hypfile)

                                    lines =[line.rstrip('\n').lstrip(' ').rstrip(' ') 
                                        for line in open(os.path.join(temp_path, hypfile))]
                                    #for line in lines:  Was used to detect electron plans before they were supported
                                        #if 'secondary=oemc' in line:
                                        #    valid_plan = False                                    

                            if valid_plan: 
                                plan_names.append(temp_plan_name)

                    for pname in plan_names:
                        #every file/folder in the 'plan' directory should be a plan
                        temp_plan = {   'plan name': pname,
                                        'plan directory':  os.path.join(
                                            self.monaco_dir, name, 'plan', pname) }
                        try:
                            temp_plan['filenamelist'] = self.get_monaco_filenames(temp_plan['plan directory'])
                        except NotADirectoryError:
                            temp_plan['filenamelist'] = None

                        self.plans.append(temp_plan)

                    self.plans = [temp_plan for temp_plan in self.plans 
                                    if temp_plan['filenamelist'] != None and temp_plan['filenamelist'] != []]

                    #print(self.plans)

                    for plan in self.plans:
                        if False in [self.is_plan_approved(plan['plan directory'], filenames) 
                                        for filenames in [plan['filenamelist'][0]]]:
                            plan['approved'] = False
                        else:
                            plan['approved'] = True

                    self.get_sites_and_prescription()                    

                break
        else:
            self.patient_folder = None

    def get_sites_and_prescription(self):

        for plan in self.plans:

            print()
            print('>>>>> Trying to read plan:', plan['plan name'])

            try:
                plan['prescription dose'] = 0

                for filenames in plan['filenamelist']:

                    tel_file = filenames['tel']
                    rx = filenames['rxlabel']

                    sequence = [rx, '0', '1', rx]
                    # find site name.  Near end of tel file.
                                  

                    tel_lines = [line.rstrip('\n').lstrip(' ').rstrip(' ') 
                                 for line in open('\\'.join([plan['plan directory'], filenames['tel']]))]

                    if tel_lines[0] == '00a7101d': #every Monaco5 tel file starts this way

                        indx = [i for i in range(len(tel_lines)) if tel_lines[i:i+len(sequence)] == sequence][0]

                        plan['site'] = tel_lines[indx-6]
                        #plan['prescription dose'] += float(tel_lines[indx-5])*100
                        try:
                            plan['prescription dose'] += float(tel_lines[indx+24])
                        except IndexError:
                            plan['prescription dose'] += float(tel_lines[indx-5])*100
                        plan['fractions'] = int(tel_lines[indx-4])

                    else:
                        plan['site'] = ''
                        plan['prescription dose'] = None
                        plan['fractions'] = None
                        
            except TypeError:

                print('Sites and prescritpions error opening files.')
                print(plan['plan directory'])

                plan['site'] = ''
                plan['prescription dose'] = None
                plan['fractions'] = None

    def get_monaco_filenames(self, plan_dir):
        #gets the relevant files in the plan directory.  They are grouped by Rx
    
        filenames = {}
        names = os.listdir(plan_dir)

        # Use XLOG files to get prescriptions in plan:
        #rxlabels = sorted([name.split('.')[0].split('x')[-1] for name in names if '.xlog' in name])
        rxlabels = sorted([name.split('.')[0][-1] for name in names if '.xlog' in name])
        #print(xlogs)

        if rxlabels == []:
            rxlabels = ['A']
        
        #find hyp file
        hypfile = [name for name in names if '.hyp' in name]
        
        filenames['rxlabel'] = rxlabels
        
        if hypfile == None:
            print('Couldn\'t find hyp file.')
            filenames['hyp'] = None
        else:
            filenames['hyp'] = []
            for i,rx in enumerate(rxlabels):
                hypname = []
                if i == 0:
                    hypname = [name for name in hypfile if '_' not in name]
                else:
                    hypname = [name for name in hypfile if rx in name]

                if len(hypname) == 1:
                    filenames['hyp'].append(hypname[0])
                else:
                    print('Error finding hyp files')
                    filenames['hyp'].append(None)
           
            
        #find approval file
        approval_files = [name for name in names if 'plan_comment' in name]
        
        if approval_files == None:
            print('Couldn\'t find approval file.')
            filenames['approval'] = None
        else:
            
            filenames['approval'] = []
            for i,rx in enumerate(rxlabels):
                approvename = []
                if i == 0:
                    approvename = [name for name in approval_files if 'rx' not in name]
                else:
                    approvename = [name for name in approval_files if rx in name]

                if len(hypname) == 1:
                    filenames['approval'].append(approvename[0])
                else:
                    print('Error finding hyp files')
                    filenames['approval'].append(None)

            
        #find tel file
        tel_files = [name for name in names if 'tel.1' in name and 'dose' not in name]
        
        if tel_files == None:
            print('Couldn\'t find tel file.')
            filenames['tel'] = None
        else:
            filenames['tel'] = []
            for i,rx in enumerate(rxlabels):
                telname = []
                if i == 0:
                    telname = [name for name in tel_files if '_' not in name]
                else:
                    telname = [name for name in tel_files if rx in name]

                if len(hypname) == 1:
                    filenames['tel'].append(telname[0])
                else:
                    print('Error finding hyp files')
                    filenames['tel'].append(None)
           
            
        #find plan file
        plan_files = [name for name in names if 'plan' in name and 'comment' not in name]
        
        if plan_files == None:
            print('Couldn\'t find plan file.')
            filenames['plan'] = None
        else:
            filenames['plan'] = []
            for i,rx in enumerate(rxlabels):
                telname = []
                if i == 0:
                    planname = [name for name in plan_files if '_' not in name]
                else:
                    planname = [name for name in plan_files if rx in name]

                if len(hypname) == 1:
                    filenames['plan'].append(planname[0])
                else:
                    print('Error finding hyp files')
                    filenames['plan'].append(None)
        
        if (len(filenames['hyp']) == len(filenames['tel']) == 
            len(filenames['approval']) == len(filenames['plan']) == len(filenames['rxlabel']) ):
            
            filenamelist = []
            
            for i in range(len(filenames['hyp'])):
                filenamelist.append( { 'hyp': filenames['hyp'][i], 
                                       'tel': filenames['tel'][i],
                                       'approval': filenames['approval'][i],
                                       'plan': filenames['plan'][i],
                                       'rxlabel': filenames['rxlabel'][i] } )
                
            return filenamelist
            
        else:
            print('get_monaco_filenames: Found different number of various files')  

    def is_plan_approved(self, plan_dir, filenames):
        try:    
            approval_lines = [line.rstrip('\n') for line in 
                                  open('\\'.join([plan_dir, filenames['approval']]))]

            if approval_lines[1] == '0':
                return False
            else:
                return True
        except TypeError:
            print('Approval opening error.', plan_dir)
            return False

    def get_doc_number(self, plan_dir, filenames):

        plan_comment_lines =  [line.rstrip('\n') for line in 
                              open('\\'.join([plan_dir, 'plan_comment']))]

        comment = ''
        for i,line in enumerate(plan_comment_lines[6:]):
            if line != '':
                comment = '\n'.join(plan_comment_lines[6+i:])
                break

        if 'rx' in filenames['approval']:
            rx_label = ' '.join(['Rx', filenames['approval'][2]])
        else:
            rx_label = 'Rx A'

        search_letter = rx_label[3]

        next_letter = chr(ord(search_letter) + 1)

        try:
            doc_number_index = plan_comment_lines[5].index(search_letter)

            try:
                end_index = plan_comment_lines[5].index(next_letter)

                doc_number = plan_comment_lines[5][doc_number_index + 1: end_index]

            except:
                doc_number = plan_comment_lines[5][doc_number_index+1:]

        except:
            #only one prescription

            doc_number = plan_comment_lines[5]

        print(doc_number)

        return rx_label, doc_number, comment

    #========================================================== 
    #==========================================================

    def get_plan_info(self, chosen_plan):

        plan_dir = chosen_plan['plan directory']
        filenamelist = chosen_plan['filenamelist']
       
        plans = []
        
        for filenames in filenamelist:
        
            print()
            print('*** Reading Monaco plan ***')
            print()
            print('Hypfile:', filenames['hyp'])

            if filenames['hyp'] == None:
                print('>>> Likely a Monaco 3.2 plan')
            else:
                print()
            
                #plandef = self.get_plandef_data_from_planfile(plan_dir, filenames)
                plandef = self.get_plandef_data(plan_dir, filenames)
                
                field_names = self.get_field_names_from_hyp_file(plan_dir, filenames)
                
                tel_lines = [line.rstrip('\n').lstrip(' ').rstrip(' ') 
                             for line in open('\\'.join([plan_dir, filenames['tel']]))]
                
                field_def = self.field_def_from_tel(tel_lines,field_names)
                
                rx_label, doc_number, comment = self.get_doc_number(plan_dir, filenames)
                
                is_approved = self.is_plan_approved(plan_dir, filenames)
                plan = {}

                plan['plan def'] = {}

                plan['plan def']['plan name'] = os.path.basename(os.path.normpath(plan_dir))

                last_name, first_name = self.get_patient_name(plandef['ID'])
                plan['plan def']['last name'] = last_name
                plan['plan def']['first name'] = first_name
                plan['plan def']['ID'] = plandef['ID']
                plan['plan def']['course number'] = None
                plan['plan def']['isocenter'] = None

                plan['plan def']['rx label'] = rx_label
                plan['plan def']['doc number'] = doc_number
                plan['plan def']['approved'] = is_approved
                plan['plan def']['comment'] = comment

                plan['plan def']['site'] = chosen_plan['site']
                plan['plan def']['prescription dose'] = chosen_plan['prescription dose']
                plan['plan def']['fractions'] = chosen_plan['fractions']

                plan['plan def']['machine'] = self.beam_model_dictionary[field_def[0]['beam model']]['machines']
                plan['plan def']['beam model'] = field_def[0]['beam model']
                
                calc_params = self.get_calc_parameters_from_hyp_file(plan_dir, filenames)
                
                plan['plan def']['calculation parameters'] = calc_params #used for QAtasks window

                fields = []
                isocenters = []
                
                (dicom_CT_zero, orientation, zero_ct_path, 
                    scan_reference_point, setup_reference_point, 
                    CTtoED, diff_flag, pt5bug, TPCTdir, import_orientation) = self.get_CT_info(plan_dir, plandef['TPCT'])
                # used for scan reference point window
                
                plan['plan def']['CTtoED'] = CTtoED
                plan['plan def']['orientation flag'] = diff_flag #get this from comparison with plandef['plan orientation']
                plan['plan def']['pt5bug'] = pt5bug
                plan['plan def']['TPCTdir'] = TPCTdir

                plan['plan def']['zero CT'] = zero_ct_path
                plan['plan def']['dicom CT zero'] = dicom_CT_zero
                plan['plan def']['setup reference point'] = setup_reference_point
                plan['plan def']['setup ref in dicom'] = [setup_reference_point[0]/10+dicom_CT_zero[0],
                                                            -setup_reference_point[2]/10+dicom_CT_zero[1],
                                                            setup_reference_point[1]/10]
                plan['plan def']['scan reference point'] = scan_reference_point
                plan['plan def']['scan ref in dicom'] = [scan_reference_point[0]/10+dicom_CT_zero[0],
                                                            -scan_reference_point[2]/10+dicom_CT_zero[1],
                                                            scan_reference_point[1]/10]

                plan['plan def']['orientation'] = orientation

                if 'Feet' in orientation:
                    head_modifier = [1, 1, 1]
                else:
                    head_modifier = [1, 1, 1]

                if 'Supine' in orientation:
                    supine_modifier = [1, 1, 1]
                else:
                    supine_modifier = [-1, 1, -1]

                orientation_modifier = [pta * ptb for (pta, ptb) in zip(head_modifier, supine_modifier)]
                
                for fld in field_def:
                    field, iso = self.get_field(tel_lines, fld, dicom_CT_zero, orientation_modifier)

                    fields.append(field)
                    isocenters.append(iso)
                
                plan['plan def']['isocenter'] = isocenters[0] #[pta * ptb for (pta, ptb) in zip(isocenters[0], orientation_modifier)]
                plan['plan def']['monaco iso'] = fields[0]['monaco iso']

                shifts = [(pt_a - pt_b)/10 for (pt_a, pt_b) in zip(plan['plan def']['monaco iso'], 
                                        plan['plan def']['scan reference point'])]
                plan['plan def']['shifts'] = shifts

                plan['fields'] = fields

                for fld in fields:
                    if 'couch included' in fld.keys():
                        plan['plan def']['couch included'] = fld['couch included']

                plans.append(plan)
        try:        
            plan_info = plans
            
            if 'couch included' in plan['plan def'].keys():
                print('Couch included:', plan['plan def']['couch included'])

        except UnboundLocalError:
            return None

        return plan_info
    
    #============================================

    def get_field(self, tel_lines, fld, dicom_CT_zero, orientation_modifier):
    
        field = {}
        
        field['original field number'] = int(tel_lines[fld['index']-4]) 
        field['original field name'] = fld['name']
        
        field['field label'] = None
        field['field name'] = fld['name']

        print(fld['name'])
        
        field['Dose'] = None
        
        field['modality'] = self.beam_model_dictionary[fld['beam model']]['modality']
        field['energy'] = self.beam_model_dictionary[fld['beam model']]['energy']
        field['number of MLC leaves'] = self.beam_model_dictionary[fld['beam model']]['number of MLC leaves']
        
        if tel_lines[fld['index']+3] == '1,0,0':
            is_SETUP = True
        else:
            is_SETUP = False
        
        
        if is_SETUP:
            field['delivery type'] = 'Static'
            field['beam type'] = 'Static'
            field['planning type'] = 'Setup'
        
        else:
            if tel_lines[fld['index']+4] == '0':
                is_inverse = True
            else:
                is_inverse = False
                
            if is_inverse:
                if tel_lines[fld['index']+31] == '0.000000':
                    if tel_lines[fld['index'] + 43] == '1':
                        field['delivery type'] = 'StepNShoot'
                        field['beam type'] = 'Static'
                    elif tel_lines[fld['index'] + 43] == '2':
                        field['delivery type'] = 'DMLC'
                        field['beam type'] = 'Static'
                    else:
                        print('Delivery type determination error.')
                else:
                    field['delivery type'] = 'VMAT'
                    field['beam type'] = 'Dynamic'
            else:
                if tel_lines[fld['index']+31] == '0.000000':

                    if tel_lines[fld['index'] + 43] == '1':

                        if ( ('mlci'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()) 
                            and (int(tel_lines[fld['index']+98])==0)):
                            field['delivery type'] = 'Static'
                        elif ( ('agility'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()) 
                            and (int(tel_lines[fld['index']+148])==0)):
                            field['delivery type'] = 'Static'
                        else:
                            field['delivery type'] = 'StepNShoot'
                    elif tel_lines[fld['index'] + 43] == '0':
                        field['delivery type'] = 'Static'
                    else:
                        field['delivery type'] = 'Static'
                field['beam type'] = 'Static'

            if is_inverse:
                field['planning type'] = 'inverse'
            else:
                field['planning type'] = 'forward'

        #find field iso
        iso_index = tel_lines[fld['index']:].index('400.000000,0.000000')+fld['index']-1
        monaco_iso = [float(pt)/10 for pt in tel_lines[iso_index].split(',')[:3]]

        field['monaco iso'] = [pt*10 for pt in monaco_iso]

        altered_monaco_iso = [pt*pt_b for (pt, pt_b) in zip(monaco_iso, orientation_modifier)]

        field['isocenter'] = [altered_monaco_iso[0]+dicom_CT_zero[0],
                              -altered_monaco_iso[2]+dicom_CT_zero[1],
                              altered_monaco_iso[1]]
            
        print('  Planning type:', field['planning type'])
        # get control points

        #AGILITY SETUP
        if (is_SETUP and 
            'Agility' in  self.beam_model_dictionary[fld['beam model']]['treatment unit']):
            
            print('  >> Agility setup beam')
            
            ctrl_pts = self.get_agility_setup_ctrlpts(tel_lines, fld['index'])
            
            field['number of control points'] = 1
            field['MUs'] = ctrl_pts[-1]['cumulative MU']
            field['control points'] = ctrl_pts
        
        #MLCi SETUP
        elif (is_SETUP and 
            ('Synergy'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()
              or 
             'mlci'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()) ):
            
            print('  >> MLCi setup beam')   
            
            ctrl_pts = self.get_synergy_setup_ctrlpts(tel_lines, fld['index'])
            
            field['number of control points'] = 1
            field['MUs'] = ctrl_pts[-1]['cumulative MU']
            field['control points'] = ctrl_pts
        
        #AGILITY VMAT
        elif (field['delivery type'] == 'VMAT' and 
            'Agility'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()):
            
            print('  >> Agility VMAT')
            
            num_ctrl_pts = int(tel_lines[fld['index']+148])
            field['number of control points'] = num_ctrl_pts
            
            ctrl_pts = self.get_agility_vmat_ctrlpts(tel_lines, fld['index'],num_ctrl_pts)
            field['MUs'] = ctrl_pts[-1]['cumulative MU']
            field['control points'] = ctrl_pts

            field['couch included'] = self.check_if_couch_included(tel_lines)
         
        #AGILITY STEP AND SHOOT    
        elif (field['delivery type'] == 'StepNShoot' and 
            'Agility'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()):
            
            print('  >> Agility StepNShoot')
            
            num_ctrl_pts = int(tel_lines[fld['index']+148])
            field['number of control points'] = num_ctrl_pts
            
            ctrl_pts = self.get_agility_sns_ctrlpts(tel_lines, fld['index'],num_ctrl_pts)
            field['MUs'] = ctrl_pts[-1]['cumulative MU']
            field['control points'] = ctrl_pts

        #AGILITY STATIC
        elif (field['delivery type'] == 'Static' and 
            'Agility'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()):
            
            print('  >> Agility Static')
            
            field['number of control points'] = 1
            
            try:
                ctrl_pts = self.get_agility_static_ctrlpts(tel_lines, fld['index'])
            except ValueError:
                print('***Setup field identified as static.***')
                ctrl_pts = self.get_agility_setup_ctrlpts(tel_lines, fld['index'])

            field['MUs'] = ctrl_pts[-1]['cumulative MU']
            field['control points'] = ctrl_pts
        
        #SYNERGY STEP AND SHOOT
        elif (field['delivery type'] == 'StepNShoot' and 
            ('Synergy'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()
              or 
             'mlci'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()) ):
            
            print('  >> MLCi StepNShoot')
            
            num_ctrl_pts = int(tel_lines[fld['index']+98])
            field['number of control points'] = num_ctrl_pts
            
            ctrl_pts = self.get_synergy_sns_ctrlpts(tel_lines, fld['index'],num_ctrl_pts)
            field['MUs'] = ctrl_pts[-1]['cumulative MU']
            field['control points'] = ctrl_pts
        
        #SYNERGY STATIC
        elif (field['delivery type'] == 'Static' and 
            ('Synergy'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()
              or 
             'mlci'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()) ):
            
            print('  >> MLCi Static')
            field['number of control points'] = 1
            ctrl_pts = self.get_synergy_static_ctrlpts(tel_lines, fld['index'])
            field['MUs'] = ctrl_pts[-1]['cumulative MU']
            field['control points'] = ctrl_pts
        
        else:
            print('>>> PROBLEM')

        if field['number of MLC leaves'] > len(field['control points'][0]['MLC positions A']):

            print('  >>>> *** ERROR READING FIELD ***')

            if 'set' in field['original field name'].lower():
                print('  >>>> Possilby setup field planned as static field:  attemping to read as set-up field')

                field['delivery type'] = 'Static'
                field['beam type'] = 'Static'
                field['planning type'] = 'Setup'

                if ('Agility' in  self.beam_model_dictionary[fld['beam model']]['treatment unit']):
            
                    print('  >> Agility setup beam')
                    
                    ctrl_pts = self.get_agility_setup_ctrlpts(tel_lines, fld['index'])
                    
                    field['number of control points'] = 1
                    field['MUs'] = ctrl_pts[-1]['cumulative MU']
                    field['control points'] = ctrl_pts

                #MLCi SETUP
                elif ('Synergy'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()
                      or 
                     'mlci'.lower() in  self.beam_model_dictionary[fld['beam model']]['treatment unit'].lower()):
                    
                    print('  >> MLCi setup beam')   
                    
                    ctrl_pts = self.get_synergy_setup_ctrlpts(tel_lines, fld['index'])
                    
                    field['number of control points'] = 1
                    field['MUs'] = ctrl_pts[-1]['cumulative MU']
                    field['control points'] = ctrl_pts
        
        return field, field['isocenter']

    #######################################################

    def check_if_couch_included(self, tel_lines):
        agility_index = tel_lines[::-1].index('Agility')

        if (tel_lines[-agility_index+26]) == '1':
            return True
        elif (tel_lines[-agility_index+26]) == '0':
            return False
        else:
            return None

    # AGILITY SETUP
    def get_agility_setup_ctrlpts(self, tel_lines, field_idx, num_ctrl_pts = 1):
       
        ctrl_pts = []
        
        try:
            idx = tel_lines[field_idx:].index('1,1,1,1,1,1') + field_idx - 16
        except:
            idx = field_idx + 216

        
        if (idx - field_idx) > 215:

            idx = tel_lines[field_idx:].index('0,0,0,0,0,0') + field_idx - 17
            cumulative_MU = 0
        
            for i in range(num_ctrl_pts):
                
                control_point = {}  
                
                control_point['control point index'] = i+1
                control_point['number of MLC leaves'] = 80
                
                all_leaf_points = [float(pt) for pt in ', '.join(tel_lines[idx:idx+16]).split(',')]

                control_point['MLC positions A'] = all_leaf_points[::2]
                control_point['MLC positions B'] = all_leaf_points[1::2]
                
                control_point['gantry angle'] = float(tel_lines[field_idx+20].split(',')[1])
                control_point['gantry direction'] = 'NONE'
                control_point['couch angle'] = -float(tel_lines[field_idx+20].split(',')[0])
                control_point['collimator angle'] = float(tel_lines[field_idx+20].split(',')[2])
                
                coll_positions = [float(num) for num in tel_lines[field_idx+14].split(',')]
                
                control_point['Coll X1'] = (-coll_positions[0]/2 + coll_positions[2])/10
                control_point['Coll X2'] =  (coll_positions[0]/2 + coll_positions[2])/10
                control_point['Coll Y1'] = (-coll_positions[1]/2 + coll_positions[3])/10
                control_point['Coll Y2'] =  (coll_positions[1]/2 + coll_positions[3])/10
                
                control_point['cumulative MU'] = 0.0

                ctrl_pts.append(control_point)
                
                idx += 38

        else:

            cumulative_MU = 0
            
            for i in range(num_ctrl_pts):
                
                control_point = {}  
                
                control_point['control point index'] = i+1
                control_point['number of MLC leaves'] = 80
                
                all_leaf_points = [float(pt) for pt in ', '.join(tel_lines[idx:idx+16]).split(',')]
                
                control_point['MLC positions A'] = all_leaf_points[::2]
                control_point['MLC positions B'] = all_leaf_points[1::2]
                
                control_point['gantry angle'] = float(tel_lines[idx+30].split(',')[1])
                control_point['gantry direction'] = 'NONE'
                control_point['couch angle'] = -float(tel_lines[field_idx+20].split(',')[0])
                        
                control_point['collimator angle'] = float(tel_lines[idx+31])
                
                coll_positions = [float(num) for num in tel_lines[idx+34].split(',')]
                
                control_point['Coll X1'] = (-coll_positions[0]/2 + coll_positions[2])/10
                control_point['Coll X2'] =  (coll_positions[0]/2 + coll_positions[2])/10
                control_point['Coll Y1'] = (-coll_positions[1]/2 + coll_positions[3])/10
                control_point['Coll Y2'] =  (coll_positions[1]/2 + coll_positions[3])/10
                
                cumulative_MU += float(tel_lines[idx+33].split(',')[0])
                
                control_point['cumulative MU'] = cumulative_MU
                
                ctrl_pts.append(control_point)
                
                idx += 38
               
        return ctrl_pts
        
    #----------------------------------------------------------------------

    # SYNERGY SETUP
    def get_synergy_setup_ctrlpts(self, tel_lines, field_idx, num_ctrl_pts = 1):
       
        ctrl_pts = []
        
        idx = field_idx + 102
        cumulative_MU = 0
        
        for i in range(num_ctrl_pts):
            
            control_point = {}  
            
            control_point['control point index'] = i+1
            control_point['number of MLC leaves'] = 40
            
            all_leaf_points = [float(pt) for pt in ', '.join(tel_lines[idx:idx+8]).split(',')]
            
            control_point['MLC positions A'] = all_leaf_points[::2]
            control_point['MLC positions B'] = all_leaf_points[1::2]
            
            control_point['gantry angle'] = float(tel_lines[idx-82].split(',')[1])
            control_point['gantry direction'] = 'NONE'
            control_point['couch angle'] = 0
            control_point['collimator angle'] = 0
            
            coll_positions = [float(num) for num in tel_lines[idx-86].split(',')]
            
            control_point['Coll X1'] = (-coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll X2'] =  (coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll Y1'] = (-coll_positions[1]/2 + coll_positions[3])/10
            control_point['Coll Y2'] =  (coll_positions[1]/2 + coll_positions[3])/10
            
            control_point['cumulative MU'] = 0.0
            
            ctrl_pts.append(control_point)
            
            idx += 38
               
        return ctrl_pts

    #----------------------------------------------------------------------

    # AGILITY VMAT
    def get_agility_vmat_ctrlpts(self, tel_lines, field_idx, num_ctrl_pts):
       
        #num_ctrlt_pts  @ line # (field_idx + 148)
        ctrl_pts = []
        
        idx = field_idx + 152
        cumulative_MU = 0
        
        for i in range(num_ctrl_pts):
            
            control_point = {}  
            
            control_point['control point index'] = i+1
            control_point['number of MLC leaves'] = 80
            
            all_leaf_points = [float(pt) for pt in ', '.join(tel_lines[idx:idx+16]).split(',')]
            
            control_point['MLC positions A'] = all_leaf_points[::2]
            control_point['MLC positions B'] = all_leaf_points[1::2]
            
            control_point['gantry angle'] = float(tel_lines[idx+30].split(',')[1])
            control_point['couch angle'] = -float(tel_lines[field_idx+20].split(',')[0])
                    
            control_point['collimator angle'] = float(tel_lines[idx+31])
            
            coll_positions = [float(num) for num in tel_lines[idx+34].split(',')]
            
            control_point['Coll X1'] = (-coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll X2'] =  (coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll Y1'] = (-coll_positions[1]/2 + coll_positions[3])/10
            control_point['Coll Y2'] =  (coll_positions[1]/2 + coll_positions[3])/10
            
            cumulative_MU += float(tel_lines[idx+33].split(',')[0])
            
            control_point['cumulative MU'] = cumulative_MU
            
            ctrl_pts.append(control_point)
            
            idx += 38
        
        for i in range(num_ctrl_pts-1):
            angle1 = ctrl_pts[i]['gantry angle']
            angle2 = ctrl_pts[i+1]['gantry angle']

            if angle1 == angle2:
                ctrl_pts[i]['gantry direction'] = 'NONE'
            elif angle1 == 180:
                if angle2 < 180:
                    ctrl_pts[i]['gantry direction'] = 'CCW'
                else:
                    ctrl_pts[i]['gantry direction'] = 'CW'
            elif angle2 == 180:
                if angle1 < 180:
                    ctrl_pts[i]['gantry direction'] = 'CW'
                else:
                    ctrl_pts[i]['gantry direction'] = 'CCW'

            else:
                        
                if angle1 < 180:
                    angle1 = angle1 + 360
                if angle2 < 180:
                    angle2 = angle2 + 360
                            
                if angle1 < angle2:
                    ctrl_pts[i]['gantry direction'] = 'CW'
                elif angle1 > angle2:
                    ctrl_pts[i]['gantry direction'] = 'CCW'
                else:
                    ctrl_pts[i]['gantry direction'] = 'NONE'
        
        ctrl_pts[-1]['gantry direction'] = 'NONE'

        return ctrl_pts

    #----------------------------------------------------------------------

    # AGILITY STEP AND SHOOT
    def get_agility_sns_ctrlpts(self, tel_lines, field_idx, num_ctrl_pts):
       
        ctrl_pts = []
        
        idx = field_idx 
        cumulative_MU = 0
        
        for i in range(num_ctrl_pts):

            idx = tel_lines[idx + 32:].index('1,1,1,1,1,1') + idx + 32 - 16
            
            control_point = {}  
            
            control_point['control point index'] = i+1
            control_point['number of MLC leaves'] = 80
            
            all_leaf_points = [float(pt) for pt in ', '.join(tel_lines[idx:idx+16]).split(',')]
            
            control_point['MLC positions A'] = all_leaf_points[::2]
            control_point['MLC positions B'] = all_leaf_points[1::2]
            
            control_point['gantry angle'] = float(tel_lines[idx+30].split(',')[1])
            control_point['couch angle'] = -float(tel_lines[idx+30].split(',')[0])
                    
            control_point['collimator angle'] = float(tel_lines[idx+31])
            
            coll_positions = [float(num) for num in tel_lines[idx+34].split(',')]
            
            control_point['Coll X1'] = (-coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll X2'] =  (coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll Y1'] = (-coll_positions[1]/2 + coll_positions[3])/10
            control_point['Coll Y2'] =  (coll_positions[1]/2 + coll_positions[3])/10
            
            cumulative_MU += float(tel_lines[idx+33].split(',')[0])
            
            control_point['cumulative MU'] = cumulative_MU
            control_point['gantry direction'] = 'NONE'
            
            ctrl_pts.append(control_point)
                
        return ctrl_pts

    #----------------------------------------------------------------------

    # SYNERGY STEP AND SHOOT
    def get_synergy_sns_ctrlpts(self, tel_lines, field_idx, num_ctrl_pts):
       
        #print(num_ctrl_pts)
        search_string = tel_lines[tel_lines[field_idx:].index('0013103b') -45 + field_idx]
        #print(search_string)

        ctrl_pts = []
        
        cumulative_MU = 0
        
        gantry_angle = float(tel_lines[field_idx+20].split(',')[1])
        couch_angle = -float(tel_lines[field_idx+20].split(',')[0])
                    
        collimator_angle = float(tel_lines[field_idx+20].split(',')[2])

        idx = tel_lines[field_idx:].index(search_string) + field_idx - 17

        

        for i in range(num_ctrl_pts):

            control_point = {}  
            
            control_point['control point index'] = i+1
            control_point['number of MLC leaves'] = 40
            
            all_leaf_points = [float(pt) for pt in ', '.join(tel_lines[idx:idx+8]).split(',')]
            
            control_point['MLC positions A'] = all_leaf_points[::2]
            control_point['MLC positions B'] = all_leaf_points[1::2]
            
            control_point['gantry angle'] = gantry_angle
            control_point['couch angle'] = couch_angle
                    
            control_point['collimator angle'] = collimator_angle
            
            coll_positions = [float(num) for num in tel_lines[idx+19].split(',')]
            
            control_point['Coll X1'] = (-coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll X2'] =  (coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll Y1'] = (-coll_positions[1]/2 + coll_positions[3])/10
            control_point['Coll Y2'] =  (coll_positions[1]/2 + coll_positions[3])/10
            
            cumulative_MU += float(tel_lines[idx+18].split(',')[0])
            
            control_point['cumulative MU'] = cumulative_MU
            control_point['gantry direction'] = 'NONE'
            
            ctrl_pts.append(control_point)
            
            idx = tel_lines[idx+18:].index(search_string) + idx + 1
        
        return ctrl_pts

    #----------------------------------------------------------------------

    # AGILITY STATIC
    def get_agility_static_ctrlpts(self, tel_lines, field_idx, num_ctrl_pts = 1):
           
        ctrl_pts = []
        
        idx = tel_lines[field_idx:].index('0013103b') + field_idx - 73
        
        cumulative_MU = 0
        
        for i in range(num_ctrl_pts):
            
            control_point = {}  
            
            control_point['control point index'] = i+1
            control_point['number of MLC leaves'] = 80
            
            all_leaf_points = [float(pt) for pt in ', '.join(tel_lines[idx:idx+16]).split(',')]
            
            control_point['MLC positions A'] = all_leaf_points[::2]
            control_point['MLC positions B'] = all_leaf_points[1::2]
            
            control_point['gantry angle'] = float(tel_lines[field_idx+20].split(',')[1])
            control_point['gantry direction'] = 'NONE'
            control_point['couch angle'] = -float(tel_lines[field_idx+20].split(',')[0])
            control_point['collimator angle'] = float(tel_lines[field_idx+20].split(',')[2])
            
            coll_positions = [float(num) for num in tel_lines[field_idx+14].split(',')]
            
            control_point['Coll X1'] = (-coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll X2'] =  (coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll Y1'] = (-coll_positions[1]/2 + coll_positions[3])/10
            control_point['Coll Y2'] =  (coll_positions[1]/2 + coll_positions[3])/10
            
            
            if len(tel_lines[idx+70].split(',')) > 1:
                cumulative_MU += float(tel_lines[idx+70].split(',')[1])
            else:
                cumulative_MU = 0
            
            control_point['cumulative MU'] = cumulative_MU
            
            ctrl_pts.append(control_point)
            
            idx += 38
        
        return ctrl_pts

    #----------------------------------------------------------------------

   
    # SYNERGY STATIC
    def get_synergy_static_ctrlpts(self, tel_lines, field_idx, num_ctrl_pts = 1):
           
        ctrl_pts = []
        
        idx = tel_lines[field_idx:].index('0,0,0,0,0,0') + field_idx - 9
        
        cumulative_MU = 0
        
        for i in range(num_ctrl_pts):
            
            control_point = {}  
            
            control_point['control point index'] = i+1
            control_point['number of MLC leaves'] = 40
            
            all_leaf_points = [float(pt) for pt in ', '.join(tel_lines[idx:idx+8]).split(',')]
            
            control_point['MLC positions A'] = all_leaf_points[::2]
            control_point['MLC positions B'] = all_leaf_points[1::2]
            
            control_point['gantry angle'] = float(tel_lines[field_idx+20].split(',')[1])
            control_point['gantry direction'] = 'NONE'
            control_point['couch angle'] = -float(tel_lines[field_idx+20].split(',')[0])
            control_point['collimator angle'] = float(tel_lines[field_idx+20].split(',')[2])
            
            coll_positions = [float(num) for num in tel_lines[field_idx+14].split(',')]
            
            control_point['Coll X1'] = (-coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll X2'] =  (coll_positions[0]/2 + coll_positions[2])/10
            control_point['Coll Y1'] = (-coll_positions[1]/2 + coll_positions[3])/10
            control_point['Coll Y2'] =  (coll_positions[1]/2 + coll_positions[3])/10
            
            if int(tel_lines[idx+8]) == 1:
                try:
                    cumulative_MU += float(tel_lines[idx+50].split(',')[1])
                except IndexError:
                    cumulative_MU += float(tel_lines[idx+43].split(',')[1])

            elif int(tel_lines[idx+8]) == 0:

                cumulative_MU += float(tel_lines[idx+43].split(',')[1])

            else:
                print('Uh oh, cumulative MU')

            control_point['cumulative MU'] = cumulative_MU
            
            ctrl_pts.append(control_point)
            
            idx += 38

        return ctrl_pts

    #============================================

    def get_patient_name(self, ID):
        pat_dir = self.patient_folder

        demographics_file = [name for name in os.listdir(pat_dir) if ID in name and 'demographic' in name]

        if len(demographics_file) < 1:
            print('Couldn\'t find patient demographics file')
            return 'Unknown', 'Unknown'

        else:
            dem_file = demographics_file[0]

        dem_lines = [line.rstrip('\n').lstrip(' ').rstrip(' ') 
                         for line in open('\\'.join([pat_dir, dem_file]))]

        if len(dem_lines[2].split('^')) < 1:

            return None, None

        elif len(dem_lines[2].split('^')) == 1:

            last_name = dem_lines[2]

            return last_name, None

        else:

            last_name = dem_lines[2].split('^')[0]
            first_name = dem_lines[2].split('^')[1]

            return last_name, first_name



    def get_plandef_data_from_planfile(self, plan_dir, filenames):
    
        plan_lines = [line.rstrip('\n') for line in open('\\'.join([plan_dir, filenames['plan']]))]
        
        plandef = {}
        plandef['ID'] = plan_lines[4]
        plandef['first name'] = None
        plandef['last name'] = None
        plandef['course number'] = None
        plandef['SOP instance UID'] = None
        plandef['TPCT'] = plan_lines[6]
        
        return plandef

    def get_plandef_data(self, plan_dir, filenames):

        info = mr.plan_info_read(os.path.join(plan_dir, filenames['plan']))

        plandef = {}
        plandef['ID'] = info['patient id']
        plandef['first name'] = None
        plandef['last name'] = None
        plandef['course number'] = None
        plandef['SOP instance UID'] = None
        plandef['TPCT'] = info['study set name']

        return plandef


    def get_calc_parameters_from_hyp_file(self, plan_dir, filenames):

        hypfilename = '\\'.join([plan_dir, filenames['hyp']])
                                 
        hypfile = hyp.read_hyp(hypfilename)

        #determine dose engine

        primary = [beam['primary'] for beam in hypfile['BEAMS'][0]['BEAMDEF']][0]
        secondary = [beam['secondary'] for beam in hypfile['BEAMS'][0]['BEAMDEF']][0]

        calc_params = {}

        calc_params['Grid spacing (cm): '] = '%0.2f' % (float(hypfile['dosegridsize'])/10)

        med_or_water = {'1': 'medium', '2': 'water'}
        calc_params['Dose deposition to: '] = med_or_water[hypfile['dosetomedium']]

        if primary == 'Undefined' and secondary == 'CC_id': #collapsed cone
            calc_params['engine'] = 'Collapsed cone'
        else:
            calc_params['engine'] = 'Monte Carlo'

            calc_params['Fluence smoothing: '] = hypfile['gradeofsmoothing']

            if 'mcvarperplan' in hypfile:
                per_what = 'per *calculation*'
            else:
                per_what = 'per *control point*'

            calc_params['Statistical uncertainty: '] = ''.join([str(float(hypfile['mcvariance'])*100), ' % ', per_what])
        

        return calc_params


    def get_field_names_from_hyp_file(self, plan_dir, filenames):
    
        hypfilename = '\\'.join([plan_dir, filenames['hyp']])
                                 
        hypfile = hyp.read_hyp(hypfilename)
        
        field_names = [beam['description'] for beam in hypfile['BEAMS'][0]['BEAMDEF']]
        print(field_names)
        
        return field_names

    def index_of_field_in_tel(self, tel_lines, field_name, start_at = 0):
    
        try:
            index = tel_lines[start_at:].index(field_name) + start_at
        except:
            print('Couldnt\'t find field name in list.')
            return None
        
        if tel_lines[index+1] not in self.beam_model_dictionary:
            print(tel_lines[index+1], 'is not a recognized beam model. Continuing search')
            
            return self.index_of_field_in_tel(tel_lines, field_name, index+1)
            
        else:
            return index

    def get_CT_info(self, plan_dir, tpct):

        pat_dir = self.patient_folder
        
        TPCTfolders = [f for f in os.listdir(pat_dir) if '~' in f]

        TPCTdir = [name for name in TPCTfolders if name.split('~')[1] == tpct]
        
        if len(TPCTdir) < 1:
            
            print('TPCT directory not found.')
            print(tpct)
            print(plan_dir)
            print(pat_dir)
            return None
        
        if len(TPCTdir) > 1:
            print('Found more than one TPCT directory.')

        TPCTdir = os.path.join(pat_dir, TPCTdir[0])

        ct_info = mr.study_set_info_read(os.path.join(TPCTdir, 'info'))

        CTtoED = ct_info['CT to ED conversion file']
        scan_reference_point = ct_info['scan reference']
        setup_reference_point = ct_info['setup reference']
        print("scan reference", scan_reference_point)
        print("setup reference", setup_reference_point)
        ctslice = int(scan_reference_point[1])

        ct_path = ''
        found = False

        print('CT STUFF:')
        print(ctslice)

        try:
            dcmfiles = [f for f in os.listdir(os.path.join(TPCTdir, 'DCMData')) if '.CT.DCM' in f]
            for f in dcmfiles:
                if len(f.split('.')[1]) > 1:
                    if f.split('.')[1][1] == '5':
                        pt5bug = True
                        break
            else:
                pt5bug = False
        except:
            pt5bug = False
            print('>>>>>> 0.5mm bug check failed.')
            print(TPCTdir)

        i = 0
        print(TPCTdir)
        icount = 0
        while not found and icount <100:
            icount+=1
            try_up_ct_path = os.path.join(TPCTdir, 'DCMData', '%g.CT.DCM' % round(ctslice+i, 1) )

            #print(try_up_ct_path)
            try_down_ct_path = os.path.join(TPCTdir, 'DCMData', '%g.CT.DCM' % round(ctslice-i, 1) )

            print(os.path.split(try_up_ct_path)[1])
            print(os.path.split(try_down_ct_path)[1])
            print('--------------')
            if os.path.isfile(try_up_ct_path):
                ct_path = try_up_ct_path
                found = True
            elif os.path.isfile(try_down_ct_path):
                ct_path = try_down_ct_path
                found = True

            else:
                i += 0.1


        orientation_label = {   'HFS': 'Head first, Supine',
                                'HFP': 'Head first, Prone',
                                'FFS' : 'Feet first, Supine',
                                'FFP' : 'Feet first, Prone'}

        orientation = orientation_label[ct_info['patient orientation']]
        diff_flag = True

        import_orientation = ct_info['import image orientation']

        # this is in mm and Monaco/MOSAIQ reports isocenter in cm so changes.
        xshift = ct_info['image shifts'][0]/10
        yshift = ct_info['image shifts'][1]/10
        dicom_CT_zero = (xshift, yshift, 0.0)

        return (dicom_CT_zero, orientation, ct_path, 
                    scan_reference_point, setup_reference_point, CTtoED, diff_flag, pt5bug, TPCTdir, import_orientation)

    def CT_zero_in_DICOM_coordinates(self, plan_dir, tpct):
        
        pat_dir = self.patient_folder
        
        TPCTfolders = [f for f in os.listdir(pat_dir) if '~' in f]

        TPCTdir = [name for name in TPCTfolders if name.split('~')[1] == tpct]
        
        if len(TPCTdir) < 1:
            
            print('TPCT directory not found.')
            print(tpct)
            print(plan_dir)
            print(pat_dir)
            return None
        
        if len(TPCTdir) > 1:
            print('Found more than one TPCT directory.')
        
        TPCTdir = '\\'.join([pat_dir, TPCTdir[0]])
        
        info_lines = [line.rstrip('\n') for line in open('\\'.join([TPCTdir, 'info']))]

        plan_lines = [line.rstrip('\n') for line in open('\\'.join([plan_dir, 'plan']))]
        
        sup_inf_string = ''
        if plan_lines[9] == '0':
            sup_inf_string = 'Head first'
        elif plan_lines[9] == '1':
            sup_inf_string = 'Feet first'
        else:
            print('HEAD/FEET FIRST ERROR in CT_zero_in_DICOM_coordinates')
        
        if len(info_lines) > 0:
            
            CTtoED = info_lines[info_lines.index(tpct)-2]

            points_index = info_lines.index(pat_dir.split('\\')[-1])+21


            scan_reference_point = [float(pt) for pt in info_lines[points_index].split(',')]

            setup_reference_point = [float(info_lines[points_index-6]), float(info_lines[points_index-5]),
                float(info_lines[points_index-4])]

            try:
                ctslice = int(scan_reference_point[1])

               #print(scan_reference_point[1])
            except IndexError:
                scan_reference_point = [float(pt) for pt in info_lines[-points_index-(6+7)].split(',')]
                setup_reference_point = [float(info_lines[-points_index-(12+7)]), float(info_lines[-points_index-(11+7)]),
                float(info_lines[-points_index-(10+7)])]

                ctslice = int(scan_reference_point[1])
                print('CT slice index error')
                #print(scan_reference_point[1])

            ct_path = ''
            found = False

            print('CT STUFF:')
            print(ctslice)

            try:
                dcmfiles = [f for f in os.listdir(os.path.join(TPCTdir, 'DCMData')) if '.CT.DCM' in f]
                for f in dcmfiles:
                    if len(f.split('.')[1]) > 1:
                        if f.split('.')[1][1] == '5':
                            pt5bug = True
                            break
                else:
                    pt5bug = False
            except:
                pt5bug = False
                print('>>>>>> 0.5mm bug check failed.')
                print(TPCTdir)

            i = 0
            print(TPCTdir)
            icount = 0
            while not found and icount <100:
                icount+=1
                try_up_ct_path = '\\'.join([TPCTdir, 'DCMData', '%g.CT.DCM' % round(ctslice+i, 1) ])

                #print(try_up_ct_path)
                try_down_ct_path = '\\'.join([TPCTdir, 'DCMData', '%g.CT.DCM' % round(ctslice-i, 1) ])

                print(os.path.split(try_up_ct_path)[1])
                print(os.path.split(try_down_ct_path)[1])
                print('--------------')
                if os.path.isfile(try_up_ct_path):
                    ct_path = try_up_ct_path
                    found = True
                elif os.path.isfile(try_down_ct_path):
                    ct_path = try_down_ct_path
                    found = True

                else:
                    i += 0.1

            diff_flag = False
           
            for line in info_lines:

                if line == 'HFS':

                    orientation =  ', '.join([sup_inf_string,'Supine'])
                    shift_index_search = '1,1'

                    if sup_inf_string == 'Feet first':
                        diff_flag = True

                    break
                
                elif line == 'FFS':

                    orientation = ', '.join([sup_inf_string,'Supine'])
                    shift_index_search = '1,1'  # CHANGE this was 1,1

                    if sup_inf_string == 'Head first':
                        diff_flag = True
                        
                    break
                
                elif line == 'HFP':

                    orientation = ', '.join([sup_inf_string,'Prone'])
                    shift_index_search = '1,-1'

                    if sup_inf_string == 'Feet first':
                        diff_flag = True

                    break

                elif line == 'FFP':

                    orientation = ', '.join([sup_inf_string,'Prone'])
                    shift_index_search = '1,-1'

                    if sup_inf_string == 'Head first':
                        diff_flag = True
                        
                    break

            else:
                orientation = 'Wut'
                print('*****FIX orientation search!')

            shift_index = info_lines.index(shift_index_search) + 1
            
            # this is in mm and Monaco/MOSAIQ reports isocenter in cm so changes.
            xshift = float(info_lines[shift_index].split(',')[0])/10 
            yshift = float(info_lines[shift_index].split(',')[1])/10 
            
            dicom_CT_zero = (xshift, yshift, 0.0)
            
            return (dicom_CT_zero, orientation, ct_path, 
                    scan_reference_point, setup_reference_point, CTtoED, diff_flag, pt5bug, TPCTdir)

    def field_def_from_tel(self, tel_lines,field_names):
        field_def = []
        
        order = 1
        
        for name in field_names:

            index = self.index_of_field_in_tel(tel_lines, name)
            beam_model = tel_lines[index+1]
            
            field = {'index': index, 'beam model': beam_model, 'order': order, 'name': name}
            
            field_def.append(field)
            
            order +=1
        
        return field_def