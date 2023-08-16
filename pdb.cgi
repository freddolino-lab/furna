#!/usr/bin/python3
import cgi
import cgitb; cgitb.enable()  # for troubleshooting
import os
import gzip
import subprocess
import textwrap
import tarfile
import gzip
import re

rootdir=os.path.dirname(os.path.abspath(__file__))

# location of the graphviz 'dot' program
dot="dot"
if os.path.isfile("graphviz/bin/dot"):
    dot="graphviz/bin/dot"

def read_taxon():
    taxid2name=dict()
    fp=gzip.open(rootdir+"/data/taxid2name.tsv.gz",'rt')
    for line in fp.read().splitlines():
        species,name=line.split('\t')
        taxid2name[species]=name
    fp.close()
    taxon_dict=dict()
    fp=gzip.open(rootdir+"/data/chain2taxonomy.tsv.gz",'rt')
    for line in fp.read().splitlines():
        p,c,species=line.split('\t')
        if species in taxid2name:
            species='<a href="https://ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id='+species+'" target=_blank>'+species+'</a> ('+taxid2name[species]+')'
        else:
            species='<a href="https://ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id='+species+'" target=_blank>'+species+'</a>'
        taxon_dict[p+':'+c]=species
    fp.close()
    return taxon_dict

def display_ligand(pdbid,asym_id,lig3,ligIdx,title):
    reso  =''
    pubmed=''
    cmd="zcat %s/data/pdb_all.tsv.gz |cut -f1,3,9|uniq|grep -P '^%s\\t'"%(
        rootdir,pdbid)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    items=stdout.decode().split('\t')
    if len(items)>=3:
        reso,pubmed=items[1:3]
        if reso=="-1.00":
            reso="N/A"
        else:
            reso=reso+" &#8491;"
    
    prefix='_'.join((pdbid,lig3,asym_id,ligIdx))
    filename="%s/output/%s.pdb.gz"%(rootdir,prefix)
    resSeq_txt=""
    if not os.path.isfile(filename):
        divided=pdbid[-3:-1]
        if os.path.isfile("%s/weekly/ligand_%s.tar.bz2"%(rootdir,divided)):
            tar = tarfile.open("%s/weekly/ligand_%s.tar.bz2"%(rootdir,divided))
            fin=tar.extractfile("ligand/%s.pdb"%prefix)
            lines=fin.read().decode().splitlines()
            txt=''
            for line in lines:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    txt+=line[:20]+" L"+line[22:]+'\n'
                    if not resSeq_txt:
                        resSeq_txt=line[22:27]
                else:
                    txt+=line+'\n'
        fout=gzip.open(filename,'wt')
        fout.write(txt)
        fout.close()
        fin.close()
        tar.close()
    else:
        fp=gzip.open(filename,'rt')
        for line in fp.read().splitlines():
            if line.startswith("ATOM") or line.startswith("HETATM"):
                resSeq_txt=line[22:27]
                break
        fp.close()
    script=''
    if lig3 in ["peptide"]:
        script="cartoons; color group;"
    elif lig3 in ["rna","dna"]:
        script="cartoons; color group; spacefill off; wireframe off;"

    print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">3D structure</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr><td align=center width=10%><strong>PDB</strong></td><td><a href=qsearch.cgi?pdbid=$pdbid target=_blank>$pdbid</a> $title</td></tr>
    <tr BGCOLOR="#DEDEDE"><td align=center><strong>Chain</strong></td><td><a href=qsearch.cgi?pdbid=$pdbid&chain=$asym_id target=_blank>$asym_id</a></td></tr>
    <tr><td align=center><strong>Resolution</strong></td><td>$reso</a></td></tr>
    <tr BGCOLOR="#DEDEDE"><td align=center><strong>Residue<br>sequence<br>number</strong></td><td>$resSeq</a></td></tr>
    <tr align=center><td align=center><strong>3D<br>structure</strong></td><td>
    <table><tr><td>

<script type="text/javascript"> 
$(document).ready(function()
{
    Info = {
        width: 400,
        height: 400,
        j2sPath: "jsmol/j2s",
        script: "load output/$prefix.pdb.gz; color background black; $script"
    }
    $("#mydiv").html(Jmol.getAppletHtml("jmolApplet0",Info))
});
</script>
<span id=mydiv></span>
    </td><td align=left>
[<a href="javascript:Jmol.script(jmolApplet0, 'spin on')">Spin on</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'spin off')">Spin off</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'Reset')">Reset orientation</a>]<p></p>
[<a href="javascript:Jmol.script(jmolApplet0, 'set antialiasDisplay true')">High quality</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'set antialiasDisplay false')">Low quality</a>]<p></p>
[<a href="javascript:Jmol.script(jmolApplet0, 'color background white')">White background</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'color background black')">Black background</a>]<p></p>
[<a href=output/$prefix.pdb.gz>Download</a>]<br>
[<a href=?pdbid=$pdbid&chain=$asym_id&lig3=$lig3&ligIdx=$ligIdx&outfmt=1 download=$prefix.pdb>Download structure with residue number starting from 1</a>]
    </td></tr></table>


    </td></tr>
    </table>
</div>
</td></tr>
'''.replace("$pdbid",pdbid
  ).replace("$title",title
  ).replace("$asym_id",asym_id
  ).replace("$lig3",lig3
  ).replace("$ligIdx",ligIdx
  ).replace("$reso",reso
  ).replace("$resSeq",resSeq_txt
  ).replace("$prefix",prefix
  ).replace("$script",script
  ))


    cmd="zcat %s/data/lig_all.tsv.gz|grep -P '^%s\\t\w+\\tBS\d+\\t%s\\t%s\\t%s\\t'"%(
        rootdir,pdbid,lig3,asym_id,ligIdx)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    lines=stdout.decode().splitlines()
    if len(lines):
        print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">Interaction with protein receptor</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr BGCOLOR="#DEDEDE" align=center>
        <th width=10%><strong>Receptor chain</strong></th>
        <th width=30%><strong>Binding residues on receptor<br>(original residue number in PDB)</strong></th>
        <th width=30%><strong>Binding residues on receptor<br>(residue number reindexed from 1)</strong></th>
        <th width=30%><strong>Binding affinity</strong></th>
    </tr>
''')
        for l,line in enumerate(lines):
            items    =line.split('\t')
            recCha   =items[1]
            bs       =items[2]
            resOrig  =items[6]
            resRenu  =items[7]
            manual   =items[8]
            moad     =items[9]
            pdbbind  =items[10]
            bindingdb=items[11]

            baff_list=[]
            if manual:
                baff_list.append("Manual survey: "+manual)
            if moad:
                baff_list.append("<a href=http://bindingmoad.org/pdbrecords/index/%s target=_blank>MOAD</a>: %s"%(pdbid,moad))
            if pdbbind:
                baff_list.append("<a href=http://pdbbind.org.cn/quickpdb.php?quickpdb=%s target=_blank>PDBbind-CN</a>: %s"%(pdbid,pdbbind))
            if bindingdb:
                baff_list.append("BindingDB: "+bindingdb)

            bgcolor=''
            if l%2==1:
                bgcolor=' BGCOLOR="#DEDEDE" '
            print('''
    <tr $bgcolor align=center>
        <td><span title="Click to view binding site"><a href="pdb.cgi?pdb=$pdbid&chain=$recCha&bs=$bs" target=_blank>$pdbid:$recCha</a></span></td>
        <td><span title="Click to view binding site"><a href="pdb.cgi?pdb=$pdbid&chain=$recCha&bs=$bs" target=_blank>$resOrig</a></span></td>
        <td><span title="Click to view binding site"><a href="pdb.cgi?pdb=$pdbid&chain=$recCha&bs=$bs" target=_blank>$resRenu</a></span></td>
        <td>$baff</td>
    </tr>
            '''.replace("$bgcolor",bgcolor
              ).replace("$pdbid",pdbid
              ).replace("$recCha",recCha
              ).replace("$bs",bs
              ).replace("$resOrig",resOrig
              ).replace("$resRenu",resRenu
              ).replace("$baff",'<br>'.join(baff_list)))

        print('''   </table>
</div>
</td></tr>
''')

    return pubmed

    

