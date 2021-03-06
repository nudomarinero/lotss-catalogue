# Run all tests

# Call with the names of source and component tables

import sys
from astropy.table import Table
import sys
from utils import banner,test_duplicate
import astropy.table

def test_duplicate_id(t):
    banner('Testing for duplicate optical IDs')
    count=test_duplicate(t,'ID_name','optical ID name',exclude=['Mult'])
    print 'Found',count,'cases of duplication'
    return count==0

def test_duplicate_sourcename(t):
    banner('Testing for optical cat sourcenames')
    count=test_duplicate(t,'Source_Name','source name')
    print 'Found',count,'cases of duplication'
    return count==0

def test_duplicate_compname(t):
    banner('Testing for duplicate component cat component names')
    count=test_duplicate(t,'Component_Name','component name')
    print 'Found',count,'cases of duplication'
    return count==0

def test_catalogue_mismatch(t,tc):
    banner('Testing for source name mismatches')
    count=0
    print 'Making lists...'
    tn=list(set(t['Source_Name']))
    tcn=list(set(tc['Source_Name']))
    print 'Sorting...'
    tn.sort()
    tcn.sort()
    print 'Checking...'
    i=0
    j=0
    while i<len(tn) and j<len(tcn):
        if tn[i]==tcn[j]:
            i+=1
            j+=1
        elif tn[i]<tcn[j]:
            print tn[i],'is in source catalogue but not component catalogue',i,j
            count+=1
            i+=1
        elif tcn[j]<tn[i]:
            print tcn[j],'is in source catalogue but not component catalogue',i,j
            j+=1
            count+=1
        else:
            raise RuntimeError('Cannot happen')
    print 'Found',count,'mismatches'
    return count==0
    

t=Table.read(sys.argv[1])
tc=Table.read(sys.argv[2])

test_duplicate_id(t)
test_duplicate_sourcename(t)
test_duplicate_compname(tc)
test_catalogue_mismatch(t,tc)
