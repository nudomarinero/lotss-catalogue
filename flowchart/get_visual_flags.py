#!/usr/bin/python

'''
get_visual_flags
add flags to catalogue based on visual inspection of subclasses of sources
'''

from lofar_source_sorter import Mask, Masks_disjoint_complete
import numpy as np
from astropy.table import Table, Column, join
import astropy.coordinates as ac
import astropy.units as u
import os

#################################################################################

path = '/local/wwilliams/projects/radio_imaging/lofar_surveys/LoTSS-DR1-July21-2017/'
lofarcat_file_srt = path+'LOFAR_HBA_T1_DR1_catalog_v0.99.srl.gmasked.presort.fits'



lofarcat = Table.read(lofarcat_file_srt)


#################################################################################
# artefacts come from find_artefact_candidates.py

'''
Candidate artefacts selected by Gulay: TBC - what was the exact selection?
'''
artefactlistfile = 'gg_artefact_case1_3-fixed.fits'
visually_confirmed = False

'''
After doing visual inspection of these candidates: provides new catalogues
'''
artefactlistfile = 'gg_artefact_case1_3-fixed-confirmed.fits'
visually_confirmed = True



artefactlist = Table.read(artefactlistfile)

#select only confirmed ones
if visually_confirmed:
    artefactlist = artefactlist[artefactlist['visual_flag']==1]

# for now, no artefacts
artefact = np.zeros(len(lofarcat),dtype=bool)
if 'artefact_flag' not in lofarcat.colnames:
    lofarcat.add_column(Column(artefact,'artefact_flag'))
else:
    #rewrite artefact info
    lofarcat['artefact_flag'] *= False
for n in artefactlist['Source_Name']:
    ni = np.where(lofarcat['Source_Name']==n)[0][0]
    lofarcat['artefact_flag'][ni] = True    

# some more artefacts from lgz and various visual checks (these are stored as a list of names in a simple text file...)
artefactlistfile = '/local/wwilliams/projects/radio_imaging/lofar_surveys/LoTSS-DR1-July21-2017/lgz_v2/artefacts.txt'
with open(artefactlistfile,'r') as f:
    artefacts = [line.strip() for line in f]
for n in artefacts:
    if n in lofarcat['Source_Name']: 
        ni = np.where(lofarcat['Source_Name']==n)[0][0]
        lofarcat['artefact_flag'][ni] = True    
    else:
        print n
    

# some more artefacts from lgz and various visual checks (all the ones with Deleted in the zoom file)
artefactlistfile = '/local/wwilliams/projects/radio_imaging/lofar_surveys/LoTSS-DR1-July21-2017/lgz_v2/zoom_deleted.txt'
with open(artefactlistfile,'r') as f:
    artefacts = [line.strip() for line in f]
for n in artefacts:
    if n in lofarcat['Source_Name']: 
        ni = np.where(lofarcat['Source_Name']==n)[0][0]
        lofarcat['artefact_flag'][ni] = True    
    else:
        print n
    

#################################################################################
# edge flags 
## produced in flowchart/flag_edge_sources.py
edge_flag_file = '/local/wwilliams/projects/radio_imaging/lofar_surveys/LoTSS-DR1-July21-2017/LOFAR_HBA_T1_DR1_catalog_v0.95_masked.srl.edgeflags.fits'

edge_flag_cat = Table.read(edge_flag_file)

# hack to deal with that one duplicate source... causes problems on the join
edge_flag_cat['Source_Name'][(edge_flag_cat['Source_Name']=='ILTJ132633.10+484745.7') ] = ''
if 'edge_flag' in lofarcat.colnames:
    lofarcat.remove_column('edge_flag')
lofarcat.sort('Source_Name')
tt=join(lofarcat, edge_flag_cat, join_type='left')
tt['Edge_flag3'].fill_value = False
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('Edge_flag3','edge_flag')

lofarcat.add_column(tt['edge_flag'])


#################################################################################
# sources with E_RA are all artefacts (visually confirmed as such)

lofarcat['artefact_flag'][lofarcat['E_RA'] == 0] = True  

#################################################################################
# the 1/300k case of a duplicate source - flag the one (higher noise as an artefact here

