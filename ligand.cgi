#!/usr/bin/python3
import cgi
import cgitb; cgitb.enable()  # for troubleshooting
import os
import gzip

rootdir=os.path.dirname(os.path.abspath(__file__))

html_header=""
html_footer=""
if os.path.isfile(rootdir+"/index.html"):
    fp=open(rootdir+"/index.html")
    txt=fp.read()
    fp.close()
    html_header=txt.split('<!-- CONTENT START -->')[0]
    html_footer=txt.split('<!-- CONTENT END -->')[-1]

form    = cgi.FieldStorage()
page    =form.getfirst("page",'')
if not page or page=='0':
    page='1'
lig3    = form.getfirst("code",'')
if not lig3:
    lig3= form.getfirst("lig3",'')
if not lig3 in ["metal","regular"]:
    lig3=lig3.upper()
formula = form.getfirst("formula",'').upper()
inchi   = form.getfirst("inchi",'').upper().replace('"','').replace(' ','').rstrip(';')
if inchi and not inchi.startswith("INCHI="):
    inchi="INCHI="+inchi
inchikey= form.getfirst("inchikey",'').upper().replace(' ','')
smiles  = form.getfirst("smiles",'').upper().replace(' ','').rstrip(';')
ligname = form.getfirst("ligname",'').upper().replace('"','').replace("'",'')
img     = form.getfirst("img",'').replace('"','').replace("'",'')
if not img in ['0','1']:
    img = '0'

para_list=[]
if lig3:
    para_list.append("lig3=%s"%lig3)
if formula:
    para_list.append("formula=%s"%formula)
if inchi:
    para_list.append('inchi="%s"'%inchi)
if inchikey:
    para_list.append('inchikey=%s'%inchikey)
if smiles:
    para_list.append("smiles=%s"%smiles)
if ligname:
    para_list.append('ligname="%s"'%ligname)
para='&'.join(para_list)



print("Content-type: text/html\n")
if len(html_header):
    print(html_header)
else:
    print('''<html>
<head>
<link rel="stylesheet" type="text/css" href="page.css" />
<title>BioLiP</title>
</head>
<body bgcolor="#F0FFF0">
<img src=images/BioLiP1.png ></br>
<p><a href=.>[Back to Home]</a></p>
''')
freq_dict=dict()
fp=open(rootdir+"/download/lig_frequency.txt")
for line in fp.read().splitlines()[4:]:
    items=line.split('\t')
    ccd=items[1]
    freq=items[2]
    freq_dict[ccd]=freq
fp.close()

print('''
<h4>Search Ligand</h4>
<FORM id="form1" name="form1" METHOD="POST" ENCTYPE="MULTIPART/FORM-DATA" ACTION="ligand.cgi">
    <span title="Search ligand by PDB CCD ID, ChEMBL ID, DrugBank ID, or ZINC ID. Example:
    ATP
    CHEMBL14249
    DB00171
    ZINC000004261765">
    Ligand ID
    <input type="text" name="code" value="" placeholder="%s" size=10>
    </span>
    &nbsp;&nbsp;
    
    <span title="Example: C10 H14 N5 O8 P">
    Formula
    <input type="text" name="formula" value="" placeholder="%s" size=10>
    </span>
    &nbsp;&nbsp;
    
    <span title="Example: InChI=1S/C10H14N5O8P/c11-10-13-7-4(8(18)14-10)12-2-15(7)9-6(17)5(16)3(23-9)1-22-24(19,20)21/h2-3,5-6,9,16-17H,1H2,(H2,19,20,21)(H3,11,13,14,18)/t3-,5-,6-,9-/m1/s1">
    InChI
    <input type="text" name="inchi" value="" placeholder="%s" size=10>
    </span>
    &nbsp;&nbsp;
    
    <span title="Example: RQFCJASXJCIDSX-UUOKFMHZSA-N">
    InChIKey
    <input type="text" name="inchikey" value="" placeholder="%s" size=10>
    </span>
    &nbsp;&nbsp;
    
    <span title="Example: c1nc2c(n1[C@H]3[C@@H]([C@@H]([C@H](O3)COP(=O)(O)O)O)O)N=C(NC2=O)N">
    SMILES
    <input type="text" name="smiles" value="" placeholder="%s" size=10>
    </span>
    &nbsp;&nbsp;
    
    <span title="Example: GUANOSINE-5'-MONOPHOSPHATE">
    Ligand name
    <input type="text" name="ligname" value="" placeholder="%s" size=20>
    </span>
    &nbsp;&nbsp;
    
    <INPUT TYPE="submit" VALUE="Submit">
    &nbsp;
    <INPUT TYPE="reset" VALUE="Clear">
</FORM>
<p></p>
'''%(lig3,formula,inchi,inchikey,smiles,ligname))

