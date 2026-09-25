"""Execute via Jupyter, or explicitly in-process for socket-restricted environments."""
import argparse
from pathlib import Path
import os
import nbformat


def execute_in_process(notebook):
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    shell=InteractiveShell.instance()
    count=0
    for cell in notebook.cells:
        if cell.cell_type != 'code': continue
        count+=1
        with capture_output() as captured:
            result=shell.run_cell(cell.source,store_history=True)
        result.raise_error()
        cell.execution_count=count
        cell.outputs=[]
        if captured.stdout:
            cell.outputs.append(nbformat.v4.new_output('stream',name='stdout',text=captured.stdout))
        if captured.stderr:
            cell.outputs.append(nbformat.v4.new_output('stream',name='stderr',text=captured.stderr))
        for output in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output('display_data',data=output.data,metadata=output.metadata))
    return count


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--in-process',action='store_true')
    a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    path=root/'notebooks/research.ipynb'
    notebook=nbformat.read(path,as_version=4)
    os.chdir(root)
    if a.in_process:
        count=execute_in_process(notebook)
        print(f'Executed {count} code cells in-process (IPython; no Jupyter transport)')
    else:
        from nbclient import NotebookClient
        NotebookClient(notebook,timeout=120,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
        print('Executed with Jupyter kernel')
    nbformat.validate(notebook)
    nbformat.write(notebook,path)

if __name__=='__main__': main()