def display_polymer_ligand(pdbid,asym_id,lig3,title):
    taxon_dict=read_taxon()
    code=lig3.upper()
    if lig3=="peptide":
        code="peptide"
    prefix="%s_%s_%s"%(pdbid,lig3,asym_id)
    cmd="zcat %s/data/%s.fasta.gz|grep -PA1 '^>%s\\t'|tail -1"%(
        rootdir,lig3,prefix)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    sequence=stdout.decode().strip()
    seq_txt='<br>'.join(textwrap.wrap(sequence,50))
    if lig3=="rna":
        cmd="zcat %s/data/rna_ss.txt.gz|grep -P '^%s\\t'|cut -f2"%(
            rootdir,prefix)
        p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        stdout,stderr=p.communicate()
        seq_txt+='''</span></td></tr>
    <tr BGCOLOR="#DEDEDE"><td><span title="CSSR secondary structure assignment">%s'''%(
        '<br>'.join(textwrap.wrap(stdout.decode(),50)))
    species=''
    if pdbid+':'+asym_id in taxon_dict:
        species="Species: "+taxon_dict[pdbid+':'+asym_id]

    cmd="zcat %s/data/%s_nr.fasta.clust.gz|sed 's/\\t/,/g'|grep -P '\\b%s\\b'"%(
        rootdir,lig3,prefix)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    homolog_link=''
    for homolog in stdout.decode().strip().split(','):
        if homolog==prefix or not homolog.strip():
            continue
        homo_pdbid,homo_asym_id=homolog.split('_'+lig3+'_')
        homolog_link+=", <a href=pdb.cgi?pdb=%s&chain=%s&lig3=%s&idx=0 target=_blank>%s:%s</a>"%(
            homo_pdbid,homo_asym_id,lig3,homo_pdbid,homo_asym_id)
    if homolog_link:
        homolog_link='<tr BGCOLOR="#DEDEDE">'
        if lig3=="rna":
            homolog_link='<tr>'
        homolog_link+='<td>(Identical to '+homolog_link[1:]+")</td></tr>"

    print('''
<tr><td><h1 align=center>Structure of PDB $pdbid Chain $asym_id</h1></td></tr>
<tr><td>
<div id="headerDiv">
    <div id="titleText">Sequence</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr><td>&gt;$prefix (length=$L) $species [<a href=ssearch.cgi?seq_type=$lig3&sequence=$sequence>Search $code sequence</a>]</td></tr>
    <tr><td><span title="Only residues with experimentally determined coordinates are included. Residues unobserved in the structure are excluded.">$seq_txt</span></td></tr>
    $homolog_link
    </table>
</div>
</td></tr>
'''.replace("$pdbid",pdbid
  ).replace("$asym_id",asym_id
  ).replace("$prefix",prefix
  ).replace("$L",str(len(sequence))
  ).replace("$lig3",lig3
  ).replace("$code",code
  ).replace("$sequence",sequence
  ).replace("$seq_txt",seq_txt
  ).replace("$homolog_link",homolog_link
  ).replace("$species",species
  ))
    return display_ligand(pdbid,asym_id,lig3,'0',title)

def display_regular_ligand(pdbid,asym_id,lig3,ligIdx,title):
    if not ligIdx:
        ligIdx='1'
    lig3=lig3.upper()

    formula=''
    InChI=''
    InChIKey=''
    SMILES=''
    name=''
    cmd="zcat %s/data/ligand.tsv.gz|grep -P '^%s\\t'"%(rootdir,lig3)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    items=stdout.decode().split('\t')
    if len(items)>=9:
        formula,InChI,InChIKey,SMILES,name,ChEMBL,DrugBank,ZINC=items[1:9]
    filename="%s/data/smiles.tsv.gz"%rootdir
    if os.path.isfile(filename):
        cmd="zcat %s | grep -P '^%s\\t'"%(filename,lig3)
        p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        stdout,stderr=p.communicate()
        smiles_dict=dict()
        for line in stdout.decode().splitlines():
            items=line.split('\t')
            if len(items)>=3:
                if not items[1] in smiles_dict:
                    smiles_dict[items[1]]=[items[2]]
                else:
                    smiles_dict[items[1]].append(items[2])
        smiles_list=SMILES.split(';')
        SMILES="<table width=100%><tr BGCOLOR='#DEDEDE'><th>Software</th><th>SMILES</th></tr>"
        for key in smiles_list:
            key=key.strip()
            if key in smiles_dict:
                SMILES+="<tr><td>"+'<br>'.join(smiles_dict[key])+"</td><td>"+key+"</td></tr>"
            else:
                SMILES+="<tr><td></td><td>"+key+"</td></tr>"
        SMILES+="</table>"
    else:
        SMILES=SMILES.replace(';',';<br>')

    svg="https://cdn.rcsb.org/images/ccd/labeled/%s/%s.svg"%(lig3[0],lig3)
    print('''
<tr><td><h1 align=center>Structure of PDB $pdbid Chain $asym_id ligand $lig3</h1></td></tr>
<tr><td>
<div id="headerDiv">
    <div id="titleText">Chemical information</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr align=center><td width=10%><strong>2D<br>diagram</strong></td><td><a href=$svg target=_blank><img src=$svg width=400></a></td></tr>
    <tr BGCOLOR="#DEDEDE"><td align=center><a href=https://wwpdb.org/data/ccd target=_blank><strong>PDB Ligand ID</strong></a></td><td><span title="The ligand ID follows the
Chemical Component Dictionary (CCD)
used by the PDB database."><a href=https://rcsb.org/ligand/$lig3>$lig3</a></span></td></tr>
    <tr><td align=center><a href=https://inchi-trust.org target=_blank><strong>InChI</strong></a></td><td>$InChI</td></tr>
    <tr BGCOLOR="#DEDEDE"><td align=center><a href=https://inchi-trust.org target=_blank><strong>InChIKey</strong></a></td><td>$InChIKey</td></tr>
    <tr><td align=center><strong>SMILES</strong></td><td>$SMILES</td></tr>
    <tr BGCOLOR="#DEDEDE"><td align=center><strong>Formula</strong></td><td>$formula</td></tr>
    <tr><td align=center><strong>Name</strong></td><td>$name</td></tr>
    <tr BGCOLOR="#DEDEDE"><td align=center><strong><a href=https://www.ebi.ac.uk/chembl target=_blank>ChEMBL</a></strong></td><td><a href="https://www.ebi.ac.uk/chembl/compound_report_card/$ChEMBL" target=_blank>$ChEMBL</a></td></tr>
    <tr><td align=center><strong><a href=https://go.drugbank.com target=_blank>DrugBank</a></strong></td><td><a href="https://go.drugbank.com/drugs/$DrugBank" target=_blank>$DrugBank</a></td></tr>
    <tr BGCOLOR="#DEDEDE"><td align=center><strong><a href=https://zinc.docking.org target=_blank>ZINC</a></strong></td><td><a href="https://zinc.docking.org/substances/$ZINC" target=_blank>$ZINC</a></td></tr>
    </table>
</div>
</td></tr>
'''.replace("$pdbid",pdbid
  ).replace("$asym_id",asym_id
  ).replace("$lig3",lig3
  ).replace("$svg",svg
  ).replace("$InChIKey",InChIKey
  ).replace("$InChI",InChI
  ).replace("$SMILES",SMILES
  ).replace("$formula",formula
  ).replace("$name",name.replace(';',';<br>')
  ).replace("$ChEMBL",ChEMBL
  ).replace("$DrugBank",DrugBank
  ).replace("$ZINC",ZINC
  ))
    return display_ligand(pdbid,asym_id,lig3,ligIdx,title)

