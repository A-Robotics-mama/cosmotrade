# stock/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import F, ExpressionWrapper, IntegerField
from imports.models import Imports
from purchases.models import Purchases
from .models import Stock
from products.models import Products
from utils.stock import calculate_stock_price

# stock/views.py
def stock_list(request):
    product_name = request.GET.get('product_name', '')  # Меняем product_id на product_name
    product_input = request.GET.get('product_input', '')

    stocks = Stock.objects.annotate(
        balance=ExpressionWrapper(F('stock_in') - F('stock_out'), output_field=IntegerField())
    ).select_related('product', 'import_id')

    if product_name:
        stocks = stocks.filter(product__product_name__icontains=product_name)  # Фильтруем по имени продукта

    stock_data = []
    for stock in stocks:
        price = calculate_stock_price(stock.product_id, stock.import_id_id) if stock.product_id and stock.import_id_id else 0
        stock_data.append({
            'stock': stock,
            'stock_price': price,
        })

    print(f"Product Name: {product_name}, Stocks count: {stocks.count()}")
    return render(request, 'stock_list.html', {
        'stocks': stock_data,
        'product_name': product_name,  # Передаём product_name вместо product_id
        'product_input': product_input,
    })

def stock_expiry_date(request):
    product_id = request.GET.get('product_id')
    import_id = request.GET.get('import_id')
    if product_id and import_id:
        try:
            stock = Stock.objects.get(product_id=product_id, import_id=import_id)
            expiry_date = stock.expiry_date.strftime('%Y-%m-%d') if stock.expiry_date else ''
            return JsonResponse({'expiry_date': expiry_date})
        except Stock.DoesNotExist:
            return JsonResponse({'expiry_date': ''}, status=404)
    return JsonResponse({'expiry_date': ''}, status=400)

def purchase_details(request):
    product_id = request.GET.get('product_id')
    import_id = request.GET.get('import_id')
    if product_id and import_id:
        try:
            import_obj = Imports.objects.get(import_id=import_id)
            purchase = Purchases.objects.filter(
                product_id=product_id,
                invoice=import_obj.invoice
            ).order_by('-timestamp').first()
            if purchase:
                return JsonResponse({
                    'stock_price': float(calculate_stock_price(product_id, import_obj.import_id)),
                    'vat': float(purchase.vat or 0)
                })

            else:
                return JsonResponse({'stock_price': 0, 'vat': 0}, status=404)
        except Imports.DoesNotExist:
            return JsonResponse({'stock_price': 0, 'vat': 0}, status=404)
    return JsonResponse({'stock_price': 0, 'vat': 0}, status=400)

def stock_imports_for_product(request):
    product_id = request.GET.get('product_id')
    if product_id:
        try:
            stocks = Stock.objects.filter(product_id=product_id, import_id__isnull=False).select_related('import_id')
            imports = []
            for stock in stocks:
                if stock.import_id:
                    imports.append({
                        'value': stock.import_id.import_id,
                        'label': f"Import {stock.import_id.import_id} (Invoice: {stock.import_id.invoice}, Stock: {stock.stock_in - stock.stock_out})"
                    })
            print(f"Imports for product_id {product_id}: {imports}")
            return JsonResponse(imports, safe=False)
        except Exception as e:
            print(f"Error fetching imports for product_id {product_id}: {str(e)}")
            return JsonResponse([], safe=False)
    print(f"No product_id provided")
    return JsonResponse([], safe=False)