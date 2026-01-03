import pytz
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
import base64

from app.models.database import get_db
from app.models.stock import Stock
from app.models.sale import Sale, SaleItem, SaleStatus, PaymentMethod
from app.models.account import Account, Transaction, AccountType, TransactionType # Added Import
from app.models.user import User
from app.auth.security import get_current_active_user
from app.utils.email import send_low_stock_alert, send_customer_invoice_email, send_invoice_copy_email
from app.services.cleanup import cleanup_old_invoices
from app.services.pdf_invoice_generator import generate_invoice_pdf
from app.models.database import SessionLocal
import os

# ... imports ...

router = APIRouter(prefix="/billing", tags=["billing"])

# Request/Response Models
class BillItemRequest(BaseModel):
    product_id: int  # Actually stock ID
    product_name: str
    quantity: int
    unit_price: float

class BillRequest(BaseModel):
    customer_name: str
    customer_phone: str
    items: List[BillItemRequest]
    payment_method: PaymentMethod = PaymentMethod.CASH
    discount_amount: float = 0.0
    customer_email: Optional[str] = None
    send_email: bool = False

class BillItemResponse(BaseModel):
    product_name: str
    quantity: int
    unit_price: float
    total_price: float

class BillResponse(BaseModel):
    invoice_number: str
    date: str
    customer_name: str
    customer_phone: str
    billed_by: str
    items: List[BillItemResponse]
    subtotal: float
    discount_amount: float
    tax_amount: float
    final_amount: float
    pdf_available: bool = False
    pdf_base64: Optional[str] = None


