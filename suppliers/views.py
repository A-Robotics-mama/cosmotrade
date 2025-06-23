# suppliers/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import Suppliers
from django_countries import countries

def supplier_list(request):
    suppliers = Suppliers.objects.all()
    return render(request, 'suppliers_list.html', {'suppliers': suppliers})

def supplier_create(request):
    if request.method == 'POST':
        legal_name = request.POST.get('legal_name')
        country = request.POST.get('country')
        str_address = request.POST.get('str_address')
        bank = request.POST.get('bank')
        bank_address = request.POST.get('bank_address')
        bic = request.POST.get('bic')
        bank_acc = request.POST.get('bank_acc')
        supplier_code = request.POST.get('supplier_code')
        phone = request.POST.get('phone')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        instagram = request.POST.get('instagram')
        web = request.POST.get('web')
        contact_person = request.POST.get('contact_person')
        notes = request.POST.get('notes')

        try:
            supplier = Suppliers(
                legal_name=legal_name,
                country=country,
                str_address=str_address,
                bank=bank,
                bank_address=bank_address,
                bic=bic,
                bank_acc=bank_acc,
                supplier_code=supplier_code,
                phone=phone,
                mobile=mobile,
                email=email,
                instagram=instagram,
                web=web,
                contact_person=contact_person,
                notes=notes
            )
            supplier.save()
            messages.success(request, 'Supplier added successfully!')
            return redirect('suppliers:supplier_list')
        except Exception as e:
            messages.error(request, f'Error adding supplier: {str(e)}')

    return render(request, 'supplier_form.html', {})

def supplier_edit(request, supplier_id):
    supplier = get_object_or_404(Suppliers, supplier_id=supplier_id)
    if request.method == 'POST':
        supplier.legal_name = request.POST.get('legal_name')
        supplier.country = request.POST.get('country')
        supplier.str_address = request.POST.get('str_address')
        supplier.bank = request.POST.get('bank')
        supplier.bank_address = request.POST.get('bank_address')
        supplier.bic = request.POST.get('bic')
        supplier.bank_acc = request.POST.get('bank_acc')
        supplier.supplier_code = request.POST.get('supplier_code')
        supplier.phone = request.POST.get('phone')
        supplier.mobile = request.POST.get('mobile')
        supplier.email = request.POST.get('email')
        supplier.instagram = request.POST.get('instagram')
        supplier.web = request.POST.get('web')
        supplier.contact_person = request.POST.get('contact_person')
        supplier.notes = request.POST.get('notes')

        try:
            supplier.save()
            messages.success(request, 'Supplier updated successfully!')
            return redirect('suppliers:supplier_list')
        except Exception as e:
            messages.error(request, f'Error updating supplier: {str(e)}')

    return render(request, 'suppliers_edit.html', {'supplier': supplier})

def country_autocomplete(request):
    term = request.GET.get('term', '').strip()
    if term:
        matching_countries = [
            {'id': code, 'label': name}
            for code, name in countries
            if term.lower() in name.lower()
        ]
    else:
        matching_countries = [
            {'id': code, 'label': name}
            for code, name in countries
        ]
    return JsonResponse(matching_countries, safe=False)