def display_ec(ec,csaOrig,csaRenu):
    print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">Enzymatic activity</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
''')
    if csaOrig:
        print('''
    <tr align=center>
        <td width=10%><strong>Catalytic site (original residue number in PDB)</strong></td>
        <td width=90% align=left><a href="https://www.ebi.ac.uk/thornton-srv/m-csa/search/?s=$pdbid" target=_blank>$csaOrig</a></td>
    </tr>
    <tr BGCOLOR="#DEDEDE" align=center>
        <td width=10%><strong>Catalytic site (residue number reindexed from 1)</strong></td>
        <td width=90% align=left><a href="https://www.ebi.ac.uk/thornton-srv/m-csa/search/?s=$pdbid" target=_blank>$csaRenu</a></td>
    </tr>
        '''.replace("$csaOrig",csaOrig
          ).replace("$csaRenu",csaRenu
          ).replace("$pdbid",pdbid))
    if ec:
        ec2name_dict=dict()
        fp=gzip.open("%s/data/enzyme.tsv.gz"%rootdir,'rt')
        for line in fp.read().splitlines():
            e,name=line.split('\t')
            ec2name_dict[e]=name
        fp.close()
        ec_list=[]
        for e in ec.replace(' ','').split(','):
            name=''
            if e in ec2name_dict:
                name=': '+ec2name_dict[e]
            ec_list.append("<a href=https://enzyme.expasy.org/EC/%s target=_blank>%s</a>"%(e,e)+name)
        print('''
    <tr align=center>
        <td width=10%><strong>Enzyme Commision number</strong></td>
        <td width=90% align=left>$ec</td>
    </tr>
        '''.replace("$ec",'<br>'.join(ec_list)))
    print('''   </table>
