# base/views.py
from django.http import JsonResponse
from django.shortcuts import render
from suppliers.models import Suppliers
from imports.models import Imports
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import logging
from base.models import Countries
from django.db.models import Q

logger = logging.getLogger(__name__)

def dashboard(request):
    return render(request, 'base.html')

def supplier_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        suppliers = Suppliers.objects.filter(legal_name__icontains=term) | Suppliers.objects.filter(supplier_code__icontains=term)
        results = [
            {
                'id': supplier.supplier_id,
                'label': f"{supplier.legal_name} ({supplier.supplier_code})",
                'value': supplier.supplier_id
            }
            for supplier in suppliers[:10]  # Ограничиваем количество результатов
        ]
        return JsonResponse(results, safe=False)
    return JsonResponse([], safe=False)

def invoices_autocomplete(request):
    if 'term' in request.GET and 'supplier_id' in request.GET:
        term = request.GET.get('term')
        supplier_id = request.GET.get('supplier_id')
        imports = Imports.objects.filter(
            supplier_id=supplier_id,
            invoice__icontains=term
        ).select_related('supplier')[:10]  # Ограничиваем количество результатов
        results = [
            {
                'id': imp.import_id,
                'label': f"Import {imp.import_id} {imp.invoice}",
                'costs_per_euro': float(imp.costs_per_euro or 0),
                'vat': float(imp.vat or 0),
                'invoice_eur': float(imp.invoice_eur or 0),
                'value': imp.invoice
            }
            for imp in imports
        ]
        return JsonResponse(results, safe=False)
    return JsonResponse([], safe=False)

def country_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        print(f"Country autocomplete term: {term}")
        qs = Countries.objects.filter(
            Q(country_iso__icontains=term) | Q(country_name__icontains=term)
        )
        countries = [
            {
                'id': item.country_iso,
                'label': f"{item.country_name} ({item.country_iso})",
                'value': item.country_iso,
                'country_code': item.country_code  # Добавляем country_code для автозаполнения
            }
            for item in qs
        ]
        print(f"Country autocomplete results: {countries}")
        return JsonResponse(countries, safe=False)
    print("Country autocomplete: No term provided")
    return JsonResponse([], safe=False)

@csrf_exempt
def log_debug(request):
    if request.method == 'POST':
        msg = request.POST.get('message', '')
        logger.debug(f"[CLIENT DEBUG] {msg}")
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def log_error(request):
    if request.method == 'POST':
        msg = request.POST.get('message', '')
        logger.error(f"[CLIENT ERROR] {msg}")
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Invalid request'}, status=400)    