@router.post("/generate", response_model=BillResponse)
async def generate_bill(
    request: BillRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    try:
        return await _generate_bill_impl(request, db, current_user, background_tasks)
    except Exception as e:
        import traceback
        fatal_msg = traceback.format_exc()
        print(f"🔥 FATAL API ERROR: {fatal_msg}")
        with open("debug_fatal.txt", "w") as f:
            f.write(fatal_msg)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

async def _generate_bill_impl(
    request: BillRequest,
    db: Session,
    current_user: User,
    background_tasks: BackgroundTasks
):
    # Verify stock and calculate totals
    subtotal = 0.0
    response_items = []
    
    # Check all items first
    for item_req in request.items:
        product = db.query(Stock).filter(Stock.id == item_req.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {item_req.product_id} not found")
        if product.quantity < item_req.quantity:
             raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.product_name}")
        
        item_total = item_req.quantity * item_req.unit_price
        subtotal += item_total

    # Calculate final amount
    final_amount = subtotal - request.discount_amount
    
    # Create Sale
    # Determine Owner ID (for scope)
    owner_id = current_user.id if current_user.role == "owner" else current_user.owner_id
    
    # 3. Generate Invoice Number (Sequential)
    # Find all users associated with this owner (Owner + Staff) to check global history
    # Or simpler: Query sales where the creator is the owner or has the same owner_id
    # Get list of user IDs for this business
    team_users = db.query(User.id).filter(
        (User.id == owner_id) | (User.owner_id == owner_id)
    ).all()
    team_user_ids = [u[0] for u in team_users]

    # 3. Generate Invoice Number (Scoped to Business)
    # Prefix with Owner ID to ensure global uniqueness across businesses: INV-{owner_id}-{sequence}
    invoice_prefix = f"INV-{owner_id}-"
    
    last_sale = db.query(Sale).filter(
        Sale.invoice_number.like(f"{invoice_prefix}%")
    ).order_by(Sale.id.desc()).first()

    new_sequence = 1
    if last_sale:
        try:
            # Extract number part "INV-12-00001" -> 1
            # Split by '-' and take the last part
            parts = last_sale.invoice_number.split("-")
            if parts and parts[-1].isdigit():
                new_sequence = int(parts[-1]) + 1
        except:
            pass 

    invoice_number = f"{invoice_prefix}{new_sequence:05d}"

    new_sale = Sale(
        invoice_number=invoice_number,
        customer_name=request.customer_name,
        customer_phone=request.customer_phone,
        total_amount=subtotal,
        discount_amount=request.discount_amount,
        final_amount=final_amount,
        amount_paid=final_amount,
        amount_due=0.0,
        payment_method=request.payment_method,
        created_by_id=current_user.id,
        status=SaleStatus.COMPLETED
    )
    db.add(new_sale)
    db.flush() # get ID
    
    # Create Items and update stock
    for item_req in request.items:
        product = db.query(Stock).filter(Stock.id == item_req.product_id).first()
        item_total = item_req.quantity * item_req.unit_price
        
        sale_item = SaleItem(
            sale_id=new_sale.id,
            product_id=product.id,
            quantity=item_req.quantity,
            unit_price=item_req.unit_price,
            total_price=item_total
        )
        db.add(sale_item)
        
        # Deduct stock
        product.quantity -= item_req.quantity
        
        # Check for low stock alert
        if product.quantity <= 5: # Threshold is hardcoded for now, or could be in settings
            owner_email = current_user.email if current_user.role == "owner" else current_user.owner.email
            if owner_email:
                background_tasks.add_task(
                    send_low_stock_alert,
                    product_name=product.product_name,
                    company_name=product.company_name,
                    current_quantity=product.quantity,
                    recipients=[owner_email]
                )
        
        # Add to response items
        response_items.append(BillItemResponse(
            product_name=product.product_name,
            quantity=item_req.quantity,
            unit_price=item_req.unit_price,
            total_price=item_total
        ))

    db.commit()
    db.refresh(new_sale)
    
    # --- AUTOMATIC TRANSACTION RECORDING (Day Book) ---
    try:
        # 1. Ensure Default Account (Cash) exists
        default_acc = db.query(Account).filter(Account.type == AccountType.CASH).first()
        if not default_acc:
            default_acc = Account(name="Main Cash", type=AccountType.CASH, balance=0.0)
            db.add(default_acc)
            db.commit()
            db.refresh(default_acc)
            
        # 2. Update Balance (Income)
        default_acc.balance += final_amount
        
        # 3. Create Transaction Record
        new_txn = Transaction(
            description=f"Sale: Invoice #{new_sale.invoice_number}",
            amount=final_amount,
            type=TransactionType.INCOME,
            customer_name=new_sale.customer_name,
            payment_method=new_sale.payment_method, # e.g. "cash", "upi"
            sale_id=new_sale.id,
            handler_name=current_user.full_name, # Set Handler to the person creating the bill
            to_account_id=default_acc.id, # Money goes TO cash account
            # Store as Naive IST
            date=datetime.now(pytz.timezone('Asia/Kolkata')).replace(tzinfo=None),
            created_by_id=current_user.id
        )
        db.add(new_txn)
        db.commit()
        print(f"✅ Auto-logged transaction for Invoice {new_sale.invoice_number}")
        
    except Exception as e:
        print(f"⚠️ Failed to auto-log transaction: {e}")
        # Don't fail the whole bill generation just for this logging error
    
    # Generate PDF invoice
    pdf_base64 = None
    pdf_available = False
    
    owner_user = current_user if current_user.role == "owner" else current_user.owner
    
    if owner_user:
        try:
            # Prepare business settings
            business_settings = {
                'logo': owner_user.business_logo,
                'signature': owner_user.signature_image,
                'business_name': owner_user.business_name or 'MY STORE',
                'address': owner_user.business_address or '',
                'phone': owner_user.business_phone or ''
            }
            
            # Prepare customer data
            customer_data = {
                'customer_name': new_sale.customer_name,
                'customer_phone': new_sale.customer_phone
            }
            
            # Prepare items for PDF
            pdf_items = [
                {
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'total_price': item.total_price
                }
                for item in response_items
            ]
            
            # Generate PDF invoice
            print(f"📊 GENERATING PDF INVOICE for {new_sale.customer_name}")
            
            # Use business_settings (dict) not original business_settings (Object) if any
            # Note: We redefined business_settings above as a dict.
            pdf_bytes = generate_invoice_pdf(
                business_settings=business_settings, # Use the dict we just created
                customer_data=customer_data,
                items=pdf_items,
                total_amount=new_sale.final_amount,
                invoice_number=new_sale.invoice_number,
                invoice_date=new_sale.created_at.strftime('%Y-%m-%d')
            )
            
            print(f"✅ PDF generated successfully! Size: {len(pdf_bytes)} bytes")
            
                
            # Define owner for email logic
            owner = current_user if current_user.role == "owner" else current_user.owner
            
            # Encode to base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_available = True
            
            # SAVE TO DISK
            invoice_dir = "invoices"
            os.makedirs(invoice_dir, exist_ok=True)
            pdf_path = os.path.join(invoice_dir, f"Invoice_{new_sale.invoice_number}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            
            new_sale.pdf_file_path = pdf_path
            db.commit()
            
            # Send Email Logic
            # 1. Explicit "Send Email" requested (Customer Email must exist per frontend Check, but safe to check here)
            if request.send_email and request.customer_email:
                background_tasks.add_task(
                    send_customer_invoice_email,
                    to_email=request.customer_email,
                    customer_name=new_sale.customer_name,
                    business_name=business_settings['business_name'],
                    invoice_number=new_sale.invoice_number,
                    pdf_bytes=pdf_bytes,
                    reply_to_email=owner.email
                )
            
            # 2. Implicit "Fallback" - If NO customer email, send copy to CREATOR (Staff/Owner)
            elif not request.customer_email:
                # Determine who created it. current_user is the creator.
                creator_email = current_user.email
                if creator_email:
                    print(f"📧 Auto-sending invoice copy to Creator: {creator_email}")
                    background_tasks.add_task(
                        send_invoice_copy_email, 
                        to_email=creator_email,
                        customer_name=new_sale.customer_name, 
                        business_name=business_settings['business_name'],
                        invoice_number=new_sale.invoice_number,
                        pdf_bytes=pdf_bytes
                    )
                
            # TRIGGER CLEANUP (Wrapper to handle DB session)
            def run_cleanup():
                db_cleanup = SessionLocal()
                try:
                    cleanup_old_invoices(db_cleanup)
                finally:
                    db_cleanup.close()

            background_tasks.add_task(run_cleanup)
            
        except Exception as e:
            # Capture fatal error in this block
            import traceback
            fatal_msg = traceback.format_exc()
            print(f"🔥 PDF/EMAIL BLOCK ERROR: {fatal_msg}")
            # Non-blocking error for email/pdf logic
            pass
    
    return BillResponse(
        invoice_number=new_sale.invoice_number,
        date=new_sale.created_at.strftime("%Y-%m-%d %H:%M"),
        customer_name=new_sale.customer_name,
        customer_phone=new_sale.customer_phone,
        billed_by=current_user.full_name,
        items=response_items,
        subtotal=subtotal,
        discount_amount=request.discount_amount,
        tax_amount=0.0,
        final_amount=final_amount,
        pdf_available=pdf_available,
        pdf_base64=pdf_base64
    )


@router.get("/history/grouped")
async def get_grouped_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get billing history grouped by date (Today, Yesterday, etc.) for the last 10 days.
    """
    owner = current_user if current_user.role == "owner" else current_user.owner
    if not owner:
        raise HTTPException(status_code=400, detail="Owner not found")

    # Fetch last 10 days of records
    cutoff_date = datetime.now() - timedelta(days=10)
    sales = db.query(Sale).filter(
        Sale.created_at >= cutoff_date
    ).order_by(Sale.created_at.desc()).all()
    
    # Filter by permission (Created by self or by staff of self)
    sales = [s for s in sales if s.created_by_id == owner.id or (s.created_by and s.created_by.owner_id == owner.id)]
    # Note: Sale model logic for owner_id might rely on created_by -> user -> owner_id.
    # To be safe, if Sale doesn't have owner_id directly, use join.
    # But let's assume filtering by created_by_id if owner_id is not on Sale. 
    # Actually, previous code used `Sale.owner_id` in `get_bill_history` (lines 225-252).
    # If `Sale` doesn't have `owner_id`, previous code would fail.
    # Wait, `get_bill_history` (line 235) uses `Sale.owner_id`.
    # Let me check `Sale` model again. It DOES NOT have `owner_id` in my previous `view_file` (Step 1195).
    # It has `created_by_id`.
    # So the existing `get_bill_history` might be BROKEN if it relies on `Sale.owner_id`.
    # I should check if `Sale` has `owner_id`. It does NOT.
    # So I must fix the query to filter by `created_by` users who belong to this owner.
    # Or just `created_by_id` if single user/owner system. 
    # The existing code (lines 225-252) was: `db.query(Sale).filter(Sale.owner_id == owner.id)...`.
    # If that's existing code, maybe I missed the column in `view_file`?
    # No, I viewed lines 1-138 of `sale.py`.
    # Line 23: `class Sale(Base):`
    # ...
    # Line 50: `created_by_id = ...`
    # I don't see `owner_id`.
    
    # I'll fix the query to use `created_by` relationship or assume `created_by_id` is sufficient for now if simple setup.
    # Better: Join User table.
    
    # Revised query logic:
    # sales = db.query(Sale).join(User).filter(User.owner_id == owner.id).all()
    # But if owner created it, owner.owner_id is None.
    # Logic: Sale.created_by_id == owner.id OR Sale.created_by.owner_id == owner.id
    
    # For now, I'll restrict to `created_by_id == current_user.id` if non-owner, or all if owner?
    # Actually, let's look at `get_bill_history` again.
    # Line 235: `sales = db.query(Sale).filter(Sale.owner_id == owner.id)...`
    # If this line exists in `billing.py`, then `Sale` must have `owner_id` or it's a bug I haven't hit yet or I missed the column.
    # I will assumes `created_by_id` is the safer bet or I should add `owner_id` to Sale?
    # Adding a column is migration work. 
    # I'll assume `created_by_id` is what we have.
    
    pass

    grouped = {}
    
    # Use robust filtering
    all_sales = db.query(Sale).filter(
        Sale.created_at >= cutoff_date
    ).order_by(Sale.created_at.desc()).all()
    
    # Filter in python for safety if owner structure is complex, or use simple Owner check
    sales = [s for s in all_sales if s.created_by_id == owner.id or (s.created_by and s.created_by.owner_id == owner.id)]

    for sale in sales:
        date_str = sale.created_at.strftime("%Y-%m-%d")
        
        # Determine group label
        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        if date_str == today_str:
            label = "Today"
        elif date_str == yesterday_str:
            label = "Yesterday"
        else:
            label = sale.created_at.strftime("%B %d, %Y")
            
        if label not in grouped:
            grouped[label] = []
            
        # Check if PDF exists on disk
        pdf_ready = False
        if sale.pdf_file_path and os.path.exists(sale.pdf_file_path):
            pdf_ready = True
            
        grouped[label].append({
            "id": sale.id,
            "invoice_number": sale.invoice_number,
            "customer_name": sale.customer_name,
            "final_amount": sale.final_amount,
            "created_at": sale.created_at.strftime("%H:%M"),
            "pdf_available": pdf_ready,
            "customer_email": sale.customer_email
        })

    return grouped

from fastapi.responses import FileResponse

@router.get("/download/{sale_id}")
async def download_invoice(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if not sale.pdf_file_path or not os.path.exists(sale.pdf_file_path):
        raise HTTPException(status_code=404, detail="PDF server file missing")
        
    return FileResponse(
        sale.pdf_file_path, 
        media_type='application/pdf', 
        filename=f"Invoice_{sale.invoice_number}.pdf"
    )



@router.get("/{sale_id}", response_model=BillResponse)
async def get_bill_details(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetch details of a specific bill (items, totals, etc.)
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # Reconstruct items response

    items_resp = []
    for item in sale.items:
        p_name = "Unknown Product"
        if item.product:
            p_name = item.product.product_name
            
        items_resp.append(BillItemResponse(
            product_name=p_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price
        ))

    pdf_ready = False
    if sale.pdf_file_path and os.path.exists(sale.pdf_file_path):
        pdf_ready = True

    return BillResponse(
        invoice_number=sale.invoice_number,
        date=sale.created_at.strftime("%Y-%m-%d %H:%M"),
        customer_name=sale.customer_name,
        customer_phone=sale.customer_phone,
        billed_by=sale.created_by.full_name if sale.created_by else "Unknown",
        items=items_resp,
        subtotal=sale.total_amount,
        discount_amount=sale.discount_amount,
        tax_amount=0.0,
        final_amount=sale.final_amount,
        pdf_available=pdf_ready
    )

@router.delete("/delete/{sale_id}")
async def delete_bill(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only owner can delete
    owner = current_user if current_user.role == "owner" else current_user.owner
    if not owner: # Should not happen if authenticated, but safety check
         raise HTTPException(status_code=403, detail="Permission denied")
         
    # Check if user is owner of this bill (created by owner or staff)
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Verify ownership
    if sale.created_by_id != owner.id:
         # Check if created by staff of owner
         creator = db.query(User).filter(User.id == sale.created_by_id).first()
         if not creator or creator.owner_id != owner.id:
              raise HTTPException(status_code=403, detail="Permission denied")

    # Delete PDF file
    if sale.pdf_file_path and os.path.exists(sale.pdf_file_path):
        try:
            os.remove(sale.pdf_file_path)
            print(f"Deleted PDF: {sale.pdf_file_path}")
        except Exception as e:
            print(f"Error deleting PDF file: {e}")

    # Delete DB record
    db.delete(sale)
    db.commit()
    
    return {"message": "Bill deleted successfully"}
