import os
import shutil
import sys
from configparser import ConfigParser
from pathlib import Path
from argparse import ArgumentParser
import tkinter as tk
from tkinter import filedialog

sys.path.append('NeoGF-gcmtool')
from gcmtool import Gcm
from gcmtool import rebuild_fst
from gcmtool import pack
from dolreader.dol import DolFile


HoLROMPath = ''
regionCode = ''
config = ConfigParser()
config.optionxform = str


def patchHoLROM(HoLRom): # Patch the HoL ROM to be compatiable with the emulator
    with open (HoLRom, mode='r+b') as file:
        data = bytearray(file.read())
    
        if data[0x0:0x4] != b'\x80\x37\x12\x40': # Check for a valid N64 ROM
            print ("Not a valid N64 ROM!")
            exit()
        
        if data[0x3B:0x3F] != b'CZLE': # Check for a valid Hero of Law ROM
            print ("Not a valid Hero of Law ROM!")
            exit()
    
        data[0x3B:0x3F] = b'NZSE'
    
    with open(HoLRom + '_new', 'wb') as output:
        output.write(data)
        output.truncate(33554432) # Pads the ROM's filesize to 32MiB to be compatiable with the emulator

def patchSaveName(): # Patches the emulator's DOL file with custom save file metadata for HoL
    regionCode = getRegionCode()
    with open("tmp/sys/boot.dol", "rb") as file:
        dol = DolFile(file)
    if regionCode in ('0', '1'): # NTSC-J and NTSC-U share the same DOL file, so apply the same patch for said regions
        dol.write_string(0x800f3b80, 'Hero of Law                ') # I know the blank space should be null characters instead but this works fine still
        dol.write_string(0x800f2ba8, 'Save Data    ')
            
    elif regionCode == '2': # PAL
        dol.write_string(0x800e2b00, 'Hero of Law                ')
        dol.write_string(0x800e1ae0, 'Save Data    ')
        
    with open ("tmp/sys/boot.dol", "wb") as file:
        dol.save(file)
            
def getRegionCode():
    return (config['bi2.bin']['CountryCode'])

def patchGCM(gcm_path, HoLROM, outputGCM):
    out_path = Path('tmp')
    gcm_path = Path(gcm_path)
    gcm = Gcm()
    
    if os.path.isdir(out_path):
        shutil.rmtree(out_path)
        
    gcm.unpack(gcm_path, out_path)

    # Set the game title and ID to custom ones using gcmtool's system.conf system
    config.read('tmp/sys/system.conf')
    
    gameTitle = (config['boot.bin']['GameName'])
    gameID = (config['boot.bin']['GameCode'])
    # But first, we need to make sure the user has the correct GCM file
    if "Majora's Mask" not in gameTitle and (gameID != 'RELS' or 'PLZE'):
        shutil.rmtree(out_path) # clean out the tmp path of the extracted game
        raise Exception("\n\nERROR: This isn't a Zelda Collector's Edition Majora's Mask image file!")
        
    config.set('boot.bin', 'GameName', 'Hero of Law')
    config.set('boot.bin', 'GameCode', 'HOLS')
    config.set('Default', 'boot.bin_section', 'enabled')
    regionCode = getRegionCode()
    
    # The filenames differ depending on the GCM's region
    if regionCode == '2': # PAL
        shutil.copy(HoLROM + '_new', "tmp/root/zelda2p.n64") 
        shutil.copy('assets/zelda2e.tpl', "tmp/root/zelda2e.tpl")
    elif regionCode == '1': # NTSC-U
        shutil.copy(HoLROM + '_new', "tmp/root/zelda2e.n64") 
        shutil.copy('assets/zelda2e.tpl', "tmp/root/zelda2e.tpl")
    elif regionCode == '0': # NTSC-J
        shutil.copy(HoLROM + '_new', "tmp/root/zelda2j.n64") 
        shutil.copy('assets/zelda2e.tpl', "tmp/root/zelda2j.tpl")
   
    shutil.copy('assets/opening.bnr', "tmp/root/opening.bnr") # Game banner
    shutil.copy('assets/z_bnr.tpl', "tmp/root/TPL/z_bnr.tpl") # Save banner
    shutil.copy('assets/z_icon.tpl', "tmp/root/TPL/z_icon.tpl") # Save icon
    patchSaveName()
    
    with open ('tmp/sys/system.conf', 'w') as configfile:
        config.write(configfile)
    
    # Now we can rebuild the GCM
    injectedGCMPath = Path(outputGCM)
    gcm.rebuild_fst(out_path, 4, 0)
    
    gcm.pack(out_path, injectedGCMPath)
    os.remove('tmp')
    os.remove(HoLROM + '_new')

def main():
    print('This is main')
    HoLROMPath = filedialog.askopenfilename(filetypes=[('Hero of Law ROM', '*.z64')], 
    title='Select a Hero of Law ROM file')
    majoraGCMPath = filedialog.askopenfilename(filetypes=[("Zelda CE Majora's Mask image", "*.gcm *.iso")],
    title="Select a Zelda: Collector's Edition (Majora's Mask) gcm/iso file")
    finalGCMFileTypes = [('GameCube Disc Image', '*.gcm'), ('GameCube Disc Image', '*.iso')]
    finalGCMFile = filedialog.asksaveasfilename(filetypes = finalGCMFileTypes, defaultextension = finalGCMFileTypes)
    
    if os.path.isfile(finalGCMFile): # Done to satsify gcmtool as it doesn't like already existing files
        os.remove(finalGCMFile)
        
    print(finalGCMFile)
    patchHoLROM(HoLROMPath)
    print('HoL ROM patched!')
    patchGCM(majoraGCMPath, HoLROMPath, finalGCMFile)
    print('Injected HoL into gcm/iso!')
        
        
if __name__ == "__main__":
    main()