</div>
</td></tr>
''')

def display_go(go,uniprot,pdbid,asym_id):
    print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">Gene Ontology</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
''')
    go2is_a=dict()
    has_svg=0
    for Aspect in "FPC":
        filename="%s/output/%s_%s_%s.svg"%(rootdir,pdbid,asym_id,Aspect)
        if os.path.isfile(filename):
            has_svg+=1
    if has_svg==0:
        fp=gzip.open("%s/data/is_a.tsv.gz"%rootdir,'rt')
        for line in fp.read().splitlines():
            GOterm,Aspect,direct_line,indirect_line=line.split('\t')
            go2is_a[GOterm]=(direct_line.split(','),indirect_line.split(','))
        fp.close()

    go2name_dict=dict()
    fp=gzip.open("%s/data/go2name.tsv.gz"%rootdir,'rt')
    for line in fp.read().splitlines():
        GOterm,Aspect,name=line.split('\t')
        go2name_dict[GOterm]=(Aspect,name)
    fp.close()
    go2aspect=dict()
    for term in go.split(','):
        term="GO:"+term.strip()
        if not term in go2name_dict:
            continue
        Aspect,name=go2name_dict[term]
        if not Aspect in go2aspect:
            go2aspect[Aspect]=[]
        go2aspect[Aspect].append((term,name))
    
    for Aspect,namespace in [('F',"Molecular Function"),
                             ('P',"Biological Process"),
                             ('C',"Cellular Component")]:
        if not Aspect in go2aspect:
            continue
        namespace_link=namespace
        if uniprot:
            u=uniprot.split(',')[0]
            namespace_link='<a href="https://www.ebi.ac.uk/QuickGO/annotations?geneProductId=%s&aspect=%s" target=_blank>%s</a>'%(
                u,
                namespace.lower().replace(' ','_'),
                namespace)
        height="height=400"
        if Aspect=='P':
            height="height=300"
        print('''
<tr>
    <table width=100%>
    <tr BGCOLOR="#DEDEDE" align=center>
        <th width=10% align=right><strong></strong></th>
        <th width=90% align=left><span title="View $namespace annotation for UniProt protein $uniprot"><strong>$namespace_link</strong></a></th>
    </tr>
        '''.replace("$namespace_link",namespace_link
          ).replace("$namespace",namespace
          ).replace("$uniprot",u
        ))
        for l,(term,name) in enumerate(go2aspect[Aspect]):
            bgcolor=' BGCOLOR="#F2F2F2"'
            #if l%2==1:
            #    bgcolor=' BGCOLOR="#DEDEDE" '
            print('''
    <tr $bgcolor>
        <td align=center width=10%><a href="https://ebi.ac.uk/QuickGO/term/$term" target=_blank>$term</td>
        <td align=left width=90%>$name</td>
    </tr>
            '''.replace("$bgcolor",bgcolor
              ).replace("$term",term
              ).replace("$name",name))
        print('''
    </table>
</tr>''')

        filename="%s/output/%s_%s_%s.svg"%(rootdir,pdbid,asym_id,Aspect)
        if os.path.isfile(filename):
            continue
        go_plotted=[]
        GVtxt='digraph G{ graph[splines=true,rankdir="BT"];\n'
        go_direct_list=[term for term,name in go2aspect[Aspect]]
        go_direct_set =set(go_direct_list)
        go_indirect_list=[]
        for term in go_direct_list:
            label=term
            if term in go2name_dict:
                label+='\n'+textwrap.fill(go2name_dict[term][1][:100],25)
            GVtxt+='"%s"[label="%s" shape=rectangle fillcolor=lightgrey style=filled];\n'%(
                term,label)
        for term in go_direct_list:
            if not term in go2is_a:
                continue
            for parent in go2is_a[term][0]+go2is_a[term][1]:
                if not parent or parent in go_direct_set \
                         or parent in go_indirect_list:
                    continue
                go_indirect_list.append(parent)
                label=parent
                if parent in go2name_dict:
                    label+='\n'+textwrap.fill(go2name_dict[parent][1][:100],25)
                GVtxt+='"%s"[label="%s" shape=rectangle fillcolor=white style=filled];\n'%(
                parent,label)
        for term in go_direct_list+go_indirect_list:
            if not term in go2is_a:
                continue
            for parent in go2is_a[term][0]:
                if parent:
                    GVtxt+='"%s"->"%s";\n'%(term,parent)
        GVtxt+="}"
        p=subprocess.Popen(dot+" -Tsvg",shell=True,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        stdout,stderr=p.communicate(input=GVtxt.encode('utf-8'))
        svgtxt=stdout.decode()
        if len(svgtxt):
            fp=open(filename,'w')
            fp.write(svgtxt)
            fp.close()
        else:
            dotfilename="%s/output/%s_%s_%s.dot"%(rootdir,pdbid,asym_id,Aspect)
            fp=open(dotfilename,'w')
            fp.write(GVtxt)
            fp.close()
            os.system(dot+" -Tsvg -O "+dotfilename)
    
    svg_size_dict=dict()
    svg_size_pat=re.compile('<svg width=\"(\d+)pt\" height=\"(\d+)pt\"')
    for Aspect in ['F','P','C']:
        filename="output/%s_%s_%s.svg"%(pdbid,asym_id,Aspect)
        if not os.path.isfile(filename):
            continue
        fp=open(filename,'r')
        findall_list=svg_size_pat.findall(fp.read())
        fp.close()
        svg_size_dict[Aspect]=1
        if len(findall_list) and len(findall_list[0])>=2:
            w,h=findall_list[0][:2]
            svg_size_dict[Aspect]=float(w)/float(h)
    if len(svg_size_dict):
        total_width=sum([svg_size_dict[a] for a in svg_size_dict])
        for a in svg_size_dict:
            svg_size_dict[a]=int(100.*svg_size_dict[a]/total_width)

    print('''   </table>
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr valign=bottom>''')
    for Aspect,namespace in [('F',"Molecular Function"),
                             ('P',"Biological Process"),
                             ('C',"Cellular Component")]:
        filename="output/%s_%s_%s.svg"%(pdbid,asym_id,Aspect)
        if not os.path.isfile(rootdir+'/'+filename):
            continue
        height="height=400"
        if Aspect=='P':
            height="height=300"
        print('''
        <td align=center width=$width%><span title="View graph for $namespace.
Grey and white boxes indidate GO terms directly annotated to the protein by SIFTS and their parent terms, respectively."><a href=$filename target=_blank><img src=$filename style="display:block;" width="100%"><br>View graph for<br>$namespace</a></td>
        '''.replace("$namespace",namespace
          ).replace("$height",height
          ).replace("$width","%d"%svg_size_dict[Aspect]
          ).replace("$filename",filename
        ))
    print("    </tr>")
    
    print('''   </table>
</div>
</td></tr>
''')

def download_pdb1(pdbid,asym_id,lig3,ligIdx):
    print("Content-type: text/plain\n")
    prefix="%s%s"%(pdbid,asym_id)
    if lig3:
        if lig3 in ["rna","dna","peptide"]:
            ligIdx='0'
        if not ligIdx:
            ligIdx='1'
        prefix='_'.join((pdbid,lig3,asym_id,ligIdx))
    filename="%s/output/%s.pdb.gz"%(rootdir,prefix)
    cmd="%s/script/receptor1 %s -"%(rootdir,filename)
    print(cmd)
    if not os.path.isfile(filename):
        exit()
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    print(stdout.decode())
    return

def display_protein_receptor(pdbid,asym_id,title):
    taxon_dict=read_taxon()
    prefix="%s%s"%(pdbid,asym_id)
    cmd="zcat %s/data/protein.fasta.gz|grep -PA1 '^>%s\\t'|tail -1"%(
        rootdir,prefix)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    sequence=stdout.decode().strip()
    seq_txt='<br>'.join(textwrap.wrap(sequence,50))
    species=''
    if pdbid+':'+asym_id in taxon_dict:
        species="Species: "+taxon_dict[pdbid+':'+asym_id]
    print('''
<tr><td><h1 align=center>Structure of PDB $pdbid Chain $asym_id</h1></td></tr>
'''.replace("$pdbid",pdbid
  ).replace("$asym_id",asym_id))

    if len(sequence):
        print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">Receptor sequence</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr><td>&gt;$prefix (length=$L) $species [<a href=ssearch.cgi?seq_type=protein&sequence=$sequence target=_blank>Search protein sequence</a>]</td></tr>
    <tr><td><span title="Only residues with experimentally determined coordinates are included. Residues unobserved in the structure are excluded.">$seq_txt</span></td></tr>
    </table>
</div>
</td></tr>
'''.replace("$pdbid",pdbid
  ).replace("$asym_id",asym_id
  ).replace("$prefix",prefix
  ).replace("$L",str(len(sequence))
  ).replace("$sequence",sequence
  ).replace("$seq_txt",seq_txt
  ).replace("$species",species
  ))

    reso   =''
    csaOrig=''
    csaRenu=''
    ec     =''
    go     =''
    uniprot=''
    pubmed =''
    cmd="zcat %s/data/pdb_all.tsv.gz %s/data/ec_all.tsv.gz|grep -P '^%s\\t%s\\t'|head -1"%(
        rootdir,rootdir,pdbid,asym_id)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    items=stdout.decode().split('\t')
    if len(items)>=9:
        reso,csaOrig,csaRenu,ec,go,uniprot,pubmed=items[2:9]
        if reso=="-1.00":
            reso="N/A"
        else:
            reso=reso+" &#8491;"
    filename="%s/output/%s.pdb.gz"%(rootdir,prefix)
    if not os.path.isfile(filename):
        divided=pdbid[-3:-1]
        for prefix_tar in ["receptor","Enzyme"]:
            if not os.path.isfile("%s/weekly/%s_%s.tar.bz2"%(
                rootdir,prefix_tar,divided)):
                continue
            tar = tarfile.open("%s/weekly/%s_%s.tar.bz2"%(
                rootdir,prefix_tar,divided))
            extract_filename="%s/%s.pdb"%(prefix_tar,prefix)
            if not extract_filename in tar.getnames():
                continue
            fin=tar.extractfile(extract_filename)
            lines=fin.read().decode().splitlines()
            txt=''
            for line in lines:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    txt+=line[:20]+" R"+line[22:]+'\n'
                else:
                    txt+=line+'\n'
            fout=gzip.open(filename,'wt')
            fout.write(txt)
            fout.close()
            fin.close()
            tar.close()
            break

    script=''
    explainLabel=''
    if csaOrig:
        explainLabel='Catalytic site residues are labeled in the structure<br>'
        resi_list=[r[1:] for r in csaOrig.split()]
        script="select "+','.join(resi_list)+"; spacefill 25%; wireframe 50; color group;"
        for resi in resi_list:
            script+="select "+resi+" and *.ca; label %m%R; color label magenta;"
    print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">3D structure</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr><td align=center width=10%><strong>PDB</strong></td><td><span title="Search BioLiP entries from the same structure"><a href=qsearch.cgi?pdbid=$pdbid target=_blank>$pdbid</a></span> $title</td></tr>
    <tr BGCOLOR="#DEDEDE"><td align=center><strong>Chain</strong></td><td><a href=qsearch.cgi?pdbid=$pdbid&chain=$asym_id target=_blank>$asym_id</a></td></tr>
    <tr><td align=center><strong>Resolution</strong></td><td>$reso</a></td></tr>
    <tr BGCOLOR="#DEDEDE" align=center><td align=center><strong>3D<br>structure</strong></td><td>
    <table><tr><td>

<script type="text/javascript"> 
$(document).ready(function()
{
    Info = {
        width: 400,
        height: 400,
        j2sPath: "jsmol/j2s",
        script: "load output/$prefix.pdb.gz; color background black; cartoons; color group; spacefill off; wireframe off; $script;"
    }
    $("#mydiv").html(Jmol.getAppletHtml("jmolApplet0",Info))
});
</script>
<span id=mydiv></span>
    </td><td align=left>
$explainLabel
[<a href="javascript:Jmol.script(jmolApplet0, 'spin on')">Spin on</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'spin off')">Spin off</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'Reset')">Reset orientation</a>]<p></p>
[<a href="javascript:Jmol.script(jmolApplet0, 'set antialiasDisplay true')">High quality</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'set antialiasDisplay false')">Low quality</a>]<p></p>
[<a href="javascript:Jmol.script(jmolApplet0, 'color background white')">White background</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'color background black')">Black background</a>]<p></p>
[<a href=output/$prefix.pdb.gz>Download</a>]<br>
[<a href=?pdbid=$pdbid&chain=$asym_id&outfmt=1 download=$prefix.pdb>Download structure with residue number starting from 1</a>]
    </td></tr></table>


    </td></tr>
    </table>
</div>
</td></tr>
'''.replace("$pdbid",pdbid
  ).replace("$title",title
  ).replace("$asym_id",asym_id
  ).replace("$reso",reso
  ).replace("$prefix",prefix
  ).replace("$explainLabel",explainLabel
  ).replace("$script",script
  ))

    if ec:
        display_ec(ec,csaOrig,csaRenu)

    cmd="zcat %s/data/lig_all.tsv.gz|grep -P '^%s\\t%s\\t'"%(
        rootdir,pdbid,asym_id)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    lines=stdout.decode().splitlines()
    if len(lines):
        print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">Interaction with ligand</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr BGCOLOR="#DEDEDE" align=center>
        <th width=5%><strong>Site<br>#</strong></th>
        <th width=5%><strong>Ligand</strong></th>
        <th width=5%><strong>Ligand<br>chain</strong></th>
        <th width=29%><strong>Binding residues on receptor<br>(original residue number in PDB)</strong></th>
        <th width=29%><strong>Binding residues on receptor<br>(residue number reindexed from 1)</strong></th>
        <th width=27%><strong>Binding affinity</strong></th>
    </tr>
