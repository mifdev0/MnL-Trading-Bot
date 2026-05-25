import sys
import os
sys.path.append(os.getcwd())

from database import SessionLocal
from models.position import Position

db = SessionLocal()
try:
    # Get all open FIDA positions
    fida_positions = db.query(Position).filter(
        Position.pair.like('%FIDA%'),
        Position.status.in_(['OPEN', 'BE', 'TRAILING'])
    ).order_by(Position.id.asc()).all()
    
    if len(fida_positions) > 1:
        # Keep the first one, delete the rest
        to_delete = fida_positions[1:]
        for p in to_delete:
            print(f'Deleting duplicate position ID {p.id} for {p.pair}')
            db.delete(p)
        db.commit()
        print(f'Successfully deleted {len(to_delete)} duplicates.')
    else:
        print('No duplicates found.')
finally:
    db.close()
