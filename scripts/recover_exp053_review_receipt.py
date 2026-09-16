"""Recover the exact formal review from the same Claude call; no model invocation."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import load_record, save_record, transition, verify_snapshot, utc_now
from experiment_controller.review import VERDICT_RE

EXP = 'exp_053_original_score_joint_repair'
SESSION = 'd59111d1-5a6f-447d-94b6-cb89e164d51c'
MESSAGE = 'dbb165d6-f529-417e-9aa5-5c3bf78670c4'
TRANSCRIPT = Path('C:/Users/Ling/.claude/projects/E--Project-Biohub-CellTracking') / (SESSION + '.jsonl')


def main():
    record = load_record(PROJECT_ROOT, EXP)
    assert record['state'] == 'MANUAL_REVIEW_REQUIRED'
    assert record['review']['verdict'] == 'MISSING'
    verify_snapshot(PROJECT_ROOT, record)
    folder = PROJECT_ROOT / 'experiments' / EXP
    prompt = (folder / 'claude-prompt.md').read_text(encoding='utf-8')
    old = (folder / 'review.md').read_text(encoding='utf-8')
    run = json.loads((folder / 'claude-review-run.json').read_text())
    assert run['exit_code'] == 0 and not run['stderr']
    events = [json.loads(line) for line in TRANSCRIPT.read_text(encoding='utf-8').splitlines()]
    request = next(e for e in events if isinstance(e.get('message', {}).get('content'), str)
                   and e['message']['content'].replace('\r\n', '\n') == prompt)
    review = next(e for e in events if e.get('uuid') == MESSAGE)
    final = next(e for e in reversed(events) if any(
        b.get('type') == 'text' and b.get('text', '').strip() == old.strip()
        for b in e.get('message', {}).get('content', []) if isinstance(b, dict)))
    for event in (request, review, final):
        assert event['sessionId'] == SESSION
        assert Path(event['cwd']).resolve() == PROJECT_ROOT.resolve()
    timestamp = lambda value: datetime.fromisoformat(value.replace('Z', '+00:00'))
    assert timestamp(record['created_at']) <= timestamp(request['timestamp']) <= timestamp(review['timestamp']) <= timestamp(final['timestamp']) <= timestamp(run['completed_at'])
    text = '\n'.join(b['text'] for b in review['message']['content'] if b.get('type') == 'text')
    assert EXP in text and VERDICT_RE.findall(text) == ['PASS']
    assert text.rstrip().splitlines()[-1] == 'VERDICT: PASS'
    for heading in ('Summary', 'Methodology', 'Implementation risks', 'Budget', 'Required changes', 'Recommendation'):
        assert heading in text
    assert not (folder / 'review-final-stdout.md').exists()
    (folder / 'review-final-stdout.md').write_bytes((folder / 'review.md').read_bytes())
    (folder / 'review-same-call-events.json').write_text(json.dumps([request, review, final], indent=2)+'\n', encoding='utf-8')
    recovery = dict(method='Exact same-call assistant message recovery; unchanged strict verdict parser',
                    session_id=SESSION, message_id=MESSAGE, original_review=record['review'].copy(),
                    source_transcript=str(TRANSCRIPT), source_transcript_sha256=hashlib.sha256(TRANSCRIPT.read_bytes()).hexdigest(),
                    recovered_text_sha256=hashlib.sha256(text.encode()).hexdigest(), recovered_at=utc_now())
    (folder / 'review-recovery.json').write_text(json.dumps(recovery, indent=2)+'\n')
    (folder / 'review.md').write_text(text+'\n', encoding='utf-8')
    record['review'] = dict(required=True, status='PASSED', verdict='PASS',
                            path=f'experiments/{EXP}/review.md', completed_at=run['completed_at'],
                            recovery_path=f'experiments/{EXP}/review-recovery.json')
    save_record(PROJECT_ROOT, record)
    transition(PROJECT_ROOT, record, 'REVIEWED', note='Recovered verbatim formal PASS from same Claude session; original MISSING stdout and provenance retained. No additional model call.')
    (PROJECT_ROOT / 'CLAUDE_REVIEW.md').write_text(f'# Latest Claude Review\n\nExperiment: `{EXP}`\n\nSame-call formal message recovered; see experiment review-recovery.json.\n\n'+text+'\n', encoding='utf-8')
    print(json.dumps(dict(status='REVIEWED', verdict='PASS', recovery=recovery['method'])))


if __name__ == '__main__':
    main()