print('''
<h4>Browse Ligand</h4>
<li>Click <strong>#</strong> to view 2D diagram of the ligand.</li>
<li>The 3-letter <strong>Ligand ID</strong> follows the <a href="https://www.wwpdb.org/data/ccd" target=_blank>Chemical Component Dictionary (CCD)</a> used by the PDB database.
    When availble, the <strong>Ligand ID</strong> from <a href=https://www.ebi.ac.uk/chembl>ChEMBL</a>, <a href=https://go.drugbank.com>DrugBank</a>, and <a href=https://zinc.docking.org>ZINC</a> databases are also listed in the form of CHEMBL*, DB*, and ZINC*, respectively. Click on the <strong>Ligand ID</strong> to view the ligand at RCSB PDB, ChEMBL, DrugBank or ZINC.</li>
<li><strong>Count</strong> is the number of BioLiP entries with the ligand. The full statistics is available at <a href=download/lig_frequency.txt>lig_frequency.txt</a>. Click <strong>Count</strong> to search the ligand through BioLiP.</li>
<li>If multiple SMILES strings exists for the same ligand, different SMILES are separated by semicolon ";".</li>
<p></p>
''')

fp=gzip.open(rootdir+"/data/metal.tsv.gz",'rt')
metal_list=[]
for line in fp.read().splitlines():
    metal_list.append(line.split('\t')[0])
fp.close()
metal_set=set(metal_list)

fp=gzip.open(rootdir+"/data/ligand.tsv.gz",'rt')
formula_query_set=set(formula.split())
lines=[]
pageLimit=200
for line in fp.read().splitlines()[1:]:
    items=line.split('\t')
    if lig3:
        if lig3=="metal" and not items[0] in metal_set:
            continue
        elif lig3=="regular" and items[0] in metal_set:
            continue
        elif not lig3 in ["metal","regular"] and not lig3 in items[:1]+items[6:]:
            continue
    if formula:
        formula_template_set=set(items[1].split())
        if len(formula_query_set)!=len(formula_template_set):
            continue
        if len(formula_query_set.intersection(formula_template_set)
            )!=len(formula_template_set):
            continue
    if inchi and items[2].upper()!=inchi:
        continue
    if inchikey and items[3]!=inchikey:
        continue
    if smiles:
        smiles_list=items[4].split(';')
        if sum([s.strip().upper()==smiles for s in smiles_list])==0:
            continue
    if ligname and not ligname in items[5].replace("'",'').upper():
        continue
    
    inchi_list=[]
    for i in range(0,len(items[2]),25):
        start=i
        end  =i+25
        inchi_list.append(items[2][start:end])
    items[2]='<br>'.join(inchi_list)
    
    smiles_list=[]
    for i in range(0,len(items[4]),40):
        start=i
        end  =i+40
        smiles_list.append(items[4][start:end])
    items[4]='<br>'.join(smiles_list)
    items[4].replace('; ',';<br>')
    lines.append(items)
    if page!="last" and len(lines)>pageLimit*int(page):
        continue

totalNum=len(lines)
totalPage=1+int(totalNum/pageLimit)
if page=="last":
    page=totalPage
else:
    page=int(page)
if page<1:
    page=1
elif page>totalPage:
    page=totalPage


