# orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import PurchaseOrder, PurchaseOrderItem
from .forms import PurchaseOrderForm, get_purchase_order_item_formset
from products.models import Products
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def purchase_order_create(request):
    FormSet = get_purchase_order_item_formset(extra=1)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = FormSet(request.POST, instance=form.instance, prefix='form')

        if form.is_valid() and formset.is_valid():
            purchase_order = form.save(commit=False)
            purchase_order.created_at = timezone.now()
            purchase_order.updated_at = timezone.now()
            purchase_order.save()

            for form in formset:
                if form.cleaned_data and form.cleaned_data.get('product'):
                    item = form.save(commit=False)
                    item.purchase_order = purchase_order
                    item.product = form.cleaned_data['product']
                    item.save()
            formset.save()

            # PDF и email
            pdf_content = generate_purchase_order_pdf(purchase_order)
            email = EmailMessage(
                subject=f'Purchase Order {purchase_order.po_number} from MS Cosmotrade Limited',
                body=f'Dear {purchase_order.supplier.legal_name},\n\nPlease find attached the Purchase Order {purchase_order.po_number}.\n\nBest regards,\nMS Cosmotrade Limited',
                from_email='office@cosmotrade-ms.com',
                to=[purchase_order.supplier.email or 'office@cosmotrade-ms.com'],
            )
            email.attach(f'PO-{purchase_order.po_number}.pdf', pdf_content, 'application/pdf')
            email.send()

            messages.success(request, f'Purchase Order {purchase_order.po_number} created and sent!')
            return redirect('orders:purchase_order_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseOrderForm(initial={
            'delivery_address': 'Aiolou 8, Kokkonis Complex, Block F, App 302, Germasogeia, 4041, Cyprus',
            'contact_person': 'Dr Sofiia Myliushko +357 99779776'
        })
        formset = FormSet(instance=None, prefix='form')

    return render(request, 'purchase_order_form.html', {
        'form': form,
        'formset': formset,
    })


def purchase_order_list(request):
    purchase_orders = PurchaseOrder.objects.all()
    return render(request, 'purchase_order_list.html', {
        'purchase_orders': purchase_orders,
    })

def purchase_order_detail(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    items = purchase_order.items.all()
    return render(request, 'purchase_order_detail.html', {
        'purchase_order': purchase_order,
        'items': items,
    })

def purchase_order_edit(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    FormSet = get_purchase_order_item_formset(extra=0)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=purchase_order)
        formset = FormSet(request.POST, instance=purchase_order, prefix='form')

        if form.is_valid() and formset.is_valid():
            purchase_order = form.save()
            for form in formset:
                if form.cleaned_data and form.cleaned_data.get('product'):
                    item = form.save(commit=False)
                    item.purchase_order = purchase_order
                    item.product = form.cleaned_data['product']
                    item.save()
            formset.save()
            messages.success(request, f'Purchase Order {purchase_order.po_number} updated successfully!')
            return redirect('orders:purchase_order_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseOrderForm(instance=purchase_order)
        formset = FormSet(instance=purchase_order, prefix='form')

    return render(request, 'purchase_order_form.html', {
        'form': form,
        'formset': formset,
        'purchase_order': purchase_order,
    })


def purchase_order_delete(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    if request.method == 'POST':
        purchase_order.delete()
        messages.success(request, f'Purchase Order {purchase_order.po_number} deleted successfully!')
        return redirect('orders:purchase_order_list')
    return redirect('orders:purchase_order_list')

def generate_purchase_order_pdf(purchase_order):
    items = purchase_order.items.all()
    html_string = render_to_string('purchase_order_pdf.html', {
        'purchase_order': purchase_order,
        'items': items,
        'current_date': timezone.now().date(),
    })
    pdf_file = HTML(string=html_string, base_url=str(BASE_DIR)).write_pdf()
    return pdf_file

def purchase_order_pdf(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    pdf_content = generate_purchase_order_pdf(purchase_order)

    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="PO-{purchase_order.po_number}.pdf"'
    return response

def purchase_order_send_email(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=po_id)
    pdf_content = generate_purchase_order_pdf(purchase_order)

    email = EmailMessage(
        subject=f'Purchase Order {purchase_order.po_number} from MS Cosmotrade Limited',
        body=f'Dear {purchase_order.supplier.legal_name},\n\nPlease find attached the Purchase Order {purchase_order.po_number}.\n\nBest regards,\nMS Cosmotrade Limited',
        from_email='office@cosmotrade-ms.com',
        to=[purchase_order.supplier.email or 'office@cosmotrade-ms.com'],
    )
    email.attach(f'PO-{purchase_order.po_number}.pdf', pdf_content, 'application/pdf')
    email.send()

    messages.success(request, f'Purchase Order {purchase_order.po_number} has been sent to {purchase_order.supplier.email or "office@cosmotrade-ms.com"}!')
    return redirect('orders:purchase_order_detail', po_id=po_id)