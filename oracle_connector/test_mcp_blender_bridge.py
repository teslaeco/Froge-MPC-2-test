"""CI-only MCP transport to real local Blender; never installed on Oracle.

Only the deterministic smoke scene is used. Production keeps its Podman sandbox.
"""
import json
from pathlib import Path
import subprocess
import sys
from blender_mcp import JobTools, serve

if __name__=='__main__':
    folder=Path(sys.argv[1]).resolve();binary=Path(sys.argv[2]).resolve()
    runtime=Path(__file__).resolve().parent/'runtime'
    def blender(candidate,finalize=False):
        expression=('import sys;from pathlib import Path;sys.path.insert(0,'+repr(str(runtime))+');'
                    +('from finalize import finalize;finalize' if finalize else 'from run import execute_job;execute_job')
                    +'(Path('+repr(str(candidate))+'))')
        with (candidate/('fixture-finalize.log' if finalize else 'fixture-build.log')).open('wb') as log:
            subprocess.run([str(binary),'--background','--factory-startup','-t','2','--python-exit-code','1',
                            '--python-expr',expression],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=160)
    serve(JobTools(folder,build=lambda p:blender(p),finalize=lambda p:blender(p,True)))
