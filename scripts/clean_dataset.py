#!/usr/bin/env python3
"""
Clean TarotCLI dataset: Remove redundant fields added in previous iteration.

Removes:
- keywords: Arbitrary extraction from upright_meaning (not from source)
- arcana: Duplicates 'type' field
- dataset_version: Unnecessary metadata for static dataset
"""
import json
from pathlib import Path

def clean_dataset(input_path: Path, output_path: Path) -> None:
    """Remove redundant fields from JSONL dataset."""
    
    cards_processed = 0
    fields_removed = {'keywords': 0, 'arcana': 0, 'dataset_version': 0}
    
    with open(input_path, 'r') as f_in, open(output_path, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            try:
                card = json.loads(line)
                
                # Track and remove redundant fields
                for field in ['keywords', 'arcana', 'dataset_version']:
                    if field in card:
                        card.pop(field)
                        fields_removed[field] += 1
                
                # Write cleaned card
                f_out.write(json.dumps(card) + '\n')
                cards_processed += 1
                
            except json.JSONDecodeError as e:
                print(f"Error on line {line_num}: {e}")
                raise
    
    # Summary
    print(f"✓ Processed {cards_processed} cards")
    print(f"✓ Removed {fields_removed['keywords']} keywords fields")
    print(f"✓ Removed {fields_removed['arcana']} arcana fields")
    print(f"✓ Removed {fields_removed['dataset_version']} dataset_version fields")
    print(f"✓ Cleaned dataset: {output_path}")

if __name__ == "__main__":
    # Paths
    data_dir = Path(__file__).parent.parent / "data"
    input_file = data_dir / "tarot_cards_RW.jsonl"
    backup_file = data_dir / "tarot_cards_RW.jsonl.bak"
    temp_file = data_dir / "tarot_cards_RW_cleaned.jsonl"
    
    # Backup original
    print(f"Creating backup: {backup_file}")
    import shutil
    shutil.copy2(input_file, backup_file)
    
    # Clean dataset
    clean_dataset(input_file, temp_file)
    
    # Verify cleaned file
    with open(temp_file) as f:
        card_count = sum(1 for _ in f)
    
    if card_count != 78:
        print(f"✗ Error: Expected 78 cards, got {card_count}")
        print(f"  Backup preserved at: {backup_file}")
        exit(1)
    
    # Replace original with cleaned version
    temp_file.replace(input_file)
    print(f"\n✓ Dataset cleaned successfully")
    print(f"  Original backed up to: {backup_file}")
    print(f"  Cleaned version at: {input_file}")