import os 
from astropy.table import Table, Column, join, vstack, hstack
from astropy.coordinates import SkyCoord
import numpy as np

from catalogue_create.process_lgz import Make_Shape
#from catalogue_create import process_lgz
'''
ID_flag
1 - ML
2 - 2MASX
3 - LGZ
32 - LGZ v2 pending
311 - lgz v1 - normal route
312 - lgz v1 zoom
4 - no id possible
5 - TBC
6 - deblending
61 - deblend directly
62 - deblend workflow
'''



'''
From the LOFAR catalogue:
Source_Name
RA
E_RA
E_RA_tot
DEC
E_DEC
E_DEC_tot
Peak_flux
E_Peak_flux
E_Peak_flux_tot
Total_flux
E_Total_flux
E_Total_flux_tot
Maj
E_Maj
Min
E_Min
PA
E_PA
Isl_rms
S_Code
Mosaic_ID
Isl_id

Append:
ID_flag
ID_wisename
ID_psname
ID_2masxname
ID_ra
ID_dec
ML_LR
LGZ_flags?

'''
def count_flags(cat, flag):
    print '{:s} counts'.format(flag)
    unique, counts = np.unique(cat[flag], return_counts=True)
    for u,c in zip(unique, counts):
        print u,c



def name_from_coords(ra,dec,prefix=''):
    sc = SkyCoord(ra,dec,frame='icrs', unit='deg')
    sc = sc.to_string(style='hmsdms',sep='',precision=2)
    name = prefix+sc.replace(' ','')[:-1]
    return name