''')
        for l,line in enumerate(lines):
            items    =line.split('\t')
            recCha   =items[1]
            bs       =items[2]
            ccd      =items[3]
            ligCha   =items[4]
            ligIdx   =items[5]
            resOrig  =items[6]
            resRenu  =items[7]
            manual   =items[8]
            moad     =items[9]
            pdbbind  =items[10]
            bindingdb=items[11]

            baff_list=[]
            if manual:
                baff_list.append("Manual survey: "+manual)
            if moad:
                baff_list.append("<a href=http://bindingmoad.org/pdbrecords/index/%s target=_blank>MOAD</a>: %s"%(pdbid,moad))
            if pdbbind:
                baff_list.append("<a href=http://pdbbind.org.cn/quickpdb.php?quickpdb=%s target=_blank>PDBbind-CN</a>: %s"%(pdbid,pdbbind))
            if bindingdb:
                baff_list.append("BindingDB: "+bindingdb)

            bgcolor=''
            if l%2==1:
                bgcolor=' BGCOLOR="#DEDEDE" '
            print('''
    <tr $bgcolor align=center>
        <td><span title="Click to view binding site"><a href="pdb.cgi?pdb=$pdbid&chain=$recCha&bs=$bs" target=_blank>$bs</a></span></td>
        <td><span title="Click to view binding site"><a href="pdb.cgi?pdb=$pdbid&chain=$recCha&bs=$bs" target=_blank>$ccd</a></span></td>
        <td><span title="Click to view binding site"><a href="pdb.cgi?pdb=$pdbid&chain=$recCha&bs=$bs" target=_blank>$ligCha</a></span></td>
        <td><span title="Click to view binding site"><a href="pdb.cgi?pdb=$pdbid&chain=$recCha&bs=$bs" target=_blank>$resOrig</a></span></td>
        <td><span title="Click to view binding site"><a href="pdb.cgi?pdb=$pdbid&chain=$recCha&bs=$bs" target=_blank>$resRenu</a></span></td>
        <td>$baff</td>
    </tr>
            '''.replace("$bgcolor",bgcolor
              ).replace("$pdbid",pdbid
              ).replace("$recCha",recCha
              ).replace("$ccd",ccd
              ).replace("$ligCha",recCha
              ).replace("$bs",bs
              ).replace("$resOrig",resOrig
              ).replace("$resRenu",resRenu
              ).replace("$baff",'<br>'.join(baff_list)))

        print('''   </table>
</div>
</td></tr>
''')

    if go:
        display_go(go,uniprot,pdbid,asym_id)
    return pubmed,uniprot

def display_interaction(pdbid,asym_id,bs,title):    
    taxon_dict=read_taxon()
    prefix="%s%s"%(pdbid,asym_id)
    cmd="zcat %s/data/protein.fasta.gz|grep -PA1 '^>%s\\t'|tail -1"%(
        rootdir,prefix)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    sequence=stdout.decode().strip()
    seq_txt='<br>'.join(textwrap.wrap(sequence,50))
    species=''
    if pdbid+':'+asym_id in taxon_dict:
        species="Species: "+taxon_dict[pdbid+':'+asym_id]
    print('''
<tr><td><h1 align=center>Structure of PDB $pdbid Chain $asym_id Binding Site $bs</h1></td></tr>
<tr><td>
<div id="headerDiv">
    <div id="titleText">Receptor Information</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr><td>&gt;$pdbid Chain $asym_id (length=$L) $species
    [<a href=ssearch.cgi?seq_type=protein&sequence=$sequence target=_blank>Search protein sequence</a>]
    [<a href=output/$prefix.pdb.gz>Download receptor structure</a>]
    [<a href=?pdbid=$pdbid&chain=$asym_id&outfmt=1 download=$prefix.pdb>Download structure with residue number starting from 1</a>]
    [<a href=?pdb=$pdbid&chain=$asym_id target=_blank>View receptor structure</a>]
    </td></tr>
    <tr><td><span title="Only residues with experimentally determined coordinates are included. Residues unobserved in the structure are excluded.">$seq_txt</span></td></tr>
    </table>
</div>
</td></tr>
'''.replace("$pdbid",pdbid
    ).replace("$asym_id",asym_id
    ).replace("$prefix",prefix
    ).replace("$bs",bs
    ).replace("$L",str(len(sequence))
    ).replace("$sequence",sequence
    ).replace("$seq_txt",seq_txt
    ).replace("$species",species
    ))

    
    cmd="zcat %s/data/lig_all.tsv.gz|grep -P '^%s\\t%s\\t%s\\t'"%(
        rootdir,pdbid,asym_id,bs)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    line     =stdout.decode().splitlines()[0]
    items    =line.split('\t')
    lig3     =items[3]
    ligCha   =items[4]
    ligIdx   =items[5]
    resOrig  =items[6]
    resRenu  =items[7]
    manual   =items[8]
    moad     =items[9]
    pdbbind  =items[10]
    bindingdb=items[11]

    score=''
    if os.path.isfile(rootdir+"/data/lig_rhea.tsv.gz") and not lig3 in ["peptide","rna","dna"]:
        cmd="zcat %s/data/lig_rhea.tsv.gz|grep -P '^%s\\t%s\\t%s\\t'"%(
            rootdir,pdbid,asym_id,lig3)
        p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        stdout,stderr=p.communicate()
        stdout   =stdout.decode()
        score    =''
        if len(stdout.strip()):
            line     =stdout.splitlines()[0]
            items    =line.split('\t')
            score    =items[3]
            if score=="cognate":
                score="<span title=FireDB:cognate>4 <img src=images/4-star.svg width=75></span>"
            elif score=="ambiguous":
                score="<span title=FireDB:ambiguous>3 <img src=images/3-star.svg width=75></span>"
            elif score=="non_cognate":
                score="<span title=FireDB:non_cognate>1 <img src=images/1-star.svg width=75></span>"
            else:

                cmd="zcat %s/data/pdb_rhea.tsv.gz|grep -P '^%s\\t%s\\t'"%(
                    rootdir,pdbid,asym_id)
                p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
                stdout,stderr=p.communicate()
                line     =stdout.decode().splitlines()[0]
                items    =line.split('\t')
                rhea     ='\n'.join(["RHEA:"+r for r in items[2].split(',')])

                score='<span title="%s">%s <img src=images/%s-star.svg width=75></span>'%(
                    rhea,score,score[0])


            score='''            <tr><td align=center><strong><span title="