if not inchi and not inchikey: # inchi only has unique hit
    print('''<p></p>
<center> 
<a class='hover' href='?&page=1&%s'>&lt&lt</a>
<a class='hover' href='?&page=%d&%s'>&lt</a>
'''%(para+"&img="+img,page-1,para+"&img="+img))
    for p in range(page-10,page+11):
        if p<1 or p>totalPage:
            continue
        elif p==page:
            print(' %d '%(p))
        else:
            print('''<a class='hover' href='?&page=%d&%s'>%d</a>'''%(p,para+"&img="+img,p))
    print('''
<a class='hover' href='?&page=%d&%s'>&gt</a>
<a class='hover' href='?&page=last&%s'>&gt&gt</a>
<form name="pform" action="ligand.cgi">Go to page <select name="page" onchange="this.form.submit()">
'''%(page+1,para+"&img="+img,para+"&img="+img))
    for p in range(1,totalPage+1):
        if p==page:
            print('<option value="%d" selected="selected">%d</option>'%(p,p))
        else:
            print('<option value="%d">%d</option>'%(p,p))
    print('''</select>
<input type=hidden name=lig3     value='%s'>
<input type=hidden name=formula  value='%s'>
<input type=hidden name=inchi    value='%s'>
<input type=hidden name=inchikey value='%s'>
<input type=hidden name=smiles   value='%s'>
<input type=hidden name=ligname  value='%s'>
<input type=hidden name=img      value='%s'>
</form></center>'''%(lig3,formula,inchi,inchikey,smiles,ligname,img))
if img=='0':
    print("<a href='?&page=%d&%s&img=1'>[Click to show 2D diagrams for ligand structures]</a>"%(page,para))
else:
    print("<a href='?&page=%d&%s&img=0'>[Click to hide 2D diagrams for ligand structures]</a>"%(page,para))


print('''<table border="0" align=center width=100%>    
<tr BGCOLOR="#FF9900">
    <th width=5%  ALIGN=center><strong> # </strong></th>
    <th width=10% ALIGN=center><strong> ID </strong></th>
    <th width=5%  ALIGN=center><strong> Count </strong></th>
    <th width=5%  ALIGN=center><strong> Chemical<br>formula </strong></th>
    <th width=12% ALIGN=center><strong> InChI;<br>InChIKey </strong></th>
    <th width=13% ALIGN=center><strong> SMILES </strong></th>
    <th width=50% ALIGN=left>  <strong> Ligand<br>Name </strong> </th>           
</tr><tr ALIGN=center>
''')

for l,items in enumerate(lines):
    if l<pageLimit*(int(page)-1) or l>=pageLimit*int(page):
        continue
    bgcolor=''
    if l%2==0:
        bgcolor='BGCOLOR="#DEDEDE"'
    freq='0'
    ccd=items[0]
    if ccd in freq_dict:
        freq='<a href="qsearch.cgi?lig3=%s" target=_blank>%s</a>'%(
            ccd,freq_dict[ccd])
    ligandID='<span title="View at RCSB PDB"><a href=http://rcsb.org/ligand/%s target=_blank>%s</a></span>'%(ccd,ccd)
    if items[6]:
        ligandID+='<br><span title="View at ChEMBL"><a href=http://ebi.ac.uk/chembl/compound_report_card/%s target=_blank>%s</a>'%(items[6],items[6])
    if items[7]:
        ligandID+='<br><span title="View at DrugBank"><a href=http://go.drugbank.com/drugs/%s target=_blank>%s</a>'%(items[7],items[7])
    if items[8]:
        ligandID+='<br><span title="View at ZINC"><a href=http://zinc.docking.org/substances/%s target=_blank>%s</a>'%(items[8],items[8])
    link_text=str(l+1)
    if img=='1':
        ligandID='<span title="View 2D diagram for %s"><a href="sym.cgi?code=%s" target=_blank><img src=https://cdn.rcsb.org/images/ccd/labeled/%s/%s.svg></a></span><br>'%(
            ccd,ccd,ccd[0],ccd)+ligandID
        
    print('''
<tr %s ALIGN=center>
    <td><span title="View 2D diagram for %s"><a href="sym.cgi?code=%s" target=_blank>%d</a></span></td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s;<br>%s</td>
    <td>%s</td>
    <td ALIGN=left><span title="%s">%s</a></span></td>
</tr>
'''%(bgcolor,
    ccd,ccd,l+1,
    ligandID,
    freq,
    items[1],
    items[2], items[3],
    items[4],
    items[5].replace(';',';\n'),items[5].replace(';',';<br>')
    ))
fp.close()


print("</table>")
if len(html_footer):
    print(html_footer)
else:
    print("</body> </html>")
