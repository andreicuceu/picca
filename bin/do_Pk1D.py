#!/usr/bin/env python


import fitsio
import argparse
import glob
import sys

from picca import constants
from picca.Pk1D import Pk1D, compute_Pk_raw, compute_Pk_noise, compute_cor_reso
from picca.data import delta

from array import array

def make_tree(tree,nb_bin_max):

    zqso = array( 'f', [ 0. ] )
    mean_z = array( 'f', [ 0. ] )
    mean_reso = array( 'f', [ 0. ] )
    mean_SNR = array( 'f', [ 0. ] )

    nb_r = array( 'i', [ 0 ] )
    k_r = array( 'f', nb_bin_max*[ 0. ] )
    Pk_r = array( 'f', nb_bin_max*[ 0. ] )
    Pk_noise_r = array( 'f', nb_bin_max*[ 0. ] )

    tree.Branch("zqso",zqso,"zqso/F")
    tree.Branch("mean_z",mean_z,"mean_z/F")
    tree.Branch("mean_reso",mean_reso,"mean_reso/F")
    tree.Branch("mean_SNR",mean_SNR,"mean_SNR/F")

    tree.Branch( 'NbBin', nb_r, 'NbBin/I' )
    tree.Branch( 'k', k_r, 'k[NbBin]/F' )
    tree.Branch( 'Pk_noise', Pk_noise_r, 'Pk_noise[NbBin]/F' )
    tree.Branch( 'Pk', Pk_r, 'Pk[NbBin]/F' )
    
    return zqso,mean_z,mean_reso,mean_SNR,nb_r,k_r,Pk_r,Pk_noise_r


if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--out-dir', type = str, default = None, required=True,
                        help = 'output file name')

    parser.add_argument('--in-dir', type = str, default = None, required=True,
                        help = 'data directory')

    parser.add_argument('--mode', type = str, default = None, required=False,
                        help = ' if root call PyRoot')



    args = parser.parse_args()

#   Debug with root
    if (args.mode=='root') :
        from ROOT import TCanvas, TH1F, TFile, TTree
        storeFile = TFile("Testpicca.root","RECREATE","PK 1D studies studies");
        nb_bin_max = 700
        tree = TTree("Pk1D","SDSS 1D Power spectrum Ly-a");
        zqso,mean_z,mean_reso,mean_SNR,nb_r,k_r,Pk_r,Pk_noise_r = make_tree(tree,nb_bin_max)
    

# Read Deltas
    fi = glob.glob(args.in_dir+"/*.fits.gz")
    print fi
    data = {}
    ndata = 0

    for i,f in enumerate(fi):
        if i%1==0:
            sys.stderr.write("\rread {} of {} {}".format(i,len(fi),ndata))
        hdus = fitsio.FITS(f)
        dels = [delta.from_fitsio(h,Pk1D_type=True) for h in hdus[1:]]
        ndata+=len(dels)
        print ' ndata = ',ndata
        for d in dels:

# Compute Pk_raw
            k,Pk_raw = compute_Pk_raw(d.de,d.ll)

# Compute Pk_noise
            Pk_noise = compute_Pk_noise(d.iv,d.diff)               

# Compute resolution correction
            cor_reso = compute_cor_reso(k)

# Compute 1D Pk
            Pk = (Pk_raw - Pk_noise)/cor_reso

# Build   Pk1D
            Pk1D_final = Pk1D(d.ra,d.dec,d.zqso,d.mean_z,d.plate,d.mjd,d.fid,k,Pk_raw,Pk_noise,cor_reso,Pk)

# save with root format
            if (args.mode=='root'):
                zqso[0] = d.zqso
                mean_z[0] = d.mean_z
                mean_reso[0] = d.mean_reso
                mean_SNR[0] = d.mean_SNR

                nb_r[0] = min(len(k),nb_bin_max)
                for i in range(nb_r[0]) :
                    k_r[i] = k[i]
                    Pk_noise_r[i] = Pk_noise[i]
                    Pk_r[i] = Pk[i]
                               
                tree.Fill()

                
# Store results           
    if (args.mode=='root'):
         storeFile.Write()

   
    print "all done"


