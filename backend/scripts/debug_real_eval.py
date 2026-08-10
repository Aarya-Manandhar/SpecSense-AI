from pathlib import Path
import json
from app.api import endpoints

if __name__ == '__main__':
    d = endpoints._compute_real_evaluation()
    out = {
        'rows_evaluated': d.get('rows_evaluated'),
        'counts': d.get('counts'),
        'by_source_keys': list(d.get('by_source', {}).keys()),
        'metrics_by_source_keys': list(d.get('metrics_by_source', {}).keys()),
        'eirene_metrics_sample': d.get('metrics_by_source', {}).get('eirene')
    }
    print(json.dumps(out, indent=2))
