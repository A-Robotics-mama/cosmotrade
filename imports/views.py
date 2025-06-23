# imports/views.py
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db import connection
from django.urls import reverse
from datetime import datetime
from decimal import Decimal
from django.db.models import F
from stock.models import Stock
from suppliers.models import Suppliers
from .models import Imports
from .forms import ImportsForm
import logging

logger = logging.getLogger(__name__)

def import_autocomplete(request):
    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse([], safe=False)
    stocks = Stock.objects.filter(
        product_id=product_id,
        stock_in__gt=F('stock_out')
    ).select_related('import_id__supplier')
    results = [
        {
            'import_id': stock.import_id.import_id,
            'label': f"Import {stock.import_id.import_id} (Supplier: {stock.import_id.supplier.legal_name} [{stock.import_id.supplier.supplier_code}], Stock: {stock.stock_in - stock.stock_out})"
        }
        for stock in stocks
    ]
    return JsonResponse(results, safe=False)

def import_new(request):
    if request.method == 'POST':
        form = ImportsForm(request.POST)
        if form.is_valid():
            import_obj = form.save()
            return redirect('imports:import_list')
        else:
            return render(request, 'import_new.html', {
                'form': form,
                'error': 'Please correct the errors below.'
            })

    form = ImportsForm()
    return render(request, 'import_new.html', {
        'form': form
    })

def import_edit(request):
    if request.method == 'POST':
        if 'edit' in request.POST:
            import_id = request.POST.get('import_id')
            supplier_code = request.POST.get('supplier_code', '').strip()
            if not import_id:
                supplier_name = ''
                if supplier_code:
                    try:
                        supplier = Suppliers.objects.get(supplier_code=supplier_code)
                        supplier_name = f"{supplier.legal_name} ({supplier.supplier_code})"
                    except Suppliers.DoesNotExist:
                        supplier_name = ''
                return render(request, 'import_edit.html', {
                    'error': 'Please select an import to edit.',
                    'imports': Imports.objects.all().select_related('supplier'),
                    'supplier_code': supplier_code,
                    'supplier_name': supplier_name
                })
            imp = Imports.objects.get(import_id=import_id)
            form = ImportsForm(instance=imp)
            supplier_code = imp.supplier.supplier_code
            supplier_name = f"{imp.supplier.legal_name} ({imp.supplier.supplier_code})"
            imports = Imports.objects.filter(supplier__supplier_code=supplier_code).select_related('supplier')
            return render(request, 'import_edit.html', {
                'form': form,
                'imp': imp,
                'supplier_code': supplier_code,
                'supplier_name': supplier_name,
                'imports': imports
            })

        elif 'update' in request.POST:
            import_id = request.POST.get('import_id')
            supplier_code = request.POST.get('supplier_code', '').strip()
            if not import_id:
                supplier_name = ''
                if supplier_code:
                    try:
                        supplier = Suppliers.objects.get(supplier_code=supplier_code)
                        supplier_name = f"{supplier.legal_name} ({supplier.supplier_code})"
                    except Suppliers.DoesNotExist:
                        supplier_name = ''
                return render(request, 'import_edit.html', {
                    'error': 'Invalid import ID.',
                    'imports': Imports.objects.all().select_related('supplier'),
                    'supplier_code': supplier_code,
                    'supplier_name': supplier_name
                })
            imp = Imports.objects.get(import_id=import_id)
            form = ImportsForm(request.POST, instance=imp)
            if form.is_valid():
                updated_imp = form.save()
                form = ImportsForm(instance=updated_imp)
                supplier_code = updated_imp.supplier.supplier_code
                supplier_name = f"{updated_imp.supplier.legal_name} ({updated_imp.supplier.supplier_code})"
                imports = Imports.objects.filter(supplier__supplier_code=supplier_code).select_related('supplier')
                return render(request, 'import_edit.html', {
                    'form': form,
                    'imp': updated_imp,
                    'message': 'Import updated successfully',
                    'supplier_code': supplier_code,
                    'supplier_name': supplier_name,
                    'imports': imports
                })
            return render(request, 'import_edit.html', {
                'form': form,
                'imp': imp,
                'supplier_code': imp.supplier.supplier_code,
                'supplier_name': f"{imp.supplier.legal_name} ({imp.supplier.supplier_code})",
                'imports': Imports.objects.filter(supplier__supplier_code=imp.supplier.supplier_code).select_related('supplier')
            })

    supplier_code = request.GET.get('supplier_code', '').strip()
    imports = Imports.objects.all().select_related('supplier')
    supplier_name = ''
    if supplier_code:
        imports = imports.filter(supplier__supplier_code__icontains=supplier_code)
        try:
            supplier = Suppliers.objects.get(supplier_code=supplier_code)
            supplier_name = f"{supplier.legal_name} ({supplier.supplier_code})"
        except Suppliers.DoesNotExist:
            supplier_name = ''

    return render(request, 'import_edit.html', {
        'imports': imports,
        'supplier_code': supplier_code,
        'supplier_name': supplier_name
    })

def import_list(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()[0]
        cursor.execute("SHOW search_path;")
        search_path = cursor.fetchone()[0]
        print(f"Current database: {current_db}, Search path: {search_path}")

        try:
            cursor.execute("SELECT import_id FROM t.imports LIMIT 1;")
            result = cursor.fetchone()
            print(f"Direct query result: {result}")
        except Exception as e:
            print(f"Direct query error: {e}")

    supplier_code = request.GET.get('supplier_code', '')
    imports = Imports.objects.filter(supplier__supplier_code__icontains=supplier_code) if supplier_code else Imports.objects.all()
    return render(request, 'import_list.html', {'imports': imports, 'supplier_code': supplier_code})

def import_success(request, message):
    return render(request, 'imports/import_success.html', {'message': message})

def supplier_code_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        print(f"Supplier code autocomplete term: {term}")
        suppliers = Suppliers.objects.filter(supplier_code__icontains=term)
        results = [
            {
                'id': supplier.supplier_code,
                'label': f"{supplier.legal_name} ({supplier.supplier_code})",
                'value': supplier.supplier_code
            }
            for supplier in suppliers
        ]
        print(f"Supplier code autocomplete results: {results}")
        return JsonResponse(results, safe=False)
    print("Supplier code autocomplete: No term provided")
    return JsonResponse([], safe=False)

def import_delete(request, import_id):
    if request.method == 'POST':
        imp = get_object_or_404(Imports, import_id=import_id)
        imp.delete()
        return redirect('imports:import_list')
    return redirect('imports:import_list')