lofarcat['artefact_flag'][(lofarcat['Source_Name']=='ILTJ132633.10+484745.7') & (lofarcat['Mosaic_ID']=='P38Hetdex07')] = True


#################################################################################
# the following come from outputs of classify.py on various subsamples

#################################################################################
### nhuge_2masx
#1: bright galaxy
#2: complex
#3: no match
#4: artefact

nhuge_2masx_vc_cat_file = 'fullsample/sample_all_src_clean_large_faint_nhuge_2masx-vflag.fits'
nhuge_2masx_vc_cat = Table.read(nhuge_2masx_vc_cat_file)

if 'nhuge_2masx_flag' in lofarcat.colnames:
    lofarcat.remove_column('nhuge_2masx_flag')
lofarcat.sort('Source_Name')
tt=join(lofarcat, nhuge_2masx_vc_cat, join_type='left')
tt['visual_flag'].fill_value = 0
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('visual_flag','nhuge_2masx_flag')


lofarcat.add_column(tt['nhuge_2masx_flag'])

#################################################################################
### clustered
#1: artefact
#2: complex

clustered_vc_cat_file = 'fullsample/sample_all_src_clean_small_nisol_clustered-vflag.fits'
clustered_vc_cat = Table.read(clustered_vc_cat_file)

if 'clustered_flag' in lofarcat.colnames:
    lofarcat.remove_column('clustered_flag')
lofarcat.sort('Source_Name')
tt=join(lofarcat, clustered_vc_cat, join_type='left')
tt['visual_flag'].fill_value = 0
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('visual_flag','clustered_flag')


lofarcat.add_column(tt['clustered_flag'])


#################################################################################
### large faint clustered
#1: artefact
#2: complex

Lclustered_vc_cat_file = 'testsample_large/sample_all_src_clean_large_faint_nhuge_n2masx_nisol_clustered-vflag.fits'
Lclustered_vc_cat = Table.read(Lclustered_vc_cat_file)

if 'Lclustered_flag' in lofarcat.colnames:
    lofarcat.remove_column('Lclustered_flag')
lofarcat.sort('Source_Name')
tt=join(lofarcat, Lclustered_vc_cat, join_type='left')
tt['visual_flag'].fill_value = 0
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('visual_flag','Lclustered_flag')


tt['Lclustered_flag'][tt['Source_Name']=='ILTJ135637.88+473205.2'] = 2

lofarcat.add_column(tt['Lclustered_flag'])


#################################################################################
### huge faint
#1: send to LGZ
#2: bright galaxy match
#3: no prospect of ID
#4: artefact

huge_faint_vc_cat_file = 'fullsample/sample_all_src_clean_large_faint_huge-vflag.fits'
huge_faint_vc_cat = Table.read(huge_faint_vc_cat_file)

if 'huge_faint_flag' in lofarcat.colnames:
    lofarcat.remove_column('huge_faint_flag')
lofarcat.sort('Source_Name')
tt=join(lofarcat, huge_faint_vc_cat, join_type='left')
tt['visual_flag'].fill_value = 0
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('visual_flag','huge_faint_flag')


## fix a few bad ones!!
tt['huge_faint_flag'][tt['Source_Name']=='ILTJ141956.60+533054.4'] = 3
tt['huge_faint_flag'][tt['Source_Name']=='ILTJ123133.59+484958.6'] = 3
tt['huge_faint_flag'][tt['Source_Name']=='ILTJ135431.79+542009.6'] = 1
tt['huge_faint_flag'][tt['Source_Name']=='ILTJ114328.67+524240.1'] = 1
tt['huge_faint_flag'][tt['Source_Name']=='ILTJ130840.28+540437.0'] = 1
tt['huge_faint_flag'][tt['Source_Name']=='ILTJ132513.22+535113.5'] = 1
tt['huge_faint_flag'][tt['Source_Name']=='ILTJ133233.91+541927.4'] = 1
tt['huge_faint_flag'][tt['Source_Name']=='ILTJ132919.17+530505.1'] = 1
tt['huge_faint_flag'][tt['Source_Name']=='ILTJ105949.84+534811.6'] = 1

lofarcat.add_column(tt['huge_faint_flag'])


