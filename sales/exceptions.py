# sales/exceptions.py

class SalesError(Exception):
    """Базовое исключение для ошибок в модуле продаж."""
    pass


class InsufficientStockError(SalesError):
    """Недостаточно товара на складе для выполнения продажи."""
    def __init__(self, product_name, required_qty, available_qty):
        self.product_name = product_name
        self.required_qty = required_qty
        self.available_qty = available_qty
        super().__init__(
            f"Недостаточно товара '{product_name}': требуется {required_qty}, доступно {available_qty}."
        )


class InvalidQuotationError(SalesError):
    """Котировка не найдена или недействительна."""
    def __init__(self, quotation_number):
        self.quotation_number = quotation_number
        super().__init__(f"Котировка с номером '{quotation_number}' не найдена или недействительна.")


class InvalidCustomerError(SalesError):
    """Указан несуществующий клиент."""
    def __init__(self, customer_id):
        self.customer_id = customer_id
        super().__init__(f"Клиент с ID '{customer_id}' не найден.")


class InvalidProductError(SalesError):
    """Указан несуществующий товар."""
    def __init__(self, product_id):
        self.product_id = product_id
        super().__init__(f"Товар с ID '{product_id}' не найден.")


class InvalidImportError(SalesError):
    """Указан несуществующий импорт."""
    def __init__(self, import_id):
        self.import_id = import_id
        super().__init__(f"Импорт с ID '{import_id}' не найден.")