Each protein-ligand interaction is assigned an annotation score ranging from
1 to 5. Higher score suggests greater biological relevance.

If the UniProt protein corresponding to the receptor chain is mapped to at
least one Rhea reaction, all non-water substrates and products of the 
reaction(s) are converted to 1024 bit Morgan fingerprint (ECFP4). Their
chemical similarity to the ligand in question can then be measured by 
Tanimoto Coefficient (TC). The highest TC among all substrates/products to
the ligand is used to assign the annotation score: TC of [0,0.4), [0.4,0.6),
[0.6,0.8), [0.8,1) and 1 correspond to annotation score of 1, 2, 3, 4 and 5, respectively.

If the receptor protein cannot be mapped to Rhea, the annotation score is 
assigned based on FireDB classification of ligands, where cognate, ambiguous
and non-cognate ligands are assigned score of 1, 3, and 4, respectively.
            ">Annotation score</span></strong><td>%s</td></tr>'''%(score)

    baff_line=''
    baff_list=[]
    if manual:
        baff_list.append("Manual survey: "+manual)
    if moad:
        baff_list.append("<a href=http://bindingmoad.org/pdbrecords/index/%s target=_blank>MOAD</a>: %s"%(pdbid,moad))
    if pdbbind:
        baff_list.append("<a href=http://pdbbind.org.cn/quickpdb.php?quickpdb=%s target=_blank>PDBbind-CN</a>: %s"%(pdbid,pdbbind))
    if bindingdb:
        baff_list.append("BindingDB: "+bindingdb)
    if len(baff_list):
        baff_line='            <tr BGCOLOR="#DEDEDE">'
        if len(score)==0:
            baff_line='            <tr>'
        baff_line+='''<td align=center><strong>Binding affinity</strong><td>$baff</td></tr>
        '''.replace("$baff",'<br>'.join(baff_list))


    lig_prefix="%s_%s_%s_%s"%(pdbid,lig3,ligCha,ligIdx)
    filename="%s/output/%s.pdb.gz"%(rootdir,lig_prefix)
    x_list=[]
    y_list=[]
    z_list=[]
    resSeq_txt=""
    if not os.path.isfile(filename):
        divided=pdbid[-3:-1]
        if os.path.isfile("%s/weekly/ligand_%s.tar.bz2"%(rootdir,divided)):
            tar = tarfile.open("%s/weekly/ligand_%s.tar.bz2"%(rootdir,divided))
            fin=tar.extractfile("ligand/%s.pdb"%lig_prefix)
            lines=fin.read().decode().splitlines()
            txt=''
            for line in lines:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    txt+=line[:20]+" L"+line[22:]+'\n'
                    x_list.append(float(line[30:38]))
                    y_list.append(float(line[38:46]))
                    z_list.append(float(line[46:54]))
                    if not resSeq_txt:
                        resSeq_txt=line[22:27]
                else:
                    txt+=line+'\n'
            fout=gzip.open(filename,'wt')
            fout.write(txt)
            fout.close()
            fin.close()
            tar.close()
    else:
        fin=gzip.open(filename,'rt')
        for line in fin.read().splitlines():
            if line.startswith("ATOM") or line.startswith("HETATM"):
                x_list.append(float(line[30:38]))
                y_list.append(float(line[38:46]))
                z_list.append(float(line[46:54]))
                if not resSeq_txt:
                    resSeq_txt=line[22:27]
        fin.close()
    if len(x_list):
        xcen=sum(x_list)/len(x_list)
        ycen=sum(y_list)/len(y_list)
        zcen=sum(z_list)/len(z_list)
    else:
        xcen=0
        ycen=0
        zcen=0
    print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">Ligand information</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    ''')
    if lig3 in ["peptide","rna","dna"]:
        code=lig3.upper()
        if lig3=="peptide":
            code=lig3
        cmd="zcat %s/data/%s.fasta.gz|grep -PA1 '^>%s_%s_%s\\t'|tail -1"%(
            rootdir,lig3,pdbid,lig3,ligCha)
        p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        stdout,stderr=p.communicate()
        lig_sequence=stdout.decode().strip()
        lig_seq_txt='<br>'.join(textwrap.wrap(lig_sequence,50))
        if lig3=="rna":
            cmd="zcat %s/data/rna_ss.txt.gz|grep -P '^%s_rna_%s\\t'|cut -f2"%(
                rootdir,pdbid,ligCha)
            p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
            stdout,stderr=p.communicate()
            lig_seq_txt+='''</span></td></tr>
<tr BGCOLOR="#DEDEDE"><td><span title="CSSR secondary structure assignment">%s'''%(
            '<br>'.join(textwrap.wrap(stdout.decode(),50)))
        species=''
        if pdbid+':'+ligCha in taxon_dict:
            species="Species: "+taxon_dict[pdbid+':'+ligCha]
        print('''
<tr><td>&gt;$pdbid Chain $asym_id (length=$L) $species
[<a href=ssearch.cgi?seq_type=$lig3&sequence=$sequence>Search $code sequence</a>]
[<a href=output/$prefix.pdb.gz>Download ligand structure</a>]
[<a href=?pdbid=$pdbid&chain=$asym_id&lig3=$lig3&outfmt=1 download=$prefix.pdb>Download structure with residue number starting from 1</a>]
[<a href=?pdb=$pdbid&chain=$asym_id&lig3=$lig3&ligIdx=0 target=_blank>View ligand structure</a>]
</td></tr>
<tr><td><span title="Only residues with experimentally determined coordinates are included. Residues unobserved in the structure are excluded.">$seq_txt</span></td></tr>
      '''.replace("$pdbid",pdbid
        ).replace("$asym_id",ligCha
        ).replace("$prefix",lig_prefix
        ).replace("$L",str(len(lig_sequence))
        ).replace("$lig3",lig3
        ).replace("$code",code
        ).replace("$sequence",lig_sequence
        ).replace("$seq_txt",lig_seq_txt
        ).replace("$species",species
        ))
    else:
        formula=''
        InChI=''
        InChIKey=''
        SMILES=''
        name=''
        ChEMBL=''
        DrugBank=''
        ZINC=''
        cmd="zcat %s/data/ligand.tsv.gz|grep -P '^%s\\t'"%(rootdir,lig3)
        p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        stdout,stderr=p.communicate()
        items=stdout.decode().split('\t')
        if len(items)>=9:
            formula,InChI,InChIKey,SMILES,name,ChEMBL,DrugBank,ZINC=items[1:9]

        filename="%s/data/smiles.tsv.gz"%rootdir
        if os.path.isfile(filename):
            cmd="zcat %s | grep -P '^%s\\t'"%(filename,lig3)
            p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
            stdout,stderr=p.communicate()
            smiles_dict=dict()
            for line in stdout.decode().splitlines():
                items=line.split('\t')
                if len(items)>=3:
                    if not items[1] in smiles_dict:
                        smiles_dict[items[1]]=[items[2]]
                    else:
                        smiles_dict[items[1]].append(items[2])
            smiles_list=SMILES.split(';')
            SMILES="<table width=100%><tr BGCOLOR='#DEDEDE'><th>Software</th><th>SMILES</th></tr>"
            for key in smiles_list:
                key=key.strip()
                if key in smiles_dict:
                    SMILES+="<tr><td>"+'<br>'.join(smiles_dict[key])+"</td><td>"+key+"</td></tr>"
                else:
                    SMILES+="<tr><td></td><td>"+key+"</td></tr>"
            SMILES+="</table>"
        else:
            SMILES=SMILES.replace(';',';<br>')



        svg="https://cdn.rcsb.org/images/ccd/labeled/%s/%s.svg"%(lig3[0],lig3)
        print('''
<tr>
    <td>
        <a href=$svg target=_blank><img src=$svg width=400></a>
    </td>
    <td>
    <table>
        <tr BGCOLOR="#DEDEDE"><td align=center><a href=https://wwpdb.org/data/ccd target=_blank>Ligand ID</a></td><td><span title="The ligand ID follows the
Chemical Component Dictionary (CCD)
used by the PDB database."><a href=https://rcsb.org/ligand/$lig3>$lig3</a></span></td></tr>
        <tr><td align=center><a href=https://inchi-trust.org target=_blank>InChI</a></td><td>$InChI</td></tr>
        <tr BGCOLOR="#DEDEDE"><td align=center><a href=https://inchi-trust.org target=_blank>InChIKey</a></td><td>$InChIKey</td></tr>
        <tr><td align=center>SMILES</td><td>$SMILES</td></tr>
        <tr BGCOLOR="#DEDEDE"><td align=center>Formula</td><td>$formula</td></tr>
        <tr><td align=center>Name</td><td>$name</td></tr>
        <tr BGCOLOR="#DEDEDE"><td align=center><a href=https://www.ebi.ac.uk/chembl target=_blank>ChEMBL</a></td><td><a href="https://www.ebi.ac.uk/chembl/compound_report_card/$ChEMBL" target=_blank>$ChEMBL</a></td></tr>
        <tr><td align=center><a href=https://go.drugbank.com target=_blank>DrugBank</a></td><td><a href="https://go.drugbank.com/drugs/$DrugBank" target=_blank>$DrugBank</a></td></tr>
        <tr BGCOLOR="#DEDEDE"><td align=center><a href=https://zinc.docking.org>ZINC</a></td><td><a href="https://zinc.docking.org/substances/$ZINC" target=_blank>$ZINC</a></td></tr>
        <tr><td align=center>PDB chain</td><td>$pdbid Chain $asym_id Residue $resSeq
        [<a href=output/$prefix.pdb.gz>Download ligand structure</a>] 
        [<a href=?pdb=$pdbid&chain=$asym_id&lig3=$lig3&ligIdx=$ligIdx&outfmt=1 download=$prefix.pdb>Download structure with residue number starting from 1</a>] 
        [<a href=?pdb=$pdbid&chain=$asym_id&lig3=$lig3&ligIdx=$ligIdx target=_blank>View ligand structure</a>]
        </td></tr>
    </table>
    </td>
</tr>
      '''.replace("$pdbid",pdbid
        ).replace("$asym_id",ligCha
        ).replace("$lig3",lig3
        ).replace("$ligIdx",ligIdx
        ).replace("$prefix",lig_prefix
        ).replace("$svg",svg
        ).replace("$InChIKey",InChIKey
        ).replace("$InChI",InChI
        ).replace("$SMILES",SMILES
        ).replace("$formula",formula
        ).replace("$name",name.replace(';',';<br>')
        ).replace("$ChEMBL",ChEMBL
        ).replace("$DrugBank",DrugBank
        ).replace("$ZINC",ZINC
        ).replace("$resSeq",resSeq_txt
        ))
    print('''
    </table>
</div>
</td></tr>''')
        
    reso   =''
    csaOrig=''
    csaRenu=''
    ec     =''
    go     =''
    uniprot=''
    pubmed =''
    cmd="zcat %s/data/pdb_all.tsv.gz |grep -P '^%s\\t%s\\t'|head -1"%(
        rootdir,pdbid,asym_id)
    p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate()
    items=stdout.decode().split('\t')
    if len(items)>=9:
        reso,csaOrig,csaRenu,ec,go,uniprot,pubmed=items[2:9]
        if reso=="-1.00":
            reso="N/A"
        else:
            reso=reso+" &#8491;"
    filename="%s/output/%s.pdb.gz"%(rootdir,prefix)
    if not os.path.isfile(filename):
        divided=pdbid[-3:-1]
        if os.path.isfile("%s/weekly/receptor_%s.tar.bz2"%(rootdir,divided)):
            tar = tarfile.open("%s/weekly/receptor_%s.tar.bz2"%(rootdir,divided))
            fin=tar.extractfile("receptor/%s.pdb"%prefix)
            lines=fin.read().decode().splitlines()
            txt=''
            for line in lines:
                if line.startswith("ATOM") or line.startswith("HETATM"):
                    txt+=line[:20]+" R"+line[22:]+'\n'
                else:
                    txt+=line+'\n'
            fout=gzip.open(filename,'wt')
            fout.write(txt)
            fout.close()
            fin.close()
            tar.close()

    script=''
    if resOrig:
        resi_list=[r[1:] for r in resOrig.split()]
        script="select "+','.join(resi_list)+"; spacefill 25%; wireframe 50; color group;"
        for resi in resi_list:
            script+="select "+resi+" and *.ca; label %m%R; color label magenta;"
    script_ligand='spacefill 70% '
    if lig3=="peptide":
        script_ligand='cartoon; spacefill off;'
    if lig3 in ["rna","dna"]:
        script_ligand='cartoons; color grey; spacefill off; wireframe off'
    print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">Receptor-Ligand Complex Structure</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr BGCOLOR="#DEDEDE" align=center>
        <th>Global view</th><th>Local view</th><th>Structure summary</th>
    </tr>
    <tr>
        <td align=center>