#################################################################################
### large, not huge faint
#(1) Send to LGZ
#(2) Accept ML match
#(3) No good match
#(4) Too zoomed in
#(5) Artefact

huge_faint_vc_cat_file = 'toclassify_171124//large_faint_toclassify-vflag.fits'
huge_faint_vc_cat = Table.read(huge_faint_vc_cat_file)

if 'nhuge_faint_flag' in lofarcat.colnames:
    lofarcat.remove_column('nhuge_faint_flag')
lofarcat.sort('Source_Name')
tt=join(lofarcat, huge_faint_vc_cat, join_type='left')
tt['visual_flag'].fill_value = 0
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('visual_flag','nhuge_faint_flag')


lofarcat.add_column(tt['nhuge_faint_flag'])



#################################################################################
#sample_small_m_nisol_nlr_nglr_nglargesep_nncomplex_nnnartefact.txt
#1 Complex (lgz)
#2 complex (lgz - should be done already)
#3 No match
#4 artefact
#5 no match, but NN is artefact
#6 other (redo)

m_nisol_sel_cat_file = 'msources_nisol/sample_small_m_nisol_nlr_nglr_nglargesep_nncomplex_nnnartefact-vflag.fits'
m_nisol_sel_cat = Table.read(m_nisol_sel_cat_file)

if 'm_nisol_flag_vc1' in lofarcat.colnames:
    lofarcat.remove_column('m_nisol_flag_vc1')
lofarcat.sort('Source_Name')
tt=join(lofarcat, m_nisol_sel_cat, join_type='left')
tt['visual_flag'].fill_value = 0
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('visual_flag','m_nisol_flag_vc1')


lofarcat.add_column(tt['m_nisol_flag_vc1'])

#################################################################################
#sample_all_src_clean_small_nisol_nclustered_S_nlr_NNnlr_simflux_dist-vflag.fits
#1 isolated, no match
#2 pair / complex (to lgz)
#3 artefact
#4 other (revisit)

double_cat_file = 'doubles/sample_all_src_clean_small_nisol_nclustered_S_nlr_NNnlr_simflux_dist-vflag-1.fits'
double_cat = Table.read(double_cat_file)

if 'double_flag' in lofarcat.colnames:
    lofarcat.remove_column('double_flag')
lofarcat.sort('Source_Name')
tt=join(lofarcat, double_cat, join_type='left')
tt['visual_flag'].fill_value = 0
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('visual_flag','double_flag')


lofarcat.add_column(tt['double_flag'])


double_cat_file = 'doubles/sample_all_src_clean_small_nisol_nclustered_S_nlr_NNnlr_simflux_dist_prob-new-vflag.fits'
double_cat = Table.read(double_cat_file)

if 'double_flag2' in lofarcat.colnames:
    lofarcat.remove_column('double_flag2')
lofarcat.sort('Source_Name')
tt=join(lofarcat, double_cat, join_type='left')
tt['visual_flag'].fill_value = 0
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('visual_flag','double_flag2')


lofarcat.add_column(tt['double_flag2'])


#################################################################################
# from visual inspection of samples of m non-isolated sources (pre-check for lgz)
  #(1) Complex (lgz)
  #(2) complex (lgz - should be done already)
  #(3) No match
  #(4) match
  #(5) deblend
  #(6) artefact
  #(7) no match, but NN is artefact
  #(8) other (redo)
#counts:
#1 358
#3 204
#4 61
#5 18
#6 9

mnisol_cat_file = 'check_msources_lgz/sample_small_m_nisol_vflags-1.fits'

mnisol_cat = Table.read(mnisol_cat_file)

if 'm_nisol_flag_vc2' in lofarcat.colnames:
    lofarcat.remove_column('m_nisol_flag_vc2')
lofarcat.sort('Source_Name')
tt=join(lofarcat, mnisol_cat, join_type='left')
tt['visual_flag'].fill_value = 0
tt = tt.filled()
tt.sort('Source_Name')
tt.rename_column('visual_flag','m_nisol_flag_vc2')


lofarcat.add_column(tt['m_nisol_flag_vc2'])


## write output file

if os.path.exists(lofarcat_file_srt):
    os.remove(lofarcat_file_srt)
lofarcat.write(lofarcat_file_srt)