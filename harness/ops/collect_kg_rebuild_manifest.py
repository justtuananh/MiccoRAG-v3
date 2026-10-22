"""Collect validated per-KB offline repair manifests into one deployment input.

This performs no database or serving-directory writes. Run after every KB copy
is prepared; the deployer must still run rebuild_kg_offline.py --verify-only
under quiescence before swapping any directory.
"""
import argparse
import json
from pathlib import Path


def collect(root: Path, expected: list[int]) -> dict:
    mapping = {}
    for kb_id in expected:
        output = root / f'kb_{kb_id}'
        path = output / 'repair-manifest.json'
        manifest = json.loads(path.read_text())
        if manifest['kb_id'] != kb_id or Path(manifest['output']) != output:
            raise ValueError(f'Wrong KB/output in manifest {kb_id}')
        required = ('source_document_ids', 'source_markdown_sha256',
                    'source_files_sha256', 'rebuilt_files_sha256',
                    'backup', 'rebuilt', 'undated_document_ids')
        if any(key not in manifest for key in required):
            raise ValueError(f'Incomplete manifest {kb_id}')
        if {str(item) for item in manifest['source_document_ids']} != set(manifest['source_markdown_sha256']):
            raise ValueError(f'Document hashes do not match allowlist in KB {kb_id}')
        if manifest['source_document_ids'] != manifest['rebuilt']['document_ids']:
            raise ValueError(f'Rebuilt document IDs do not match allowlist in KB {kb_id}')
        mapping[str(kb_id)] = {
            'output': str(output),
            'backup': manifest['backup'],
            'document_ids': manifest['source_document_ids'],
            'source_markdown_sha256': manifest['source_markdown_sha256'],
            'source_files_sha256': manifest['source_files_sha256'],
            'rebuilt_files_sha256': manifest['rebuilt_files_sha256'],
            'undated_document_ids': manifest['undated_document_ids'],
            'serving_eligible_at_build': manifest['serving_eligible'],
            'verified_empty': manifest['verified_empty'],
            'rebuilt': manifest['rebuilt'],
        }
    actual = {int(p.name[3:]) for p in root.glob('kb_*') if p.is_dir() and p.name[3:].isdigit()}
    if actual != set(expected):
        raise ValueError(f'Prepared KB set mismatch: expected {sorted(expected)}, got {sorted(actual)}')
    return {'schema_version': 1, 'source': 'separate offline KG repair copies',
            'requires_quiesced_verify_only': True, 'knowledge_bases': mapping}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--kb-ids', type=int, nargs='+', required=True)
    args = parser.parse_args()
    result = collect(args.root.resolve(), args.kb_ids)
    target = args.root / 'manifest.json'
    if target.exists():
        raise FileExistsError('Aggregate manifest already exists')
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    print(json.dumps({'manifest': str(target),
                      'kb_ids': sorted(map(int, result['knowledge_bases'])),
                      'document_count': sum(len(item['document_ids']) for item in result['knowledge_bases'].values())}))


if __name__ == '__main__':
    main()
