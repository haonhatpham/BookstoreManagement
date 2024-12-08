def cart_stats(cart):
    total_amount, total_quantity = 0, 0

    if cart:
        for c in cart.values():
            total_quantity += c['quantity']
            total_amount += c['quantity'] * c['unit_price']

    return {
        'total_amount': total_amount,
        'total_quantity': total_quantity
    }

# def handle_cart():
#     configuration = dao.get_configuration()
#     products = []
#     grand_total = 0
#     index = 0
#     quantity_total = 0
#     for item in session['cart']:
#         product = Book.query.filter_by(id=item['id']).first()
#         quantity = int(item['quantity'])
#         total = quantity * product.unit_price
#         grand_total += total
#
#         quantity_total += quantity
#
#         products.append({'id': product.id, 'name': product.name, 'unit_price': product.unit_price,
#                          'image_src': product.image_src, 'quantity': quantity, 'total': total, 'index': index})
#         index += 1
#     grand_total_plus_shipping = grand_total + configuration.quick_ship
#
#     return products, grand_total, grand_total_plus_shipping, quantity_total
#
#
