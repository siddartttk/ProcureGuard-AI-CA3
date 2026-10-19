"""Build and verify the handoff ZIP without environments, runtime databases or drafts."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'ProcureGuard_AI_CA3_Improved_Submission.zip'
ARCHIVE_ROOT='ProcureGuard_AI_CA3_Improved'
FOLDERS=['procureguard','data','tests','.streamlit']
TOP=['app.py','README.md','requirements.txt','requirements-tested.txt','pytest.ini','launch_demo.ps1','setup.ps1','START_DEMO.cmd','.gitignore']
DOCS=['agents_and_orchestration.md','architecture_overview.png','architecture.mmd','architecture.png',
      'architecture.svg','domain_analysis.md','final_verification.md','problem_statement.md',
      'problem_statement.pdf','ProcureGuard_AI_CA3_Report.docx','requirements_traceability.md','technical_explanation.md','upgrade_plan.md','validation_report.md',
      'assets/sit_pune_official_logo.png','assets/logo_source.json']
REPORTS=['browser_smoke.json','docx_validation.json','environment-freeze.txt','evolving_case_demo.json','investigation_packets.json',
         'live_planner_run.json','presentation_validation.json','pytest-output.txt','pytest-results.xml',
         'scenario_comparison.csv','validation_v2.json','validation_v3.json']
SCRIPTS=['browser_smoke.mjs','build_deck.mjs','build_docs.py','build_docs_v3.py','build_printable.py','build_report_docx.py',
         'freeze_challenge.py','package_submission.py','render_architecture.mjs',
         'run_live_planner.py','validate.py','validate_v2.py','validate_v3.py']
PRESENTATION=['ProcureGuard_AI_CA3_Improved.pptx','slide_outline.json','5_minute_script.md','cheat_sheet.md','viva_questions.md',
              'evidence/ui_decision_crop.png']
SCREENSHOTS=['01_command_center.png','02_resolved_case.png','03_adaptive_plan.png','04_provenance.png',
             '05_controls.png','06_validation.png','07_lifecycle.png','08_revalidated_allocation.png',
             '09_recovered_case.png','10_challenge_comparison.png']


def main():
    files=[ROOT/name for name in TOP]
    for folder,names in [('docs',DOCS),('reports',REPORTS),('scripts',SCRIPTS),('presentation',PRESENTATION)]:
        files.extend(ROOT/folder/name for name in names)
    files.extend(ROOT/'presentation/slide_previews'/f'slide-{i:02d}.png' for i in range(1,9))
    files.extend(ROOT/'docs/screenshots'/name for name in SCREENSHOTS)
    for folder in FOLDERS:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts
                     and p.suffix not in ('.pyc','.sqlite') and p.name!='reviewer_events.jsonl')
    files=sorted(set(files))
    missing=[str(p) for p in files if not p.is_file()]
    if missing:raise ValueError('Missing required handoff files: '+', '.join(missing))
    # Record a portable per-file digest list. The checksum manifest excludes itself.
    manifest={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)
              if p.name!='submission_manifest.json'}
    manifest_path=ROOT/'reports/submission_manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    files=[p for p in files if p!=manifest_path]+[manifest_path]
    with ZipFile(TARGET,'w',ZIP_DEFLATED) as archive:
        for file in sorted(files):archive.write(file,Path(ARCHIVE_ROOT)/file.relative_to(ROOT))
    with ZipFile(TARGET) as archive:
        if archive.testzip() is not None:raise ValueError('ZIP integrity check failed')
        for name,expected in manifest.items():
            if hashlib.sha256(archive.read(ARCHIVE_ROOT+'/'+name)).hexdigest()!=expected:
                raise ValueError('Packaged checksum mismatch: '+name)
        assert not any('/.venv/' in n or '/runtime/' in n or '/build/' in n or n.endswith('.sqlite') for n in archive.namelist())
        assert len([n for n in archive.namelist() if n.endswith('.pptx')])==1
        assert len([n for n in archive.namelist() if n.endswith('.docx')])==1
        assert len([n for n in archive.namelist() if '/slide_previews/' in n])==8
        print(f'{TARGET}\n{len(archive.namelist())} files; {TARGET.stat().st_size:,} bytes; archive and checksums verified')


if __name__=='__main__':main()
