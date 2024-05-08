import shutil
from rdkit import Chem

# this is to modify the intermediate tinker key files generated by poltype

def modkey2(poltype):
  rdkitmol = Chem.MolFromMolFile(poltype.molstructfname,removeHs=False)
  scaleDipoleAtoms = []
  fixDipoleAtoms = []
  # acid or ester
  smt1 = "[C](=O)[O][#6,#1]" 
  # acetate anion 
  smt2 = "[C](=O)[O-]" 
  smts = [smt1, smt2]
  for smt in smts:
    pattern = Chem.MolFromSmarts(smt)
    match = rdkitmol.GetSubstructMatches(pattern)
    if match:
      for i in range(len(match)):	
        scaleDipoleAtoms += match[i][1:3]
        fixDipoleAtoms += match[i][0:3]
  
  # scale dipole of the atoms
  scaleDipoleRatio = 0.3
  atom2type = {}
  lines = open(poltype.xyzoutfile).readlines()
  for line in lines[1:]:
    ss = line.split()
    atom2type[int(ss[0])] = ss[5]

  scaleDipoleTypes = [atom2type[int(i)+1] for i in scaleDipoleAtoms]
  
  tmpkeyfile = poltype.key2fnamefromavg + '_tmp'
  lines = open(poltype.key2fnamefromavg).readlines()
  lines_append = []
  for atm in fixDipoleAtoms:
    lines_append.append(f"FIX-ATOM-DIPOLE {int(atm)+1} X\n")
    lines_append.append(f"FIX-ATOM-DIPOLE {int(atm)+1} Y\n")
    lines_append.append(f"FIX-ATOM-DIPOLE {int(atm)+1} Z\n")
  
  for i in range(len(lines)):
    line = lines[i]
    if ('multipole ' in line) and (line.split()[1] in scaleDipoleTypes):
      [dx, dy, dz] = lines[i+1].split()
      lines[i+1] = ' '*37 + f"{float(dx)*scaleDipoleRatio:10.5f}{float(dy)*scaleDipoleRatio:10.5f}{float(dz)*scaleDipoleRatio:10.5f}\n"
      
  with open(tmpkeyfile, 'w') as f:
    for line in lines:
      if "RESP-WEIGHT " in line:
        f.write(line)
        for apline in lines_append:
          f.write(apline)
          f.write(apline)
          f.write(apline)
      else:
        f.write(line)

  # rename key2 to key2b
  shutil.move(poltype.key2fnamefromavg, poltype.key2fnamefromavg+'b')
  # rename key2_tmp to key2
  shutil.move(poltype.key2fnamefromavg + '_tmp', poltype.key2fnamefromavg)

def modkey2_mpole(poltype):
  key2 = poltype.key2fnamefromavg
  type2element = {}
  lines = open(key2).readlines()
  for line in lines:
    if 'atom ' in line:
      s = line.split()
      type2element[s[1]] = s[3].upper()
  
  # detect the big dipole and quadrupole and rewrite a keyfile
  blank = 34*' '
  mpole_lines = []
  with open('tmp_key_2', 'w') as f:
    for i in range(len(lines)):
      line = lines[i]
      if ("multipole " in line) and (line.split()[1] in type2element.keys()):
        current_type = line.split()[1]
        mpole_lines += [i, i+1, i+2, i+3, i+4]
        dx = float(lines[i+1].split()[-3])
        dy = float(lines[i+1].split()[-2])
        dz = float(lines[i+1].split()[-1])
        
        # modify dipole on-the-fly
        if (abs(dx) > 1.0 or abs(dy) > 1.0 or abs(dz) > 1.0) and (type2element[current_type] == 'C'):
          biggest = max([abs(dx), abs(dy), abs(dz)])
          ratio = biggest/0.5

          dx /= ratio
          dy /= ratio
          dz /= ratio

        qxx = float(lines[i+2].split()[-1])
        qyy = float(lines[i+3].split()[-1])
        qzz = float(lines[i+4].split()[-1])
        
        qxz = float(lines[i+4].split()[-3])
        qyz = float(lines[i+4].split()[-2])
        qxy = float(lines[i+3].split()[-2])
        
        # modify quadrupole on-the-fly
        if (abs(qxx) > 2.0 or abs(qyy) > 2.0 or abs(qzz) > 2.0) and (type2element[current_type] == 'C'):
          biggest = max([abs(qxx), abs(qyy), abs(qzz)])
          ratio = biggest/1.95

          qxx /= ratio
          qxy /= ratio
          qyy /= ratio
          qxz /= ratio
          qyz /= ratio
          qzz /= ratio
          poltype.WriteToLog(f"Scaling Down Big Quadrupoles for Atom Type {current_type}")
        
        # write multipole
        # charge
        f.write(line) 
        # dipole
        f.write(f"{blank}{dx:11.5f}{dy:11.5f}{dz:11.5f}\n")
        # quadrupole
        f.write(f"{blank}{qxx:11.5f}\n")
        f.write(f"{blank}{qxy:11.5f}{qyy:11.5f}\n")
        f.write(f"{blank}{qxz:11.5f}{qyz:11.5f}{qzz:11.5f}\n")
      else:
        if i not in mpole_lines:
          f.write(line)
  # rename key2 to key2b
  shutil.move(poltype.key2fnamefromavg, poltype.key2fnamefromavg+'b')
  # rename key2_tmp to key2
  shutil.move('tmp_key_2', poltype.key2fnamefromavg)
