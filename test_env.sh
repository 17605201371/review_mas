#!/bin/bash
export DRMAS_DIAGPENDING_RECOVERY=1
python3 -c "import os; print('DRMAS_DIAGPENDING_RECOVERY:', os.environ.get('DRMAS_DIAGPENDING_RECOVERY'))"