if __name__=='__main__':

    ### Required INPUTS
    
    version =  '1.2'
    
    # lofar source catalogue, gaussian catalogue and ML catalogues for each


    path = '/local/wwilliams/projects/radio_imaging/lofar_surveys/LoTSS-DR1-July21-2017/'

    lofargcat_file = path+'LOFAR_HBA_T1_DR1_catalog_v0.99.gaus.fits'
    lofarcat_orig_file = path+'LOFAR_HBA_T1_DR1_catalog_v0.99.srl.gmasked.fits'

    # sorted output from flowchart
    #lofarcat_file_srt = path+'LOFAR_HBA_T1_DR1_catalog_v0.95_masked.srl.fixed.sorted.fits'
    lofarcat_file_srt = path+'LOFAR_HBA_T1_DR1_catalog_v0.99.srl.gmasked.sorted.fits'

    # LGZ output
    lgz_cat_file = os.path.join(path,'lgz_v2/HETDEX-LGZ-cat-v1.1-filtered-zooms.fits') 
    lgz_component_file = os.path.join(path,'lgz_v2/lgz_components.txt')

    comp_out_file = os.path.join(path,'LOFAR_HBA_T1_DR1_merge_ID_v{v:s}.comp.fits'.format(v=version))
    art_out_file = os.path.join(path,'LOFAR_HBA_T1_DR1_merge_ID_v{v:s}.art.fits'.format(v=version))
    merge_out_file = os.path.join(path,'LOFAR_HBA_T1_DR1_merge_ID_v{v:s}.fits'.format(v=version))
    merge_out_full_file = merge_out_file.replace('.fits','.full.fits')
    comp_out_full_file = comp_out_file.replace('.fits','.full.fits')

    lofarcat_sorted = Table.read(lofarcat_file_srt)
    lofarcat_sorted_antd = Table.read(lofarcat_file_srt)
    lgz_components = Table.read(lgz_component_file, format='ascii', names=['lgz_component', 'lgz_src', 'lgz_flag'])
    
    
    #psmlcat = Table.read(psmlcat_file)
    
    #lgz_compcat = Table.read(lgz_compcat_file)
    lgz_cat_full = Table.read(lgz_cat_file)
    
    
    print 'Starting with {:d} sources'.format(len(lofarcat_sorted))

    ### add some needed columns
    
    lofarcat_sorted.add_column(Column(np.zeros(len(lofarcat_sorted),dtype='S60'),'ID_name'))
    #lofarcat_sorted.add_column(Column(['None']*len(lofarcat_sorted),'ID_name'))
    lofarcat_sorted.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted),dtype=float),'ID_ra'))
    lofarcat_sorted.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted),dtype=float),'ID_dec'))
    
    
    ##
    lofarcat_sorted.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted),dtype=float),'ML_LR'))

    #lofarcat_sorted_antd.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted_antd),dtype=float),'Removed'))
    tc  = lofarcat_sorted['Source_Name'].copy()
    tc.name = 'New_Source_Name'
    lofarcat_sorted_antd.add_column(tc)

    ## remove sources associated/flagged by LGZ
    # ideally this would just remove the components in the LGZ comp catalogue  - but using legacy catalogues mean that these don't directly map onto the new sources
    # martin has produced lgz_components.txt to do this.


    lgz_select = np.ones(len(lofarcat_sorted), dtype=bool)
    tlgz_component = Table([Column(lgz_components['lgz_component'], 'Source_Name'), Column(np.ones(len(lgz_components)),'LGZ_remove')])
    lofarcat_sorted.sort('Source_Name')
    tc = join(lofarcat_sorted, tlgz_component, join_type='left')
    tc['LGZ_remove'].fill_value = 0
    tc = tc.filled()
    tc.sort('Source_Name')
    lgz_select = (tc['LGZ_remove']!=1)

    lofarcat_sorted_del = lofarcat_sorted[~lgz_select]
    #sys.exit()

    is_lgz_art = np.zeros(len(lofarcat_sorted), dtype=bool)
    # keep a list of the lgz artefacts
    lgz_art = lgz_cat_full[lgz_cat_full['Art_prob'] >= 0.5]
    for ll in lgz_art:
        if ll['Assoc'] > 1:
            #get the comp naes
            llcomps = lgz_components[lgz_components['lgz_src'] ==  ll['Source_Name']]['lgz_component']
            for llcompi in llcomps:
                is_lgz_art[lofarcat_sorted['Source_Name'] == llcompi] = 1


        else:
            is_lgz_art[lofarcat_sorted['Source_Name'] == ll['Source_Name']] = 1

    # save  ist of the artefacts
    lofarcat_sorted[(lofarcat_sorted['Artefact_flag'] == 1) & (is_lgz_art)].write(art_out_file, overwrite=True)
    #sys.exit()

    print 'Removing {n:d} sources associated in LGZ'.format(n=np.sum(~lgz_select))
    lofarcat_sorted = lofarcat_sorted[lgz_select]
    # we don't know what their new names are
    lofarcat_sorted_antd['New_Source_Name'][~lgz_select] = 'LGZ' # there shouldn't be any of these left afterwards!
    for lgzci in lgz_components:
        lc, ls, lf = lgzci['lgz_component'], lgzci['lgz_src'], lgzci['lgz_flag']
        ind = np.where(lofarcat_sorted_antd['Source_Name'] == lc)[0]
        lofarcat_sorted_antd['New_Source_Name'][ind] = ls
        
        if lf == 1:
            lofarcat_sorted_antd['ID_flag'][ind] = 311
        elif lf == 2:
            lofarcat_sorted_antd['ID_flag'][ind] = 312
            #if lofarcat_sorted_antd['ID_flag'][ind] == 3220:
                #lofarcat_sorted_antd['ID_flag'][ind] = 322  # we now have the zoomed in
            #else:
                #lofarcat_sorted_antd['ID_flag'][ind] = 312

    
    ## remove artefacts
    # all the artefacts identified and visually confirmed in the flowchart process
    print 'Throwing away {n:d} artefacts'.format(n=np.sum(lofarcat_sorted['Artefact_flag'] == 1))
    lofarcat_sorted = lofarcat_sorted[lofarcat_sorted['Artefact_flag'] == 0]
    

    # artefacts have no name in the merged catalogue cos they don't appear there
    # except for ones deemed to be part of another source by the wisdom of LGZ
    # not true anymore - these are now removed from the associations
    lofarcat_sorted_antd['New_Source_Name'][(lofarcat_sorted_antd['Artefact_flag'] != 0) & (lofarcat_sorted_antd['New_Source_Name']==lofarcat_sorted_antd['Source_Name'])] = ''
    
    print 'left with {n:d} sources'.format(n=len(lofarcat_sorted))




    # handle TBC

    # handle 2MASX sources
    ## HUGE 2MASX sources need to be removed, associated and added back
    ## the rest need a flag for 2MASX
    sel2mass = (lofarcat_sorted['ID_flag']==2)
    print 'adding info for {n:d} 2MASX source matches'.format(n=np.sum(sel2mass))
    # add the 2MASXJ
    names = lofarcat_sorted['2MASX_name'][sel2mass]
    names = np.array(['2MASX J'+n for n in names])
    
    
    lofarcat_sorted['ID_name'][sel2mass] = names
    lofarcat_sorted['ID_ra'][sel2mass] = lofarcat_sorted['2MASX_ra'][sel2mass]
    lofarcat_sorted['ID_dec'][sel2mass] = lofarcat_sorted['2MASX_dec'][sel2mass]
    
    #lofarcat_sorted['LGZ_Assoc'][sel2mass] = 1
    #lofarcat_sorted['LGZ_Assoc_Qual'][sel2mass] = 1.
    #lofarcat_sorted['LGZ_ID_Qual'][sel2mass] = 1.
    
    # some sources come from a tag 'match to bright galaxy' - not necesarily 2MASX - look in SDSS for these:
    sel2masssdss = (lofarcat_sorted['ID_flag']==2) & (lofarcat_sorted['ID_name']=='2MASX J')
    #sdss_matches =  (names == '2MASXJ')
    
    #lofarcat_sorted['ID_name'][sel2mass ] = names
    #lofarcat_sorted[sel2mass ][sdss_matches]
    
    print 'resorting to an SDSS match for {n:d} sources'.format(n=np.sum(sel2masssdss))
    
    #### TBD ####
    import astropy.units as u
    from astroquery.sdss import SDSS
    snames = np.zeros(np.sum(sel2masssdss),dtype='S60')
    sdss_ra = np.zeros(np.sum(sel2masssdss))
    sdss_dec = np.zeros(np.sum(sel2masssdss))
    for ti,t in enumerate(lofarcat_sorted[sel2masssdss ]):
        ra,dec = t['RA'],t['DEC']
        #print ra,dec
        c = SkyCoord(ra,dec, frame='icrs', unit='deg')
        
        try:
            st = SDSS.query_region(c,radius=0.5*t['Maj']*u.arcsec, photoobj_fields=['ra','dec','objID','petroR50_r','petroMag_r'])
            st = st[(st['petroMag_r'] <20.) & (st['petroMag_r'] > 0 )] 
            #print st['petroMag_r'].max()
            c2 = SkyCoord(st['ra'],st['dec'], frame='icrs', unit='deg')
            sep = c.separation(c2)
            a = sep.argmin()
            #print st
            #print st[a]
            sdss_ra[ti] = st['ra'][a]
            sdss_dec[ti] = st['dec'][a]
            snames[ti] = name_from_coords(sdss_ra[ti],sdss_dec[ti],prefix='SDSS J')
        except:
            print 'error - sdss', ra,dec
            import pdb ; pdb.set_trace()
            
        
    
    #c = SkyCoord(lofarcat_sorted['RA'][sel2mass ][sdss_matches], lofarcat_sorted['DEC'][sel2mass ][sdss_matches], frame='icrs', unit='deg')
    #sdss_tab = SDSS.query_crossid(c,radius=20*u.arcsec)
    
    lofarcat_sorted['ID_name'][sel2masssdss] = snames
    lofarcat_sorted['ID_ra'][sel2masssdss] = sdss_ra
    lofarcat_sorted['ID_dec'][sel2masssdss] = sdss_dec
    
    lofarcat_sorted.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted),dtype=float),'LGZ_Size'))
    lofarcat_sorted.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted),dtype=float),'LGZ_Width'))
    lofarcat_sorted.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted),dtype=float),'LGZ_PA'))
    lofarcat_sorted.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted),dtype=float),'LGZ_Assoc'))
    
    
    lofarcat_sorted.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted),dtype=float),'LGZ_Assoc_Qual'))
    lofarcat_sorted.add_column(Column(np.nan*np.zeros(len(lofarcat_sorted),dtype=float),'LGZ_ID_Qual'))

    print 'going to merge'
    
    ok_matches =  (names != '2MASXJ')
    
    unames, ucounts = np.unique(lofarcat_sorted['ID_name'][sel2mass ][ok_matches], return_counts=True)
    remove_2mass_mult = np.zeros(len(lofarcat_sorted),dtype=bool)
    lofarcat_add_2mass_mult = lofarcat_sorted[1:1]
    nmerge = np.sum(ucounts>1)
    nn = 0

    nok = 0
    nok1 = 0
    nnok = 0

    # we need to consider the 2MASX sources that were in the first LGZ selections (to be consistent with what came later we take the 2MASX merge and 'throw away' the lgz assoc as if they had never been in lgz) warning - this can be complicated if something is associated in lgz but not to the 2masx source... does this happen?
    # these are all the lgz sources that are mixed up with the 2msss sources - they should be removed from the lgz source list when these are added in later...
    # make sure all the components in the components cat point to the 2mass source
    remove_2mass_lgz_srcs = []

    for n in unames: #[ucounts>1]:
        if 'SDSS' in n: continue
        mergeok = True

        #ii = np.where(lofarcat_sorted['ID_name'] == n)[0]
        
        i = np.where(lofarcat_sorted['2MASX_name'] == n.replace('2MASX J',''))[0]
        #lofarcat_sorted_del

        i2 = np.where(lofarcat_sorted_del['2MASX_name'] == n.replace('2MASX J',''))[0]
        #print len(ii), len(i)
        if len(i2) > 0:
            #print '\n##',n
            #print len(i), len(i2)
            #print 'not removed (will be combined) - '
            #print lofarcat_sorted['Source_Name','ID_flag'][i]
            #print 'removed (in lgz) - '
            #print lofarcat_sorted_del['Source_Name','ID_flag'][i2]
            nnok += 1
            lofarcat_sorted[i].write('check_large_opt/'+n.replace(' ','_')+'.fits',overwrite=True)

            lgz_srcs = []
            lgz_src_comps = []
            missing_comp = []
            for ii in i2:
                lgz_srci = lgz_components['lgz_src'][lgz_components['lgz_component'] == lofarcat_sorted_del['Source_Name'][ii]][0]
                all_lgz_comp = lgz_components['lgz_component'][lgz_components['lgz_src'] == lgz_srci]

                #print '-',lofarcat_sorted_del['Source_Name'][ii], 'is in lgz src', lgz_srci, 'which has',len(all_lgz_comp),'components'
                ## make sure all the components of this to be removed source are part of the 2MASX source... otherwise ????
                remove_2mass_lgz_srcs.append(lgz_srci)
                if lgz_srci not in lgz_srcs:
                    lgz_srcs.append(lgz_srci)
            for lgz_src in lgz_srcs:
                #print 'checking', lgz_src
                lgz_src_comp = lgz_components['lgz_component'][lgz_components['lgz_src'] == lgz_src]
                for lgz_src_compi in lgz_src_comp:
                    if lgz_src_compi not in lgz_src_comps:
                        lgz_src_comps.append(lgz_src_compi)

                    #if (lgz_src_compi not in lofarcat_sorted['Source_Name'][i])
                    if (lgz_src_compi not in lofarcat_sorted_del['Source_Name'][i2]):
                        if lgz_src_compi not in missing_comp:
                            missing_comp.append(lgz_src_compi)
                            print 'adding lgz component to 2MASX assoc', lgz_src_compi
                            i2 = np.hstack((i2, np.where(lofarcat_sorted_del['Source_Name'] == lgz_src_compi)[0] ))
                            mergeok = False

            lofarcat_sorted_del[i2].write('check_large_opt/'+n.replace(' ','_')+'-lgz.fits',overwrite=True)
            #print n, missing_comp
            #print lgz_srcs
            #print lgz_src_comps
            #print lofarcat_sorted_del['Source_Name'][i2]
        # else i2 = 0 - i.e. no part is in lgz
        else:
            if len(i) == 1:
                #print n, 'ok1'
                nok1 += 1
            else:
                #print n, 'ok'
                nok += 1

        nn += len(i)
        #print n, i
        remove_2mass_mult[i] = True
        
        complist = vstack(( lofarcat_sorted[i].copy() , lofarcat_sorted_del[i2].copy() ))
        assoc_2mass = lofarcat_sorted[i].copy()[0]
        
        
        # merging multiple S/M will be M, unless merging 1 S source
        if len(complist) > 0:
            
            assoc_2mass['RA']=np.average(complist['RA'], weights=complist['Total_flux'])
            assoc_2mass['DEC']=np.average(complist['DEC'], weights=complist['Total_flux'])
            
            assoc_2mass['ID_flag'] = 2 # ensure the ID_flag is 2 (if the first of the other components was not 2)
            
            assoc_2mass['Source_Name'] = name_from_coords(assoc_2mass['RA'],assoc_2mass['DEC'],prefix='ILTJ')
            
            assoc_2mass['E_RA']=np.sqrt(np.sum(complist['E_RA']**2.0))/len(complist)
            assoc_2mass['E_DEC']=np.sqrt(np.sum(complist['E_DEC']**2.0))/len(complist)
            assoc_2mass['Isl_rms']=np.mean(complist['Isl_rms'])
            assoc_2mass['Total_flux']=np.sum(complist['Total_flux'])
            # total flux error is error on the sum
            assoc_2mass['E_Total_flux']=np.sqrt(np.sum(complist['E_Total_flux']**2.0))
            # peak flux and error from brightest component
            maxpk=np.argmax(complist['Peak_flux'])
            assoc_2mass['Peak_flux']=complist[maxpk]['Peak_flux']
            assoc_2mass['E_Peak_flux']=complist[maxpk]['E_Peak_flux']
            
            assoc_2mass['Isl_id'] = -99
            if len(complist) > 1:
                assoc_2mass['S_Code'] = 'M'
            #else:
                #assoc_2mass['S_Code'] = 'S'
            
        for t in ['Maj', 'Min', 'PA']:
            assoc_2mass[t] = np.nan
            assoc_2mass['E_'+t] = np.nan
            assoc_2mass['DC_'+t] = np.nan
            assoc_2mass['E_DC_'+t] = np.nan
                        
        
        #c =SkyCoord(complist['RA'], complist['DEC'], unit='deg')
        # TBD 'Mosiac_ID'
        
        # size is taken from convex hull of components - as in LGZ process
        if len(complist) > 0:
            cshape = Make_Shape(complist)
            assoc_2mass['LGZ_Size'] = cshape.length()
            assoc_2mass['LGZ_Width'] = cshape.width()
            assoc_2mass['LGZ_PA'] = cshape.pa()
            
            #if cshape.length() < 1:
                #print complist
            #print np.array(complist['Source_Name']), np.array(complist['Maj']), cshape.length()
        else:
            assoc_2mass['LGZ_Size'] = complist['DC_Maj'][0]
            assoc_2mass['LGZ_Width'] = complist['DC_Min'][0]
            assoc_2mass['LGZ_PA'] = complist['DC_PA'][0]
        
        
        assoc_2mass['LGZ_Assoc'] = len(complist)
        
        # give them quality flags like LGZ
        assoc_2mass['LGZ_Assoc_Qual'] = 1.
        assoc_2mass['LGZ_ID_Qual'] = 1.
                
        # to save the new names
        for c in complist:
            ni = np.where(lofarcat_sorted_antd['Source_Name'] == c['Source_Name'])[0]
            lofarcat_sorted_antd['New_Source_Name'][ni] = assoc_2mass['Source_Name']
            lofarcat_sorted_antd['ID_flag'][ni] = 2
        
        
        lofarcat_add_2mass_mult = vstack([lofarcat_add_2mass_mult, assoc_2mass]) 
        
    print nok, 'are ok'
    print nok1, 'are ok (single)'
    print nnok, 'are partly in an lgz source'
    #sys.exit()
    lofarcat_sorted = lofarcat_sorted[~remove_2mass_mult]
    lofarcat_sorted = vstack([lofarcat_sorted,lofarcat_add_2mass_mult])
        
    print 'merging components of {n:d} 2MASX sources'.format(n=nmerge)
    print 'removing merged components {n:d} from catalogue'.format(n=np.sum(remove_2mass_mult))
    print 'adding back {n:d} merged sources'.format(n=len(lofarcat_add_2mass_mult))
    
    
    
    # handle ML sources
    lLR_thresh = 0.639
    selml = ((lofarcat_sorted['ID_flag']==1) |(lofarcat_sorted['ID_flag']==61) | (lofarcat_sorted['ID_flag']==62)) & (np.log10(1+lofarcat_sorted['LR']) > lLR_thresh)
    print 'adding info for {n:d} ML source matches'.format(n=np.sum(selml))
    

    # take the PS name over the WISE name
    # why is PS name just some number ?? - pepe?
    namesP = lofarcat_sorted['LR_name_ps'][selml]
    namesP = [ 'PS '+str(nP) if nP != 999999 else '' for nP in namesP ]
    #namesP = [name_from_coords(ra,dec, prefix='PSO J') for ra,dec,n in zip(lofarcat_sorted['LR_ra'][selml],lofarcat_sorted['LR_dec'][selml],lofarcat_sorted['LR_name_ps'][selml])  ]
    namesW = lofarcat_sorted['LR_name_wise'][selml]
    namesW = [ 'AllWISE'+nW  if nW != 'N/A' else '' for nW in namesW]
    names = [nP if nP != '' else nW  for nP,nW in zip(namesP,namesW)]
    
    
    lofarcat_sorted['ID_name'][selml] = names
    lofarcat_sorted['ID_ra'][selml] = lofarcat_sorted['LR_ra'][selml]
    lofarcat_sorted['ID_dec'][selml] = lofarcat_sorted['LR_dec'][selml]
    lofarcat_sorted['ML_LR'][selml] = lofarcat_sorted['LR'][selml]
    
    # use gaus info where it is needed:
    # for the blends where there is no source match
    selmlg_blend = ((lofarcat_sorted['ID_flag']==61) | (lofarcat_sorted['ID_flag']==62)) & (np.log10(1+lofarcat_sorted['LR']) <= lLR_thresh)
    # and for the msources that are selected to have best G match
    selmlg_auto = (lofarcat_sorted['ID_flag']==1) & ( ((lofarcat_sorted['msource1_flag']==2) | (lofarcat_sorted['msource2_flag']==2)))
    selmlg = selmlg_blend | selmlg_auto
    print 'adding info for {n:d} ML gaus source matches'.format(n=np.sum(selmlg))
    

    # take the PS name over the WISE name
    # why is PS name just some number ?? - pepe?
    namesP = lofarcat_sorted['gLR_name_ps'][selmlg]
    namesP = [ 'PS '+str(nP) if nP != 999999 else '' for nP in namesP ]
    #namesP = [name_from_coords(ra,dec, prefix='PSO J') for ra,dec,n in zip(lofarcat_sorted['LR_ra'][selmlg],lofarcat_sorted['LR_dec'][selmlg],lofarcat_sorted['LR_name_ps'][selmlg])  ]
    namesW = lofarcat_sorted['gLR_name_wise'][selmlg]
    namesW = [ 'AllWISE'+nW  if nW != 'N/A' else '' for nW in namesW]
    names = [nP if nP != '' else nW  for nP,nW in zip(namesP,namesW)]
    
    
    lofarcat_sorted['ID_name'][selmlg] = names
    lofarcat_sorted['ID_ra'][selmlg] = lofarcat_sorted['gLR_ra'][selmlg]
    lofarcat_sorted['ID_dec'][selmlg] = lofarcat_sorted['gLR_dec'][selmlg]
    lofarcat_sorted['ML_LR'][selmlg] = lofarcat_sorted['gLR'][selmlg]
    
    
    
    selml = (lofarcat_sorted['ID_flag']==1) & (np.log10(1+lofarcat_sorted['LR']) <= lLR_thresh)
    print 'adding info for {n:d} ML source non-matches'.format(n=np.sum(selml))
    
    lofarcat_sorted['ID_name'][selml] = ''

    lgz_cat_full.add_column(Column(np.zeros(len(lgz_cat_full), dtype=bool),'2MASSoverlap'))
    for s in remove_2mass_lgz_srcs:
        lgz_cat_full['2MASSoverlap'][lgz_cat_full['Source_Name'] == s] = True
    print np.sum(lgz_cat_full['2MASSoverlap']), ' removed because they are in a 2MASS assoc'

    # get a list of the lgz artefacts...
    lgz_art['Assoc'] > 1

    ## add LGz v1 associated sources
    # 
    lgz_select = (lgz_cat_full['Compoverlap']==0)&(lgz_cat_full['Art_prob']<0.5)&(lgz_cat_full['Zoom_prob']<0.5)&(lgz_cat_full['2MASSoverlap']==0)
    print 'Selecting {n2:d} of {n1:d} sources in the LGZ catalogue to add'.format(n1=len(lgz_cat_full),n2=np.sum(lgz_select))
    lgz_cat = lgz_cat_full[lgz_select]
    lgz_cat.rename_column('optRA','ID_ra')
    lgz_cat.rename_column('optDec','ID_dec')
    lgz_cat.rename_column('OptID_Name','ID_name')
    #lgz_cat.rename_column('Size','LGZ_Size')
    lgz_cat.rename_column('Assoc','LGZ_Assoc')
    lgz_cat.rename_column('Assoc_Qual','LGZ_Assoc_Qual')
    lgz_cat.rename_column('ID_Qual','LGZ_ID_Qual')
    
    lgz_cat.rename_column('New_size','LGZ_Size')
    lgz_cat.rename_column('New_width','LGZ_Width')
    lgz_cat.rename_column('New_PA','LGZ_PA')
    
    lgz_cat.add_column(Column(3*np.ones(len(lgz_cat),dtype=int),'ID_flag'))
    for lgzci in lgz_components:
        ls, lf  =  lgzci['lgz_src'], lgzci['lgz_flag']
        ind = np.where(lgz_cat['Source_Name'] == ls)[0]
        if lf == 1:
            lgz_cat['ID_flag'][ind] = 311
        elif lf == 2:
            lgz_cat['ID_flag'][ind] = 312
            ## check if it comes from v2
            
            #inds = np.where(ls == lofarcat_sorted_antd['New_Source_Name'])[0]
            #if np.any(lofarcat_sorted_antd['ID_flag'][inds] == 322):
                #lgz_cat['ID_flag'][ind] = 322
            #else:
                #lgz_cat['ID_flag'][ind] = 312
        else:
            print 'error'
            
        

    ## change None to ''
    lgz_cat['ID_name'][lgz_cat['ID_name']=='None'] = ''

    lgz_cat.meta = lofarcat_sorted.meta
    mergecat = vstack([lofarcat_sorted, lgz_cat])
    print 'now we have {n:d} sources'.format(n=len(mergecat))


    # remove the artefact components from the component file
    lgz_select_art = (lgz_cat_full['Art_prob']>=0.5)
    print 'Selecting {n2:d} of {n1:d} artefact sources in the LGZ catalogue to remove their componnents'.format(n1=len(lgz_cat_full),n2=np.sum(lgz_select_art))
    lgz_cat_art = lgz_cat_full[lgz_select_art]
    for s in lgz_cat_art['Source_Name']:
        # look up component names
        si = (lgz_components['lgz_src'] == s)
        lgz_c = lgz_components['lgz_component'][si]
        for c in lgz_c:
            ci = lofarcat_sorted_antd['Source_Name'] == c
            lofarcat_sorted_antd['New_Source_Name'][ci] = ''
            
    comp_arts = (lofarcat_sorted_antd['New_Source_Name'] == '')
    print 'removing {0:d} components that are artefacts'.format(np.sum(comp_arts))
    lofarcat_sorted_antd = lofarcat_sorted_antd[~comp_arts]
    
    
    
    
    ### this is blend and should be dealt with later:
    # but update the ID_flag before we discard the Blend_prob column
    mergecat['ID_flag'][mergecat['Blend_prob'] > 0.5] = 63
    
    # remove the artefact components from the component file
    lgz_select_blend = (lgz_cat_full['Blend_prob']>=0.5)
    print 'Selecting {n2:d} of {n1:d} artefact sources in the LGZ catalogue to update ID_flag'.format(n1=len(lgz_cat_full),n2=np.sum(lgz_select_blend))
    lgz_cat_blend = lgz_cat_full[lgz_select_blend]
    for s in lgz_cat_blend['Source_Name']:
        # look up component names
        si = (lgz_components['lgz_src'] == s)
        lgz_c = lgz_components['lgz_component'][si]
        for c in lgz_c:
            ci = lofarcat_sorted_antd['Source_Name'] == c
            lofarcat_sorted_antd['ID_flag'][ci] = 63
    
    
    
    # write some flag counts for both catalogues    
    count_flags(mergecat, 'ID_flag')
    count_flags(lofarcat_sorted_antd, 'ID_flag')
    
    print 'dropping ID_flag 3 sources'
    #lofarcat_sorted_antd = lofarcat_sorted_antd[lofarcat_sorted_antd['ID_flag']!=3]
    #mergecat = mergecat[mergecat['ID_flag']!=3]
        
    lofarcat_sorted_antd.rename_column('Source_Name', 'Component_Name')
    lofarcat_sorted_antd.rename_column('New_Source_Name', 'Source_Name')
    
    lofarcat_sorted_antd.write(comp_out_full_file, overwrite=True)
    
    lofarcat_sorted_antd.keep_columns(['Component_Name', 'Source_Name', 'RA', 'E_RA', 'DEC', 'E_DEC', 'Peak_flux', 'E_Peak_flux', 'Total_flux', 'E_Total_flux', 'Maj', 'E_Maj', 'Min', 'E_Min', 'PA', 'E_PA', 'DC_Maj', 'E_DC_Maj', 'DC_Min', 'E_DC_Min', 'DC_PA', 'E_DC_PA', 'Isl_rms', 'S_Code', 'Ng', 'Mosaic_ID', 'Number_Masked', 'Number_Pointings', 'Masked_Fraction', 'ID_flag'])
    
    lofarcat_sorted_antd.write(comp_out_file, overwrite=True)

    mergecat.write(merge_out_full_file, overwrite=True)


    ## throw away extra columns
    mergecat.keep_columns(['Source_Name', 'RA', 'E_RA', 'DEC', 'E_DEC', 'Peak_flux', 'E_Peak_flux', 'Total_flux', 'E_Total_flux', 'Maj', 'E_Maj', 'Min', 'E_Min', 'PA', 'E_PA', 'DC_Maj', 'E_DC_Maj', 'DC_Min', 'E_DC_Min', 'DC_PA', 'E_DC_PA', 'Isl_rms', 'S_Code', 'Mosaic_ID', 'Number_Masked', 'Number_Pointings', 'Masked_Fraction', 'ID_flag', 'ID_name', 'ID_ra', 'ID_dec', 'ML_LR', 'LGZ_Size', 'LGZ_Width', 'LGZ_PA', 'LGZ_Assoc', 'LGZ_Assoc_Qual', 'LGZ_ID_Qual'])

    mergecat.write(merge_out_file, overwrite=True)
    '''
    
    sys.exit()
    tt = mergecat['ID_name']
    tt = tt[tt!='']
    tt = tt[tt!='2MASXJ']
    tt = tt[tt!='Mult']
    n,u=np.unique(tt,return_counts=True)

    tout = mergecat[1:1]
    for nn,uu in zip(n,u):
        if uu > 1: 
            #print nn,uu
            tt=mergecat[mergecat['ID_name']==nn]
            if tt['ID_flag'][0] == 1:
                xx  = Table([tt['Source_Name'], tt['ID_flag'], tt['ID_name'], tt['FC_flag'], tt['Art_prob'],tt['Blend_prob'],tt['Zoom_prob'],tt['Hostbroken_prob'],tt['Total_flux']])
                print xx
                tout = vstack([tout,tt])
    '''