<script type="text/javascript"> 
$(document).ready(function()
{
    Info = {
        width: 400,
        height: 400,
        j2sPath: "jsmol/j2s",
        script: "load output/$prefix.pdb.gz; color background black; cartoons; color group; spacefill off; wireframe off; $script; load append output/$lig_prefix.pdb.gz; select hetero; $script_ligand; frame all;"
    }
    $("#mydiv0").html(Jmol.getAppletHtml("jmolApplet0",Info))
});
</script>
<span id=mydiv0></span>
<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'spin on')">Spin on</a>]
[<a href="javascript:Jmol.script(jmolApplet0, 'spin off')">Spin off</a>]
[<a href="javascript:Jmol.script(jmolApplet0, 'Reset')">Reset</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'set antialiasDisplay true')">High quality</a>]
[<a href="javascript:Jmol.script(jmolApplet0, 'set antialiasDisplay false')">Low quality</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet0, 'color background white')">White background</a>]
[<a href="javascript:Jmol.script(jmolApplet0, 'color background black')">Black background</a>]
        </td>
        <td align=center>
<script type="text/javascript"> 
$(document).ready(function()
{
    Info = {
        width: 400,
        height: 400,
        j2sPath: "jsmol/j2s",
        script: "load output/$prefix.pdb.gz; color background black; color group; spacefill off; wireframe off; $script; load append output/$lig_prefix.pdb.gz; select hetero; $script_ligand; zoomto 0 {$xcen $ycen $zcen}; frame all;"
    }
    $("#mydiv1").html(Jmol.getAppletHtml("jmolApplet1",Info))
});
</script>
<span id=mydiv1></span>
<br>
[<a href="javascript:Jmol.script(jmolApplet1, 'spin on')">Spin on</a>]
[<a href="javascript:Jmol.script(jmolApplet1, 'spin off')">Spin off</a>]
[<a href="javascript:Jmol.script(jmolApplet1, 'Reset')">Reset</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet1, 'set antialiasDisplay true')">High quality</a>]
[<a href="javascript:Jmol.script(jmolApplet1, 'set antialiasDisplay false')">Low quality</a>]<br>
[<a href="javascript:Jmol.script(jmolApplet1, 'color background white')">White background</a>]
[<a href="javascript:Jmol.script(jmolApplet1, 'color background black')">Black background</a>]
        </td>
        <td>
        <table>
            <tr><td align=center><strong>PDB</strong><td><span title="Search BioLiP entries from the same structure"><a href=qsearch.cgi?pdbid=$pdbid target=_blank>$pdbid</a></span> $title</td></tr>
            <tr BGCOLOR="#DEDEDE"><td align=center><strong>Resolution</strong><td>$reso</td></tr>
            <tr><td align=center><strong>Binding residue<br>(original residue number in PDB)</strong><td>$resOrig</td></tr>
            <tr BGCOLOR="#DEDEDE"><td align=center><strong>Binding residue<br>(residue number reindexed from 1)</strong><td>$resRenu</td></tr>
            $score
            $baff_line
        </table>
        </td>
    </tr>
    </table>
