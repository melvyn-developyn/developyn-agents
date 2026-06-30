from pathlib import Path

from .database import Database
from .quickbooks_client import QuickBooksClient

VAT_TO_QB_TAX_CODE = {
    'standard': 'T1',
    'reduced': 'T1',
    'zero_rated': 'T2',
    'exempt': 'T3',
    'outside_scope': 'T7',
    'reverse_charge': 'T8',
    'no_vat': 'T9',
    'unknown': 'T1',
}


class Reconciler:
    def __init__(self, qb_client: QuickBooksClient, db: Database):
        self.qb_client = qb_client
        self.db = db

    def reconcile_approved_matches(self, interactive: bool = True) -> dict:
        summary = {
            'reconciled': 0,
            'failed': 0,
            'uploaded': 0,
            'categories_updated': 0,
            'vat_codes_set': 0,
            'details': []
        }
        
        approved_matches = self.db.get_approved_matches_for_reconciliation()
        
        if not approved_matches:
            return summary
        
        if interactive:
            accounts = self.qb_client.get_accounts()
            account_map = {a['Name']: a['Id'] for a in accounts}
        
        for match_row in approved_matches:
            if not match_row['approved']:
                continue
            
            transaction_id = match_row['qb_transaction_id']
            attachment_path = match_row['attachment_path']
            vat_type = match_row['vat_type']
            
            print(f"\nProcessing: {match_row['payee_name']} | £{match_row['txn_amount']:.2f}")
            
            if vat_type:
                qb_tax_code = VAT_TO_QB_TAX_CODE.get(vat_type, 'T1')
                print(f"  VAT type: {vat_type} → QuickBooks tax code: {qb_tax_code}")
                
                if self.qb_client.token:
                    success = self.qb_client.update_transaction_tax_code(transaction_id, qb_tax_code)
                    if success:
                        summary['vat_codes_set'] += 1
                        print(f"  ✓ Tax code set to: {qb_tax_code}")
            
            if interactive and accounts:
                print(f"  Current category: {match_row['memo'] or 'N/A'}")
                print(f"  Available categories:")
                for i, name in enumerate(sorted(account_map.keys())[:20], 1):
                    print(f"    {i}. {name}")
                
                choice = input("\nChange category? (enter number or skip): ").strip()
                if choice.isdigit():
                    category_list = sorted(account_map.keys())[:20]
                    if int(choice) <= len(category_list):
                        selected_category = category_list[int(choice) - 1]
                        account_id = account_map[selected_category]
                        success = self.qb_client.update_transaction_category(transaction_id, account_id)
                        if success:
                            summary['categories_updated'] += 1
                            print(f"  ✓ Category updated to: {selected_category}")
            
            if attachment_path and Path(attachment_path).exists():
                file_name = Path(attachment_path).name
                if self.qb_client.token:
                    success = self.qb_client.upload_attachment(transaction_id, attachment_path, file_name)
                    if success:
                        summary['uploaded'] += 1
                        print(f"  ✓ PDF uploaded: {file_name}")
                else:
                    print(f"  ⚠ PDF upload skipped (CSV mode): {file_name}")
            
            if self.qb_client.token:
                success = self.qb_client.mark_as_reconciled(transaction_id)
                
                if success:
                    self.db.update_transaction_status(transaction_id, 'reconciled')
                    summary['reconciled'] += 1
                    summary['details'].append({
                        'transaction_id': transaction_id,
                        'status': 'reconciled'
                    })
                    print(f"  ✓ Marked as reconciled")
                else:
                    print(f"  ⚠ Creating categorized expense instead...")
                    result = self.qb_client.create_categorized_expense(
                        txn_date=str(match_row['txn_date']),
                        amount=float(match_row['txn_amount']),
                        vendor_name=match_row['payee_name'][:100],
                        account_id='7',
                        tax_code=VAT_TO_QB_TAX_CODE.get(vat_type, 'T1'),
                        attachment_path=attachment_path
                    )
                    if result:
                        self.db.update_transaction_status(transaction_id, 'reconciled')
                        summary['reconciled'] += 1
                        print(f"  ✓ Expense created in QuickBooks")
                    else:
                        summary['failed'] += 1
                        print(f"  ✗ Failed to categorize")
            else:
                self.db.update_transaction_status(transaction_id, 'reconciled')
                summary['reconciled'] += 1
                summary['details'].append({
                    'transaction_id': transaction_id,
                    'status': 'reconciled (CSV mode)'
                })
                print(f"  ✓ Marked as reconciled (CSV mode)")
        
        return summary
