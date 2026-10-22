"""Run with python3 harness/tests/test_gate.py; no services or network required."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class HarnessGateTests(unittest.TestCase):
    def test_child_exit_and_summary_must_both_succeed(self):
        scenarios=[('pass','echo "TỔNG: 1 PASS / 0 FAIL / 0 WARN"; exit 0',True),
                   ('crash','exit 2',False),
                   ('lying_summary','echo "TỔNG: 1 PASS / 0 FAIL / 0 WARN"; exit 2',False),
                   ('missing_summary','exit 0',False)]
        for name,body,expected in scenarios:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                h=Path(temp)/'harness';h.mkdir()
                for file in ['lib.sh','qa.sh','run.sh']:shutil.copy2(ROOT/file,h/file)
                for component in ['smoke','be','fe','test','deploy']:
                    (h/(component+'.sh')).write_text('#!/bin/bash\n'+body+'\n')
                for runner,args in [('qa.sh',[]),('run.sh',['all'])]:
                    result=subprocess.run(['bash',str(h/runner),*args],capture_output=True,text=True)
                    self.assertEqual(result.returncode==0,expected,result.stdout)

    def test_duckdns_optional_does_not_hide_required_or_stopped_services(self):
        scenarios=[('micco-duckdns-updater','',0,'0 0 1'),
                   ('micco-duckdns-updater','',1,'0 1 0'),
                   ('micco-duckdns-updater','exited',0,'0 1 0'),
                   ('micco-duckdns-updater','running',0,'1 0 0'),
                   ('nexusrag-postgres','',0,'0 1 0')]
        for container,state,required,expected in scenarios:
            with self.subTest(container=container,state=state,required=required):
                script=f'source "{ROOT}/lib.sh"; dki(){{ echo "{state}"; }}; REQUIRE_DUCKDNS={required}; check_container {container} >/dev/null; echo "$pass $fail $warn"'
                result=subprocess.run(['bash','-c',script],capture_output=True,text=True)
                self.assertEqual(result.stdout.strip(),expected)


if __name__=='__main__':unittest.main()