</div>
</td></tr>
    '''.replace("$pdbid",pdbid
    ).replace("$title",title
    ).replace("$asym_id",asym_id
    ).replace("$reso",reso
    ).replace("$lig_prefix",lig_prefix
    ).replace("$prefix",prefix
    ).replace("$script_ligand",script_ligand
    ).replace("$script",script
    ).replace("$resOrig",resOrig
    ).replace("$resRenu",resRenu
    ).replace("$baff_line",baff_line
    ).replace("$score",score
    ).replace("$xcen","%.3f"%xcen
    ).replace("$ycen","%.3f"%ycen
    ).replace("$zcen","%.3f"%zcen
    ))

    if ec:
        display_ec(ec,csaOrig,csaRenu)
    if go:
        display_go(go,uniprot,pdbid,asym_id)
    return pubmed,uniprot

def pdb2title(pdbid):
    title=''
    fp=gzip.open(rootdir+"/data/title.tsv.gz",'rt')
    for line in fp.read().splitlines():
        if line.startswith(pdbid+'\t'):
            title=line.split('\t')[-1]
    fp.close()
    return title

def sanitize(inString):
    alphabet=set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890-")
    return ''.join([s for s in inString if s in alphabet])

def get_rna_info(pdbid,asym_id):
    rna_info_list=[]
    fp=gzip.open("%s/data/rna.tsv.gz"%rootdir,'rt')
    for line in fp.read().splitlines():
        if not line.startswith(pdbid):
            continue
        items=line.split('\t')
        if items[0]==pdbid and items[1]==asym_id:
            rna_info_list=items
    fp.close()
    return rna_info_list

if __name__=="__main__":
    form   =cgi.FieldStorage()
    pdbid  =form.getfirst("pdbid",'').lower()
    if not pdbid:
        pdbid=form.getfirst("pdb",'').lower()
    asym_id=form.getfirst("chain",'')
    if not asym_id:
        asym_id=form.getfirst("asym_id",'')
    ligIdx =form.getfirst("idx",'')
    if not ligIdx:
        ligIdx =form.getfirst("ligIdx",'')
    ligCha =form.getfirst("ligCha",'')
    lig3   =form.getfirst("lig3",'')
    outfmt =form.getfirst("outfmt",'')

    pdbid  =sanitize(pdbid)
    asym_id=sanitize(asym_id)
    ligIdx =sanitize(ligIdx)
    ligCha =sanitize(ligCha)
    lig3   =sanitize(lig3)
    outfmt =sanitize(outfmt)

    if outfmt=='1':
        download_pdb1(pdbid,asym_id,lig3,ligCha,ligIdx)
        exit(0)
        
    print("Content-type: text/html\n")
    print('''<html>
<head>
<link rel="stylesheet" type="text/css" href="page.css" />
<title>FURNA</title>
</head>
<body bgcolor="#F0FFF0">
<img src=images/furna.png ></br>

<script type="text/javascript" src="jsmol/JSmol.min.js"></script>
<table style="table-layout:fixed;" width="100%" cellpadding="2" cellspacing="0">
<table width=100%>
''')
    fp=open("%s/index.html"%rootdir)
    txt=fp.read()
    if '<!-- MENU START -->' in txt and '<!-- MENU END -->' in txt:
        print(txt.split('<!-- MENU START -->')[1].split('<!-- MENU END -->')[0])
    fp.close()

    rna_info_list=[]
    if pdbid and asym_id:
        rna_info_list=get_rna_info(pdbid,asym_id)
    if len(rna_info_list)==0:
        print('''</table>
Unknown pdb chain %s:%s
<p></p>
[<a href=.>Back to HOME</a>]
</body> </html>'''%(pdbid,asym_id))
        exit()

    #if lig3 and ligCha and ligIdx:
        #display_interaction(rna_info_list)
    #else:
        #display_receptor(rna_info_list)
   
    rnacentral=''
    if len(rna_info_list[5]):
        rnacentral_list=[]
        for r in rna_info_list[5].split(','):
            rnacentral_list.append("<a href=https://rnacentral.org/rna/%s target=_blank>%s</a>"%(r,r))
        rnacentral+='''<tr BGCOLOR="#DEDEDE"><td align=center><strong>RNAcentral</strong></td><td>%s</td></tr>'''%(''.join(rnacentral_list))
    
    pubmed=''
    if len(rna_info_list[6]):
        pubmed_dict=dict()
        fp=gzip.open("%s/data/pubmed.tsv.gz"%rootdir,'rt')
        for line in fp.read().splitlines():
            items=line.split('\t')
            pubmed_dict[items[0]]=items[1]
        fp.close()
        pubmed_list=[]
        for p in rna_info_list[6].split(','):
            pubmed="<a href=https://pubmed.ncbi.nlm.nih.gov/%s target=_blank>%s</a>"%(p,p)
            if p in pubmed_dict:
                pubmed=pubmed_dict[p]+' '+pubmed
            pubmed_list.append("<li>"+pubmed+"</li>")
        if rnacentral:
            pubmed='''<tr>'''
        else:
            pubmed='''<tr BGCOLOR="#DEDEDE">'''
        pubmed+='''<td align=center><strong>PubMed</strong></td><td>%s</td></tr>'''%(''.join(pubmed_list))
            
            
    print('''
<tr><td>
<div id="headerDiv">
    <div id="titleText">External links</div>
</div>
<div style="clear:both;"></div>
<div id="contentDiv">
    <div id="RContent" style="display: block;">
    <table width=100% border="0" style="font-family:Monospace;font-size:14px;background:#F2F2F2;" >
    <tr><td align=center width=10%><strong>PDB</strong></td>
        <td width=90%>
            <a href=https://rcsb.org/structure/$pdbid target=_blank>RCSB</a>,
            <a href=https://ebi.ac.uk/pdbe/entry/pdb/$pdbid target=_blank>PDBe</a>,
            <a href=https://pdbj.org/mine/summary/$pdbid target=_blank>PDBj</a>,
            <a href=http://ebi.ac.uk/pdbsum/$pdbid target=_blank>PDBsum</a>,
            <a href=https://nakb.org/atlas=$pdbid target=_blank>NAKB</a>,
            <a href=https://dnatco.datmos.org/conformers_cif.php?cifcode=$pdbid target=_blank>DNATCO</a>,
            <a href=http://rna.bgsu.edu/rna3dhub/pdb/$pdbid target=_blank>BGSU RNA</a>
        </td>
    </tr>
    $rnacentral
    $pubmed
    </tr>
'''.replace("$pdbid",pdbid
  ).replace("$pubmed",pubmed
  ).replace("$rnacentral",rnacentral
  ))
    
    print('''</table>
<p></p>
</body> </html>''')
