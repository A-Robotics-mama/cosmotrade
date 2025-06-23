# devices/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Devices
from leasing.models import Leasing
from sales.models import TradeMargin, SalesInvoice
from imports.models import Imports
from purchases.models import Purchases
from rent.models import Rent
from suppliers.models import Suppliers
from customers.models import Customers

def devices_edit(request):
    if request.method == 'POST':
        if 'edit' in request.POST:
            device_id = request.POST.get('device_id')
            if not device_id:
                return render(request, 'devices/devices_edit.html', {
                    'error': 'Please select a device to edit.',
                    'devices': Devices.objects.all().select_related('supplier_id', 'customer_id'),
                    'supplier_code': request.GET.get('supplier_code', ''),
                    'serial_number': request.GET.get('serial_number', ''),
                    'customer_name': request.GET.get('customer_name', '')
                })
            device = Devices.objects.get(id=device_id)
            return render(request, 'devices/devices_edit.html', {'device': device})

        elif 'update' in request.POST:
            device_id = request.POST.get('device_id')
            if not device_id:
                return render(request, 'devices/devices_edit.html', {
                    'error': 'Invalid device ID.',
                    'devices': Devices.objects.all().select_related('supplier_id', 'customer_id'),
                    'supplier_code': request.GET.get('supplier_code', ''),
                    'serial_number': request.GET.get('serial_number', ''),
                    'customer_name': request.GET.get('customer_name', '')
                })
            device = Devices.objects.get(id=device_id)
            device.supplier_id = Suppliers.objects.get(supplier_id=request.POST.get('supplier_id'))
            device.serial_number = request.POST.get('serial_number')
            device.purchase_date = request.POST.get('purchase_date')
            device.sale_date = request.POST.get('sale_date') if request.POST.get('sale_date') else None
            device.customer_id = Customers.objects.get(customer_id=request.POST.get('customer_id')) if request.POST.get('customer_id') else None
            device.installation_date = request.POST.get('installation_date') if request.POST.get('installation_date') else None
            device.notes = request.POST.get('notes')
            device.save()
            return render(request, 'devices/devices_edit.html', {
                'device': device,
                'message': 'Device updated successfully'
            })

    supplier_code = request.GET.get('supplier_code', '').strip()
    serial_number = request.GET.get('serial_number', '').strip()
    customer_name = request.GET.get('customer_name', '').strip()
    devices = Devices.objects.all().select_related('supplier_id', 'customer_id')
    if supplier_code:
        devices = devices.filter(supplier_id__supplier_code__icontains=supplier_code)
    if serial_number:
        devices = devices.filter(serial_number__icontains=serial_number)
    if customer_name:
        devices = devices.filter(customer_id__fullname__icontains=customer_name)
    return render(request, 'devices/devices_edit.html', {
        'devices': devices,
        'supplier_code': supplier_code,
        'serial_number': serial_number,
        'customer_name': customer_name
    })

def devices_list(request):
    supplier_code = request.GET.get('supplier_code', '').strip()
    serial_number = request.GET.get('serial_number', '').strip()
    customer_name = request.GET.get('customer_name', '').strip()
    devices = Devices.objects.all().select_related('supplier_id', 'customer_id')
    if supplier_code:
        devices = devices.filter(supplier_id__supplier_code__icontains=supplier_code)
    if serial_number:
        devices = devices.filter(serial_number__icontains=serial_number)
    if customer_name:
        devices = devices.filter(customer_id__fullname__icontains=customer_name)
    return render(request, 'devices/devices_list.html', {
        'devices': devices,
        'supplier_code': supplier_code,
        'serial_number': serial_number,
        'customer_name': customer_name
    })

def device_detail(request, device_id):
    device = Devices.objects.get(id=device_id)
    context = {
        'device': device,
        'services': device.services.all(),
        'part_replacements': device.part_replacements.all(),
        'monitorings': device.monitorings.all(),
    }
    return render(request, 'devices/device_detail.html', context)

def serial_number_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term', '').strip()
        print(f"Serial number autocomplete term: '{term}'")
        all_serials = Purchases.objects.filter(serial_number__isnull=False).values_list('serial_number', flat=True)
        used_serials = set(SalesInvoice.objects.filter(serial_number__isnull=False).values_list('serial_number', flat=True)) | \
                      set(Leasing.objects.filter(serial_number__isnull=False).values_list('serial_number', flat=True)) | \
                      set(Rent.objects.filter(serial_number__isnull=False).values_list('serial_number', flat=True))
        print(f"All serials: {list(all_serials)}")
        print(f"Used serials: {used_serials}")
        # Фильтруем серийные номера, если term задан, иначе возвращаем все доступные
        available_serials = [s for s in all_serials if s not in used_serials and (not term or term.lower() in s.lower())]
        print(f"Available serials after filtering with term '{term}': {available_serials}")
        results = [{'id': s, 'label': s, 'value': s} for s in available_serials]
        return JsonResponse(results, safe=False)
    print("Serial number autocomplete: No term provided")
    return JsonResponse([], safe=False)