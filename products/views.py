# products/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models.functions import Lower
from django.db.models import ProtectedError
from .models import Products, Brands, ProductForms, ProductCategory
from suppliers.models import Suppliers

def product_list(request):
    products = Products.objects.all()

    # Фильтрация по названию
    name = request.GET.get('name', '')
    if name:
        products = products.annotate(lower_name=Lower('product_name')).filter(lower_name__icontains=name.lower())

    return render(request, 'product_list.html', {
        'products': products,
    })

def product_list_json(request):
    products = Products.objects.all()

    # Фильтрация по названию
    name = request.GET.get('name', '')
    if name:
        products = products.annotate(lower_name=Lower('product_name')).filter(lower_name__icontains=name.lower())
        # Исправляем отладочный print
        found_products = [[p.id, p.product_name] for p in products]
        print(f"Search term: '{name}', Found products: {found_products}")

    # Рендерим HTML-таблицу
    html = render_to_string('product_table.html', {'products': products}, request=request)
    return JsonResponse({'html': html})

def product_create(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        brand_id = request.POST.get('brand')
        supplier_id = request.POST.get('supplier')
        form_id = request.POST.get('form')
        category_id = request.POST.get('category')
        product_volume = request.POST.get('product_volume')
        manufacturer_code = request.POST.get('manufacturer_code')

        try:
            product = Products(
                product_name=product_name,
                brand_id=brand_id,
                supplier_id=supplier_id,
                form_id=form_id,
                category_id=category_id,
                product_volume=product_volume,
                manufacturer_code=manufacturer_code
            )
            product.save()
            messages.success(request, 'Product added successfully!')
            return redirect('products:product_list')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')

    brands = Brands.objects.all()
    suppliers = Suppliers.objects.all()
    forms = ProductForms.objects.all()
    categories = ProductCategory.objects.all()
    return render(request, 'product_form.html', {
        'brands': brands,
        'suppliers': suppliers,
        'forms': forms,
        'categories': categories,
    })

def product_edit(request, product_id):
    product = get_object_or_404(Products, id=product_id)

    if request.method == 'POST':
        if 'delete' in request.POST:
            try:
                product.delete()
                messages.success(request, 'Product deleted successfully.')
                return redirect('products:product_list')
            except ProtectedError:
                messages.error(request, 'Cannot delete this product because it is referenced elsewhere.')
                return redirect('products:product_edit', product_id=product.id)

        # Если это обновление
        product.product_name = request.POST.get('product_name')
        product.brand_id = request.POST.get('brand')
        product.supplier_id = request.POST.get('supplier')
        product.form_id = request.POST.get('form')
        product.category_id = request.POST.get('category')
        product.product_volume = request.POST.get('product_volume')
        product.manufacturer_code = request.POST.get('manufacturer_code')

        try:
            product.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('products:product_list')
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')

    brands = Brands.objects.all()
    suppliers = Suppliers.objects.all()
    forms = ProductForms.objects.all()
    categories = ProductCategory.objects.all()

    return render(request, 'product_edit.html', {
        'product': product,
        'brands': brands,
        'suppliers': suppliers,
        'forms': forms,
        'categories': categories,
    })

def product_autocomplete(request):
    if 'term' in request.GET:
        term = request.GET.get('term')
        supplier_id = request.GET.get('supplier_id', '')
        print(f"Product autocomplete term: {term}, supplier_id: {supplier_id}")
        
        available_suppliers = [int(supplier_id)] if supplier_id else list(Suppliers.objects.values_list('supplier_id', flat=True))
        
        products = Products.objects.filter(
            product_name__icontains=term,
            supplier_id__in=available_suppliers,
        ).distinct()

        results = [
            {
                'id': product.id,
                'label': product.product_name,
                'value': product.product_name
            }
            for product in products
        ]
        print(f"Product autocomplete results: {results}")
        return JsonResponse(results, safe=False)